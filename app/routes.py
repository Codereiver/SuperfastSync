"""Route handlers for SuperfastSync."""

import os
from pathlib import Path
from flask import (
    Blueprint,
    render_template,
    request,
    send_from_directory,
    jsonify,
    abort,
    Response,
)
from werkzeug.utils import secure_filename

from .benchmarks import BenchmarkTracker, TransferTimer
from .synthetic import (
    SYNTHETIC_FILES,
    is_synthetic_file,
    get_synthetic_file,
    create_synthetic_file_stream,
)

# Create blueprint
bp = Blueprint("main", __name__)

# Storage directory - IMPORTANT: All file operations must be within this directory
STORAGE_DIR = Path("storage").absolute()
STORAGE_DIR.mkdir(exist_ok=True)

# Initialize benchmark tracker
tracker = BenchmarkTracker()


def get_client_ip() -> str:
    """Get the real client IP address, accounting for proxies."""
    # Check for X-Real-IP header (set by nginx)
    if request.headers.get("X-Real-IP"):
        return request.headers.get("X-Real-IP")
    # Check for X-Forwarded-For header
    if request.headers.get("X-Forwarded-For"):
        return request.headers.get("X-Forwarded-For").split(",")[0].strip()
    # Fall back to direct connection
    return request.remote_addr


def is_safe_path(filename: str) -> bool:
    """
    Check if a filename is safe (no path traversal).

    Args:
        filename: The filename to check

    Returns:
        True if safe, False otherwise
    """
    # Secure the filename (removes .. and other dangerous characters)
    safe_name = secure_filename(filename)

    # Ensure the secured filename is not empty and matches the original
    if not safe_name or safe_name != filename:
        return False

    # Ensure the resolved path is within STORAGE_DIR
    target_path = (STORAGE_DIR / safe_name).resolve()
    return target_path.parent == STORAGE_DIR


@bp.route("/")
def index():
    """Main page - file browser and upload interface."""
    # Add synthetic test files first
    files = []
    for synthetic_file in SYNTHETIC_FILES:
        files.append(
            {
                "name": synthetic_file.name,
                "size": synthetic_file.size_bytes,
                "modified": 0,  # Always at the top
                "synthetic": True,
            }
        )

    # List all real files in storage directory
    for file_path in STORAGE_DIR.iterdir():
        if file_path.is_file():
            stat = file_path.stat()
            files.append(
                {
                    "name": file_path.name,
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "synthetic": False,
                }
            )

    # Sort: synthetic files first, then by modification time
    files.sort(key=lambda x: (not x.get("synthetic", False), -x["modified"]))

    return render_template("index.html", files=files)


@bp.route("/upload", methods=["POST"])
def upload_file():
    """Handle file upload."""
    import sys

    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    # Secure the filename
    filename = secure_filename(file.filename)
    if not filename:
        return jsonify({"error": "Invalid filename"}), 400

    # Ensure path safety
    if not is_safe_path(filename):
        return jsonify({"error": "Invalid filename"}), 400

    file_path = STORAGE_DIR / filename
    client_ip = get_client_ip()

    try:
        # Save file and time the operation
        with TransferTimer() as timer:
            file.save(file_path)

        # Get file size
        file_size = file_path.stat().st_size

        # Debug logging
        print(f"[UPLOAD] File saved: {file_path}, size: {file_size}", file=sys.stderr)
        print(f"[UPLOAD] Tracker data file: {tracker.data_file}", file=sys.stderr)

        # Record benchmark
        benchmark = tracker.record_transfer(
            operation="upload",
            filename=filename,
            file_size=file_size,
            duration=timer.duration,
            client_ip=client_ip,
        )

        print(f"[UPLOAD] Benchmark recorded: {benchmark}", file=sys.stderr)

        return jsonify(
            {
                "success": True,
                "filename": filename,
                "size": file_size,
                "duration": timer.duration,
                "speed_mbps": benchmark["avg_speed_mbps"],
            }
        )
    except Exception as e:
        print(f"[UPLOAD ERROR] {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@bp.route("/download/<filename>")
def download_file(filename):
    """Handle file download (supports both real and synthetic files)."""
    # Secure the filename
    filename = secure_filename(filename)
    if not filename:
        abort(404)

    client_ip = get_client_ip()

    # Check if it's a synthetic file
    if is_synthetic_file(filename):
        synthetic_file = get_synthetic_file(filename)
        file_size = synthetic_file.size_bytes

        # Start timing
        start_time = TransferTimer()
        start_time.__enter__()

        # Create streaming response with synthetic data
        def generate():
            # Generate and yield the synthetic data
            for chunk in create_synthetic_file_stream(filename):
                yield chunk

        response = Response(generate(), mimetype="application/octet-stream")
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        response.headers["Content-Length"] = str(file_size)

        # Record benchmark (approximate timing since we can't track actual download completion)
        start_time.__exit__(None, None, None)
        tracker.record_transfer(
            operation="download",
            filename=filename,
            file_size=file_size,
            duration=start_time.duration,
            client_ip=client_ip,
        )

        return response

    # Handle real file download
    # Ensure path safety
    if not is_safe_path(filename):
        abort(404)

    file_path = STORAGE_DIR / filename

    if not file_path.exists() or not file_path.is_file():
        abort(404)

    file_size = file_path.stat().st_size

    # Note: We record the benchmark before sending to capture timing
    # In a production app, you might want to stream and time more accurately
    start_time = TransferTimer()
    start_time.__enter__()

    # Send file
    response = send_from_directory(
        STORAGE_DIR, filename, as_attachment=True, download_name=filename
    )

    # Record benchmark (approximate timing)
    start_time.__exit__(None, None, None)
    tracker.record_transfer(
        operation="download",
        filename=filename,
        file_size=file_size,
        duration=start_time.duration,
        client_ip=client_ip,
    )

    return response


@bp.route("/delete/<filename>", methods=["DELETE"])
def delete_file(filename):
    """Handle file deletion (synthetic files cannot be deleted)."""
    # Secure the filename
    filename = secure_filename(filename)
    if not filename:
        return jsonify({"error": "Invalid filename"}), 400

    # Prevent deletion of synthetic files
    if is_synthetic_file(filename):
        return jsonify({"error": "Cannot delete synthetic test files"}), 403

    # Ensure path safety
    if not is_safe_path(filename):
        return jsonify({"error": "Invalid filename"}), 400

    file_path = STORAGE_DIR / filename

    if not file_path.exists() or not file_path.is_file():
        return jsonify({"error": "File not found"}), 404

    try:
        file_path.unlink()
        return jsonify({"success": True, "filename": filename})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/dashboard")
def dashboard():
    """Dashboard page - view benchmark history."""
    benchmarks = tracker.get_all_benchmarks()
    return render_template("dashboard.html", benchmarks=benchmarks)


@bp.route("/api/benchmarks")
def api_benchmarks():
    """API endpoint for benchmark data."""
    limit = request.args.get("limit", default=50, type=int)
    benchmarks = tracker.get_recent_benchmarks(limit)
    return jsonify(benchmarks)

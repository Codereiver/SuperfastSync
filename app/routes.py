"""Route handlers for SuperfastSync."""

import os
from pathlib import Path
from functools import wraps
from flask import (
    Blueprint,
    render_template,
    request,
    send_from_directory,
    jsonify,
    abort,
    Response,
    session,
    redirect,
    url_for,
    current_app,
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


def login_required(f):
    """Decorator to require authentication for routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("main.login"))
        return f(*args, **kwargs)
    return decorated_function


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


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Handle user login."""
    if request.method == "POST":
        import secrets

        username = request.form.get("username", "")
        password = request.form.get("password", "")

        auth_username = current_app.config.get("AUTH_USERNAME")
        auth_password = current_app.config.get("AUTH_PASSWORD")

        # Use constant-time comparison to prevent timing attacks
        username_valid = secrets.compare_digest(username, auth_username)
        password_valid = secrets.compare_digest(password, auth_password)

        if username_valid and password_valid:
            session["logged_in"] = True
            session.permanent = True  # Respect PERMANENT_SESSION_LIFETIME
            return redirect(url_for("main.index"))
        else:
            return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")


@bp.route("/logout")
def logout():
    """Handle user logout."""
    session.pop("logged_in", None)
    return redirect(url_for("main.login"))


@bp.route("/")
@login_required
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
@login_required
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
@login_required
def download_file(filename):
    """Handle file download (supports both real and synthetic files)."""
    import sys

    # Secure the filename
    filename = secure_filename(filename)
    if not filename:
        abort(404)

    client_ip = get_client_ip()

    try:
        # Check if it's a synthetic file
        if is_synthetic_file(filename):
            synthetic_file = get_synthetic_file(filename)
            file_size = synthetic_file.size_bytes

            print(f"[DOWNLOAD] Synthetic file: {filename}, size: {file_size}", file=sys.stderr)
            print(f"[DOWNLOAD] Client IP: {client_ip}", file=sys.stderr)

            # Create streaming response with synthetic data and track timing
            def generate_with_tracking():
                import time
                start = time.time()

                # Generate and yield the synthetic data
                for chunk in create_synthetic_file_stream(filename):
                    yield chunk

                # After all data is sent, record the benchmark
                duration = time.time() - start
                print(f"[DOWNLOAD] Transfer completed in {duration:.3f}s", file=sys.stderr)
                print(f"[DOWNLOAD] Tracker data file: {tracker.data_file}", file=sys.stderr)

                benchmark = tracker.record_transfer(
                    operation="download",
                    filename=filename,
                    file_size=file_size,
                    duration=duration,
                    client_ip=client_ip,
                )

                print(f"[DOWNLOAD] Benchmark recorded: {benchmark}", file=sys.stderr)

            response = Response(generate_with_tracking(), mimetype="application/octet-stream")
            response.headers["Content-Disposition"] = f"attachment; filename={filename}"
            response.headers["Content-Length"] = str(file_size)

            # Prevent browser caching to ensure accurate benchmarking
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

            return response

        # Handle real file download
        # Ensure path safety
        if not is_safe_path(filename):
            abort(404)

        file_path = STORAGE_DIR / filename

        if not file_path.exists() or not file_path.is_file():
            abort(404)

        file_size = file_path.stat().st_size

        print(f"[DOWNLOAD] Real file: {file_path}, size: {file_size}", file=sys.stderr)
        print(f"[DOWNLOAD] Client IP: {client_ip}", file=sys.stderr)

        # Stream file with timing
        def generate_file_with_tracking():
            import time
            start = time.time()

            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(64 * 1024)  # 64KB chunks
                    if not chunk:
                        break
                    yield chunk

            # After all data is sent, record the benchmark
            duration = time.time() - start
            print(f"[DOWNLOAD] Transfer completed in {duration:.3f}s", file=sys.stderr)
            print(f"[DOWNLOAD] Tracker data file: {tracker.data_file}", file=sys.stderr)

            benchmark = tracker.record_transfer(
                operation="download",
                filename=filename,
                file_size=file_size,
                duration=duration,
                client_ip=client_ip,
            )

            print(f"[DOWNLOAD] Benchmark recorded: {benchmark}", file=sys.stderr)

        response = Response(generate_file_with_tracking(), mimetype="application/octet-stream")
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        response.headers["Content-Length"] = str(file_size)

        # Prevent browser caching to ensure accurate benchmarking
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

        return response
    except Exception as e:
        print(f"[DOWNLOAD ERROR] {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        abort(500)


@bp.route("/delete/<filename>", methods=["DELETE"])
@login_required
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
@login_required
def dashboard():
    """Dashboard page - view benchmark history."""
    benchmarks = tracker.get_all_benchmarks()
    return render_template("dashboard.html", benchmarks=benchmarks)


@bp.route("/api/benchmarks")
@login_required
def api_benchmarks():
    """API endpoint for benchmark data."""
    limit = request.args.get("limit", default=50, type=int)
    benchmarks = tracker.get_recent_benchmarks(limit)
    return jsonify(benchmarks)


@bp.route("/clear-benchmarks", methods=["POST"])
@login_required
def clear_benchmarks():
    """Clear all benchmark data."""
    try:
        tracker.data_file.write_text("[]")
        return jsonify({"success": True, "message": "All benchmarks cleared"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

"""Flask server for SuperfastSync."""

from flask import Flask
from .routes import bp


def create_app():
    """Create and configure the Flask application."""
    import os
    import sys
    import tempfile
    from pathlib import Path
    from datetime import timedelta

    app = Flask(__name__)

    # Debug mode configuration
    debug_mode = os.environ.get("DEBUG", "false").lower() in ("true", "1", "yes")
    app.debug = debug_mode

    # Configuration
    app.config["MAX_CONTENT_LENGTH"] = None  # No file size limit

    # SECRET_KEY - CRITICAL SECURITY SETTING
    secret_key = os.environ.get("SECRET_KEY")
    if not secret_key:
        if not debug_mode:
            print("SECURITY ERROR: SECRET_KEY environment variable must be set in production!", file=sys.stderr)
            print("Generate one with: python3 -c 'import secrets; print(secrets.token_hex(32))'", file=sys.stderr)
            sys.exit(1)
        secret_key = "dev-secret-key-INSECURE-development-only"
        print("WARNING: Using insecure default SECRET_KEY (development mode only)", file=sys.stderr)

    app.config["SECRET_KEY"] = secret_key

    # Session security configuration
    app.config["SESSION_COOKIE_SECURE"] = not debug_mode  # HTTPS only in production
    app.config["SESSION_COOKIE_HTTPONLY"] = True  # Prevent JavaScript access
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"  # CSRF protection
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=24)  # Session timeout

    # Authentication configuration
    app.config["AUTH_USERNAME"] = os.environ.get("AUTH_USERNAME", "admin")
    app.config["AUTH_PASSWORD"] = os.environ.get("AUTH_PASSWORD", "admin")

    if debug_mode and (app.config["AUTH_USERNAME"] == "admin" or app.config["AUTH_PASSWORD"] == "admin"):
        print("WARNING: Using default credentials (admin/admin) - change in production!", file=sys.stderr)

    # Use a custom temp directory for uploads instead of /tmp
    # This avoids disk quota issues on tmpfs filesystems
    upload_temp_dir = Path("upload_temp").absolute()
    upload_temp_dir.mkdir(exist_ok=True)
    tempfile.tempdir = str(upload_temp_dir)
    os.environ["TMPDIR"] = str(upload_temp_dir)

    # Register blueprint
    app.register_blueprint(bp)

    return app


def main():
    """Run the development server."""
    import os
    app = create_app()
    port = int(os.environ.get("PORT", 5001))
    # Debug mode is now controlled by the DEBUG environment variable in create_app()
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()

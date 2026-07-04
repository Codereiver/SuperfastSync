"""Flask server for SuperfastSync."""

from flask import Flask
from .routes import bp


def create_app():
    """Create and configure the Flask application."""
    import os
    import tempfile
    from pathlib import Path

    app = Flask(__name__)

    # Configuration
    app.config["MAX_CONTENT_LENGTH"] = None  # No file size limit
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

    # Authentication configuration
    app.config["AUTH_USERNAME"] = os.environ.get("AUTH_USERNAME", "admin")
    app.config["AUTH_PASSWORD"] = os.environ.get("AUTH_PASSWORD", "admin")

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
    app.run(host="0.0.0.0", port=port, debug=True)


if __name__ == "__main__":
    main()

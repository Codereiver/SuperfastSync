"""Flask server for SuperfastSync."""

from flask import Flask
from .routes import bp


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Configuration
    app.config["MAX_CONTENT_LENGTH"] = None  # No file size limit
    app.config["SECRET_KEY"] = "dev-secret-key-change-in-production"

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

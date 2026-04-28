"""
app.py
------
Main Flask application entry point for the Food Wastage Management System.
Registers blueprints, configures extensions, and initializes the database.
"""

import os

# Load .env file so GMAIL_APP_PASSWORD etc. are available via os.environ
_env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _key, _val = _line.split("=", 1)
                os.environ.setdefault(_key.strip(), _val.strip())

from flask import Flask
from flask_login import LoginManager

from database.models import db, User
from routes.auth   import auth_bp
from routes.food   import food_bp
from routes.main   import main_bp



def create_app() -> Flask:
    """Application factory – creates and configures the Flask app."""
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # ── Configuration ────────────────────────────────────────────────────────
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-me-in-production")
    # Use absolute path so the DB file is always created inside the project folder
    db_path = os.path.join(os.path.dirname(__file__), "database", "food_waste.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # ── Extensions ───────────────────────────────────────────────────────────
    db.init_app(app)

    login_manager = LoginManager(app)
    login_manager.login_view = "auth.login"           # redirect here if not logged in
    login_manager.login_message_category = "warning"

    @login_manager.user_loader
    def load_user(user_id: str):
        """Flask-Login hook: loads user from session by primary key."""
        return User.query.get(int(user_id))

    # ── Blueprints ────────────────────────────────────────────────────────────
    app.register_blueprint(main_bp)          # home page
    app.register_blueprint(auth_bp,  url_prefix="/auth")
    app.register_blueprint(food_bp,  url_prefix="/food")

    # ── Database initialisation ───────────────────────────────────────────────
    with app.app_context():
        db.create_all()

    return app


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    application = create_app()
    application.run(debug=True, host="0.0.0.0", port=5050)

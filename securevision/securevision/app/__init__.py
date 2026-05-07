"""
SecureVision - Production-Ready Security Monitoring Application
Flask Application Factory
"""

import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(config_name: str = "default") -> Flask:
    """Application factory pattern."""
    app = Flask(__name__, instance_relative_config=True)

    # ── Load configuration ──────────────────────────────────────────────────
    from app.config import config_map
    app.config.from_object(config_map[config_name])

    # Load instance/config.py (secrets, never committed to VCS)
    app.config.from_pyfile("config.py", silent=True)

    # ── Ensure instance folder exists ───────────────────────────────────────
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(os.path.join(app.root_path, "..", "logs"), exist_ok=True)

    # ── Initialize extensions ───────────────────────────────────────────────
    db.init_app(app)
    csrf.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "info"

    # ── Register blueprints ─────────────────────────────────────────────────
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.camera import camera_bp
    from app.routes.admin import admin_bp
    from app.routes.errors import errors_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(camera_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(errors_bp)

    # ── Create database tables ──────────────────────────────────────────────
    with app.app_context():
        db.create_all()
        _seed_default_admin(app)

    # ── Configure structured logging ────────────────────────────────────────
    if not app.debug:
        _configure_logging(app)

    return app


def _seed_default_admin(app: Flask) -> None:
    """Create default admin account if none exists."""
    from app.models.user import User
    if not User.query.filter_by(role="admin").first():
        admin = User.create_admin(
            username=app.config.get("DEFAULT_ADMIN_USERNAME", "admin"),
            email=app.config.get("DEFAULT_ADMIN_EMAIL", "admin@securevision.local"),
            password=app.config.get("DEFAULT_ADMIN_PASSWORD", "ChangeMe123!"),
        )
        db.session.add(admin)
        db.session.commit()
        app.logger.warning(
            "Default admin created. Change DEFAULT_ADMIN_PASSWORD immediately!"
        )


def _configure_logging(app: Flask) -> None:
    """Rotating file handler for production logging."""
    log_path = os.path.join(app.root_path, "..", "logs", "securevision.log")
    handler = RotatingFileHandler(log_path, maxBytes=10_485_760, backupCount=5)
    handler.setFormatter(
        logging.Formatter(
            "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
        )
    )
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info("SecureVision startup")

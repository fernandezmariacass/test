"""
app/config.py — Configuration Classes
⚠️  SECURITY LOGIC — Do NOT commit secrets here.
    Override in instance/config.py (git-ignored).
"""

import os
from datetime import timedelta


class BaseConfig:
    # ── Flask core ──────────────────────────────────────────────────────────
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-CHANGE-IN-PRODUCTION")
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600

    # ── Database ────────────────────────────────────────────────────────────
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # ── Session ─────────────────────────────────────────────────────────────
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # ── Rate limiting (requests per minute) ────────────────────────────────
    LOGIN_RATE_LIMIT = int(os.environ.get("LOGIN_RATE_LIMIT", 5))

    # ── Camera ─────────────────────────────────────────────────────────────
    CAMERA_SOURCE = os.environ.get("CAMERA_SOURCE", "0")   # 0 = webcam, or RTSP URL
    CAMERA_FPS = int(os.environ.get("CAMERA_FPS", 15))
    CAMERA_WIDTH = int(os.environ.get("CAMERA_WIDTH", 1280))
    CAMERA_HEIGHT = int(os.environ.get("CAMERA_HEIGHT", 720))

    # ── Allow-list ─────────────────────────────────────────────────────────
    # ⚠️  SECURITY LOGIC: Comma-separated trusted IPs; override in instance/config.py
    ALLOWED_IPS_RAW = os.environ.get("ALLOWED_IPS", "127.0.0.1,::1")

    @property
    def ALLOWED_IPS(self):  # noqa: N802
        return {ip.strip() for ip in self.ALLOWED_IPS_RAW.split(",")}

    # ── Notification: Email (Resend / SMTP) ────────────────────────────────
    NOTIFY_EMAIL_ENABLED = os.environ.get("NOTIFY_EMAIL_ENABLED", "false").lower() == "true"
    RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
    NOTIFY_FROM_EMAIL = os.environ.get("NOTIFY_FROM_EMAIL", "alerts@securevision.local")
    NOTIFY_TO_EMAIL = os.environ.get("NOTIFY_TO_EMAIL", "admin@example.com")

    # Fallback SMTP (used when Resend key is absent)
    SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
    SMTP_USER = os.environ.get("SMTP_USER", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")  # ⚠️  NEVER commit

    # ── Notification: Telegram ─────────────────────────────────────────────
    NOTIFY_TELEGRAM_ENABLED = os.environ.get("NOTIFY_TELEGRAM_ENABLED", "false").lower() == "true"
    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")   # ⚠️  NEVER commit
    TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

    # ── Default admin seed (override immediately after first run) ───────────
    DEFAULT_ADMIN_USERNAME = os.environ.get("DEFAULT_ADMIN_USERNAME", "admin")
    DEFAULT_ADMIN_EMAIL = os.environ.get("DEFAULT_ADMIN_EMAIL", "admin@securevision.local")
    DEFAULT_ADMIN_PASSWORD = os.environ.get("DEFAULT_ADMIN_PASSWORD", "ChangeMe123!")  # ⚠️


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///dev.db"
    )
    SESSION_COOKIE_SECURE = False


class ProductionConfig(BaseConfig):
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///prod.db"
    )
    SESSION_COOKIE_SECURE = True   # Requires HTTPS
    WTF_CSRF_SSL_STRICT = True

    @classmethod
    def init_app(cls, app):
        BaseConfig.init_app(app)
        # Log to stderr in production
        import logging
        from logging import StreamHandler
        handler = StreamHandler()
        handler.setLevel(logging.INFO)
        app.logger.addHandler(handler)


class TestingConfig(BaseConfig):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}

from app.routes.auth import auth_bp
from app.routes.dashboard import dashboard_bp
from app.routes.camera import camera_bp
from app.routes.admin import admin_bp
from app.routes.errors import errors_bp

__all__ = ["auth_bp", "dashboard_bp", "camera_bp", "admin_bp", "errors_bp"]

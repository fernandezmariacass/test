"""
app/routes/dashboard.py — Main dashboard blueprint
"""

from flask import Blueprint, render_template
from flask_login import login_required

from app.models.user import LoginLog
from app.services.camera import camera_manager
from app.services.security import get_client_ip

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def index():
    recent_logs = (
        LoginLog.query.order_by(LoginLog.timestamp.desc()).limit(10).all()
    )
    return render_template(
        "dashboard/index.html",
        recent_logs=recent_logs,
        camera_active=camera_manager.is_active,
        client_ip=get_client_ip(),
    )

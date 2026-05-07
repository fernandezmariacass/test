"""
app/routes/camera.py — MJPEG camera streaming endpoints
"""

from flask import Blueprint, Response, jsonify, render_template
from flask_login import login_required

from app.services.camera import camera_manager
from app.services.security import require_role

camera_bp = Blueprint("camera", __name__, url_prefix="/camera")


@camera_bp.route("/feed")
@login_required
def feed():
    """MJPEG live stream — consumed by <img src='/camera/feed'>."""
    if not camera_manager.is_active:
        return Response(b"Camera unavailable", status=503, mimetype="text/plain")

    return Response(
        camera_manager.generate_mjpeg(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@camera_bp.route("/snapshot")
@login_required
def snapshot():
    """Return single JPEG frame."""
    frame = camera_manager.snapshot_jpeg()
    if frame is None:
        return Response(b"No frame", status=503, mimetype="text/plain")
    return Response(frame, mimetype="image/jpeg")


@camera_bp.route("/status")
@login_required
def status():
    return jsonify({"active": camera_manager.is_active})


@camera_bp.route("/view")
@login_required
def view():
    return render_template("dashboard/camera.html", camera_active=camera_manager.is_active)

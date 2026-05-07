"""
app/services/camera.py — OpenCV CCTV / webcam integration
Thread-safe singleton camera manager with MJPEG streaming.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Generator, Optional

logger = logging.getLogger(__name__)

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.warning("opencv-python not installed — camera feed disabled.")


class CameraManager:
    """
    Thread-safe wrapper around cv2.VideoCapture.
    Supports webcam index (int) or RTSP/HTTP stream URL (str).
    """

    def __init__(self) -> None:
        self._cap: Optional["cv2.VideoCapture"] = None
        self._lock = threading.Lock()
        self._running = False
        self._source: str | int = 0
        self._fps: int = 15
        self._latest_frame: Optional[bytes] = None
        self._thread: Optional[threading.Thread] = None

    # ── Lifecycle ──────────────────────────────────────────────────────────

    def start(self, source: str | int, fps: int = 15, width: int = 1280, height: int = 720) -> bool:
        if not CV2_AVAILABLE:
            return False
        self._source = source
        self._fps = fps
        try:
            src = int(source) if str(source).isdigit() else source
            cap = cv2.VideoCapture(src)
            if not cap.isOpened():
                logger.error("Cannot open camera source: %s", source)
                return False
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            self._cap = cap
            self._running = True
            self._thread = threading.Thread(target=self._capture_loop, daemon=True)
            self._thread.start()
            logger.info("Camera started: source=%s %dx%d @ %dfps", source, width, height, fps)
            return True
        except Exception as exc:
            logger.error("Camera start failed: %s", exc)
            return False

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)
        with self._lock:
            if self._cap:
                self._cap.release()
                self._cap = None
        logger.info("Camera stopped")

    # ── Capture loop (background thread) ───────────────────────────────────

    def _capture_loop(self) -> None:
        interval = 1.0 / self._fps
        while self._running:
            t0 = time.monotonic()
            with self._lock:
                if not self._cap:
                    break
                ret, frame = self._cap.read()
            if ret:
                _, jpeg = cv2.imencode(
                    ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80]
                )
                self._latest_frame = jpeg.tobytes()
            else:
                logger.warning("Camera read failed — reconnecting…")
                time.sleep(2)
                with self._lock:
                    if self._cap:
                        self._cap.release()
                    src = int(self._source) if str(self._source).isdigit() else self._source
                    self._cap = cv2.VideoCapture(src)
            elapsed = time.monotonic() - t0
            sleep_time = interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    # ── MJPEG generator ────────────────────────────────────────────────────

    def generate_mjpeg(self) -> Generator[bytes, None, None]:
        """
        Yields MJPEG boundary frames for use with Flask's streaming response.
        Usage:  Response(camera.generate_mjpeg(), mimetype='multipart/x-mixed-replace; boundary=frame')
        """
        while True:
            frame = self._latest_frame
            if frame is None:
                time.sleep(0.1)
                continue
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
            )
            time.sleep(1.0 / self._fps)

    @property
    def is_active(self) -> bool:
        return self._running and self._cap is not None

    def snapshot_jpeg(self) -> Optional[bytes]:
        """Return the latest JPEG frame bytes (for single-frame endpoint)."""
        return self._latest_frame


# ── App-level singleton ────────────────────────────────────────────────────

camera_manager = CameraManager()


def init_camera(app) -> None:
    """Call from app factory after config is loaded."""
    source = app.config.get("CAMERA_SOURCE", "0")
    fps = int(app.config.get("CAMERA_FPS", 15))
    width = int(app.config.get("CAMERA_WIDTH", 1280))
    height = int(app.config.get("CAMERA_HEIGHT", 720))
    ok = camera_manager.start(source=source, fps=fps, width=width, height=height)
    if not ok:
        app.logger.warning("Camera unavailable — live feed disabled")

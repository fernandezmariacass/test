"""
app/services/notifications.py
⚠️  SECURITY LOGIC — Admin alert system.
    API keys / credentials must live in env vars or instance/config.py only.
"""

from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from threading import Thread
from typing import Optional

import requests
from flask import current_app

logger = logging.getLogger(__name__)


# ── Internal dispatcher ────────────────────────────────────────────────────

def _fire_async(fn, *args, **kwargs) -> None:
    """Run notification in a background thread so it never blocks a request."""
    t = Thread(target=fn, args=args, kwargs=kwargs, daemon=True)
    t.start()


# ── Public alert functions ─────────────────────────────────────────────────

def notify_unauthorized_ip(ip: str) -> None:
    subject = f"[SecureVision] 🚨 Unauthorized IP access attempt: {ip}"
    body = (
        f"An access attempt was made from an IP address not on the allow-list.\n\n"
        f"  IP Address : {ip}\n"
        f"  Action     : Request blocked (HTTP 403)\n\n"
        f"If this IP should be allowed, add it to ALLOWED_IPS in your environment.\n"
        f"If this looks malicious, consider blocking it at the firewall level."
    )
    _fire_async(_send_all, subject, body)


def notify_failed_login(username: str, ip: str, reason: str) -> None:
    subject = f"[SecureVision] ⚠️  Failed login attempt for '{username}'"
    body = (
        f"A login attempt failed.\n\n"
        f"  Username   : {username}\n"
        f"  IP Address : {ip}\n"
        f"  Reason     : {reason}\n\n"
        f"Review login logs at /admin/logs for more details."
    )
    _fire_async(_send_all, subject, body)


def notify_successful_login(username: str, ip: str) -> None:
    subject = f"[SecureVision] ✅ Successful login: '{username}'"
    body = (
        f"A user has logged in successfully.\n\n"
        f"  Username   : {username}\n"
        f"  IP Address : {ip}\n"
    )
    _fire_async(_send_all, subject, body)


# ── Dispatch to all enabled channels ──────────────────────────────────────

def _send_all(subject: str, body: str) -> None:
    app = current_app._get_current_object()
    with app.app_context():
        if app.config.get("NOTIFY_EMAIL_ENABLED"):
            _send_email(app, subject, body)
        if app.config.get("NOTIFY_TELEGRAM_ENABLED"):
            _send_telegram(app, f"{subject}\n\n{body}")


# ── Email via Resend API ───────────────────────────────────────────────────

def _send_email(app, subject: str, body: str) -> None:
    resend_key = app.config.get("RESEND_API_KEY", "")
    if resend_key:
        _send_via_resend(app, resend_key, subject, body)
    else:
        _send_via_smtp(app, subject, body)


def _send_via_resend(app, api_key: str, subject: str, body: str) -> None:
    """Send email using the Resend API (https://resend.com)."""
    try:
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "from": app.config["NOTIFY_FROM_EMAIL"],
                "to": [app.config["NOTIFY_TO_EMAIL"]],
                "subject": subject,
                "text": body,
            },
            timeout=10,
        )
        resp.raise_for_status()
        logger.info("Alert email sent via Resend (id=%s)", resp.json().get("id"))
    except Exception as exc:
        logger.error("Resend email failed: %s", exc)


def _send_via_smtp(app, subject: str, body: str) -> None:
    """Fallback: send email via SMTP (Gmail, etc.)."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = app.config["NOTIFY_FROM_EMAIL"]
        msg["To"] = app.config["NOTIFY_TO_EMAIL"]
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(app.config["SMTP_HOST"], app.config["SMTP_PORT"]) as server:
            server.ehlo()
            server.starttls()
            server.login(app.config["SMTP_USER"], app.config["SMTP_PASSWORD"])
            server.sendmail(
                app.config["NOTIFY_FROM_EMAIL"],
                app.config["NOTIFY_TO_EMAIL"],
                msg.as_string(),
            )
        logger.info("Alert email sent via SMTP")
    except Exception as exc:
        logger.error("SMTP email failed: %s", exc)


# ── Telegram Bot ───────────────────────────────────────────────────────────

def _send_telegram(app, message: str) -> None:
    """
    ⚠️  SECURITY LOGIC: Bot token in TELEGRAM_BOT_TOKEN env var only.
    """
    token = app.config.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = app.config.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        logger.warning("Telegram not configured — skipping notification")
        return
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"},
            timeout=10,
        )
        resp.raise_for_status()
        logger.info("Telegram alert sent")
    except Exception as exc:
        logger.error("Telegram notification failed: %s", exc)

"""
app/services/security.py
⚠️  SECURITY LOGIC — IP Allow-list enforcement & threat detection.
    This file must NEVER be committed with real IP lists or secrets.
"""

from __future__ import annotations

import ipaddress
import logging
from functools import wraps
from typing import Callable

from flask import abort, current_app, request
from flask_login import current_user

logger = logging.getLogger(__name__)


# ── IP Extraction ──────────────────────────────────────────────────────────

def get_client_ip() -> str:
    """
    Extract the real client IP, respecting X-Forwarded-For when behind
    a trusted reverse proxy.  Falls back to remote_addr.
    ⚠️  SECURITY: Only trust X-Forwarded-For if you control the proxy.
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the left-most IP (the original client)
        ip = forwarded_for.split(",")[0].strip()
    else:
        ip = request.remote_addr or "unknown"

    try:
        # Normalise (strips leading zeros, expands IPv6)
        return str(ipaddress.ip_address(ip))
    except ValueError:
        return ip


# ── Allow-list Check ───────────────────────────────────────────────────────

def is_ip_allowed(ip: str) -> bool:
    """
    ⚠️  SECURITY LOGIC: Returns True if the IP is in ALLOWED_IPS or
    matches any configured CIDR range (ALLOWED_NETWORKS).
    Override ALLOWED_IPS in instance/config.py — never hardcode here.
    """
    allowed_ips: set[str] = current_app.config.get("ALLOWED_IPS", set())
    allowed_networks_raw: list[str] = current_app.config.get("ALLOWED_NETWORKS", [])

    # Direct match
    if ip in allowed_ips:
        return True

    # CIDR range match
    try:
        client_addr = ipaddress.ip_address(ip)
        for cidr in allowed_networks_raw:
            try:
                if client_addr in ipaddress.ip_network(cidr, strict=False):
                    return True
            except ValueError:
                logger.warning("Invalid CIDR in ALLOWED_NETWORKS: %s", cidr)
    except ValueError:
        pass  # Non-parseable IP → deny

    return False


# ── Decorators ─────────────────────────────────────────────────────────────

def require_allowed_ip(f: Callable) -> Callable:
    """Route decorator: block requests from non-allow-listed IPs (403)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        ip = get_client_ip()
        if not is_ip_allowed(ip):
            logger.warning("Blocked request from unlisted IP: %s", ip)
            from app.services.notifications import notify_unauthorized_ip
            notify_unauthorized_ip(ip)
            abort(403)
        return f(*args, **kwargs)
    return decorated


def require_role(*roles: str) -> Callable:
    """Route decorator: enforce role-based access control."""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated
    return decorator


# ── Brute-force rate limiter (in-memory, simple) ──────────────────────────

_login_attempts: dict[str, list[float]] = {}


def record_failed_login(ip: str) -> None:
    import time
    _login_attempts.setdefault(ip, [])
    _login_attempts[ip].append(time.time())
    # Prune records older than 10 minutes
    cutoff = time.time() - 600
    _login_attempts[ip] = [t for t in _login_attempts[ip] if t > cutoff]


def is_rate_limited(ip: str) -> bool:
    import time
    limit = current_app.config.get("LOGIN_RATE_LIMIT", 5)
    cutoff = time.time() - 600
    attempts = [t for t in _login_attempts.get(ip, []) if t > cutoff]
    return len(attempts) >= limit


def clear_failed_logins(ip: str) -> None:
    _login_attempts.pop(ip, None)

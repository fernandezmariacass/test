"""
app/models/allowed_ip.py — Persistent IP allow-list model
⚠️  SECURITY LOGIC: entries here control who can access the application
"""

from datetime import datetime, timezone
from app import db


class AllowedIP(db.Model):
    __tablename__ = "allowed_ips"

    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String(50), unique=True, nullable=False)  # IP or CIDR
    label = db.Column(db.String(80), nullable=False, default="")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<AllowedIP {self.value!r} '{self.label}'>"

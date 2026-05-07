"""
app/models/user.py — User & LoginLog models
⚠️  SECURITY LOGIC: password hashing, role-based access
"""

from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    _password_hash = db.Column("password_hash", db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="viewer")  # admin | operator | viewer
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime, nullable=True)

    # Relationships
    login_logs = db.relationship("LoginLog", back_populates="user", lazy="dynamic")

    # ── Password ────────────────────────────────────────────────────────────

    @property
    def password(self):
        raise AttributeError("password is write-only")

    @password.setter
    def password(self, raw: str):
        self._password_hash = generate_password_hash(raw, method="pbkdf2:sha256:600000")

    def verify_password(self, raw: str) -> bool:
        return check_password_hash(self._password_hash, raw)

    # ── Factories ───────────────────────────────────────────────────────────

    @classmethod
    def create_admin(cls, username: str, email: str, password: str) -> "User":
        user = cls(username=username, email=email, role="admin")
        user.password = password
        return user

    # ── Helpers ─────────────────────────────────────────────────────────────

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_operator(self) -> bool:
        return self.role in ("admin", "operator")

    def touch_last_login(self):
        self.last_login = datetime.now(timezone.utc)

    def __repr__(self):
        return f"<User {self.username!r} [{self.role}]>"


class LoginLog(db.Model):
    """Immutable audit record of every login attempt."""
    __tablename__ = "login_logs"

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )
    username_attempted = db.Column(db.String(64), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)   # IPv6-safe
    user_agent = db.Column(db.String(256), nullable=True)
    success = db.Column(db.Boolean, nullable=False, default=False)
    failure_reason = db.Column(db.String(120), nullable=True)

    # FK — nullable because unknown usernames have no matching user
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    user = db.relationship("User", back_populates="login_logs")

    @classmethod
    def record(
        cls,
        username: str,
        ip: str,
        user_agent: str,
        success: bool,
        failure_reason: str | None = None,
        user_id: int | None = None,
    ) -> "LoginLog":
        entry = cls(
            username_attempted=username,
            ip_address=ip,
            user_agent=user_agent[:256] if user_agent else "",
            success=success,
            failure_reason=failure_reason,
            user_id=user_id,
        )
        db.session.add(entry)
        db.session.commit()
        return entry

    def __repr__(self):
        status = "OK" if self.success else "FAIL"
        return f"<LoginLog {self.timestamp} {self.username_attempted!r} {self.ip_address} {status}>"


# ── Flask-Login user loader ─────────────────────────────────────────────────

@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(User, int(user_id))

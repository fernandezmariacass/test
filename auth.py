"""
app/routes/auth.py — Authentication blueprint
⚠️  SECURITY LOGIC: IP check, rate limiting, audit logging, notifications
"""

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user

from app import db
from app.models.user import LoginLog, User
from app.services.notifications import notify_failed_login, notify_successful_login
from app.services.security import (
    clear_failed_logins,
    get_client_ip,
    is_ip_allowed,
    is_rate_limited,
    record_failed_login,
)
from app.utils.forms import LoginForm

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/", methods=["GET", "HEAD"])
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = LoginForm()
    ip = get_client_ip()

    # ── Pre-flight: IP allow-list ──────────────────────────────────────────
    if not is_ip_allowed(ip):
        from app.services.notifications import notify_unauthorized_ip
        notify_unauthorized_ip(ip)
        LoginLog.record(
            username="<unknown>",
            ip=ip,
            user_agent=request.user_agent.string,
            success=False,
            failure_reason="IP not on allow-list",
        )
        return render_template("errors/403.html"), 403

    # ── Rate limiting ──────────────────────────────────────────────────────
    if is_rate_limited(ip):
        flash("Too many failed attempts. Please wait a few minutes.", "danger")
        return render_template("auth/login.html", form=form, rate_limited=True), 429

    if form.validate_on_submit():
        username = form.username.data.strip()
        user = User.query.filter_by(username=username, is_active=True).first()

        if user and user.verify_password(form.password.data):
            # ── Success ────────────────────────────────────────────────────
            login_user(user, remember=form.remember_me.data)
            user.touch_last_login()
            db.session.commit()
            clear_failed_logins(ip)
            LoginLog.record(
                username=username,
                ip=ip,
                user_agent=request.user_agent.string,
                success=True,
                user_id=user.id,
            )
            notify_successful_login(username, ip)
            next_page = request.args.get("next")
            # Prevent open redirect
            if next_page and not next_page.startswith("/"):
                next_page = None
            return redirect(next_page or url_for("dashboard.index"))

        else:
            # ── Failure ────────────────────────────────────────────────────
            reason = "Invalid credentials"
            record_failed_login(ip)
            LoginLog.record(
                username=username,
                ip=ip,
                user_agent=request.user_agent.string,
                success=False,
                failure_reason=reason,
                user_id=user.id if user else None,
            )
            notify_failed_login(username, ip, reason)
            flash("Incorrect username or password. Please try again.", "danger")

    return render_template("auth/login.html", form=form, rate_limited=False)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("auth.login"))

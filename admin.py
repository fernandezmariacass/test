"""
app/routes/admin.py — Admin-only management blueprint
⚠️  SECURITY LOGIC: protected by require_role("admin")
"""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from app.models.user import LoginLog, User
from app.services.security import require_role
from app.utils.forms import AddUserForm, AllowIPForm

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.before_request
@login_required
def _require_admin():
    """All admin routes require authentication + admin role."""
    from flask_login import current_user
    if not current_user.is_admin:
        from flask import abort
        abort(403)


# ── User management ────────────────────────────────────────────────────────

@admin_bp.route("/users")
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    form = AddUserForm()
    return render_template("dashboard/admin_users.html", users=all_users, form=form)


@admin_bp.route("/users/add", methods=["POST"])
def add_user():
    form = AddUserForm()
    if form.validate_on_submit():
        if User.query.filter(
            (User.username == form.username.data) | (User.email == form.email.data)
        ).first():
            flash("A user with that username or email already exists.", "danger")
        else:
            new_user = User(
                username=form.username.data,
                email=form.email.data,
                role=form.role.data,
            )
            new_user.password = form.password.data
            db.session.add(new_user)
            db.session.commit()
            flash(f"User '{new_user.username}' created successfully.", "success")
    else:
        for field, errors in form.errors.items():
            for err in errors:
                flash(f"{field}: {err}", "danger")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/toggle", methods=["POST"])
def toggle_user(user_id: int):
    user = db.get_or_404(User, user_id)
    from flask_login import current_user
    if user.id == current_user.id:
        flash("You cannot deactivate your own account.", "warning")
    else:
        user.is_active = not user.is_active
        db.session.commit()
        state = "activated" if user.is_active else "deactivated"
        flash(f"User '{user.username}' has been {state}.", "info")
    return redirect(url_for("admin.users"))


# ── Login logs ─────────────────────────────────────────────────────────────

@admin_bp.route("/logs")
def logs():
    page = request.args.get("page", 1, type=int)
    filter_status = request.args.get("status", "all")
    query = LoginLog.query.order_by(LoginLog.timestamp.desc())
    if filter_status == "success":
        query = query.filter_by(success=True)
    elif filter_status == "failed":
        query = query.filter_by(success=False)
    pagination = query.paginate(page=page, per_page=25, error_out=False)
    return render_template(
        "dashboard/admin_logs.html",
        pagination=pagination,
        filter_status=filter_status,
    )


# ── Allow-list management ──────────────────────────────────────────────────

@admin_bp.route("/allowlist", methods=["GET", "POST"])
def allowlist():
    """
    ⚠️  SECURITY LOGIC: Runtime management of the IP allow-list.
    Persists to the AllowedIP table (see models).
    """
    from app.models.allowed_ip import AllowedIP
    form = AllowIPForm()
    if form.validate_on_submit():
        import ipaddress
        raw = form.ip_address.data.strip()
        try:
            # Validate: must be valid IP or CIDR
            if "/" in raw:
                ipaddress.ip_network(raw, strict=False)
            else:
                ipaddress.ip_address(raw)
        except ValueError:
            flash("Invalid IP address or CIDR range.", "danger")
            return redirect(url_for("admin.allowlist"))

        if AllowedIP.query.filter_by(value=raw).first():
            flash("That IP is already on the allow-list.", "warning")
        else:
            entry = AllowedIP(value=raw, label=form.label.data or "")
            db.session.add(entry)
            db.session.commit()
            flash(f"{raw} added to allow-list.", "success")
    entries = AllowedIP.query.order_by(AllowedIP.created_at.desc()).all()
    return render_template("dashboard/admin_allowlist.html", entries=entries, form=form)


@admin_bp.route("/allowlist/<int:entry_id>/delete", methods=["POST"])
def delete_allowlist(entry_id: int):
    from app.models.allowed_ip import AllowedIP
    entry = db.get_or_404(AllowedIP, entry_id)
    db.session.delete(entry)
    db.session.commit()
    flash(f"{entry.value} removed from allow-list.", "info")
    return redirect(url_for("admin.allowlist"))

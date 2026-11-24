from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from .extensions import db, limiter
from .models import User, AuditEvent
from .security import password_is_strong

auth_bp = Blueprint("auth", __name__)

def audit(action, details=""):
    event = AuditEvent(
        actor_user_id=current_user.id if current_user.is_authenticated else None,
        action=action, entity_type="user",
        entity_id=str(current_user.id) if current_user.is_authenticated else None,
        details=details[:500],
        ip_address=request.remote_addr
    )
    db.session.add(event)
    db.session.commit()

@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("fleet.dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email, active=True).first()
        if user and user.check_password(password):
            login_user(user)
            audit("login_success", "User authenticated")
            return redirect(url_for("fleet.dashboard"))
        flash("Invalid email or password.", "error")
        event = AuditEvent(action="login_failure", entity_type="user",
                           details="Invalid credentials", ip_address=request.remote_addr)
        db.session.add(event)
        db.session.commit()
    return render_template("login.html")

@auth_bp.post("/logout")
@login_required
def logout():
    audit("logout", "User logged out")
    logout_user()
    return redirect(url_for("auth.login"))

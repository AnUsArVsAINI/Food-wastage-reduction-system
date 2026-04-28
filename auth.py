"""
routes/auth.py
--------------
Authentication routes: register, login, logout.
Uses Flask-Login for session management and Werkzeug for password hashing.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from database.models     import db, User
from utils.mailer        import send_login_email, send_welcome_email

auth_bp = Blueprint("auth", __name__)


# ── Register ──────────────────────────────────────────────────────────────────
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Show registration form (GET) or process it (POST)."""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        name     = request.form.get("name", "").strip()
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm_password", "")
        phone    = request.form.get("phone", "").strip()
        location = request.form.get("location", "").strip()

        # ── Basic validation ──────────────────────────────────────────────────
        if not name or not email or not password:
            flash("Name, email, and password are required.", "danger")
            return render_template("register.html")

        if password != confirm:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return render_template("register.html")

        if User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "warning")
            return render_template("register.html")

        # ── Create user ───────────────────────────────────────────────────────
        user = User(name=name, email=email, phone=phone, location=location)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        # Send a welcome email in the background (non-blocking)
        send_welcome_email(user.name, user.email)

        flash("Account created! A welcome email has been sent. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


# ── Login ─────────────────────────────────────────────────────────────────────
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Show login form (GET) or authenticate the user (POST)."""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user, remember=remember)

            # Send login-notification email in the background (non-blocking)
            send_login_email(user.name, user.email)

            flash(f"Welcome back, {user.name}! 🎉 A login notification has been sent to {user.email}.", "success")
            # Redirect to the page the user originally tried to visit
            next_page = request.args.get("next")
            return redirect(next_page or url_for("main.dashboard"))

        flash("Invalid email or password.", "danger")

    return render_template("login.html")


# ── Logout ────────────────────────────────────────────────────────────────────
@auth_bp.route("/logout")
@login_required
def logout():
    """Log the user out and redirect to home."""
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.home"))

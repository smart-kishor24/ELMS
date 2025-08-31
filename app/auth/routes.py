from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, current_user
from .forms import LoginForm, RegisterForm, ForgotPasswordForm, ResetPasswordForm
from ..extensions import db, mail
from ..models import User
from ..decorators import roles_required
from .import auth_bp
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message

# ---------------- Helper: Role-based redirection ----------------
def redirect_role_dashboard(user):
    role = user.role.lower()
    if role == "admin":
        return redirect(url_for("admin.dashboard"))
    elif role == "manager":
        return redirect(url_for("manager.dashboard"))
    elif role == "employee":
        return redirect(url_for("employee.dashboard"))
    else:
        flash("Role not recognized. Contact admin.", "warning")
        return redirect(url_for("auth.login"))

# ---------------- Login Route ----------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        flash("You are already logged in.", "info")
        return redirect_role_dashboard(current_user)

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            flash("Welcome back!", "success")
            next_url = request.args.get("next")
            return redirect(next_url) if next_url else redirect_role_dashboard(user)
        flash("Invalid email or password.", "danger")
    return render_template("auth/login.html", form=form)

# ---------------- Logout Route ----------------
@auth_bp.route("/logout")
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))

# ---------------- Register Route ----------------
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()

    if current_user.is_authenticated:
        # Non-admin users cannot create Admin/Manager
        if form.role.data in ["Admin", "Manager"] and current_user.role != "Admin":
            flash("Only Admins can create Manager/Admin accounts.", "danger")
            return redirect(url_for("auth.register"))

    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        if User.query.filter_by(email=email).first():
            flash("This email is already registered.", "warning")
            return render_template("auth/register.html", form=form)

        user = User(
            name=form.name.data.strip(),
            email=email,
            role=form.role.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f"User created: {user.email} ({user.role})", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)

# ---------------- Password Reset Helpers ----------------
def generate_reset_token(email):
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return s.dumps(email, salt="password-reset-salt")

def verify_reset_token(token, expiration=3600):
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        email = s.loads(token, salt="password-reset-salt", max_age=expiration)
    except:
        return None
    return email

# ---------------- Forgot Password Route ----------------
@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user:
            token = generate_reset_token(user.email)
            reset_url = url_for("auth.reset_password", token=token, _external=True)

            # Flash the URL for the clickable button
            flash(reset_url, "info")
        else:
            flash("If your email is registered, a password reset link has been generated.", "info")

        return redirect(url_for("auth.login"))

    return render_template("auth/forgot_password.html", form=form)




# ---------------- Reset Password Route ----------------
@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    email = verify_reset_token(token)
    if not email:
        flash("Invalid or expired token.", "danger")
        return redirect(url_for("auth.forgot_password"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=email).first()
        if user:
            user.set_password(form.password.data)
            db.session.commit()
            flash("Password reset successfully. Please log in.", "success")
            return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", form=form)
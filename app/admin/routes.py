from flask import Blueprint, render_template, redirect, url_for, flash, send_file, request
from flask_login import login_required, current_user
from ..models import User, LeaveRequest, AuditLog, db
from .forms import CreateUserForm, EditUserForm, ReportForm, DeleteForm
import pandas as pd
from io import BytesIO
from weasyprint import HTML

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# ------------------ Admin Dashboard ------------------
@admin_bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.role != "Admin":
        flash("Access denied", "danger")
        return redirect(url_for("employee.dashboard"))
    
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    admins = User.query.filter_by(role="Admin").count()
    employees = User.query.filter_by(role="Employee").count()
    total_leaves = LeaveRequest.query.count()
    pending_leaves = LeaveRequest.query.filter_by(status="Pending").count()
    users = User.query.all()
    
    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        active_users=active_users,
        admins=admins,
        employees=employees,
        total_leaves=total_leaves,
        pending_leaves=pending_leaves,
        users=users
    )

# ------------------ Manage Users ------------------
from .forms import CreateUserForm, DeleteForm

@admin_bp.route("/manage-users", methods=["GET", "POST"])
@login_required
def manage_users():
    if current_user.role != "Admin":
        flash("Access denied", "danger")
        return redirect(url_for("employee.dashboard"))

    form = CreateUserForm()
    delete_form = DeleteForm()  # Pass this to template for CSRF

    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash("Email already exists!", "danger")
        else:
            user = User(
                name=form.name.data,
                email=form.email.data,
                role=form.role.data
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash("User created successfully!", "success")
            return redirect(url_for("admin.manage_users"))

    users = User.query.all()
    return render_template(
        "admin/manage_users.html",
        form=form,
        users=users,
        delete_form=delete_form
    )


# ------------------ Edit User ------------------
@admin_bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
def edit_user(user_id):
    if current_user.role != "Admin":
        flash("Access denied", "danger")
        return redirect(url_for("employee.dashboard"))

    user = User.query.get_or_404(user_id)
    form = EditUserForm(obj=user)

    if form.validate_on_submit():
        user.name = form.name.data.strip()
        user.email = form.email.data.strip().lower()
        user.role = form.role.data
        db.session.commit()
        flash("User updated successfully.", "success")
        return redirect(url_for("admin.manage_users"))

    return render_template("admin/edit_user.html", form=form, user=user)

# ------------------ Delete User ------------------
@admin_bp.route("/users/delete/<int:user_id>", methods=["POST"])
@login_required
def delete_user(user_id):
    form = DeleteForm()
    if form.validate_on_submit():  # CSRF is checked here
        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        flash(f"User {user.name} deleted successfully.", "success")
    else:
        flash("Invalid CSRF token.", "danger")
    return redirect(url_for("admin.manage_users"))


# ------------------ Generate Reports ------------------
@admin_bp.route("/generate-report", methods=["GET", "POST"])
@login_required
def generate_report():
    if current_user.role != "Admin":
        flash("Access denied", "danger")
        return redirect(url_for("employee.dashboard"))

    form = ReportForm()
    leaves = None
    month = None
    
    if form.validate_on_submit():
        month = form.month.data  # Format YYYY-MM
        start_date = pd.to_datetime(f"{month}-01")
        end_date = start_date + pd.offsets.MonthEnd(1)
        
        leaves = LeaveRequest.query.filter(
            LeaveRequest.start_date >= start_date,
            LeaveRequest.end_date <= end_date
        ).all()

        data = []
        for l in leaves:
            data.append({
                "Employee": l.employee.name,
                "Type": l.leave_type,
                "Start Date": l.start_date,
                "End Date": l.end_date,
                "Status": l.status,
                "Manager": l.manager.name if l.manager else ""
            })
        df = pd.DataFrame(data)

        # CSV Export
        csv_stream = BytesIO()
        df.to_csv(csv_stream, index=False)
        csv_stream.seek(0)

        # PDF Export
        html_string = render_template("admin/generate_report.html",form=form, leaves=leaves, month=month)
        pdf_stream = BytesIO()
        HTML(string=html_string).write_pdf(pdf_stream)
        pdf_stream.seek(0)

        flash("Reports generated! Download links below.", "success")
        return render_template(
            "admin/generate_report.html",
            form=form,
            leaves=leaves,
            month=month,
            csv_stream=csv_stream,
            pdf_stream=pdf_stream
        )

    return render_template("admin/generate_report.html", form=form)


@admin_bp.route("/download-csv/<month>")
@login_required
def download_csv(month):
    if current_user.role != "Admin":
        flash("Access denied", "danger")
        return redirect(url_for("employee.dashboard"))

    start_date = pd.to_datetime(f"{month}-01")
    end_date = start_date + pd.offsets.MonthEnd(1)

    leaves = LeaveRequest.query.filter(
        LeaveRequest.start_date >= start_date,
        LeaveRequest.end_date <= end_date
    ).all()

    data = []
    for l in leaves:
        data.append({
            "Employee": l.employee.name,
            "Type": l.leave_type,
            "Start Date": l.start_date,
            "End Date": l.end_date,
            "Status": l.status
        })

    df = pd.DataFrame(data)
    csv_stream = BytesIO()
    df.to_csv(csv_stream, index=False)
    csv_stream.seek(0)

    return send_file(
        csv_stream,
        as_attachment=True,
        download_name=f"leave_report_{month}.csv",
        mimetype="text/csv"
    )


@admin_bp.route("/download-pdf/<month>")
@login_required
def download_pdf(month):
    if current_user.role != "Admin":
        flash("Access denied", "danger")
        return redirect(url_for("employee.dashboard"))

    # Convert month to start and end dates
    start_date = pd.to_datetime(f"{month}-01")
    end_date = start_date + pd.offsets.MonthEnd(1)

    # Query leaves in that month
    leaves = LeaveRequest.query.filter(
        LeaveRequest.start_date >= start_date,
        LeaveRequest.end_date <= end_date
    ).all()

    # Render HTML table template for PDF
    html_string = render_template("admin/report_pdf.html", leaves=leaves, month=month)

    # Generate PDF in memory
    pdf_stream = BytesIO()
    HTML(string=html_string).write_pdf(pdf_stream)
    pdf_stream.seek(0)

    # Return PDF as attachment
    return send_file(
        pdf_stream,
        as_attachment=True,
        download_name=f"leave_report_{month}.pdf",
        mimetype="application/pdf"
    )
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ..models import LeaveRequest, User, db, AuditLog
from .forms import ApproveLeaveForm
from sqlalchemy import and_, or_

manager_bp = Blueprint("manager", __name__, url_prefix="/manager")

# -------------------------------
# Dashboard - show all team leaves
# -------------------------------
@manager_bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.role != "Manager":
        flash("Access denied", "danger")
        return redirect(url_for("employee.dashboard"))

    leaves = LeaveRequest.query.order_by(LeaveRequest.start_date.desc()).all()
    return render_template("manager/dashboard.html", leaves=leaves)

# -------------------------------
# View & Approve/Reject a leave
# -------------------------------
@manager_bp.route("/leave/<int:leave_id>", methods=["GET", "POST"])
@login_required
def view_leave(leave_id):
    leave = LeaveRequest.query.get_or_404(leave_id)

    if current_user.role != "Manager":
        flash("Access denied", "danger")
        return redirect(url_for("employee.dashboard"))

    form = ApproveLeaveForm()

    if form.validate_on_submit():
        # Update leave
        leave.status = form.status.data
        leave.manager_comment = form.comment.data
        leave.manager_id = current_user.id

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating leave: {str(e)}", "danger")
            return redirect(url_for("manager.dashboard"))

        # Create audit log
        try:
            log = AuditLog(
                user_id=current_user.id,
                action=f"{leave.status} leave request",
                meta_info=f"Leave ID: {leave.id}, Employee ID: {leave.employee_id}"
            )
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating audit log: {str(e)}", "warning")

        flash(f"Leave {leave.status.lower()} successfully!", "success")
        return redirect(url_for("manager.dashboard"))

    return render_template("manager/view_leave.html", leave=leave, form=form)

# -------------------------------
# Filter leaves by criteria
# -------------------------------
@manager_bp.route("/filter", methods=["GET"])
@login_required
def filter_leaves():
    if current_user.role != "Manager":
        flash("Access denied", "danger")
        return redirect(url_for("employee.dashboard"))

    status = request.args.get("status")
    employee_id = request.args.get("employee_id")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    query = LeaveRequest.query

    if status:
        query = query.filter(LeaveRequest.status == status)

    if employee_id:
        try:
            emp_id = int(employee_id)
            query = query.filter(LeaveRequest.employee_id == emp_id)
        except ValueError:
            flash("Invalid Employee ID", "warning")

    if start_date:
        query = query.filter(LeaveRequest.start_date >= start_date)
    if end_date:
        query = query.filter(LeaveRequest.end_date <= end_date)

    leaves = query.order_by(LeaveRequest.start_date.desc()).all()
    return render_template("manager/dashboard.html", leaves=leaves)
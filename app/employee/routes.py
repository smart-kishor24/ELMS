from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import current_user, login_required
from ..decorators import roles_required
from ..extensions import db
from ..models import LeaveRequest, AuditLog, User
from . import employee_bp
from .forms import LeaveApplyForm, LeaveEditForm
from .forms import EmptyForm

@employee_bp.route("/dashboard")
@roles_required("Employee")
def dashboard():
    # Show pending and upcoming leaves
    pending = LeaveRequest.query.filter_by(employee_id=current_user.id).order_by(LeaveRequest.start_date.desc()).limit(5).all()
    return render_template("dashboard.html", pending=pending)

@employee_bp.route("/apply", methods=["GET", "POST"])
@roles_required("Employee")
def apply_leave():
    form = LeaveApplyForm()
    if form.validate_on_submit():
        s = form.start_date.data
        e = form.end_date.data

        # Overlap validation
        if LeaveRequest.overlaps(current_user.id, s, e):
            flash("You already have a leave overlapping with that period.", "warning")
            return render_template("employee/apply.html", form=form)

        lr = LeaveRequest(
            employee_id=current_user.id,
            start_date=s,
            end_date=e,
            leave_type=form.leave_type.data,
            reason=form.reason.data.strip(),
            status=LeaveRequest.STATUS_PENDING
        )
        db.session.add(lr)
        db.session.commit()

        # Audit log
        log = AuditLog(user_id=current_user.id, action="Applied for leave", metadata=f"LeaveRequest ID: {lr.id}")
        db.session.add(log)
        db.session.commit()

        flash("Leave request submitted.", "success")
        return redirect(url_for("employee.history"))
    return render_template("apply.html", form=form)

@employee_bp.route("/history")
@roles_required("Employee")
def history():
    page = request.args.get("page", 1, type=int)
    q = LeaveRequest.query.filter_by(employee_id=current_user.id).order_by(LeaveRequest.start_date.desc())
    leaves = q.paginate(page=page, per_page=10, error_out=False)
    form = EmptyForm()   # Pass an empty form to template
    return render_template("history.html", leaves=leaves, form=form)


@employee_bp.route("/edit/<int:request_id>", methods=["GET", "POST"])
@roles_required("Employee")
def edit_request(request_id):
    lr = LeaveRequest.query.filter_by(id=request_id, employee_id=current_user.id).first_or_404()

    # Only allow edit if pending
    if lr.status != LeaveRequest.STATUS_PENDING:
        flash("Only pending requests can be edited.", "warning")
        return redirect(url_for("employee.history"))

    form = LeaveEditForm(obj=lr)
    if form.validate_on_submit():
        s = form.start_date.data
        e = form.end_date.data

        if LeaveRequest.overlaps(current_user.id, s, e, exclude_id=lr.id):
            flash("This update overlaps with another existing leave.", "warning")
            return render_template("edit_request.html", form=form, lr=lr)

        lr.start_date = s
        lr.end_date = e
        lr.leave_type = form.leave_type.data
        lr.reason = form.reason.data.strip()
        db.session.commit()

        log = AuditLog(user_id=current_user.id, action="Edited leave request", metadata=f"LeaveRequest ID: {lr.id}")
        db.session.add(log)
        db.session.commit()

        flash("Leave request updated.", "success")
        return redirect(url_for("employee.history"))
    return render_template("edit_request.html", form=form, lr=lr)

@employee_bp.route("/cancel/<int:request_id>", methods=["POST"])
@roles_required("Employee")
def cancel_request(request_id):
    lr = LeaveRequest.query.filter_by(id=request_id, employee_id=current_user.id).first_or_404()
    if lr.status != LeaveRequest.STATUS_PENDING:
        flash("Only pending requests can be cancelled.", "warning")
        return redirect(url_for("employee.history"))

    lr.status = LeaveRequest.STATUS_CANCELLED
    db.session.commit()

    log = AuditLog(user_id=current_user.id, action="Cancelled leave request", metadata=f"LeaveRequest ID: {lr.id}")
    db.session.add(log)
    db.session.commit()

    flash("Leave request cancelled.", "info")
    return redirect(url_for("employee.history"))
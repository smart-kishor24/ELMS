from flask import Blueprint, render_template, flash, redirect
from flask_login import login_required, current_user
from ..models import AuditLog

audit_bp = Blueprint("audit", __name__, url_prefix="/audit")

@audit_bp.route("/logs")
@login_required
def logs():
    if current_user.role != "Admin":
        flash("Access denied", "danger")
        return redirect("/")
    
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).all()
    return render_template("audit/logs.html", logs=logs)
from datetime import datetime, date
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="Employee")  # Admin | Manager | Employee
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # relationships
    # leave requests submitted by this user
    leave_requests = db.relationship(
        "LeaveRequest",
        backref="employee",
        lazy="dynamic",
        foreign_keys="LeaveRequest.employee_id"
    )
    # leave requests approved by this user (if manager)
    approved_leaves = db.relationship(
        "LeaveRequest",
        backref="manager",
        lazy="dynamic",
        foreign_keys="LeaveRequest.manager_id"
    )
    audit_logs = db.relationship("AuditLog", backref="user", lazy="dynamic")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return str(self.id)



class LeaveRequest(db.Model):
    __tablename__ = "leave_requests"

    STATUS_PENDING = "Pending"
    STATUS_APPROVED = "Approved"
    STATUS_REJECTED = "Rejected"
    STATUS_CANCELLED = "Cancelled"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    leave_type = db.Column(db.String(50), nullable=False)  # Sick, Casual, etc.
    reason = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default=STATUS_PENDING, nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)  # manager who approves/rejects
    manager_comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def duration(self):
        return (self.end_date - self.start_date).days + 1

    @staticmethod
    def overlaps(employee_id, start_date, end_date, exclude_id=None):
        """
        Return True if the given date range overlaps with any existing leave of the employee
        that is not cancelled. Optionally exclude a request id (for editing).
        """
        q = LeaveRequest.query.filter(
            LeaveRequest.employee_id == employee_id,
            LeaveRequest.status != LeaveRequest.STATUS_CANCELLED
        )
        if exclude_id:
            q = q.filter(LeaveRequest.id != exclude_id)

        # overlap condition: not (existing_end < new_start or existing_start > new_end)
        overlaps = q.filter(
            db.not_(
                db.or_(
                    LeaveRequest.end_date < start_date,
                    LeaveRequest.start_date > end_date
                )
            )
        ).first()
        return bool(overlaps)


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action = db.Column(db.String(255), nullable=False)
    meta_info = db.Column(db.Text, nullable=True)  # renamed from 'metadata'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


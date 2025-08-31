# app/audit/utils.py
from ..models import AuditLog, db
from flask_login import current_user

def log_action(action, meta_info=None, user_id=None):
    if not user_id:
        user_id = current_user.id if current_user.is_authenticated else None
    log = AuditLog(user_id=user_id, action=action, meta_info=meta_info)
    db.session.add(log)
    db.session.commit()
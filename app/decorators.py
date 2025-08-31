from functools import wraps
from flask import abort
from flask_login import current_user, login_required

def roles_required(*roles):
    """
    Usage:
        @roles_required("Admin")
        def admin_only(): ...

        @roles_required("Admin", "Manager")
        def managers_and_admins(): ...
    """
    def decorator(fn):
        @wraps(fn)
        @login_required
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                # login_required handles redirect to login
                return fn(*args, **kwargs)
            if current_user.role not in roles:
                # 403 Forbidden for unauthorized roles
                abort(403)
            return fn(*args, **kwargs)
        return wrapped
    return decorator

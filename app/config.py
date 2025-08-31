import os

class Config:
    # Secret Key (use environment variable in production)
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    # Database
    db_url = os.environ.get("DATABASE_URL", "sqlite:///instance/elms.db")
    # Fix Heroku’s postgres:// URI format
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # CSRF (can be limited or removed in prod)
    WTF_CSRF_TIME_LIMIT = None

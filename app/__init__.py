import os
import click
from flask import Flask, render_template
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import your app modules
from .config import Config
from .extensions import db, login_manager, csrf
from .models import User
from .auth import auth_bp
from .employee import employee_bp
from .manager.routes import manager_bp
from .admin.routes import admin_bp
from .audit.routes import audit_bp
from .reports.routes import reports_bp


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Secret key from environment or default
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'mysecretkey')

    # SQLite database for local development
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///elms.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Flask-Login configuration
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(employee_bp)
    app.register_blueprint(manager_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(reports_bp)

    # Default home page
    @app.route("/")
    def index():
        return render_template("base.html")

    # CLI command to initialize the database
    @app.cli.command("init-db")
    def init_db():
        """Create all database tables."""
        with app.app_context():
            db.create_all()
            click.echo("✅ Database initialized successfully!")

    # CLI command to create a user
    @app.cli.command("create-user")
    @click.option("--name", prompt=True)
    @click.option("--email", prompt=True)
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
    @click.option(
        "--role",
        type=click.Choice(["Admin", "Manager", "Employee"], case_sensitive=False),
        prompt=True
    )
    def create_user(name, email, password, role):
        """Create a user with a specified role."""
        with app.app_context():
            if User.query.filter_by(email=email).first():
                click.echo("⚠️ User with that email already exists.")
                return
            u = User(name=name, email=email, role=role.capitalize())
            u.set_password(password)
            db.session.add(u)
            db.session.commit()
            click.echo(f"👤 Created {u.role} user: {u.email}")

    return app

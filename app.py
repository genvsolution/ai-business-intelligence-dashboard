from flask import Flask, redirect, url_for, flash, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
import os

# Import configuration
from config import Config

# Initialize extensions outside the factory, but defer initialization to the factory
# This allows them to be imported by other modules without circular dependencies
# and ensures they are properly initialized with the app context.
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
bcrypt = Bcrypt()
migrate = Migrate()

def create_app(config_class=Config):
    """
    Flask application factory function.

    This function creates and configures the Flask application instance,
    initializes extensions, registers blueprints, and sets up error handlers.
    Using a factory function allows for different configurations (e.g., testing, development, production)
    and makes the application more modular and testable.

    Args:
        config_class: The configuration class to use (e.g., Config, DevelopmentConfig, ProductionConfig).
                      Defaults to the base `Config` class.

    Returns:
        Flask: A configured Flask application instance.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions with the app instance
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db) # Initialize Flask-Migrate for database migrations

    # Configure Flask-Login
    login_manager.login_view = 'auth.login'  # The view function name for the login page
    login_manager.login_message_category = 'info' # Category for flash messages when login is required
    login_manager.login_message = 'Please log in to access this page.' # Message displayed

    @login_manager.user_loader
    def load_user(user_id):
        """
        Loads a user from the database given their ID.
        This function is required by Flask-Login to reload the user object
        from the user ID stored in the session.

        Args:
            user_id (str): The string representation of the user's ID.

        Returns:
            User: The User object if found, otherwise None.
        """
        # Import User model here to avoid potential circular imports
        # if models were to import `db` from this file directly.
        from app.models.user import User
        try:
            return User.query.get(int(user_id))
        except ValueError:
            # Handle cases where user_id might not be an integer
            return None

    # Register Blueprints
    # Blueprints modularize the application, allowing different parts of the app
    # (e.g., authentication, main dashboard, lead management) to be developed
    # independently and then registered with the main application.
    from app.auth.routes import auth_bp
    from app.main.routes import main_bp
    from app.leads.routes import leads_bp
    from app.analytics.routes import analytics_bp
    from app.admin.routes import admin_bp
    from app.errors.handlers import errors_bp
    from app.api.routes import api_bp # For any RESTful API endpoints

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp) # No URL prefix for main application routes
    app.register_blueprint(leads_bp, url_prefix='/leads')
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(errors_bp) # Error handlers are often registered without a prefix
    app.register_blueprint(api_bp, url_prefix='/api')

    # Global Error Handlers
    # These handlers catch exceptions that bubble up to the application level
    # and render user-friendly error pages.
    @app.errorhandler(404)
    def not_found_error(error):
        """
        Handles 404 Not Found errors.

        Args:
            error: The error object passed by Flask.

        Returns:
            tuple: Rendered error page and HTTP status code.
        """
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden_error(error):
        """
        Handles 403 Forbidden errors (e.g., unauthorized access).

        Args:
            error: The error object passed by Flask.

        Returns:
            tuple: Rendered error page and HTTP status code.
        """
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def internal_error(error):
        """
        Handles 500 Internal Server errors.
        This handler also attempts to rollback any pending database transactions
        to ensure the database session is clean after an unexpected error.

        Args:
            error: The error object passed by Flask.

        Returns:
            tuple: Rendered error page and HTTP status code.
        """
        db.session.rollback() # Rollback any pending database transactions
        return render_template('errors/500.html'), 500

    # Shell context for Flask CLI (e.g., `flask shell`)
    @app.shell_context_processor
    def make_shell_context():
        """
        Provides a shell context for the Flask CLI.
        This makes `db` and various models directly accessible when running `flask shell`,
        which is useful for debugging and database interaction.

        Returns:
            dict: A dictionary of objects to make available in the shell.
        """
        # Import models here to ensure they are loaded and accessible in the shell
        from app.models.user import User
        from app.models.leads import Lead
        from app.models.analytics import KPI, SalesRecord # Example models
        from app.models.tasks import Task # Example task model
        return {
            'db': db,
            'User': User,
            'Lead': Lead,
            'KPI': KPI,
            'SalesRecord': SalesRecord,
            'Task': Task
        }

    # Global Jinja2 context processor (optional)
    @app.context_processor
    def inject_global_variables():
        """
        Injects global variables into all Jinja2 templates.
        This is useful for making certain data or objects (like `current_user`)
        available in every template without explicitly passing them.

        Returns:
            dict: A dictionary of variables to inject into the template context.
        """
        return dict(current_user=current_user)

    return app

# To ensure Flask-Migrate discovers all models, it's often necessary to import
# them somewhere in the application's startup path. The `make_shell_context`
# helps for `flask shell`, but for `flask db migrate`, models need to be
# loaded when `db` is initialized. The blueprint imports will load models
# that are used within those blueprints. For models not directly used in a blueprint's
# `routes.py` but still part of the `db` schema, ensure they are imported
# in `app.models.__init__.py` or explicitly in `create_app` if necessary.
# For this project structure, the explicit imports within `make_shell_context`
# and the implicit imports when blueprints load their respective models are generally sufficient.
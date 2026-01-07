import os
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from celery import Celery

# Initialize Flask extensions globally.
# These instances are created once and then initialized with the Flask app
# inside the create_app factory function.
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
bcrypt = Bcrypt()
csrf = CSRFProtect()
mail = Mail()

# Initialize Celery globally.
# The broker and backend URLs, along with other configurations, will be
# updated from Flask's app.config inside the create_app factory function.
celery_app = Celery(__name__)

def create_app(config_class=None):
    """
    Flask application factory function.

    This function initializes the Flask application, loads its configuration,
    registers all necessary extensions, blueprints, and sets up logging.
    It allows for flexible configuration loading based on environment.

    Args:
        config_class: An optional configuration class to use (e.g., DevelopmentConfig, ProductionConfig).
                      If provided, the application will be configured using this class.
                      If None, the function attempts to load configuration based on the
                      'FLASK_CONFIG' environment variable (e.g., 'production', 'testing', 'development'),
                      defaulting to 'development' if the variable is not set.

    Returns:
        Flask: The fully configured Flask application instance.
    """
    app = Flask(__name__)

    # Load application configuration
    if config_class:
        # Load configuration directly from the provided class
        app.config.from_object(config_class)
    else:
        # Dynamically load configuration based on the FLASK_CONFIG environment variable.
        # This provides a flexible way to manage different environments (dev, test, prod).
        from config import Config, DevelopmentConfig, ProductionConfig, TestingConfig
        config_name = os.environ.get('FLASK_CONFIG', 'development')
        if config_name == 'production':
            app.config.from_object(ProductionConfig)
        elif config_name == 'testing':
            app.config.from_object(TestingConfig)
        else: # Default to development configuration
            app.config.from_object(DevelopmentConfig)

    # Initialize Flask extensions with the application instance.
    # This binds the extensions to the specific Flask app being created.
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)

    # Configure Flask-Login for user authentication and session management.
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'  # Specifies the login route for unauthenticated users.
    login_manager.login_message_category = 'info' # Category for flash messages when redirecting to login.
    login_manager.login_message = 'Please log in to access this page.' # Message shown to unauthenticated users.

    # Configure Celery with Flask app context.
    # This step is crucial for Celery tasks to be able to access Flask's application
    # context, including extensions like SQLAlchemy (db), and the application's configuration.
    celery_app.conf.update(app.config)
    class ContextTask(celery_app.Task):
        """
        A custom Celery Task class that ensures every task runs within a Flask application context.
        This allows tasks to interact with Flask extensions and configuration as if they were
        running inside a standard Flask request.
        """
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    celery_app.Task = ContextTask

    # Register Blueprints.
    # Blueprints help in modularizing the application into distinct components,
    # improving organization, maintainability, and scalability.
    # Each blueprint typically represents a feature area or module.

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth') # Authentication routes

    from app.sales import bp as sales_bp
    app.register_blueprint(sales_bp, url_prefix='/sales') # Sales analytics and reporting

    from app.leads import bp as leads_bp
    app.register_blueprint(leads_bp, url_prefix='/leads') # Lead management CRM

    from app.ai_insights import bp as ai_insights_bp
    app.register_blueprint(ai_insights_bp, url_prefix='/ai') # AI-driven insights and reports

    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin') # Administrative functionalities

    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp) # Custom error pages (e.g., 404, 500)

    # Setup Logging for production environments.
    # In production, logs are typically written to files to provide a persistent
    # record of application activity, errors, and warnings, which is essential for
    # monitoring, debugging, and auditing. Console logging is usually sufficient for development.
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        # Use RotatingFileHandler to manage log file size and rotation.
        file_handler = RotatingFileHandler('logs/sales_dashboard.log',
                                           maxBytes=10240,  # Max 10 KB per log file
                                           backupCount=10) # Keep up to 10 rotated log files
        # Define the format for log messages.
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        # Set the logging level for the file handler.
        file_handler.setLevel(logging.INFO)
        # Add the file handler to the application's logger.
        app.logger.addHandler(file_handler)

        # Set the overall logging level for the application.
        app.logger.setLevel(logging.INFO)
        app.logger.info('Sales Dashboard startup')

    return app

# Import models here to avoid circular dependencies.
# This ensures that the 'db' object (SQLAlchemy) is fully initialized
# before any model attempts to use it to define its database schema.
# Importing `app.models` ensures all models are registered with SQLAlchemy's metadata.
from app import models
from app.models import User # Explicitly import User for the user_loader function.

@login_manager.user_loader
def load_user(user_id):
    """
    Callback function for Flask-Login to load a user from the database by their ID.

    This function is crucial for Flask-Login's session management. It is called
    whenever Flask-Login needs to retrieve a user object from the database based
    on the user ID stored in the session cookie.

    Args:
        user_id (str): The unique identifier (primary key) of the user,
                       provided as a string by Flask-Login.

    Returns:
        User: The User object corresponding to the given user_id if found,
              otherwise None. Flask-Login handles cases where None is returned.
    """
    # Convert user_id to an integer as database IDs are typically integers.
    try:
        return User.query.get(int(user_id))
    except (ValueError, TypeError):
        # Handle cases where user_id might not be a valid integer
        return None
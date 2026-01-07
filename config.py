import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists.
# This is crucial for local development to manage sensitive information
# without hardcoding it directly into the codebase.
load_dotenv()

class Config:
    """
    Base configuration class. Contains default settings applicable to all environments
    and common settings loaded from environment variables. This class serves as the
    foundation for environment-specific configurations.
    """
    # General Flask Application Settings
    # The SECRET_KEY is used for signing session cookies, CSRF tokens, and other security-related functions.
    # It MUST be a strong, randomly generated string and kept confidential.
    SECRET_KEY = os.environ.get('SECRET_KEY')
    # Default Flask application entry point, useful for CLI commands.
    FLASK_APP = os.environ.get('FLASK_APP') or 'app.py'
    # Default environment, typically overridden by specific configuration classes or FLASK_ENV env var.
    FLASK_ENV = os.environ.get('FLASK_ENV') or 'development'

    # Database Settings (Flask-SQLAlchemy)
    # Disables the Flask-SQLAlchemy event system, which saves memory.
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Security Settings
    # Enable Cross-Site Request Forgery (CSRF) protection for Flask-WTF forms.
    WTF_CSRF_ENABLED = True
    # Number of rounds for bcrypt hashing. Higher values increase security but also computation time.
    # 13 is a common secure default for production.
    BCRYPT_LOG_ROUNDS = 13

    # Mail Settings (for password resets, notifications, etc.)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587) # Default TLS port
    # Check if TLS/SSL is explicitly enabled via environment variables.
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'False').lower() == 'true'
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'False').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    # List of email addresses to send application error reports to.
    ADMINS = ['admin@example.com']

    # AI/ML Module Settings (for integration with commercial LLM APIs)
    LLM_API_KEY = os.environ.get('LLM_API_KEY')
    LLM_API_BASE_URL = os.environ.get('LLM_API_BASE_URL') or 'https://api.openai.com/v1' # Example default for OpenAI

    # Caching and Asynchronous Task Queue Settings (Redis, Celery)
    # Redis URL for caching and as a message broker for Celery.
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    # Celery broker URL (where tasks are sent). Defaults to REDIS_URL.
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL') or REDIS_URL
    # Celery result backend URL (where task results are stored). Defaults to REDIS_URL.
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND') or REDIS_URL

    # Logging and Error Monitoring
    # Sentry DSN (Data Source Name) for error tracking and performance monitoring.
    SENTRY_DSN = os.environ.get('SENTRY_DSN')
    # Default logging level for the application.
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'

    # File Upload Settings
    # Directory where uploaded files will be stored.
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'app', 'static', 'uploads')
    # Maximum allowed content length for uploads (e.g., 16 MB).
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    # Pagination Settings for lists and tables
    ITEMS_PER_PAGE = 20

    # --- Critical Production Checks ---
    # Ensure SECRET_KEY is set in production for security.
    if FLASK_ENV == 'production' and not SECRET_KEY:
        raise ValueError("SECRET_KEY must be set in the environment for production.")

class DevelopmentConfig(Config):
    """
    Development configuration.
    Uses an SQLite database for simplicity, enables debug mode for detailed error
    messages, and sets a lower bcrypt round count for faster development iterations.
    """
    DEBUG = True
    TESTING = False # Explicitly set to False for development
    # SQLite database path for development.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
                              'sqlite:///' + os.path.join(os.getcwd(), 'app', 'dev.db')
    MAIL_DEBUG = True # Enable debugging for mail sending
    BCRYPT_LOG_ROUNDS = 4 # Faster hashing for development
    LOG_LEVEL = 'DEBUG' # Detailed logging in development
    FLASK_ENV = 'development'
    SENTRY_DSN = None # Sentry typically not used in local development

class TestingConfig(Config):
    """
    Testing configuration.
    Uses an in-memory SQLite database for fast, isolated tests, enables testing mode,
    and disables CSRF protection to simplify automated form testing.
    """
    DEBUG = True # Keep debug enabled to see errors during tests
    TESTING = True
    # In-memory SQLite database for testing, ensuring a clean state for each test run.
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False # Disable CSRF for easier form testing without token management
    BCRYPT_LOG_ROUNDS = 4 # Faster hashing for tests
    LOG_LEVEL = 'INFO'
    FLASK_ENV = 'testing'
    SENTRY_DSN = None # Sentry not used during tests

class ProductionConfig(Config):
    """
    Production configuration.
    Uses PostgreSQL for robust data management, disables debug mode, enforces secure
    cookie settings, and expects all critical configurations to be provided via
    environment variables for security and scalability.
    """
    DEBUG = False
    TESTING = False
    # PostgreSQL database URI, must be provided via environment variable.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

    # --- Critical Production Checks ---
    if SQLALCHEMY_DATABASE_URI is None:
        raise ValueError("DATABASE_URL must be set in the environment for production.")

    # Enhanced security for production environments
    SESSION_COOKIE_SECURE = True # Transmit session cookies only over HTTPS
    SESSION_COOKIE_HTTPONLY = True # Prevent client-side JavaScript access to session cookie
    REMEMBER_COOKIE_SECURE = True # For Flask-Login 'remember me' cookie
    REMEMBER_COOKIE_HTTPONLY = True # For Flask-Login 'remember me' cookie
    WTF_CSRF_ENABLED = True # Ensure CSRF is enabled and active

    BCRYPT_LOG_ROUNDS = 13 # Standard secure hashing rounds for production
    LOG_LEVEL = 'WARNING' # Log only warnings and errors in production to minimize verbosity
    FLASK_ENV = 'production'

    # Ensure critical services are configured for production
    if Config.MAIL_SERVER is None:
        raise ValueError("MAIL_SERVER, MAIL_USERNAME, MAIL_PASSWORD must be set in the environment for production email functionality.")
    if Config.LLM_API_KEY is None:
        # Depending on criticality, this could be a ValueError. For now, a warning.
        print("Warning: LLM_API_KEY not set for production. AI features might be limited or disabled.")
    if Config.SENTRY_DSN is None:
        # Error monitoring is crucial, but not necessarily app-halting.
        print("Warning: SENTRY_DSN not set for production. Error monitoring will be disabled.")
    if Config.REDIS_URL is None or Config.CELERY_BROKER_URL is None or Config.CELERY_RESULT_BACKEND is None:
        raise ValueError("REDIS_URL, CELERY_BROKER_URL, and CELERY_RESULT_BACKEND must be set for production for caching and async tasks.")


# A dictionary to easily select the configuration class based on an environment name.
config_by_name = dict(
    development=DevelopmentConfig,
    testing=TestingConfig,
    production=ProductionConfig,
    default=DevelopmentConfig # Fallback to development if environment is not specified
)

def get_config(env_name=None):
    """
    Retrieves the appropriate configuration object based on the provided environment name.
    If no environment name is given, it defaults to the 'FLASK_ENV' environment variable,
    or 'development' if 'FLASK_ENV' is not set.

    Args:
        env_name (str, optional): The name of the environment (e.g., 'development', 'testing', 'production').
                                  Defaults to None, which triggers environment variable lookup.

    Returns:
        Config: An instance of the configuration class for the specified environment.

    Raises:
        ValueError: If an unknown environment name is provided.
    """
    if env_name is None:
        env_name = os.environ.get('FLASK_ENV', 'development')

    config_class = config_by_name.get(env_name)
    if config_class is None:
        raise ValueError(f"Unknown environment: '{env_name}'. Available environments: {', '.join(config_by_name.keys())}")
    return config_class
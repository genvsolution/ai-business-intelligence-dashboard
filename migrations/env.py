import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# This is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add the project root to the path to allow importing application modules.
# This assumes the 'migrations' directory is directly under the project root.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# Import the Flask application and its SQLAlchemy instance.
# This is crucial for Alembic to discover your models defined via Flask-SQLAlchemy.
try:
    from app import create_app, db
except ImportError as e:
    raise ImportError(
        f"Could not import Flask app or db instance. "
        f"Ensure 'app' package is correctly structured and 'create_app', 'db' are available. "
        f"Error: {e}"
    )

# Create a Flask application instance and push an application context.
# This makes the app's configuration and the db.metadata available to Alembic.
# We assume create_app() can be called without arguments for migration purposes
# and loads appropriate configuration (e.g., from .env or FLASK_ENV).
app = create_app()
app_context = app.app_context()
app_context.push()

# target_metadata is where Alembic gets its database metadata.
# For Flask-SQLAlchemy, this is typically db.metadata, which aggregates all
# models registered with the SQLAlchemy instance.
target_metadata = db.metadata

def get_db_url() -> str:
    """
    Docstring: Retrieves the database URL from the Flask application's configuration.

    This function prioritizes the 'SQLALCHEMY_DATABASE_URI' key from the Flask
    application's configuration. This ensures that Alembic uses the same
    database connection string as the Flask application, respecting environment
    variables and configuration files used by the Flask app (e.g., .env).

    Raises:
        ValueError: If 'SQLALCHEMY_DATABASE_URI' is not found in the Flask app config.

    Returns:
        str: The database connection URL.
    """
    try:
        db_url = app.config.get('SQLALCHEMY_DATABASE_URI')
        if not db_url:
            raise ValueError(
                "SQLALCHEMY_DATABASE_URI not found in Flask app config. "
                "Ensure your Flask application's configuration (e.g., config.py, .env) "
                "is correctly loaded and defines this variable."
            )
        return db_url
    except Exception as e:
        context.log.error(f"Failed to retrieve database URL from Flask app config: {e}")
        # Re-raise to stop migration if DB URL is critical for operation
        raise

def run_migrations_offline() -> None:
    """
    Docstring: Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine.
    By skipping the Engine creation, we don't even need a DBAPI to be available.
    Calls to context.execute() here emit the given string to the script output.
    This mode is typically used for generating SQL scripts for migrations.
    """
    url = get_db_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """
    Docstring: Run migrations in 'online' mode.

    In this scenario, we need to create an Engine and associate a connection
    with the context. This mode connects to the database and applies migrations directly.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        url=get_db_url()  # Explicitly pass the URL from Flask app config
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # `compare_type=True` enables Alembic to detect changes in column types
            # (e.g., from String(50) to String(100)), which is very useful.
            compare_type=True,
            # `render_as_batch=True` is often useful for SQLite,
            # which has limited ALTER TABLE capabilities.
            # If using PostgreSQL primarily, it might not be strictly necessary,
            # but doesn't hurt. It wraps operations in batch statements.
            render_as_batch=True if 'sqlite' in get_db_url() else False
        )

        with context.begin_transaction():
            context.run_migrations()

# Determine whether to run migrations in offline or online mode based on Alembic's context.
try:
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()
finally:
    # Pop the application context to clean up resources.
    # This is important for long-running processes or if the script were part of a larger app.
    app_context.pop()
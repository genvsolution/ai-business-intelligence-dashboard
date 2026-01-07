from celery import Celery
from flask import Flask

# Initialize Celery without a specific configuration yet.
# The broker and backend URLs are set to None initially, as they will be
# configured dynamically when `celery_init_app` is called with the Flask app.
celery = Celery(__name__, broker=None, backend=None)

def celery_init_app(app: Flask) -> Celery:
    """
    Initializes the Celery application with Flask app configuration.

    This function configures the Celery instance using settings provided in
    the Flask application's configuration (`app.config`). It also wraps
    Celery tasks in a Flask application context, ensuring that tasks can
    access Flask's `current_app`, database connections, and other
    context-dependent resources.

    Args:
        app (Flask): The Flask application instance.

    Returns:
        Celery: The configured Celery application instance.
    """
    # Load Celery configuration from Flask app.config.
    # All Celery-specific settings should be prefixed with 'CELERY_' in Flask's config.
    # Set default values if not explicitly provided in app.config.
    app.config.setdefault('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    app.config.setdefault('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    app.config.setdefault('CELERY_ACCEPT_CONTENT', ['json'])
    app.config.setdefault('CELERY_TASK_SERIALIZER', 'json')
    app.config.setdefault('CELERY_RESULT_SERIALIZER', 'json')
    app.config.setdefault('CELERY_TIMEZONE', 'UTC')
    app.config.setdefault('CELERY_ENABLE_UTC', True)
    app.config.setdefault('CELERY_TASK_TRACK_STARTED', True) # Track STARTED state

    # Update Celery's configuration with values from Flask's config
    # by filtering keys that start with 'CELERY_'.
    celery_config = {key.replace('CELERY_', ''): value
                     for key, value in app.config.items()
                     if key.startswith('CELERY_')}
    celery.conf.update(celery_config)

    # Create a custom Task class that pushes a Flask application context
    # before executing the task and pops it afterwards. This is essential
    # for tasks that interact with Flask extensions or `current_app`.
    class ContextTask(celery.Task):
        """
        A custom Celery Task class that ensures Flask's application context
        is available during task execution.

        This allows tasks to safely access Flask-related resources, such as
        the database (via SQLAlchemy), current application configuration,
        and other extensions, just as they would in a regular request context.
        """
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask

    # Auto-discover tasks in modules specified by CELERY_IMPORTS if defined,
    # or ensure they are imported explicitly in the worker's startup script.
    # For a modular Flask app, tasks are typically defined in separate files
    # within the `app/tasks` package (e.g., `app/tasks/ai_tasks.py`).
    # The worker can then be started pointing to the Flask app factory
    # and Celery will discover tasks from specified imports.

    return celery

# Note: Actual task definitions (e.g., @celery.task) should reside in separate
# modules within this `app/tasks` package (e.g., `app/tasks/ai_tasks.py`,
# `app/tasks/data_tasks.py`) to keep this `__init__.py` clean and focused
# solely on Celery initialization. These modules can then be imported
# by the Celery worker or explicitly listed in `celery.conf.imports`.
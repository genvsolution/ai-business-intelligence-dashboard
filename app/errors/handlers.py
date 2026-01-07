from flask import Blueprint, render_template, current_app
from app.extensions import db  # Assuming db (SQLAlchemy instance) is initialized in app/extensions.py

# Create a Blueprint for error handlers.
# This allows us to register error handlers that apply globally to the application.
errors_bp = Blueprint('errors', __name__)

@errors_bp.app_errorhandler(403)
def forbidden_error(error):
    """
    Handles HTTP 403 Forbidden errors.

    This handler is triggered when a user attempts to access a resource
    they do not have permission for. It logs the event as a warning
    and renders a user-friendly 403 error page.

    Args:
        error: The exception object associated with the 403 error.

    Returns:
        A tuple containing the rendered HTML for the 403 page and the
        HTTP status code (403).
    """
    current_app.logger.warning(f"403 Forbidden Error: {error}")
    return render_template('errors/403.html'), 403

@errors_bp.app_errorhandler(404)
def not_found_error(error):
    """
    Handles HTTP 404 Not Found errors.

    This handler is triggered when a user requests a URL that does not
    exist in the application. It logs the event as a warning
    and renders a user-friendly 404 error page.

    Args:
        error: The exception object associated with the 404 error.

    Returns:
        A tuple containing the rendered HTML for the 404 page and the
        HTTP status code (404).
    """
    current_app.logger.warning(f"404 Not Found Error: {error}")
    return render_template('errors/404.html'), 404

@errors_bp.app_errorhandler(500)
def internal_error(error):
    """
    Handles HTTP 500 Internal Server Errors.

    This handler is triggered when an unexpected server-side error occurs.
    It performs several critical actions:
    1. Logs the full exception traceback for debugging purposes using the
       application's logger (which might be configured for Sentry, etc.).
    2. Attempts to rollback the database session to ensure that any
       incomplete or corrupted transactions are discarded, preventing
       the database from being left in an inconsistent state.
    3. Renders a user-friendly 500 error page, avoiding exposure of
       sensitive internal error details to the end-user.

    Args:
        error: The exception object associated with the 500 error.

    Returns:
        A tuple containing the rendered HTML for the 500 page and the
        HTTP status code (500).
    """
    # Log the full exception traceback. `logger.exception` is preferred
    # over `logger.error` when an exception object is available, as it
    # automatically includes the traceback information.
    current_app.logger.exception(f"500 Internal Server Error: {error}")

    # Rollback the database session. This is crucial for applications
    # using Flask-SQLAlchemy (or any ORM) to ensure that if an error
    # occurred during a transaction, the session is reset and not left
    # in a broken state for subsequent requests.
    # We check if `db` is available to avoid errors in environments
    # where it might not be initialized (e.g., specific test setups).
    if db:
        db.session.rollback()

    return render_template('errors/500.html'), 500

# Additional error handlers can be added here as needed, for example:
# @errors_bp.app_errorhandler(400)
# def bad_request_error(error):
#     """
#     Handles HTTP 400 Bad Request errors.
#     """
#     current_app.logger.warning(f"400 Bad Request Error: {error}")
#     return render_template('errors/400.html'), 400

# @errors_bp.app_errorhandler(401)
# def unauthorized_error(error):
#     """
#     Handles HTTP 401 Unauthorized errors (e.g., when Flask-Login redirects).
#     """
#     current_app.logger.warning(f"401 Unauthorized Error: {error}")
#     return render_template('errors/401.html'), 401
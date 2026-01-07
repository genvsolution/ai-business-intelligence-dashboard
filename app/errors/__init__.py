"""
Initializes the 'errors' Flask Blueprint for centralized error handling.

This blueprint will register custom error pages and handlers for HTTP
errors (e.g., 404 Not Found, 500 Internal Server Error) and potentially
application-specific exceptions.

It imports the `handlers` module to ensure that all error handling
functions defined within it are registered with this blueprint
when the blueprint is registered with the main Flask application.
"""
from flask import Blueprint

# Create a Blueprint instance for error handling.
# The name 'errors' is used to refer to this blueprint when registering
# URLs or templates, and the __name__ argument helps Flask locate
# resources within this blueprint's package.
errors = Blueprint('errors', __name__)

# Import the error handlers module.
# This ensures that the error handler functions (e.g., for 404, 500 errors)
# defined in app/errors/handlers.py are registered with this 'errors' blueprint
# when the application starts.
from app.errors import handlers
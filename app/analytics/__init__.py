"""
Initializes the 'analytics' blueprint for interactive sales analytics and data visualization.

This module sets up the Flask Blueprint for the analytics section of the application,
defining its name, template folder, static folder, and URL prefix. It also imports
the associated routes to register them with this blueprint, ensuring that all
analytics-related functionalities are properly organized and accessible under
the '/analytics' URL path.
"""

from flask import Blueprint

# Define and initialize the analytics blueprint.
# The blueprint will manage all routes, templates, and static files specific to the
# interactive sales analytics and data visualization features.
analytics_bp = Blueprint(
    'analytics',
    __name__,
    template_folder='templates',  # Specifies the directory for HTML templates relative to this file.
    static_folder='static',       # Specifies the directory for static assets (CSS, JS, images) relative to this file.
    url_prefix='/analytics'       # All routes registered with this blueprint will be prefixed with '/analytics'.
)

# Import the routes module to associate the view functions with this blueprint.
# This ensures that the URL routes defined in 'routes.py' are registered under the
# 'analytics_bp' blueprint, making them accessible in the application.
from . import routes
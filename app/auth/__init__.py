from flask import Blueprint

# Define and initialize the 'auth' blueprint.
# This blueprint encapsulates all authentication-related routes, forms,
# templates, and static assets, promoting modularity and separation of concerns.
#
# - 'auth': The name of the blueprint, used for URL prefixing and template lookup.
# - __name__: The name of the current Python module, used by Flask to locate
#             resources relative to this file.
# - template_folder: Specifies the directory for templates specific to this blueprint.
#                    Flask will look for templates in 'app/auth/templates'.
# - static_folder: Specifies the directory for static files (CSS, JS, images)
#                  specific to this blueprint. Flask will look in 'app/auth/static'.
auth_bp = Blueprint('auth', __name__, template_folder='templates', static_folder='static')

# Import the views (routes) module for the authentication blueprint.
# This ensures that all routes defined in `app/auth/routes.py` are registered
# with the `auth_bp` blueprint when the application initializes.
# This is a crucial step for Flask to discover and map URLs to their
# corresponding handler functions.
from app.auth import routes

# Import the forms module for the authentication blueprint.
# While forms don't directly define routes, importing them here ensures
# that any blueprint-specific configurations or dependencies within the
# forms module are properly loaded and associated with the 'auth' context.
from app.auth import forms

# Note: Models are typically defined in a central `app/models.py` file
# and imported directly into views or other modules as needed, rather
# than being imported directly into the blueprint's __init__.py.
# This maintains a cleaner separation of concerns and avoids circular imports
# if models depend on other parts of the application.
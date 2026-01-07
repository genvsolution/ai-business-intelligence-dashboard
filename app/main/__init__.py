from flask import Blueprint

# Create the 'main' blueprint instance.
# This blueprint will handle general application routes like the homepage,
# static pages, and common error pages.
main = Blueprint('main', __name__)

# Import views and error handlers to ensure they are registered with the blueprint.
# These imports are placed at the bottom of the file to avoid circular dependencies.
# For example, 'views.py' might import the 'main' blueprint itself.
from . import views
from . import errors
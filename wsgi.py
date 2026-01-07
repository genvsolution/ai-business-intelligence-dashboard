"""
WSGI entry point for the Flask application.

This file is responsible for importing the Flask application instance and making it available
to production WSGI servers like Gunicorn or uWSGI. It typically loads the application
using a factory function (e.g., `create_app`) and sets the appropriate configuration
based on environment variables.
"""

import os
from app import create_app

# Determine the configuration environment.
# By default, it uses 'production' unless FLASK_CONFIG environment variable is set.
# This allows different configurations (e.g., 'development', 'testing', 'production')
# to be loaded based on the deployment environment.
config_name = os.getenv('FLASK_CONFIG', 'production')

# Create the Flask application instance using the factory function.
# The 'application' variable is the standard name that WSGI servers
# (like Gunicorn or uWSGI) look for to run the Flask app.
application = create_app(config_name)

# Optional: If you want to run the app directly for quick local testing
# without a WSGI server (though not recommended for production setup),
# you could add a block like this. However, for a dedicated wsgi.py,
# it's usually kept minimal and focused solely on providing the app instance.
# if __name__ == '__main__':
#     application.run()
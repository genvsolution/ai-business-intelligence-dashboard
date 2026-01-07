import pytest
import json
from datetime import datetime, timedelta

# Assuming 'app' and 'db' are available from your main application setup
# You'll need to import your Flask app instance and SQLAlchemy db instance
# and potentially your models.
from app import create_app, db
from app.models import User, Role, Lead, LeadStatus, Task, Activity, SalesData  # Assuming these models exist
from app.utils.security import generate_password_hash # For creating test users

# --- Pytest Fixtures ---

@pytest.fixture(scope='session')
def flask_app():
    """
    Fixture for creating and configuring the Flask app for testing.
    Uses an in-memory SQLite database for integration tests.
    """
    app = create_app(config_object='config.TestingConfig') # Ensure you have a config.TestingConfig
    with app.app_context():
        db.create_all()
        # Create default roles if they don't exist
        if not Role.query.filter_by(name='Admin').first():
            db.session.add(Role(name='Admin', description='Administrator'))
        if not Role.query.filter_by(name='Sales Manager').first():
            db.session.add(Role(name='Sales Manager', description='Sales Manager'))
        if not Role.query.filter_by(name='Sales Representative').first():
            db.session.add(Role(name='Sales Representative',
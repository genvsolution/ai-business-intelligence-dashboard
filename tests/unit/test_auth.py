import pytest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import os
import secrets

# --- Minimal Flask App and DB Setup for Testing ---
# This setup mimics the project's SQLAlchemy and Flask-Login integration
# within a test context. In a real project, `db` and `User` would be
# imported from `app.models` and `app.__init__` or similar.

# Initialize SQLAlchemy outside of the app creation to be shared
db = SQLAlchemy()

class User(UserMixin, db.Model):
    """
    User model for authentication and authorization.
    Inherits from UserMixin for Flask-Login integration, providing properties
    like `is_authenticated`, `is_active`, `is_anonymous`, and `get_id()`.
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(64), default='Viewer', nullable=False)

    def set_password(self, password):
        """
        Hashes the provided password using werkzeug.security's generate_password_hash
        and stores it in the `password_hash` attribute.
        """
        if not isinstance(password, str):
            raise TypeError("Password must be a string.")
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        Checks if the provided plain-text password matches the stored hashed password
        using werkzeug.security's check_password_hash.

        Args:
            password (str): The plain-text password to check.

        Returns:
            bool: True if the password matches, False otherwise.
        """
        if not isinstance(password, str):
            return False # Or raise an error, depending on desired strictness
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        """
        Returns a string representation of the User object, useful for debugging.
        """
        return f'<User {self.username}>'

    # Flask-Login UserMixin methods are implicitly available or can be overridden.
    # get_id() is usually handled by UserMixin, but explicitly defining it
    # ensures it returns a string, which Flask-Login expects.
    def get_id(self):
        """
        Returns the unique ID for the user, required by Flask-Login.
        """
        return str(self.id)


def create_test_app():
    """
    Creates a minimal Flask application configured for testing.
    Uses an in-memory SQLite database to ensure tests are isolated
    and do not affect a real database.
    """
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # A secret key is required for session management by Flask-Login
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(16))

    db.init_app(app)

    # Define a user_loader for Flask-Login to find users by ID
    from flask_login import LoginManager
    login_manager = LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        """
        Flask-Login user loader callback.
        Given a user ID, it should return the corresponding User object.
        """
        return User.query.get(int(user_id))

    return app

@pytest.fixture(scope='session')
def app():
    """
    Pytest fixture for a Flask application instance.
    This fixture is scoped to 'session', meaning a single Flask app instance
    is created and used for all tests in the session.
    """
    _app = create_test_app()
    # Establish an application context before yielding the app
    # This ensures that operations like db.create_all() work correctly.
    with _app.app_context():
        db.create_all()
        yield _app
        # Teardown: Drop all tables after all tests in the session are done.
        db.drop_all()

@pytest.fixture(scope='function')
def db_session(app):
    """
    Pytest fixture for a database session, ensuring a clean state for each test function.
    It creates a new transaction for each test and rolls it back afterwards,
    effectively isolating database operations per test.
    """
    with app.app_context():
        # Use a nested transaction for isolation
        connection = db.engine.connect()
        transaction = connection.begin()
        options = dict(bind=connection, binds={})
        session = db.create_scoped_session(options=options)
        db.session = session

        yield session

        # Rollback the transaction and clean up the session after the test
        transaction.rollback()
        connection.close()
        session.remove()

# --- Unit Tests for Authentication Module ---

def test_user_creation(db_session):
    """
    Test the creation of a new User instance and its basic attributes.
    Ensures that a user can be instantiated and saved to the database.
    """
    user = User(username='testuser', email='test@example.com', role='Admin')
    user.set_password('password123')

    db_session.add(user)
    db_session.commit()

    retrieved_user = User.query.filter_by(username='testuser').first()

    assert retrieved_user is not None
    assert retrieved_user.username == 'testuser'
    assert retrieved_user.email == 'test@example.com'
    assert retrieved_user.role == 'Admin'
    assert retrieved_user.id is not None
    assert retrieved_user.password_hash is not None
    # Ensure password hash is not the plain text password
    assert retrieved_user.password_hash != 'password123'

def test_set_password_hashing(db_session):
    """
    Test the `set_password` method to ensure it correctly hashes the password.
    """
    user = User(username='hasher', email='hasher@example.com')
    plain_password = 'securepassword'
    user.set_password(plain_password)

    assert user.password_hash is not None
    # Verify that the hash is not the plain text password
    assert user.password_hash != plain_password
    # Verify that the hash looks like a bcrypt hash (starts with 'pbkdf2:sha256:')
    assert user.password_hash.startswith('pbkdf2:sha256:')

def test_check_password_correct(db_session):
    """
    Test the `check_password` method with the correct password.
    """
    user = User(username='checker', email='checker@example.com')
    plain_password = 'correcthorsebatterystaple'
    user.set_password(plain_password)
    db_session.add(user)
    db_session.commit()

    assert user.check_password(plain_password) is True

def test_check_password_incorrect(db_session):
    """
    Test the `check_password` method with an incorrect password.
    """
    user = User(username='wrongpass', email='wrong@example.com')
    user.set_password('rightpassword')
    db_session.add(user)
    db_session.commit()

    assert user.check_password('wrongpassword') is False
    assert user.check_password('Rightpassword') is False # Case sensitivity

def test_password_hashing_is_secure_and_salted(db_session):
    """
    Test that `set_password` generates different hashes for the same password
    due to salting, enhancing security.
    """
    user1 = User(username='user1', email='user1@example.com')
    user2 = User(username='user2', email='user2@example.com')
    common_password = 'mysecretpassword'

    user1.set_password(common_password)
    user2.set_password(common_password)

    db_session.add_all([user1, user2])
    db_session.commit()

    assert user1.password_hash != user2.password_hash
    assert user1.check_password(common_password) is True
    assert user2.check_password(common_password) is True

def test_user_mixin_properties(db_session):
    """
    Test the properties provided by Flask-Login's UserMixin.
    """
    user = User(username='mixinuser', email='mixin@example.com')
    user.set_password('password')
    db_session.add(user)
    db_session.commit()

    assert user.is_authenticated is True
    assert user.is_active is True
    assert user.is_anonymous is False
    assert user.get_id() == str(user.id)

def test_load_user_function(app, db_session):
    """
    Test the `load_user` function (user_loader) used by Flask-Login.
    This ensures that Flask-Login can correctly retrieve a user by their ID.
    """
    user = User(username='loaderuser', email='loader@example.com')
    user.set_password('loaderpass')
    db_session.add(user)
    db_session.commit()

    # Simulate Flask-Login's user_loader call
    with app.app_context():
        from flask_login import current_app
        # Access the user_loader from the LoginManager initialized in create_test_app
        # This is a bit indirect, but reflects how Flask-Login works.
        # Alternatively, if load_user was a standalone function, we'd call it directly.
        loaded_user = current_app.login_manager.user_loader(user.id)

    assert loaded_user is not None
    assert loaded_user.id == user.id
    assert loaded_user.username == 'loaderuser'
    assert loaded_user.email == 'loader@example.com'

def test_user_repr(db_session):
    """
    Test the __repr__ method of the User model.
    """
    user = User(username='repuser', email='rep@example.com')
    assert repr(user) == '<User repuser>'

def test_set_password_non_string_input():
    """
    Test that set_password raises an error for non-string inputs.
    """
    user = User(username='badpass', email='bad@example.com')
    with pytest.raises(TypeError, match="Password must be a string."):
        user.set_password(12345)
    with pytest.raises(TypeError, match="Password must be a string."):
        user.set_password(None)

def test_check_password_non_string_input(db_session):
    """
    Test that check_password handles non-string inputs gracefully (returns False).
    """
    user = User(username='checkbad', email='checkbad@example.com')
    user.set_password('validpass')
    db_session.add(user)
    db_session.commit()

    assert user.check_password(12345) is False
    assert user.check_password(None) is False
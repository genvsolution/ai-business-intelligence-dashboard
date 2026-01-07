import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

# Assume the Flask app and models are structured like this:
# from app import create_app, db
# from app.models import User, Role, Lead, Task, Activity, SalesData

# For the purpose of this test file, we'll mock a minimal app and models
# to ensure the tests are self-contained and runnable without the full app context.

# --- Mocking Flask App and Models for Testing ---
# In a real project, these would be imported from your actual app/models.py
# and app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize a SQLAlchemy instance without an app initially
db = SQLAlchemy()

# Define a many-to-many relationship table for User and Role
user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    """
    User model representing application users.
    Includes authentication methods and role management.
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    roles = db.relationship('Role', secondary=user_roles, lazy='subquery',
                            backref=db.backref('users', lazy=True))

    leads_created = db.relationship('Lead', backref='creator', lazy='dynamic', foreign_keys='Lead.created_by_id')
    leads_assigned = db.relationship('Lead', backref='assignee', lazy='dynamic', foreign_keys='Lead.assigned_to_id')
    tasks = db.relationship('Task', backref='assignee', lazy='dynamic')
    activities = db.relationship('Activity', backref='performer', lazy='dynamic')
    sales_data = db.relationship('SalesData', backref='sales_rep', lazy='dynamic')

    def set_password(self, password):
        """Hashes the given password and stores it."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Checks if the given password matches the stored hash."""
        return check_password_hash(self.password_hash, password)

    def has_role(self, role_name):
        """Checks if the user has a specific role."""
        return any(role.name == role_name for role in self.roles)

    def get_id(self):
        """Returns the user ID for Flask-Login."""
        return str(self.id)

    def __repr__(self):
        """Returns a string representation of the User object."""
        return f'<User {self.username}>'

class Role(db.Model):
    """
    Role model for defining user roles and permissions.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(256))

    def __repr__(self):
        """Returns a string representation of the Role object."""
        return f'<Role {self.name}>'

class Lead(db.Model):
    """
    Lead model representing potential customers in the sales pipeline.
    """
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(128), nullable=False)
    contact_person = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), index=True)
    phone = db.Column(db.String(64))
    status = db.Column(db.String(64), default='New', nullable=False) # e.g., New, Qualified, Contacted, Proposal Sent, Converted, Lost
    lead_source = db.Column(db.String(64)) # e.g., Web, Referral, Event
    industry = db.Column(db.String(64))
    budget = db.Column(db.Numeric(10, 2))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    tasks = db.relationship('Task', backref='lead', lazy='dynamic', cascade="all, delete-orphan")
    activities = db.relationship('Activity', backref='lead', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        """Returns a string representation of the Lead object."""
        return f'<Lead {self.company_name} - {self.contact_person}>'

class Task(db.Model):
    """
    Task model for managing follow-ups and actions related to leads.
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.DateTime)
    is_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'), nullable=False)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def mark_as_completed(self):
        """Marks the task as completed and sets the completion timestamp."""
        if not self.is_completed:
            self.is_completed = True
            self.completed_at = datetime.utcnow()

    def __repr__(self):
        """Returns a string representation of the Task object."""
        return f'<Task {self.title} for Lead {self.lead_id}>'

class Activity(db.Model):
    """
    Activity model for logging interactions with leads.
    """
    id = db.Column(db.Integer, primary_key=True)
    activity_type = db.Column(db.String(64), nullable=False) # e.g., Call, Email, Meeting, Note
    description = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'), nullable=False)
    performed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        """Returns a string representation of the Activity object."""
        return f'<Activity {self.activity_type} on Lead {self.lead_id} at {self.timestamp}>'

class SalesData(db.Model):
    """
    SalesData model for storing sales performance metrics.
    """
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    revenue = db.Column(db.Numeric(10, 2), nullable=False)
    volume = db.Column(db.Integer, nullable=False) # Number of units/deals
    product_category = db.Column(db.String(128))
    region = db.Column(db.String(64))
    lead_source = db.Column(db.String(64))
    customer_segment = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sales_rep_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        """Returns a string representation of the SalesData object."""
        return f'<SalesData {self.date} - Revenue: {self.revenue}>'

# --- End Mocking ---


@pytest.fixture(scope='session')
def app():
    """
    Fixture for creating a Flask test application.
    Configures an in-memory SQLite database for testing.
    """
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'test_secret_key' # Required for Flask-Login

    db.init_app(app)

    with app.app_context():
        # Ensure all models are imported so SQLAlchemy can create tables for them
        # (In a real app, this might be handled by importing models in __init__.py)
        pass # Models are already defined above for this test file

    return app

@pytest.fixture(scope='function')
def init_database(app):
    """
    Fixture to initialize and tear down the database for each test function.
    Creates all tables before a test and drops them afterwards.
    """
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()

@pytest.fixture
def test_user_data():
    """Provides test user data."""
    return {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123'
    }

@pytest.fixture
def admin_role_data():
    """Provides test admin role data."""
    return {
        'name': 'Admin',
        'description': 'Administrator role with full access.'
    }

@pytest.fixture
def sales_rep_role_data():
    """Provides test sales representative role data."""
    return {
        'name': 'Sales Representative',
        'description': 'Sales representative role with lead management access.'
    }

@pytest.fixture
def test_lead_data():
    """Provides test lead data."""
    return {
        'company_name': 'Acme Corp',
        'contact_person': 'John Doe',
        'email': 'john.doe@acmecorp.com',
        'phone': '123-456-7890',
        'lead_source': 'Web Form',
        'industry': 'Technology',
        'budget': 50000.00,
        'notes': 'Interested in enterprise solution.'
    }

@pytest.fixture
def test_task_data():
    """Provides test task data."""
    return {
        'title': 'Follow-up call',
        'description': 'Call John Doe regarding initial proposal.',
        'due_date': datetime.utcnow() + timedelta(days=7)
    }

@pytest.fixture
def test_activity_data():
    """Provides test activity data."""
    return {
        'activity_type': 'Call',
        'description': 'Called John Doe, left a voicemail.'
    }

@pytest.fixture
def test_sales_data():
    """Provides test sales data."""
    return {
        'date': datetime.strptime('2023-01-15', '%Y-%m-%d').date(),
        'revenue': 15000.00,
        'volume': 3,
        'product_category': 'Software',
        'region': 'North America',
        'lead_source': 'Referral',
        'customer_segment': 'Enterprise'
    }


class TestUserModel:
    """
    Unit tests for the User model.
    """
    def test_create_user(self, init_database, test_user_data):
        """
        Tests user creation and retrieval.
        """
        db = init_database
        user = User(username=test_user_data['username'], email=test_user_data['email'])
        user.set_password(test_user_data['password'])

        db.session.add(user)
        db.session.commit()

        retrieved_user = User.query.filter_by(username=test_user_data['username']).first()
        assert retrieved_user is not None
        assert retrieved_user.username == test_user_data['username']
        assert retrieved_user.email == test_user_data['email']
        assert retrieved_user.is_active is True
        assert retrieved_user.created_at is not None
        assert retrieved_user.updated_at is not None
        assert retrieved_user.check_password(test_user_data['password'])

    def test_password_hashing(self, init_database, test_user_data):
        """
        Tests password hashing and verification.
        """
        db = init_database
        user = User(username='hasher', email='hasher@example.com')
        user.set_password('secure_password')
        db.session.add(user)
        db.session.commit()

        assert user.password_hash is not None
        assert user.check_password('secure_password')
        assert not user.check_password('wrong_password')

    def test_user_roles(self, init_database, test_user_data, admin_role_data, sales_rep_role_data):
        """
        Tests user-role relationship and `has_role` method.
        """
        db = init_database
        user = User(username=test_user_data['username'], email=test_user_data['email'])
        user.set_password(test_user_data['password'])

        admin_role = Role(name=admin_role_data['name'], description=admin_role_data['description'])
        sales_role = Role(name=sales_rep_role_data['name'], description=sales_rep_role_data['description'])

        db.session.add_all([admin_role, sales_role])
        db.session.commit()

        user.roles.append(admin_role)
        db.session.commit()

        retrieved_user = User.query.filter_by(username=test_user_data['username']).first()
        assert retrieved_user is not None
        assert len(retrieved_user.roles) == 1
        assert retrieved_user.roles[0].name == 'Admin'
        assert retrieved_user.has_role('Admin')
        assert not retrieved_user.has_role('Sales Representative')

        # Add another role
        retrieved_user.roles.append(sales_role)
        db.session.commit()
        retrieved_user = User.query.filter_by(username=test_user_data['username']).first() # Refresh
        assert len(retrieved_user.roles) == 2
        assert retrieved_user.has_role('Admin')
        assert retrieved_user.has_role('Sales Representative')

    def test_flask_login_properties(self, init_database, test_user_data):
        """
        Tests Flask-Login required properties.
        """
        db = init_database
        user = User(username=test_user_data['username'], email=test_user_data['email'])
        user.set_password(test_user_data['password'])
        db.session.add(user)
        db.session.commit()

        assert user.is_active is True
        assert user.is_authenticated is True
        assert user.is_anonymous is False
        assert user.get_id() == str(user.id)

        # Test with inactive user
        user.is_active = False
        db.session.commit()
        assert user.is_active is False
        assert user.is_authenticated is False # Flask-Login considers inactive users not authenticated

    def test_user_repr(self, init_database, test_user_data):
        """
        Tests the __repr__ method of the User model.
        """
        db = init_database
        user = User(username=test_user_data['username'], email=test_user_data['email'])
        user.set_password(test_user_data['password'])
        db.session.add(user)
        db.session.commit()
        assert repr(user) == f'<User {test_user_data["username"]}>'

class TestRoleModel:
    """
    Unit tests for the Role model.
    """
    def test_create_role(self, init_database, admin_role_data):
        """
        Tests role creation and retrieval.
        """
        db = init_database
        role = Role(name=admin_role_data['name'], description=admin_role_data['description'])
        db.session.add(role)
        db.session.commit()

        retrieved_role = Role.query.filter_by(name=admin_role_data['name']).first()
        assert retrieved_role is not None
        assert retrieved_role.name == admin_role_data['name']
        assert retrieved_role.description == admin_role_data['description']

    def test_role_repr(self, init_database, admin_role_data):
        """
        Tests the __repr__ method of the Role model.
        """
        db = init_database
        role = Role(name=admin_role_data['name'], description=admin_role_data['description'])
        db.session.add(role)
        db.session.commit()
        assert repr(role) == f'<Role {admin_role_data["name"]}>'

class TestLeadModel:
    """
    Unit tests for the Lead model.
    """
    def test_create_lead(self, init_database, test_lead_data, test_user_data):
        """
        Tests lead creation with default values and relationships.
        """
        db = init_database
        user = User(username=test_user_data['username'], email=test_user_data['email'])
        user.set_password(test_user_data['password'])
        db.session.add(user)
        db.session.commit()

        lead = Lead(
            company_name=test_lead_data['company_name'],
            contact_person=test_lead_data['contact_person'],
            email=test_lead_data['email'],
            phone=test_lead_data['phone'],
            lead_source=test_lead_data['lead_source'],
            industry=test_lead_data['industry'],
            budget=test_lead_data['budget'],
            notes=test_lead_data['notes'],
            created_by_id=user.id,
            assigned_to_id=user.id
        )
        db.session.add(lead)
        db.session.commit()

        retrieved_lead = Lead.query.filter_by(company_name=test_lead_data['company_name']).first()
        assert retrieved_lead is not None
        assert retrieved_lead.company_name == test_lead_data['company_name']
        assert retrieved_lead.contact_person == test_lead_data['contact_person']
        assert retrieved_lead.status == 'New' # Default status
        assert retrieved_lead.created_by.username == user.username
        assert retrieved_lead.assignee.username == user.username
        assert retrieved_lead.created_at is not None
        assert retrieved_lead.updated_at is not None
        assert retrieved_lead.budget == test_lead_data['budget'] # Check Numeric type

    def test_update_lead_status(self, init_database, test_lead_data):
        """
        Tests updating a lead's status.
        """
        db = init_database
        lead = Lead(
            company_name=test_lead_data['company_name'],
            contact_person=test_lead_data['contact_person']
        )
        db.session.add(lead)
        db.session.commit()

        assert lead.status == 'New'

        lead.status = 'Qualified'
        db.session.commit()

        retrieved_lead = Lead.query.get(lead.id)
        assert retrieved_lead.status == 'Qualified'

    def test_lead_relationships_cascade_delete(self, init_database, test_lead_data, test_user_data, test_task_data, test_activity_data):
        """
        Tests lead relationships with tasks and activities, and cascade delete.
        """
        db = init_database
        user = User(username=test_user_data['username'], email=test_user_data['email'])
        user.set_password(test_user_data['password'])
        db.session.add(user)
        db.session.commit()

        lead = Lead(
            company_name=test_lead_data['company_name'],
            contact_person=test_lead_data['contact_person'],
            created_by_id=user.id,
            assigned_to_id=user.id
        )
        db.session.add(lead)
        db.session.commit()

        task1 = Task(title=test_task_data['title'], lead_id=lead.id, assigned_to_id=user.id)
        task2 = Task(title='Send follow-up email', lead_id=lead.id, assigned_to_id=user.id)
        activity1 = Activity(activity_type=test_activity_data['activity_type'], description=test_activity_data['description'], lead_id=lead.id, performed_by_id=user.id)
        activity2 = Activity(activity_type='Email', description='Sent initial info pack.', lead_id=lead.id, performed_by_id=user.id)

        db.session.add_all([task1, task2, activity1, activity2])
        db.session.commit()

        retrieved_lead = Lead.query.get(lead.id)
        assert retrieved_lead.tasks.count() == 2
        assert retrieved_lead.activities.count() == 2

        # Check backrefs
        assert task1.lead.id == lead.id
        assert activity1.lead.id == lead.id
        assert task1.assignee.id == user.id
        assert activity1.performer.id == user.id

        # Test cascade delete
        db.session.delete(retrieved_lead)
        db.session.commit()

        assert Lead.query.get(lead.id) is None
        assert Task.query.filter_by(lead_id=lead.id).count() == 0
        assert Activity.query.filter_by(lead_id=lead.id).count() == 0

    def test_lead_repr(self, init_database, test_lead_data):
        """
        Tests the __repr__ method of the Lead model.
        """
        db = init_database
        lead = Lead(
            company_name=test_lead_data['company_name'],
            contact_person=test_lead_data['contact_person']
        )
        db.session.add(lead)
        db.session.commit()
        assert repr(lead) == f'<Lead {test_lead_data["company_name"]} - {test_lead_data["contact_person"]}>'

class TestTaskModel:
    """
    Unit tests for the Task model.
    """
    def test_create_task(self, init_database, test_task_data, test_lead_data, test_user_data):
        """
        Tests task creation with relationships and default values.
        """
        db = init_database
        user = User(username=test_user_data['username'], email=test_user_data['email'])
        user.set_password(test_user_data['password'])
        db.session.add(user)
        db.session.commit()

        lead = Lead(company_name=test_lead_data['company_name'], contact_person=test_lead_data['contact_person'])
        db.session.add(lead)
        db.session.commit()

        task = Task(
            title=test_task_data['title'],
            description=test_task_data['description'],
            due_date=test_task_data['due_date'],
            lead_id=lead.id,
            assigned_to_id=user.id
        )
        db.session.add(task)
        db.session.commit()

        retrieved_task = Task.query.filter_by(title=test_task_data['title']).first()
        assert retrieved_task is not None
        assert retrieved_task.title == test_task_data['title']
        assert retrieved_task.description == test_task_data['description']
        assert retrieved_task.due_date == test_task_data['due_date']
        assert retrieved_task.is_completed is False
        assert retrieved_task.completed_at is None
        assert retrieved_task.lead.id == lead.id
        assert retrieved_task.assignee.id == user.id
        assert retrieved_task.created_at is not None

    def test_mark_task_as_completed(self, init_database, test_task_data, test_lead_data):
        """
        Tests the `mark_as_completed` method of the Task model.
        """
        db = init_database
        lead = Lead(company_name=test_lead_data['company_name'], contact_person=test_lead_data['contact_person'])
        db.session.add(lead)
        db.session.commit()

        task = Task(title=test_task_data['title'], lead_id=lead.id)
        db.session.add(task)
        db.session.commit()

        assert task.is_completed is False
        assert task.completed_at is None

        # Use patch to mock datetime.utcnow for predictable timestamping
        mock_completion_time = datetime(2023, 1, 1, 12, 0, 0)
        with patch('app.models.datetime') as mock_dt: # Adjust 'app.models' if your models are elsewhere
            mock_dt.utcnow.return_value = mock_completion_time
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw) # Allow other datetime calls
            task.mark_as_completed()
            db.session.commit()

        retrieved_task = Task.query.get(task.id)
        assert retrieved_task.is_completed is True
        assert retrieved_task.completed_at == mock_completion_time

        # Test marking an already completed task (should not change completed_at)
        old_completed_at = retrieved_task.completed_at
        with patch('app.models.datetime') as mock_dt:
            mock_dt.utcnow.return_value = datetime(2023, 1, 2, 12, 0, 0) # A later time
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            retrieved_task.mark_as_completed()
            db.session.commit()
        assert retrieved_task.completed_at == old_completed_at # Should remain the same

    def test_task_repr(self, init_database, test_task_data, test_lead_data):
        """
        Tests the __repr__ method of the Task model.
        """
        db = init_database
        lead = Lead(company_name=test_lead_data['company_name'], contact_person=test_lead_data['contact_person'])
        db.session.add(lead)
        db.session.commit()

        task = Task(title=test_task_data['title'], lead_id=lead.id)
        db.session.add(task)
        db.session.commit()
        assert repr(task) == f'<Task {test_task_data["title"]} for Lead {lead.id}>'

class TestActivityModel:
    """
    Unit tests for the Activity model.
    """
    def test_create_activity(self, init_database, test_activity_data, test_lead_data, test_user_data):
        """
        Tests activity creation with relationships and default timestamp.
        """
        db = init_database
        user = User(username=test_user_data['username'], email=test_user_data['email'])
        user.set_password(test_user_data['password'])
        db.session.add(user)
        db.session.commit()

        lead = Lead(company_name=test_lead_data['company_name'], contact_person=test_lead_data['contact_person'])
        db.session.add(lead)
        db.session.commit()

        activity = Activity(
            activity_type=test_activity_data['activity_type'],
            description=test_activity_data['description'],
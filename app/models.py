from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize SQLAlchemy instance. This will be bound to the Flask app later.
db = SQLAlchemy()

# --- Mixins ---
class TimestampMixin:
    """
    Mixin for adding `created_at` and `updated_at` timestamp fields to models.
    This ensures consistency across models for auditing and tracking changes.
    """
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

# --- Association Tables ---
# Define the many-to-many relationship between User and Role.
# This table stores which users have which roles.
user_roles = db.Table(
    'user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True)
)

# --- User Authentication & RBAC Models ---
class User(UserMixin, TimestampMixin, db.Model):
    """
    Represents a user in the system. Inherits from UserMixin for Flask-Login
    integration and TimestampMixin for creation/update tracking.
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)  # Stores hashed password
    is_active = db.Column(db.Boolean, default=True, nullable=False) # For deactivating users

    # Relationships
    # Many-to-many relationship with Role through the user_roles association table.
    roles = db.relationship('Role', secondary=user_roles, backref=db.backref('users', lazy='dynamic'))

    # One-to-many relationships for associated data
    assigned_leads = db.relationship('Lead', foreign_keys='Lead.assigned_to_id', backref='assignee', lazy='dynamic')
    created_tasks = db.relationship('LeadTask', foreign_keys='LeadTask.created_by_id', backref='creator', lazy='dynamic')
    assigned_tasks = db.relationship('LeadTask', foreign_keys='LeadTask.assigned_to_id', backref='task_assignee', lazy='dynamic')
    activities = db.relationship('LeadActivity', backref='user', lazy='dynamic')
    report_configurations = db.relationship('ReportConfiguration', backref='user', lazy='dynamic')

    def set_password(self, password):
        """
        Hashes the provided password using werkzeug.security and stores it.
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        Checks if the provided password matches the stored hash.
        """
        return check_password_hash(self.password_hash, password)

    def has_role(self, role_name):
        """
        Checks if the user has a specific role by name.
        """
        return any(role.name == role_name for role in self.roles)

    def __repr__(self):
        """
        Returns a string representation of the User object.
        """
        return f'<User {self.username}>'

class Role(TimestampMixin, db.Model):
    """
    Represents a user role, defining permissions and access levels within the application.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False) # e.g., 'Admin', 'Sales Manager', 'Sales Rep', 'Viewer'
    description = db.Column(db.String(200))

    def __repr__(self):
        """
        Returns a string representation of the Role object.
        """
        return f'<Role {self.name}>'

# --- Lead Management Models ---
class LeadStatus(TimestampMixin, db.Model):
    """
    Defines the possible statuses for a sales lead, enabling workflow management.
    e.g., 'New', 'Qualified', 'Contacted', 'Proposal Sent', 'Converted', 'Lost'.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(200))
    order = db.Column(db.Integer, default=0, nullable=False) # For ordering statuses in UI (e.g., Kanban)

    # Relationships
    leads = db.relationship('Lead', backref='status', lazy='dynamic')

    def __repr__(self):
        """
        Returns a string representation of the LeadStatus object.
        """
        return f'<LeadStatus {self.name}>'

class Lead(TimestampMixin, db.Model):
    """
    Represents a sales lead, tracking its details, current status, and assignment.
    """
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(128), index=True, nullable=False)
    contact_person = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), index=True)
    phone = db.Column(db.String(64))
    lead_source = db.Column(db.String(64)) # e.g., 'Website', 'Referral', 'Cold Call', 'Event'
    industry = db.Column(db.String(128))
    budget = db.Column(db.Numeric(10, 2)) # Estimated budget or deal size
    notes = db.Column(db.Text)
    is_converted = db.Column(db.Boolean, default=False, nullable=False) # Flag for converted leads

    # Foreign Keys
    status_id = db.Column(db.Integer, db.ForeignKey('lead_status.id'), nullable=False)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id')) # User responsible for this lead

    # Relationships
    # Cascade delete ensures activities and tasks are removed if the lead is deleted.
    activities = db.relationship('LeadActivity', backref='lead', lazy='dynamic', cascade="all, delete-orphan")
    tasks = db.relationship('LeadTask', backref='lead', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        """
        Returns a string representation of the Lead object.
        """
        return f'<Lead {self.company_name} - {self.contact_person}>'

class LeadActivity(TimestampMixin, db.Model):
    """
    Records interactions and activities related to a specific lead, providing a history
    of engagement (e.g., calls, emails, meetings, notes).
    """
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'), nullable=False)
    activity_type = db.Column(db.String(64), nullable=False) # e.g., 'Call', 'Email', 'Meeting', 'Note', 'Status Change'
    description = db.Column(db.Text, nullable=False)
    activity_timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False) # When the activity occurred

    # Foreign Key
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # User who performed the activity

    def __repr__(self):
        """
        Returns a string representation of the LeadActivity object.
        """
        return f'<LeadActivity {self.activity_type} for Lead {self.lead_id}>'

class LeadTask(TimestampMixin, db.Model):
    """
    Represents a task associated with a lead, assigned to a user, with a due date
    and completion status.
    """
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'), nullable=False)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.DateTime)
    completed = db.Column(db.Boolean, default=False, nullable=False)
    completed_at = db.Column(db.DateTime) # When the task was marked as completed

    # Foreign Keys
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id')) # User assigned to complete the task
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # User who created the task

    def __repr__(self):
        """
        Returns a string representation of the LeadTask object.
        """
        return f'<LeadTask {self.title} for Lead {self.lead_id}>'

# --- Sales Analytics & AI Insights Models (Configuration) ---
class ReportConfiguration(TimestampMixin, db.Model):
    """
    Stores user-defined configurations for generating custom reports or AI insights.
    This allows users to save and reuse specific filter sets, chart types, or
    parameters for data analysis and generation.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    report_name = db.Column(db.String(128), nullable=False)
    report_type = db.Column(db.String(64), nullable=False) # e.g., 'Sales Performance', 'Lead Conversion', 'AI Forecast'
    configuration_json = db.Column(db.Text, nullable=False) # JSON string storing filter parameters, chart options, etc.
    is_public = db.Column(db.Boolean, default=False, nullable=False) # Can other users see/use this configuration?

    def __repr__(self):
        """
        Returns a string representation of the ReportConfiguration object.
        """
        return f'<ReportConfig {self.report_name} by User {self.user_id}>'

# --- Utility Function for initialization ---
def init_app(app):
    """
    Initializes the SQLAlchemy database with the Flask application.
    This function should be called during the Flask app's setup phase.
    """
    db.init_app(app)
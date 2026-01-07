from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DecimalField, SubmitField, DateField, DateTimeField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional, ValidationError
# from wtforms_sqlalchemy.fields import QuerySelectField # Uncomment if using SQLAlchemy models directly for choices
from datetime import datetime

# --- IMPORTANT: Dynamic Choices ---
# In a production application, these choices would typically be loaded dynamically
# from a database (e.g., a 'Settings' or 'Lookup' table), configuration files,
# or by querying your SQLAlchemy models using QuerySelectField.
# For this example, they are hardcoded lists.

LEAD_SOURCES = [
    ('Website', 'Website'),
    ('Referral', 'Referral'),
    ('Cold Call', 'Cold Call'),
    ('Event', 'Event'),
    ('Partner', 'Partner'),
    ('Social Media', 'Social Media'),
    ('Advertisement', 'Advertisement'),
    ('Other', 'Other')
]

INDUSTRIES = [
    ('Technology', 'Technology'),
    ('Finance', 'Finance'),
    ('Healthcare', 'Healthcare'),
    ('Retail', 'Retail'),
    ('Manufacturing', 'Manufacturing'),
    ('Education', 'Education'),
    ('Real Estate', 'Real Estate'),
    ('Automotive', 'Automotive'),
    ('Telecommunications', 'Telecommunications'),
    ('Other', 'Other')
]

LEAD_STATUSES = [
    ('New', 'New'),
    ('Qualified', 'Qualified'),
    ('Contacted', 'Contacted'),
    ('Proposal Sent', 'Proposal Sent'),
    ('Negotiation', 'Negotiation'),
    ('Converted', 'Converted'),
    ('Lost', 'Lost'),
    ('On Hold', 'On Hold')
]

TASK_PRIORITIES = [
    ('Low', 'Low'),
    ('Medium', 'Medium'),
    ('High', 'High'),
    ('Urgent', 'Urgent')
]

TASK_STATUSES = [
    ('Pending', 'Pending'),
    ('In Progress', 'In Progress'),
    ('Completed', 'Completed'),
    ('Deferred', 'Deferred'),
    ('Cancelled', 'Cancelled')
]

ACTIVITY_TYPES = [
    ('Call', 'Call'),
    ('Email', 'Email'),
    ('Meeting', 'Meeting'),
    ('Note', 'Note'),
    ('Demo', 'Demo'),
    ('Follow-up', 'Follow-up'),
    ('Proposal Sent', 'Proposal Sent')
]

# Dummy users for 'assigned_to' field. In a real application, you would query
# your User model (e.g., from app.models import User) and populate this dynamically.
# Example for QuerySelectField:
# from app.models import User
# def get_users_query():
#     return User.query.order_by(User.username).all()
DUMMY_USERS = [
    (1, 'John Doe (Sales Rep)'),
    (2, 'Jane Smith (Sales Manager)'),
    (3, 'Peter Jones (Admin)'),
    (4, 'Alice Brown (Sales Rep)')
]

def get_dummy_users_for_select():
    """
    Returns a list of (value, label) tuples for user selection in a SelectField.
    In a real app, this would fetch users from the database.
    """
    return [(str(user_id), username) for user_id, username in DUMMY_USERS]


class LeadForm(FlaskForm):
    """
    Form for creating and editing lead information.
    Includes fields for core lead details, contact information,
    source, industry, budget, notes, and current status.
    """
    company_name = StringField(
        'Company Name',
        validators=[DataRequired(message="Company name is required."), Length(min=2, max=100)],
        render_kw={"placeholder": "e.g., Acme Corp"}
    )
    contact_person = StringField(
        'Contact Person',
        validators=[DataRequired(message="Contact person's name is required."), Length(min=2, max=100)],
        render_kw={"placeholder": "e.g., Jane Doe"}
    )
    email = StringField(
        'Email',
        validators=[DataRequired(message="Email is required."), Email(message="Invalid email address."), Length(max=120)],
        render_kw={"placeholder": "e.g., jane.doe@example.com"}
    )
    phone = StringField(
        'Phone Number',
        validators=[Optional(), Length(max=20)],
        render_kw={"placeholder": "e.g., +1-555-123-4567"}
    )
    lead_source = SelectField(
        'Lead Source',
        choices=LEAD_SOURCES,
        validators=[DataRequired(message="Please select a lead source.")]
    )
    industry = SelectField(
        'Industry',
        choices=INDUSTRIES,
        validators=[DataRequired(message="Please select an industry.")]
    )
    budget = DecimalField(
        'Estimated Budget ($)',
        validators=[Optional(), NumberRange(min=0, message="Budget must be a positive number.")],
        places=2,
        render_kw={"placeholder": "e.g., 50000.00"}
    )
    notes = TextAreaField(
        'Notes',
        validators=[Optional(), Length(max=500)],
        render_kw={"rows": 5, "placeholder": "Any relevant details about the lead, past interactions, or specific requirements..."}
    )
    status = SelectField(
        'Status',
        choices=LEAD_STATUSES,
        validators=[DataRequired(message="Please select a lead status.")]
    )
    submit = SubmitField('Save Lead')

    def validate_phone(self, field):
        """
        Custom validator for phone number format.
        Allows digits, spaces, hyphens, and a leading plus sign.
        More robust validation might use a specific regex pattern.
        """
        if field.data:
            # Remove common formatting characters for basic digit check
            cleaned_phone = field.data.replace(' ', '').replace('-', '')
            if not cleaned_phone.replace('+', '', 1).isdigit():
                raise ValidationError('Invalid phone number format. Only digits, spaces, hyphens, and a leading "+" are allowed.')
            if len(cleaned_phone) < 7: # Minimum reasonable length for a phone number
                raise ValidationError('Phone number is too short.')


class TaskForm(FlaskForm):
    """
    Form for creating and editing tasks associated with a specific lead.
    Includes fields for task title, description, due date, priority,
    assigned user, and task status.
    """
    title = StringField(
        'Task Title',
        validators=[DataRequired(message="Task title is required."), Length(min=2, max=150)],
        render_kw={"placeholder": "e.g., Follow-up call with Acme Corp on proposal"}
    )
    description = TextAreaField(
        'Description',
        validators=[Optional(), Length(max=500)],
        render_kw={"rows": 5, "placeholder": "Detailed description of the task, including specific actions or objectives."}
    )
    due_date = DateField(
        'Due Date',
        format='%Y-%m-%d', # Expected format from HTML date input
        validators=[DataRequired(message="Due date is required.")],
        render_kw={"placeholder": "YYYY-MM-DD"}
    )
    priority = SelectField(
        'Priority',
        choices=TASK_PRIORITIES,
        validators=[DataRequired(message="Please select a task priority.")]
    )
    # If using QuerySelectField for 'assigned_to' (recommended for database-backed choices):
    # assigned_to = QuerySelectField(
    #     'Assigned To',
    #     query_factory=get_users_query, # Function that returns all User objects
    #     get_pk=lambda user: user.id,
    #     get_label=lambda user: user.username,
    #     allow_blank=False,
    #     validators=[DataRequired(message="Please assign this task to a user.")]
    # )
    # Using SelectField with dummy choices for demonstration:
    assigned_to = SelectField(
        'Assigned To',
        choices=get_dummy_users_for_select(),
        validators=[DataRequired(message="Please assign this task to a user.")]
    )
    status = SelectField(
        'Status',
        choices=TASK_STATUSES,
        validators=[DataRequired(message="Please select a task status.")]
    )
    submit = SubmitField('Save Task')

    def validate_due_date(self, field):
        """
        Validate that the due date is not in the past.
        """
        if field.data and field.data < datetime.now().date():
            raise ValidationError('Due date cannot be in the past.')


class ActivityLogForm(FlaskForm):
    """
    Form for logging interactions and activities related to a lead.
    Captures the type of activity, a detailed description, and the
    date and time it occurred.
    """
    activity_type = SelectField(
        'Activity Type',
        choices=ACTIVITY_TYPES,
        validators=[DataRequired(message="Please select an activity type.")]
    )
    description = TextAreaField(
        'Description',
        validators=[DataRequired(message="Activity description is required."), Length(min=5, max=1000)],
        render_kw={"rows": 7, "placeholder": "Detailed description of the activity (e.g., discussed budget, sent proposal, next steps)."}
    )
    activity_datetime = DateTimeField(
        'Activity Date & Time',
        format='%Y-%m-%d %H:%M', # Expected format from HTML datetime-local input
        default=datetime.now, # Pre-fill with current date and time
        validators=[DataRequired(message="Activity date and time is required.")],
        render_kw={"placeholder": "YYYY-MM-DD HH:MM"}
    )
    submit = SubmitField('Log Activity')

    def validate_activity_datetime(self, field):
        """
        Validate that the activity date/time is not in the future.
        """
        if field.data and field.data > datetime.now():
            raise ValidationError('Activity date and time cannot be in the future.')
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, ValidationError, SelectField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Regexp
from app.models import User, Role # Assuming these models are defined in app.models

# --- Authentication Forms ---

class RegistrationForm(FlaskForm):
    """
    Form for user registration.
    Includes fields for username, email, password, and confirmation,
    along with strong password policy validation and uniqueness checks for username and email.
    """
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password',
                             validators=[DataRequired(), Length(min=8),
                                         Regexp('^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$',
                                                message='Password must be at least 8 characters long and include '
                                                        'uppercase, lowercase, digit, and special characters.')])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        """
        Validates if the provided username already exists in the database.
        Raises a ValidationError if the username is taken.
        """
        try:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That username is taken. Please choose a different one.')
        except Exception as e:
            # Log the error if necessary for debugging database issues
            raise ValidationError(f'An error occurred while validating username: {e}')

    def validate_email(self, email):
        """
        Validates if the provided email already exists in the database.
        Raises a ValidationError if the email is taken.
        """
        try:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email is taken. Please choose a different one.')
        except Exception as e:
            # Log the error if necessary for debugging database issues
            raise ValidationError(f'An error occurred while validating email: {e}')


class LoginForm(FlaskForm):
    """
    Form for user login.
    Includes fields for email, password, and a 'remember me' option.
    """
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password',
                             validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class RequestResetForm(FlaskForm):
    """
    Form for requesting a password reset.
    Requires the user's email to send a reset link.
    """
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

    def validate_email(self, email):
        """
        Validates if the provided email exists in the database before allowing a password reset.
        Raises a ValidationError if no account is associated with the email.
        """
        try:
            user = User.query.filter_by(email=email.data).first()
            if user is None:
                raise ValidationError('There is no account with that email. You must register first.')
        except Exception as e:
            # Log the error if necessary for debugging database issues
            raise ValidationError(f'An error occurred while validating email for reset: {e}')


class ResetPasswordForm(FlaskForm):
    """
    Form for setting a new password during a password reset process.
    Includes fields for the new password and its confirmation, with strong password policy validation.
    """
    password = PasswordField('New Password',
                             validators=[DataRequired(), Length(min=8),
                                         Regexp('^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$',
                                                message='Password must be at least 8 characters long and include '
                                                        'uppercase, lowercase, digit, and special characters.')])
    confirm_password = PasswordField('Confirm New Password',
                                     validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Reset Password')


# --- Admin Forms for User and Role Management ---

class UserAdminForm(FlaskForm):
    """
    Form for creating and editing user accounts in the administrative interface.
    Allows modification of username, email, role, and active status.
    Includes uniqueness checks for username and email, accommodating edits of existing users.
    """
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    role_id = SelectField('Role', coerce=int, validators=[DataRequired()])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save User')

    def __init__(self, original_username=None, original_email=None, *args, **kwargs):
        """
        Initializes the UserAdminForm.
        Args:
            original_username (str, optional): The original username of the user being edited.
                                               Used to allow the current user's username to pass uniqueness validation.
            original_email (str, optional): The original email of the user being edited.
                                            Used to allow the current user's email to pass uniqueness validation.
        """
        super().__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email
        # Populate role choices dynamically from the database
        try:
            self.role_id.choices = [(role.id, role.name) for role in Role.query.order_by(Role.name).all()]
        except Exception as e:
            # In case of database connection issues during form initialization
            print(f"Error populating role choices: {e}")
            self.role_id.choices = [] # Provide empty choices to prevent application crash

    def validate_username(self, username):
        """
        Validates if the username already exists, excluding the original username if editing an existing user.
        Raises a ValidationError if the username is taken by another user.
        """
        if username.data != self.original_username:
            try:
                user = User.query.filter_by(username=username.data).first()
                if user:
                    raise ValidationError('That username is already taken by another user. Please choose a different one.')
            except Exception as e:
                raise ValidationError(f'An error occurred while validating username: {e}')

    def validate_email(self, email):
        """
        Validates if the email already exists, excluding the original email if editing an existing user.
        Raises a ValidationError if the email is taken by another user.
        """
        if email.data != self.original_email:
            try:
                user = User.query.filter_by(email=email.data).first()
                if user:
                    raise ValidationError('That email is already taken by another user. Please choose a different one.')
            except Exception as e:
                raise ValidationError(f'An error occurred while validating email: {e}')


class RoleAdminForm(FlaskForm):
    """
    Form for creating and editing roles in the administrative interface.
    Allows modification of role name and description.
    Includes uniqueness checks for role name, accommodating edits of existing roles.
    """
    name = StringField('Role Name',
                       validators=[DataRequired(), Length(min=2, max=50)])
    description = TextAreaField('Description',
                                validators=[Length(max=200)],
                                render_kw={"rows": 3, "placeholder": "A brief description of this role's permissions or purpose."})
    submit = SubmitField('Save Role')

    def __init__(self, original_name=None, *args, **kwargs):
        """
        Initializes the RoleAdminForm.
        Args:
            original_name (str, optional): The original name of the role being edited.
                                           Used to allow the current role's name to pass uniqueness validation.
        """
        super().__init__(*args, **kwargs)
        self.original_name = original_name

    def validate_name(self, name):
        """
        Validates if the role name already exists, excluding the original name if editing an existing role.
        Raises a ValidationError if a role with the same name already exists.
        """
        if name.data != self.original_name:
            try:
                role = Role.query.filter_by(name=name.data).first()
                if role:
                    raise ValidationError('A role with that name already exists. Please choose a different one.')
            except Exception as e:
                raise ValidationError(f'An error occurred while validating role name: {e}')
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
import functools

from app import db
from app.models import User, Role
from app.auth.forms import (
    LoginForm, RegistrationForm, RequestResetForm, ResetPasswordForm,
    UserForm, RoleForm, AssignRoleForm
)
from app.utils.email import send_email # Assuming this utility exists

auth_bp = Blueprint('auth', __name__, template_folder='templates')

# Custom decorator for role-based access control
def role_required(role_names):
    """
    Decorator to restrict access to a route based on user roles.
    Accepts a single role name (string) or a list of role names (list of strings).
    If the current user does not have any of the specified roles,
    they will be redirected to the login page or receive a 403 Forbidden error.
    """
    if not isinstance(role_names, list):
        role_names = [role_names]

    def decorator(f):
        @login_required
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                # This case should ideally be handled by @login_required,
                # but it's a good fallback for explicit clarity.
                flash('You need to be logged in to access this page.', 'warning')
                return redirect(url_for('auth.login'))

            # Check if the user has any of the required roles
            user_roles = {role.name for role in current_user.roles}
            if not any(required_role in user_roles for required_role in role_names):
                flash('You do not have the required permissions to access this page.', 'danger')
                abort(403) # Forbidden
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- User Authentication Routes ---

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Handles user registration.
    If the user is already authenticated, they are redirected to the main index.
    On successful registration, a new user is created with a hashed password
    and assigned a default 'Viewer' role (creating it if it doesn't exist).
    """
    if current_user.is_authenticated:
        flash('You are already logged in.', 'info')
        return redirect(url_for('main.index')) # Assuming a 'main' blueprint with an index route

    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        try:
            # Assign a default role, e.g., 'Viewer'
            default_role = Role.query.filter_by(name='Viewer').first()
            if not default_role:
                # If 'Viewer' role doesn't exist, create it
                current_app.logger.warning("Default 'Viewer' role not found. Creating it.")
                default_role = Role(name='Viewer', description='Basic user with view-only access.')
                db.session.add(default_role)
                db.session.commit() # Commit the role creation to make it available immediately

            user = User(
                username=form.username.data,
                email=form.email.data,
                password_hash=hashed_password,
                is_active=True # New users are active by default
            )
            user.roles.append(default_role) # Assign default role
            db.session.add(user)
            db.session.commit()
            flash('Your account has been created! You are now able to log in.', 'success')
            return redirect(url_for('auth.login'))
        except IntegrityError:
            db.session.rollback()
            flash('Registration failed. Username or email already exists.', 'danger')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error during user registration: {e}")
            flash('An unexpected error occurred during registration. Please try again.', 'danger')
    return render_template('auth/register.html', title='Register', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handles user login.
    If the user is already authenticated, they are redirected to the main index.
    On successful login, the user's session is established using Flask-Login.
    """
    if current_user.is_authenticated:
        flash('You are already logged in.', 'info')
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            if not user.is_active:
                flash('Your account is deactivated. Please contact an administrator.', 'danger')
                return redirect(url_for('auth.login'))
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(next_page or url_for('main.index'))
        else:
            flash('Login Unsuccessful. Please check email and password.', 'danger')
    return render_template('auth/login.html', title='Login', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """
    Handles user logout.
    Terminates the user's session and redirects to the login page.
    """
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


# --- Password Management Routes ---

@auth_bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    """
    Handles requesting a password reset.
    If an account with the provided email exists, a password reset token
    is generated and sent to the user's email address.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    
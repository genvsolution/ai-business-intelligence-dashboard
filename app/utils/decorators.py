import functools
from flask import abort, flash, redirect, url_for, current_app, request
from flask_login import current_user, login_required as flask_login_required

def login_required(f):
    """
    Custom decorator for routes that require user authentication.

    This decorator ensures that a user is logged in before accessing the
    decorated route. If the user is not authenticated, a flash message
    is displayed, and the user is redirected to the login page. The
    original URL is stored as a 'next' parameter for redirection after login.

    This decorator provides a consistent user experience by always showing
    a flash message upon redirection for unauthenticated access.

    Args:
        f (function): The view function to be decorated.

    Returns:
        function: The decorated function.
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in to access this page.", "info")
            login_view = current_app.config.get('LOGIN_VIEW', 'auth.login')
            return redirect(url_for(login_view, next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    """
    Decorator to restrict access to a route based on user roles.

    This decorator ensures that:
    1. The user is authenticated (handled by an internal call to `login_required`).
    2. The authenticated user possesses at least one of the specified roles.

    If the user is not authenticated, they will be redirected to the login page
    (with a flash message). If the user is authenticated but does not have
    any of the required roles, an HTTP 403 Forbidden error will be raised
    with an appropriate flash message.

    This decorator assumes that `current_user` has a `roles` attribute which
    is an iterable of objects, and each object has a `name` attribute (e.g.,
    `current_user.roles` could be a list of `Role` objects, where `Role.name`
    is 'Admin', 'Sales Manager', etc.).

    Args:
        *roles: Variable length argument list of role names (strings) that are
                allowed to access the decorated function.

    Returns:
        function: The decorated function if the user has the required role(s).
                  Otherwise, redirects or aborts.
    """
    def decorator(f):
        @functools.wraps(f)
        @login_required  # Ensure user is logged in first using our custom decorator
        def decorated_function(*args, **kwargs):
            # At this point, current_user is guaranteed to be authenticated
            # because @login_required has already run and redirected if not.

            # Extract the names of roles possessed by the current user
            # This assumes current_user.roles is an iterable of Role objects
            # and each Role object has a 'name' attribute.
            user_roles = {role.name for role in current_user.roles}

            # Check if the user has any of the required roles
            if not any(r in user_roles for r in roles):
                flash("You do not have the necessary permissions to access this page.", "danger")
                abort(403)  # Forbidden

            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """
    Decorator to restrict access to a route to 'Admin' users only.

    This is a convenience decorator that uses `role_required('Admin')`.
    It ensures the user is logged in and has the 'Admin' role.

    Args:
        f (function): The view function to be decorated.

    Returns:
        function: The decorated function.
    """
    return role_required('Admin')(f)
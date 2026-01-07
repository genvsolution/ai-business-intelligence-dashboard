"""
Initializes the 'utils' package, providing a centralized location for helper functions,
decorators, and common utilities used across the application.

This package aims to encapsulate reusable logic, promote code modularity, and
reduce redundancy. It includes submodules for security, data processing,
email services, and custom decorators, among others.

Key decorators and utility functions are directly imported here for convenience,
allowing them to be accessed via `from app.utils import some_function_or_decorator`.
"""

# Import commonly used decorators from the 'decorators' submodule.
# These are essential for role-based access control and authentication flow.
from .decorators import role_required, login_required_roles

# Import security-related helper functions from the 'security' submodule.
# These include password hashing, verification, and token generation for features
# like password resets, adhering to project's security measures (Bcrypt).
from .security import hash_password, verify_password, generate_uuid_token

# Import general utility functions from the 'helpers' submodule.
# These provide common functionalities like date/time formatting and string manipulation.
from .helpers import format_datetime, generate_unique_slug

# Import email sending functionality from the 'email' submodule.
# This is used for sending notifications, password reset links, and other system emails.
from .email import send_email

# Define __all__ to explicitly specify what symbols are exported when
# `from app.utils import *` is used. This is good practice for package interfaces
# and helps with static analysis and code clarity.
__all__ = [
    'role_required',
    'login_required_roles',
    'hash_password',
    'verify_password',
    'generate_uuid_token',
    'format_datetime',
    'generate_unique_slug',
    'send_email',
]
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db

# Association table for User and Role (Many-to-Many)
user_roles = db.Table(
    'user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True)
)

# Association table for Role and Permission (Many-to-Many)
role_permissions = db.Table(
    'role_permissions',
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permission.id'), primary_key=True)
)

class Permission(db.Model):
    """
    Represents a specific permission within the application.
    Permissions are granular actions or access rights that can be assigned to roles.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255))

    def __repr__(self):
        """
        Returns a string representation of the Permission object.
        """
        return f'<Permission {self.name}>'

class Role(db.Model):
    """
    Represents a user role within the application, grouping a set of permissions.
    Users are assigned roles, and roles grant permissions.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255))

    # Many-to-Many relationship with Permission
    permissions = db.relationship(
        'Permission',
        secondary=role_permissions,
        backref=db.backref('roles', lazy='dynamic'),
        lazy='dynamic'
    )

    def __repr__(self):
        """
        Returns a string representation of the Role object.
        """
        return f'<Role {self.name}>'

    def add_permission(self, permission: Permission) -> None:
        """
        Adds a permission to this role if it's not already present.

        Args:
            permission: The Permission object to add.
        """
        if not self.has_permission(permission.name):
            self.permissions.append(permission)

    def remove_permission(self, permission: Permission) -> None:
        """
        Removes a permission from this role.

        Args:
            permission: The Permission object to remove.
        """
        if self.has_permission(permission.name):
            self.permissions.remove(permission)

    def has_permission(self, permission_name: str) -> bool:
        """
        Checks if this role has a specific permission.

        Args:
            permission_name: The name of the permission to check.

        Returns:
            True if the role has the permission, False otherwise.
        """
        return self.permissions.filter_by(name=permission_name).first() is not None

class User(UserMixin, db.Model):
    """
    Represents a user in the application, integrating with Flask-Login
    for session management and providing methods for password handling
    and role/permission checking.
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True, nullable=False)
    email = db.Column(db.String(120), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Many-to-Many relationship with Role
    roles = db.relationship(
        'Role',
        secondary=user_roles,
        backref=db.backref('users', lazy='dynamic'),
        lazy='dynamic'
    )

    def __repr__(self):
        """
        Returns a string representation of the User object.
        """
        return f'<User {self.username}>'

    def set_password(self, password: str) -> None:
        """
        Hashes the given password using werkzeug.security and stores it.

        Args:
            password: The plain-text password to hash.
        """
        try:
            self.password_hash = generate_password_hash(password)
        except Exception as e:
            # Log the error or raise a custom exception
            print(f"Error hashing password: {e}")
            raise

    def check_password(self, password: str) -> bool:
        """
        Checks if the provided plain-text password matches the stored hash.

        Args:
            password: The plain-text password to check.

        Returns:
            True if the password matches, False otherwise.
        """
        try:
            return check_password_hash(self.password_hash, password)
        except Exception as e:
            # Log the error or handle it as appropriate (e.g., return False for safety)
            print(f"Error checking password: {e}")
            return False

    def add_role(self, role: Role) -> None:
        """
        Adds a role to the user if it's not already assigned.

        Args:
            role: The Role object to assign.
        """
        if not self.has_role(role.name):
            self.roles.append(role)

    def remove_role(self, role: Role) -> None:
        """
        Removes a role from the user.

        Args:
            role: The Role object to remove.
        """
        if self.has_role(role.name):
            self.roles.remove(role)

    def has_role(self, role_name: str) -> bool:
        """
        Checks if the user has a specific role.

        Args:
            role_name: The name of the role to check.

        Returns:
            True if the user has the role, False otherwise.
        """
        return self.roles.filter_by(name=role_name).first() is not None

    def can(self, permission_name: str) -> bool:
        """
        Checks if the user has a specific permission through any of their assigned roles.

        Args:
            permission_name: The name of the permission to check.

        Returns:
            True if the user has the permission, False otherwise.
        """
        for role in self.roles:
            if role.has_permission(permission_name):
                return True
        return False

    def is_administrator(self) -> bool:
        """
        Convenience method to check if the user has 'admin_access' permission.

        Returns:
            True if the user has 'admin_access', False otherwise.
        """
        return self.can('admin_access')

# Flask-Login user loader function
@db.event.listens_for(User, 'before_insert')
def receive_before_insert(mapper, connection, target):
    """
    SQLAlchemy event listener to set `created_at` for new User objects.
    """
    target.created_at = datetime.utcnow()

@db.event.listens_for(User, 'before_update')
def receive_before_update(mapper, connection, target):
    """
    SQLAlchemy event listener to set `updated_at` for updated User objects.
    """
    target.updated_at = datetime.utcnow()
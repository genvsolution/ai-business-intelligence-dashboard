import os
from flask import Blueprint, current_app
from flask_login import current_user
from . import routes, models
from app import db, login_manager
from app.models import User, Role, Permission
from app.utils.decorators import permission_required

# Define the Blueprint for the leads module
leads_bp = Blueprint('leads', __name__, template_folder='templates', static_folder='static')

# Register routes with the blueprint
routes.init_app(leads_bp)

@login_manager.user_loader
def load_user(user_id):
    """
    Reloads the user object from the user ID stored in the session.
    This function is required by Flask-Login.
    """
    return User.query.get(int(user_id))

@leads_bp.before_request
def before_request():
    """
    This function runs before every request to the leads blueprint.
    It can be used for common tasks like checking user permissions or
    setting up context variables.
    """
    # Example: Log access to leads module
    if current_user.is_authenticated:
        current_app.logger.debug(f"User {current_user.email} accessing leads module.")
    else:
        current_app.logger.debug("Unauthenticated user accessing leads module.")

    # You could also enforce a general permission here, e.g.,
    # if not current_user.can(Permission.VIEW_LEADS):
    #     abort(403) # Or redirect to an unauthorized page

def create_leads_initial_data():
    """
    Creates initial data for the leads module, such as default lead statuses
    or permissions, if they don't already exist.
    This function should be called during application initialization or setup.
    """
    current_app.logger.info("Checking for initial leads module data...")

    # Example: Ensure default lead statuses exist
    default_statuses = ['New', 'Qualified', 'Contacted', 'Proposal Sent', 'Negotiation', 'Converted', 'Lost']
    existing_statuses = [s.name for s in models.LeadStatus.query.all()]

    for status_name in default_statuses:
        if status_name not in existing_statuses:
            try:
                new_status = models.LeadStatus(name=status_name)
                db.session.add(new_status)
                current_app.logger.info(f"Added default lead status: {status_name}")
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error adding default lead status '{status_name}': {e}")
    
    # Example: Ensure lead-specific permissions exist
    leads_permissions = {
        'VIEW_LEADS': 'View all leads and lead details.',
        'CREATE_LEAD': 'Create new leads.',
        'EDIT_LEAD': 'Edit existing lead information.',
        'DELETE_LEAD': 'Delete leads.',
        'MANAGE_LEAD_STATUSES': 'Manage lead status workflows.'
    }

    for perm_name, perm_desc in leads_permissions.items():
        if not Permission.query.filter_by(name=perm_name).first():
            try:
                new_permission = Permission(name=perm_name, description=perm_desc)
                db.session.add(new_permission)
                current_app.logger.info(f"Added lead-specific permission: {perm_name}")
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error adding permission '{perm_name}': {e}")

    # Example: Assign lead permissions to roles (e.g., Sales Representative, Sales Manager, Admin)
    # This part assumes roles already exist or are created elsewhere.
    # It's better to manage role-permission assignments in a dedicated setup script or admin interface.
    # For demonstration, we'll assign some here.
    try:
        admin_role = Role.query.filter_by(name='Admin').first()
        sales_manager_role = Role.query.filter_by(name='Sales Manager').first()
        sales_rep_role = Role.query.filter_by(name='Sales Representative').first()
        viewer_role = Role.query.filter_by(name='Viewer').first()

        if admin_role:
            for perm_name in leads_permissions.keys():
                perm = Permission.query.filter_by(name=perm_name).first()
                if perm and perm not in admin_role.permissions:
                    admin_role.permissions.append(perm)
                    current_app.logger.info(f"Assigned {perm_name} to Admin role.")
        
        if sales_manager_role:
            for perm_name in ['VIEW_LEADS', 'CREATE_LEAD', 'EDIT_LEAD', 'DELETE_LEAD', 'MANAGE_LEAD_STATUSES']:
                perm = Permission.query.filter_by(name=perm_name).first()
                if perm and perm not in sales_manager_role.permissions:
                    sales_manager_role.permissions.append(perm)
                    current_app.logger.info(f"Assigned {perm_name} to Sales Manager role.")

        if sales_rep_role:
            for perm_name in ['VIEW_LEADS', 'CREATE_LEAD', 'EDIT_LEAD']:
                perm = Permission.query.filter_by(name=perm_name).first()
                if perm and perm not in sales_rep_role.permissions:
                    sales_rep_role.permissions.append(perm)
                    current_app.logger.info(f"Assigned {perm_name} to Sales Representative role.")

        if viewer_role:
            perm = Permission.query.filter_by(name='VIEW_LEADS').first()
            if perm and perm not in viewer_role.permissions:
                viewer_role.permissions.append(perm)
                current_app.logger.info(f"Assigned VIEW_LEADS to Viewer role.")

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error assigning leads permissions to roles: {e}")

    try:
        db.session.commit()
        current_app.logger.info("Leads module initial data check complete and committed.")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error committing leads module initial data: {e}")

# This function can be called from the main app factory to initialize the blueprint
def init_app(app):
    """
    Initializes the leads blueprint with the Flask application.
    Registers the blueprint and ensures initial data is set up.

    Args:
        app (Flask): The Flask application instance.
    """
    app.register_blueprint(leads_bp, url_prefix='/leads')

    # Ensure initial data is created when the app context is available
    @app.before_first_request
    def setup_leads_initial_data():
        with app.app_context():
            create_leads_initial_data()

    current_app.logger.info("Leads blueprint initialized and registered.")
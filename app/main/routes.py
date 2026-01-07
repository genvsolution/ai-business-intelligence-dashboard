from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user

# Define the blueprint for general application routes.
# This blueprint will handle public-facing informational pages and the main landing page.
bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """
    Renders the home page of the application.

    If a user is currently authenticated, they are redirected to the dashboard
    to provide a seamless experience for logged-in users. Otherwise, the public
    landing page is displayed.

    Returns:
        A rendered HTML template for the home page or a redirect response.
    """
    if current_user.is_authenticated:
        # Redirect authenticated users to their main dashboard.
        # Assumes a 'dashboard' blueprint exists with an 'index' route.
        return redirect(url_for('dashboard.index'))
    # For unauthenticated users, display the public landing page.
    return render_template('main/index.html', title='Welcome')

@bp.route('/about')
def about():
    """
    Renders the 'About Us' informational page.

    This page provides general information about the application or organization.

    Returns:
        A rendered HTML template for the 'About Us' page.
    """
    return render_template('main/about.html', title='About Us')

@bp.route('/contact')
def contact():
    """
    Renders the 'Contact Us' informational page.

    This page typically provides contact details or a contact form. For simplicity
    in this blueprint, it renders a static informational page. If a contact form
    were to be implemented, it would involve Flask-WTF for form handling and
    potentially email sending logic, which might be handled in a separate module
    or a more specialized blueprint.

    Returns:
        A rendered HTML template for the 'Contact Us' page.
    """
    return render_template('main/contact.html', title='Contact Us')

@bp.route('/terms')
def terms():
    """
    Renders the 'Terms of Service' informational page.

    This page outlines the legal terms and conditions for using the application.

    Returns:
        A rendered HTML template for the 'Terms of Service' page.
    """
    return render_template('main/terms.html', title='Terms of Service')

@bp.route('/privacy')
def privacy():
    """
    Renders the 'Privacy Policy' informational page.

    This page details how user data is collected, used, and protected.

    Returns:
        A rendered HTML template for the 'Privacy Policy' page.
    """
    return render_template('main/privacy.html', title='Privacy Policy')
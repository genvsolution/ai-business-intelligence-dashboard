from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app, send_file
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError
import uuid
import os
from datetime import datetime
import json

# Import extensions
from app.extensions import db, celery_app

# Import forms (assuming these exist in app.ai_insights.forms)
from app.ai_insights.forms import ReportGenerationForm, ReportParameterForm

# Import models (assuming AIReport and ReportParameter are defined in app.models)
# You might need to adjust the import path if they are in a different module
from app.models import AIReport, User, ReportParameter

# Import tasks (assuming these exist in app.ai_insights.tasks)
from app.ai_insights.tasks import generate_sales_report_task, run_predictive_analysis_task

# Import custom decorators (assuming this exists in app.utils.decorators)
from app.utils.decorators import roles_required

ai_insights_bp = Blueprint('ai_insights', __name__, url_prefix='/ai_insights',
                           template_folder='templates', static_folder='static')

def _get_report_storage_path():
    """
    Constructs and ensures the existence of the directory where AI reports are stored.
    """
    report_folder = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'ai_reports')
    os.makedirs(report_folder, exist_ok=True)
    return report_folder

@ai_insights_bp.route('/')
@login_required
@roles_required(['Admin', 'Sales Manager', 'Sales Representative', 'Viewer'])
def dashboard():
    """
    Displays the main AI Insights dashboard.
    Shows a summary of generated reports, trends, and options to generate new reports.
    """
    try:
        # Fetch recent reports for the current user or all if admin/manager
        if current_user.has_role('Admin') or current_user.has_role('Sales Manager'):
            recent_reports = AIReport.query.order_by(AIReport.generated_at.desc()).limit(10).all()
        else:
            recent_reports = AIReport.query.filter_by(user_id=current_user.id).order_by(AIReport.generated_at.desc()).limit(10).all()

        # Placeholder for fetching summary data for dashboard charts.
        # These would typically be API calls or fetched via background tasks
        # For now, we just pass empty data or simple placeholders.
        summary_data = {
            'sales_trends': [],  # Data for a sales trend chart
            'conversion
import os
import json
from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, send_file, current_app
from flask_login import login_required, current_user
from werkzeug.exceptions import abort

# Assuming these services and utilities exist in the project structure
from app.analytics.services import analytics_service, data_exporter, ai_insights_service
from app.utils.rbac import role_required
from app.utils.helpers import generate_temp_file, cleanup_temp_file

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')

@analytics_bp.route('/')
@analytics_bp.route('/dashboard')
@login_required
@role_required(['Admin', 'Sales Manager', 'Sales Representative', 'Viewer'])
def dashboard():
    """
    Renders the main sales analytics dashboard page.

    This page displays an overview of key performance indicators (KPIs) and
    initial charts. Data is typically loaded via AJAX calls after the page loads.
    Requires user to be logged in and have at least 'Viewer' role.
    """
    try:
        # Initial data for filters, e.g., product categories, regions, sales reps
        # This could come from a service layer or directly from the database
        filter_options = {
            'product_categories': analytics_service.get_available_product_categories(),
            'regions': analytics_service.get_available_regions(),
            'sales_reps': analytics_service.get_available_sales_representatives(),
            'date_ranges': [
                {'label': 'Last 7 Days', 'value': 'last_7_days'},
                {'label': 'Last 30 Days', 'value': 'last_30_days'},
                {'label': 'This Quarter', 'value': 'this_quarter'},
                {'label': 'Last Quarter', 'value': 'last_quarter'},
                {'label': 'This Year', 'value': 'this_year'},
                {'label': 'Last Year', 'value': 'last_year'},
                {'label': 'Custom', 'value': 'custom'}
            ]
        }
        return render_template('analytics/dashboard.html', filter_options=filter_options)
    except Exception as e:
        current_app.logger.error(f"Error rendering analytics dashboard: {e}")
        flash('An error occurred while loading the dashboard. Please try again later.', 'danger')
        return redirect(url_for('main.index')) # Redirect to a safe page

@analytics_bp.route('/kpis', methods=['GET'])
@login_required
@role_required(['Admin', 'Sales Manager', 'Sales Representative', 'Viewer'])
def get_kpis():
    """
    API endpoint to fetch Key Performance Indicators (KPIs) based on provided filters.

    Expects filter parameters like 'start_date', 'end_date', 'product_id', 'region', etc.,
    as query parameters.
    Returns JSON data containing the calculated KPIs.
    """
    try:
        filters = request.args.to_dict()
        kpis_data = analytics_service.get_kpis(filters, current_user.id, current_user.roles)
        return jsonify(kpis_data)
    except ValueError as ve:
        current_app.logger.warning(f"Validation error in get_kpis: {ve}")
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        current_app.logger.error(f"Error fetching KPIs: {e}")
        return jsonify({'error': 'Failed to retrieve KPIs. Please try again.'}), 500

@analytics_bp.route('/chart-data/<string:chart_name>', methods=['GET'])
@login_required
@role_required(['Admin', 'Sales Manager', 'Sales Representative', 'Viewer'])
def get_chart_data(chart_name):
    """
    API endpoint to fetch data for a specific chart type.

    The `chart_name` path parameter specifies which chart's data to retrieve
    (e.g., 'sales_over_time', 'sales_by_product', 'conversion_rates').
    Filter parameters are expected as query arguments.
    Returns JSON data formatted for Chart.js.
    """
    try:
        filters = request.args.to_dict()
        chart_data = analytics_service.get_chart_data(chart_name, filters, current_user.id, current_user.roles)
        if chart_data is None:
            return jsonify({'error': f'Chart data for "{chart_name}" not found or not supported.'}), 404
        return jsonify(chart_data)
    except ValueError as ve:
        current_app.logger.warning(f"Validation error in get_chart_data for {chart_name}: {ve}")
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        current_app.logger.error(f"Error fetching chart data for {chart_name}: {e}")
        return jsonify({'error': f'Failed to retrieve data for chart "{chart_name}". Please try again.'}), 500

@analytics_bp.route('/drilldown/<string:chart_name>/<string:data_point_id>', methods=['GET'])
@login_required
@role_required(['Admin', 'Sales Manager', 'Sales Representative', 'Viewer'])
def get_drilldown_data(chart_name, data_point_id):
    """
    API endpoint for drill-down functionality, providing more detailed data
    related to a specific data point on a chart.

    `chart_name` indicates the source chart, and `data_point_id` identifies the
    specific element clicked (e.g., a month, a product category ID).
    Returns JSON data with detailed information.
    """
    try:
        filters = request.args.to_dict()
        drilldown_data = analytics_service.get_drilldown_data(
            chart_name, data_point_id, filters, current_user.id, current_user.roles
        )
        if drilldown_data is None:
            return jsonify({'error': 'No detailed data found for the selected point.'}), 404
        return jsonify(drilldown_data)
    except ValueError as ve:
        current_app.logger.warning(f"Validation error in get_drilldown_data for {chart_name}/{data_point_id}: {ve}")
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        current_app.logger.error(f"Error fetching drilldown data for {chart_name}/{data_point_id}: {e}")
        return jsonify({'error': 'Failed to retrieve drill-down data. Please try again.'}), 500

@analytics_bp.route('/export/<string:export_type>', methods=['GET'])
@login_required
@role_required(['Admin', 'Sales Manager', 'Sales Representative'])
def export_data(export_type):
    """
    API endpoint to export analytics data in various formats (CSV, PDF, PNG).

    `export_type` specifies the desired output format.
    Query parameters should include `data_context` (e.g., 'kpis', 'sales_over_time_chart', 'drilldown_table')
    and relevant filters for the data to be exported.
    Returns a file download or a JSON response with a download link.
    """
    try:
        data_context = request.args.get('data_context')
        if not data_context:
            return jsonify({'error': 'Missing data_context parameter for export.'}), 400

        filters = request.args.to_dict()
        # Remove data_context from filters to avoid passing it to the service logic
        filters.pop('data_context', None)

        file_path, filename = data_exporter.export_data(
            export_type, data_context, filters, current_user.id, current_user.roles
        )

        if not file_path or not os.path.exists(file_path):
            current_app.logger.error(f"Export failed: File not created for type {export_type}, context {data_context}")
            return jsonify({'error': 'Failed to generate export file.'}), 500

        # Send the file and then clean it up
        response = send_file(file_path, as_attachment=True, download_name=filename, mimetype=data_exporter.get_mimetype(export_type))
        response.call_on_close(lambda: cleanup_temp_file(file_path))
        return response

    except ValueError as ve:
        current_app.logger.warning(f"Validation error during data export: {ve}")
        return jsonify({'error': str(ve)}), 400
    except NotImplementedError as nie:
        current_app.logger.warning(f"Export type not implemented: {nie}")
        return jsonify({'error': str(nie)}), 400
    except Exception as e:
        current_app.logger.error(f"Error during data export ({export_type}, {data_context}): {e}")
        return jsonify({'error': 'An unexpected error occurred during export. Please try again.'}), 500

@analytics_bp.route('/ai-insights', methods=['GET'])
@login_required
@role_required(['Admin', 'Sales Manager'])
def ai_insights_dashboard():
    """
    Renders the AI Insights dashboard, displaying a list of generated reports,
    forecasts, and options to generate new insights.
    Requires 'Admin' or 'Sales Manager' role.
    """
    try:
        # Fetch a list of recent insights or available report types
        recent_insights = ai_insights_service.get_recent_insights(current_user.id, current_user.roles)
        return render_template('analytics/ai_insights.html', recent_insights=recent_insights)
    except Exception as e:
        current_app.logger.error(f"Error rendering AI Insights dashboard: {e}")
        flash('An error occurred while loading AI insights. Please try again later.', 'danger')
        return redirect(url_for('analytics.dashboard'))

@analytics_bp.route('/ai-insights/generate-report', methods=['POST'])
@login_required
@role_required(['Admin', 'Sales Manager'])
def generate_ai_report():
    """
    API endpoint to trigger the generation of an AI-powered summary report.

    Expects report parameters (e.g., 'report_type', 'date_range', 'focus_area')
    in the request body (JSON). Report generation might be asynchronous.
    Returns JSON indicating the status of the report generation request.
    """
    try:
        report_params = request.get_json()
        if not report_params:
            return jsonify({'error': 'No report parameters provided.'}), 400

        # Trigger asynchronous report generation
        task_id = ai_insights_service.generate_report_async(
            report_params, current_user.id, current_user.roles
        )
        return jsonify({
            'status': 'Report generation initiated successfully.',
            'task_id': task_id,
            'message': 'You will be notified when the report is ready.'
        }), 202 # 202 Accepted for asynchronous processing
    except ValueError as ve:
        current_app.logger.warning(f"Validation error in generate_ai_report: {ve}")
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        current_app.logger.error(f"Error triggering AI report generation: {e}")
        return jsonify({'error': 'Failed to initiate report generation. Please try again.'}), 500

@analytics_bp.route('/ai-insights/report/<string:report_id>', methods=['GET'])
@login_required
@role_required(['Admin', 'Sales Manager'])
def get_ai_report(report_id):
    """
    API endpoint to retrieve a specific AI-generated report.

    `report_id` identifies the report.
    Returns JSON containing the report content or a download link.
    """
    try:
        report_data = ai_insights_service.get_report_content(
            report_id, current_user.id, current_user.roles
        )
        if not report_data:
            return jsonify({'error': 'Report not found or not accessible.'}), 404

        # If the report is a file, send it for download
        if report_data.get('file_path') and os.path.exists(report_data['file_path']):
            response = send_file(
                report_data['file_path'],
                as_attachment=True,
                download_name=report_data.get('filename', f'report_{report_id}.pdf'),
                mimetype=report_data.get('mimetype', 'application/pdf')
            )
            response.call_on_close(lambda: cleanup_temp_file(report_data['file_path']))
            return response
        else:
            return jsonify(report_data) # Otherwise, return JSON content
    except ValueError as ve:
        current_app.logger.warning(f"Validation error in get_ai_report for {report_id}: {ve}")
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        current_app.logger.error(f"Error retrieving AI report {report_id}: {e}")
        return jsonify({'error': 'Failed to retrieve report. Please try again.'}), 500

@analytics_bp.route('/ai-insights/forecast', methods=['GET'])
@login_required
@role_required(['Admin', 'Sales Manager'])
def get_sales_forecast():
    """
    API endpoint to retrieve sales forecast data.

    Expects forecast parameters (e.g., 'period', 'product_category', 'region')
    as query arguments.
    Returns JSON data containing the sales forecast.
    """
    try:
        forecast_params = request.args.to_dict()
        forecast_data = ai_insights_service.get_sales_forecast(
            forecast_params, current_user.id, current_user.roles
        )
        if not forecast_data:
            return jsonify({'message': 'No forecast data available for the given parameters.'}), 404
        return jsonify(forecast_data)
    except ValueError as ve:
        current_app.logger.warning(f"Validation error in get_sales_forecast: {ve}")
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        current_app.logger.error(f"Error fetching sales forecast: {e}")
        return jsonify({'error': 'Failed to retrieve sales forecast. Please try again.'}), 500

@analytics_bp.errorhandler(403)
def forbidden_error(error):
    """
    Handles 403 Forbidden errors for analytics routes.
    """
    current_app.logger.warning(f"Access Forbidden: User {current_user.id if current_user.is_authenticated else 'anonymous'} tried to access {request.path}")
    flash('You do not have permission to access this page.', 'warning')
    return render_template('errors/403.html'), 403

@analytics_bp.errorhandler(404)
def not_found_error(error):
    """
    Handles 404 Not Found errors for analytics routes.
    """
    current_app.logger.warning(f"Not Found: {request.path}")
    return render_template('errors/404.html'), 404

@analytics_bp.errorhandler(500)
def internal_error(error):
    """
    Handles 500 Internal Server Errors for analytics routes.
    """
    current_app.logger.error(f"Internal Server Error on {request.path}: {error}")
    flash('An unexpected server error occurred. Our team has been notified.', 'danger')
    return render_template('errors/500.html'), 500
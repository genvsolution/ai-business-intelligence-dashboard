from flask import Blueprint

# Define the Blueprint for the AI Insights module.
# This blueprint will handle all routes and logic related to AI/ML-driven insights
# and automated report generation, including data analysis, predictive modeling,
# and natural language generation.
ai_insights_bp = Blueprint('ai_insights', __name__, url_prefix='/insights')

# Import the routes to ensure they are registered with this blueprint.
# This import is placed here to avoid circular dependencies that might arise
# if routes were to import the blueprint from this file directly.
from . import routes
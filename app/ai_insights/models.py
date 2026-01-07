from datetime import datetime
from app.extensions import db
from sqlalchemy import JSON, Text, ForeignKey
from sqlalchemy.orm import relationship

class TimestampMixin:
    """
    Mixin for adding 'created_at' and 'updated_at' timestamp fields to database models.
    'created_at' is set once upon creation, and 'updated_at' is updated on every modification.
    """
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

class AIModel(TimestampMixin, db.Model):
    """
    Represents metadata for an AI/ML model used within the system for tasks
    like sales forecasting, lead scoring, or anomaly detection.

    Attributes:
        id (int): Primary key.
        name (str): Unique name of the AI model (e.g., "Sales Forecasting Model v1.0").
        model_type (str): Categorization of the model (e.g., 'Regression', 'Classification', 'Time-Series').
        description (str): Detailed description of the model's purpose and methodology.
        version (str): Version identifier of the model.
        training_date (datetime): Timestamp when the model was last trained.
        last_evaluation_date (datetime): Timestamp when the model's performance was last evaluated.
        performance_metrics (JSON): JSON object storing key performance indicators (e.g., {'MAE': 0.1, 'RMSE': 0.2, 'Accuracy': 0.9}).
        status (str): Current operational status of the model (e.g., 'Active', 'Archived', 'Retraining').
        report_results (relationship): One-to-many relationship with AIReportResult.
        predictive_results (relationship): One-to-many relationship with AIPredictiveResult.
    """
    __tablename__ = 'ai_models'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    model_type = db.Column(db.String(64), nullable=False)  # e.g., 'Regression', 'Classification', 'Time-Series'
    description = db.Column(db.Text, nullable=True)
    version = db.Column(db.String(32), nullable=False, default='1.0.0')
    training_date = db.Column(db.DateTime, nullable=True)
    last_evaluation_date = db.Column(db.DateTime, nullable=True)
    performance_metrics = db.Column(JSON, nullable=True)  # Store as JSON for flexibility
    status = db.Column(db.String(32), nullable=False, default='Active', index=True) # e.g., 'Active', 'Archived', 'Retraining'
    
    # Relationships
    report_results = relationship('AIReportResult', backref='ai_model', lazy=True, cascade="all, delete-orphan")
    predictive_results = relationship('AIPredictiveResult', backref='ai_model', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        """
        Returns a string representation of the AIModel instance.
        """
        return f"<AIModel {self.id}: {self.name} v{self.version} ({self.status})>"

class AIReportTemplate(TimestampMixin, db.Model):
    """
    Defines templates for automated AI-generated reports. Users can create
    and customize these templates to generate specific types of reports.

    Attributes:
        id (int): Primary key.
        name (str): Unique name for the report template (e.g., "Quarterly Sales Performance Summary").
        template_type (str): Category of the report (e.g., 'Sales Summary', 'Lead Conversion Analysis').
        description (str): Description of what the template generates.
        default_parameters (JSON): JSON object of default parameters to be used for report generation
                                   if not overridden by the user (e.g., {'time_period': 'quarter', 'region': 'all'}).
        nlg_prompt_template (Text): Template string for Natural Language Generation (NLG) prompt,
                                    if an LLM is used to generate report text.
        created_by_user_id (int): Foreign key to the User who created this template.
        report_results (relationship): One-to-many relationship with AIReportResult.
    """
    __tablename__ = 'ai_report_templates'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    template_type = db.Column(db.String(64), nullable=False, index=True) # e.g., 'Sales Summary', 'Lead Conversion Analysis'
    description = db.Column(db.Text, nullable=True)
    default_parameters = db.Column(JSON, nullable=True) # JSON of default parameters for generation
    nlg_prompt_template = db.Column(Text, nullable=True) # Template for LLM prompt if used for NLG
    
    # Foreign key to User model (assuming a 'users' table exists in app.auth.models)
    created_by_user_id = db.Column(db.Integer, ForeignKey('users.id'), nullable=True) 
    # Relationship to User model will be defined in the User model itself to avoid circular imports
    # created_by = relationship('User', backref='ai_report_templates', lazy=True)

    # Relationships
    report_results = relationship('AIReportResult', backref='report_template', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        """
        Returns a string representation of the AIReportTemplate instance.
        """
        return f"<AIReportTemplate {self.id}: {self.name} ({self.template_type})>"

class AIReportResult(TimestampMixin, db.Model):
    """
    Stores the results of a generated AI report, including its content,
    the parameters used for generation, and links to the template and model.

    Attributes:
        id (int): Primary key.
        template_id (int): Foreign key to the AIReportTemplate used.
        model_id (int): Optional foreign key to the AIModel that contributed to the report.
        generated_by_user_id (int): Foreign key to the User who initiated the report generation.
        generation_date (datetime): Timestamp when the report was generated.
        parameters_used (JSON): Actual parameters (overriding defaults) used for this specific report instance.
        report_content (Text): The human-readable text content of the report, possibly NLG generated.
        report_charts_data (JSON): Data structures suitable for rendering charts on the frontend (e.g., Chart.js format).
        status (str): Current status of the report generation (e.g., 'Completed', 'Failed', 'Pending').
        download_path (str): Optional path to a stored downloadable file (e.g., PDF, DOCX).
    """
    __tablename__ = 'ai_report_results'

    id = db.Column(db.Integer, primary_key=True)
    
    template_id = db.Column(db.Integer, ForeignKey('ai_report_templates.id'), nullable=False)
    model_id = db.Column(db.Integer, ForeignKey('ai_models.id'), nullable=True) # Optional: which model contributed to the report
    
    # Foreign key to User model (assuming a 'users' table exists in app.auth.models)
    generated_by_user_id = db.Column(db.Integer, ForeignKey('users.id'), nullable=True) 
    # Relationship to User model will be defined in the User model itself to avoid circular imports
    # generated_by = relationship('User', backref='generated_ai_reports', lazy=True)

    generation_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    parameters_used = db.Column(JSON, nullable=True) # Actual parameters used for this specific report instance
    report_content = db.Column(Text, nullable=True) # The NLG generated text or structured summary
    report_charts_data = db.Column(JSON, nullable=True) # Data structures for Chart.js rendering
    status = db.Column(db.String(32), nullable=False, default='Completed', index=True) # e.g., 'Completed', 'Failed', 'Pending'
    download_path = db.Column(db.String(256), nullable=True) # Path to stored PDF/DOCX file if applicable

    def __repr__(self):
        """
        Returns a string representation of the AIReportResult instance.
        """
        return f"<AIReportResult {self.id} (Template: {self.template_id}, Status: {self.status})>"

class AIPredictiveResult(TimestampMixin, db.Model):
    """
    Stores specific predictive analysis outcomes, such as sales forecasts,
    lead conversion probabilities, or anomaly detections.

    Attributes:
        id (int): Primary key.
        model_id (int): Foreign key to the AIModel that generated this prediction.
        result_type (str): Type of prediction (e.g., 'Sales Forecast', 'Lead Conversion Probability', 'Anomaly Score').
        target_entity_context (JSON): JSON object providing context about the entity
                                       this prediction is for (e.g., {'lead_id': 123}, {'product_id': 456, 'region': 'EMEA'}).
        prediction_date (datetime): Timestamp when the prediction was made.
        prediction_value (JSON): The actual prediction value(s). Can be a float, dict, or list
                                 (e.g., {'forecast': 100000.0}, {'probability': 0.75}).
        confidence_score (float): A score indicating the confidence or reliability of the prediction (0.0-1.0).
        context_data (JSON): Input features or additional contextual data used for generating the prediction.
        status (str): Status of the predictive result (e.g., 'Active', 'Superseded', 'Validated').
    """
    __tablename__ = 'ai_predictive_results'

    id = db.Column(db.Integer, primary_key=True)
    
    model_id = db.Column(db.Integer, ForeignKey('ai_models.id'), nullable=False)
    
    result_type = db.Column(db.String(64), nullable=False, index=True) # e.g., 'Sales Forecast', 'Lead Conversion Probability'
    
    # Generic identifier for the entity this prediction is about.
    # Storing as JSON allows flexibility for different types of predictions.
    target_entity_context = db.Column(JSON, nullable=True) # e.g., {'lead_id': 123}, {'product_id': 456, 'region': 'EMEA'}
    
    prediction_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    prediction_value = db.Column(JSON, nullable=False) # Can be a float, dict, or list
    confidence_score = db.Column(db.Float, nullable=True) # e.g., 0.0-1.0
    context_data = db.Column(JSON, nullable=True) # Input features used for prediction or additional context
    status = db.Column(db.String(32), nullable=False, default='Active', index=True) # e.g., 'Active', 'Superseded', 'Validated'

    def __repr__(self):
        """
        Returns a string representation of the AIPredictiveResult instance.
        """
        return f"<AIPredictiveResult {self.id}: {self.result_type} for {self.target_entity_context} ({self.status})>"
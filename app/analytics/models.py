from datetime import datetime
from app.extensions import db
# from app.auth.models import User # Assuming User model is defined elsewhere, e.g., app/auth/models.py
                                 # SQLAlchemy can resolve 'User' by string name if it's imported
                                 # or registered with the ORM before use.

class KPI(db.Model):
    """
    Represents a Key Performance Indicator (KPI) definition.

    This model stores the metadata and configuration for a specific KPI,
    such as its name, description, unit, and how it's calculated.
    KPIs are central to the interactive sales analytics dashboard.
    """
    __tablename__ = 'kpis'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    unit = db.Column(db.String(32), nullable=True)  # e.g., "$", "%", "units", "count", "days"
    
    # calculation_method can be a string representing a SQL query, a reference to a Python function,
    # or a JSON object describing a more complex calculation logic.
    calculation_method = db.Column(db.Text, nullable=False) 
    
    target_value = db.Column(db.Float, nullable=True) # Optional target value for the KPI
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        """
        Returns a string representation of the KPI object.
        """
        return f'<KPI {self.name}>'

    def to_dict(self):
        """
        Converts the KPI object to a dictionary for API responses or serialization.
        """
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'unit': self.unit,
            'calculation_method': self.calculation_method,
            'target_value': self.target_value,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ReportConfiguration(db.Model):
    """
    Defines the configuration for a specific analytical report.

    This model specifies the type of report, its parameters (e.g., date ranges, filters),
    generation frequency, and the user who created it. It serves as a template
    for generating actual reports.
    """
    __tablename__ = 'report_configurations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), unique=True, nullable=False, index=True)
    report_type = db.Column(db.String(64), nullable=False) # e.g., "Sales Performance", "Lead Conversion", "AI Insight Summary"
    description = db.Column(db.Text, nullable=True)
    
    # JSON field for report-specific parameters (e.g., date range, product categories, regions, AI model parameters).
    # SQLAlchemy's native JSON type handles serialization/deserialization and maps to JSONB in PostgreSQL.
    parameters = db.Column(db.JSON, nullable=False, default={}) 
    
    frequency = db.Column(db.String(32), nullable=False, default='on-demand') # e.g., 'daily', 'weekly', 'monthly', 'quarterly', 'on-demand'
    last_generated_at = db.Column(db.DateTime, nullable=True) # Timestamp of the last successful generation
    next_generation_at = db.Column(db.DateTime, nullable=True) # Timestamp of the next scheduled generation
    
    # Foreign key to the User model, assuming 'users' table exists.
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # Relationship to the User model. 'User' is resolved by string name.
    created_by = db.relationship('User', backref=db.backref('report_configurations', lazy=True))

    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship to generated reports, allowing access to all reports generated from this configuration.
    generated_reports = db.relationship('GeneratedReport', backref='report_config', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        """
        Returns a string representation of the ReportConfiguration object.
        """
        return f'<ReportConfiguration {self.name} ({self.report_type})>'

    def to_dict(self):
        """
        Converts the ReportConfiguration object to a dictionary for API responses or serialization.
        """
        return {
            'id': self.id,
            'name': self.name,
            'report_type': self.report_type,
            'description': self.description,
            'parameters': self.parameters,
            'frequency': self.frequency,
            'last_generated_at': self.last_generated_at.isoformat() if self.last_generated_at else None,
            'next_generation_at': self.next_generation_at.isoformat() if self.next_generation_at else None,
            'created_by_id': self.created_by_id,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class GeneratedReport(db.Model):
    """
    Stores metadata and content for a specific instance of a generated report.

    This model links to a ReportConfiguration and holds details about the
    generation process, status, file paths, AI-generated summaries, and insights.
    """
    __tablename__ = 'generated_reports'

    id = db.Column(db.Integer, primary_key=True)
    # Foreign key to the ReportConfiguration that this report was generated from.
    report_config_id = db.Column(db.Integer, db.ForeignKey('report_configurations.id'), nullable=False)
    
    generated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(32), nullable=False, default='pending') # e.g., 'pending', 'generating', 'completed', 'failed', 'error'
    
    file_path = db.Column(db.String(512), nullable=True) # Path or URL to the stored report file (e.g., PDF, CSV, DOCX)
    summary_text = db.Column(db.Text, nullable=True) # AI-generated concise summary of the report
    
    # Snapshot of raw data used for the report (or a reference/link to it).
    # Useful for reproducibility and auditing.
    raw_data_snapshot = db.Column(db.JSON, nullable=True) 
    
    # AI-generated key insights, recommendations, or anomalies identified.
    insights = db.Column(db.JSON, nullable=True) 
    
    error_message = db.Column(db.Text, nullable=True) # Stores error details if generation failed
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        """
        Returns a string representation of the GeneratedReport object.
        """
        return f'<GeneratedReport {self.id} for Config {self.report_config_id} at {self.generated_at}>'

    def to_dict(self):
        """
        Converts the GeneratedReport object to a dictionary for API responses or serialization.
        """
        return {
            'id': self.id,
            'report_config_id': self.report_config_id,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None,
            'status': self.status,
            'file_path': self.file_path,
            'summary_text': self.summary_text,
            'raw_data_snapshot': self.raw_data_snapshot,
            'insights': self.insights,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# Note: The 'User' model is expected to be defined in 'app/auth/models.py' or 'app/models.py'.
# The ForeignKey('users.id') and db.relationship('User', ...) will correctly link to it
# as long as the 'User' model is known to SQLAlchemy when the application initializes.
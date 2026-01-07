from datetime import datetime
from app.extensions import db
from sqlalchemy.schema import UniqueConstraint

# The User model is assumed to exist in app.auth.models.
# To avoid circular imports, we will refer to it by its string name 'User' in foreign keys
# and relationships. SQLAlchemy will resolve this to the 'users' table (default for a User model).

class LeadStatus(db.Model):
    """
    Represents a configurable status for a lead in the CRM system.
    Examples: 'New', 'Qualified', 'Contacted', 'Proposal Sent', 'Negotiation', 'Converted', 'Lost'.
    This model allows for a flexible lead workflow.
    """
    __tablename__ = 'lead_statuses'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_converted_status = db.Column(db.Boolean, default=False, nullable=False)
    is_lost_status = db.Column(db.Boolean, default=False, nullable=False)
    order = db.Column(db.Integer, default=0, nullable=False) # For pipeline visualization order

    leads = db.relationship('Lead', backref='status', lazy=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, server_default=db.func.now())

    def __repr__(self):
        """
        Returns a string representation of the LeadStatus object.
        """
        return f"<LeadStatus {self.name}>"

class LeadSource(db.Model):
    """
    Represents a configurable source from which a lead was acquired.
    Examples: 'Website', 'Referral', 'Cold Call', 'Advertisement', 'Event'.
    This model helps track the effectiveness of different marketing channels.
    """
    __tablename__ = 'lead_sources'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    leads = db.relationship('Lead', backref='source', lazy=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, server_default=db.func.now())

    def __repr__(self):
        """
        Returns a string representation of the LeadSource object.
        """
        return f"<LeadSource {self.name}>"

class Industry(db.Model):
    """
    Represents a configurable industry type for a lead's company.
    Examples: 'Technology', 'Healthcare', 'Finance', 'Manufacturing'.
    This model helps categorize leads by their business sector.
    """
    __tablename__ = 'industries'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    leads = db.relationship('Lead', backref='industry', lazy=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, server_default=db.func.now())

    def __repr__(self):
        """
        Returns a string representation of the Industry object.
        """
        return f"<Industry {self.name}>"

class Lead(db.Model):
    """
    Represents a sales lead in the CRM system.
    Stores comprehensive information about a potential customer,
    including contact details, source, industry, budget, and current status.
    """
    __tablename__ = 'leads'

    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(255), nullable=False)
    contact_person = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    zip_code = db.Column(db.String(20), nullable=True)
    country = db.Column(db.String(100), nullable=True)

    lead_source_id = db.Column(db.Integer, db.ForeignKey('lead_sources.id'), nullable=False)
    industry_id = db.Column(db.Integer, db.ForeignKey('industries.id'), nullable=False)
    
    budget = db.Column(db.Numeric(10, 2), nullable=True) # E.g., 100000.00
    notes = db.Column(db.Text, nullable=True)

    status_id = db.Column(db.Integer, db.ForeignKey('lead_statuses.id'), nullable=False)
    
    # The 'users.id' refers to the 'id' column in the 'users' table (User model).
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) 
    owner = db.relationship('User', backref='owned_leads', lazy=True, foreign_keys=[owner_id])

    is_converted = db.Column(db.Boolean, default=False, nullable=False)
    converted_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, server_default=db.func.now())

    tasks = db.relationship('Task', backref='lead', lazy=True, cascade="all, delete-orphan")
    activities = db.relationship('Activity', backref='lead', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        """
        Returns a string representation of the Lead object.
        """
        return f"<Lead {self.company_name} - {self.contact_person} (ID: {self.id})>"

    def update_status(self, new_status_id):
        """
        Updates the lead's status and handles conversion logic based on the new status.
        
        Args:
            new_status_id (int): The ID of the new LeadStatus to assign to the lead.
        
        Raises:
            ValueError: If the new_status_id does not correspond to an existing LeadStatus.
            RuntimeError: If a database error occurs during the update.
        """
        try:
            new_status = LeadStatus.query.get(new_status_id)
            if not new_status:
                raise ValueError(f"LeadStatus with ID {new_status_id} not found.")
            
            self.status = new_status
            
            # Logic to handle automatic setting/unsetting of is_converted and converted_at
            if new_status.is_converted_status and not self.is_converted:
                self.is_converted = True
                self.converted_at = datetime.utcnow()
            elif not new_status.is_converted_status and self.is_converted:
                self.is_converted = False
                self.converted_at = None
            
            db.session.add(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            # In a real application, this error should be logged for debugging.
            raise RuntimeError(f"Failed to update lead status for Lead ID {self.id}: {e}") from e

class Task(db.Model):
    """
    Represents a task associated with a specific lead.
    Examples: 'Follow-up Call', 'Send Proposal', 'Schedule Meeting'.
    Tasks have due dates, can be assigned to users, and have a status and priority.
    """
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=False)
    
    # The 'users.id' refers to the 'id' column in the 'users' table (User model).
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assigned_to = db.relationship('User', backref='assigned_tasks', lazy=True, foreign_keys=[assigned_to_id])

    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.DateTime, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Using a string for status for flexibility. Could be an Enum or FK to a lookup table if needed.
    status = db.Column(db.String(50), default='Pending', nullable=False) # e.g., 'Pending', 'Completed', 'Overdue', 'Cancelled'
    priority = db.Column(db.String(50), default='Medium', nullable=False) # e.g., 'Low', 'Medium', 'High'

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, server_default=db.func.now())

    def __repr__(self):
        """
        Returns a string representation of the Task object
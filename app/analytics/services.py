import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import func, extract, and_, case, cast, Date
from app.extensions import db
from app.models import Sale, Product, Lead, User, Customer, Region # Assuming these models exist

class AnalyticsService:
    """
    Service class for performing sales analytics, calculating KPIs,
    and preparing data for interactive charts.
    It encapsulates the business logic for data retrieval, filtering,
    aggregation, and transformation.
    """

    def __init__(self, db_session=None):
        """
        Initializes the AnalyticsService with a database session.

        Args:
            db_session: An SQLAlchemy session object. If None, uses the default db.session.
        """
        self.db = db_session if db_session else db.session

    def _apply_filters(self, query, model, filters):
        """
        Applies a set of common filters to a given SQLAlchemy query.
        This method dynamically adds WHERE clauses based on the provided filters dictionary.

        Args:
            query: The base SQLAlchemy query object.
            model: The primary model being queried (e.g., Sale, Lead) to determine the date field
                   for date range filtering.
            filters (dict): A dictionary of filters to apply. Expected keys:
                            - 'start_date': str (YYYY-MM-DD) - inclusive start date
                            - 'end_date': str (YYYY-MM
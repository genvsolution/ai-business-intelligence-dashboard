from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length


class GlobalSearchForm(FlaskForm):
    """
    A global search form for the application.

    This form provides a simple text input for users to enter search queries
    across various parts of the application. It is intended for common,
    application-wide search functionality rather than blueprint-specific searches.
    """
    query = StringField(
        'Search',
        validators=[
            DataRequired(message='Search query cannot be empty.'),
            Length(
                min=2,
                max=100,
                message='Search query must be between 2 and 100 characters long.'
            )
        ],
        render_kw={"placeholder": "Search throughout the application..."}
    )
    submit = SubmitField('Search')
import os
import secrets
import datetime
import csv
from io import StringIO
import re

from flask import current_app, render_template, Response
from flask_mail import Message
# Assuming 'mail' object is initialized in app/__init__.py and imported globally
# If not, you might need to import Mail and initialize it with current_app within a function.
try:
    from app import mail
except ImportError:
    # Fallback for environments where 'mail' might not be directly importable from 'app'
    # This might happen in testing or if mail is initialized lazily.
    # In a real Flask app, ensure 'mail' is properly initialized and accessible.
    print("Warning: 'mail' object not directly importable from 'app'. Email sending might fail.")
    mail = None # Placeholder, actual implementation would need Flask-Mail setup


# --- Email Utilities ---

def send_email(to_email, subject, template_name, **template_context):
    """
    Sends an email to a specified recipient using a Jinja2 template.

    Args:
        to_email (str or list): The recipient's email address or a list of addresses.
        subject (str): The subject line of the email.
        template_name (str): The name of the Jinja2 template file (e.g., 'email/welcome.html').
        **template_context: Keyword arguments to pass to the email template.

    Returns:
        bool: True if the email was sent successfully, False otherwise.
    """
    if mail is None:
        current_app.logger.error("Email sending skipped: Flask-Mail 'mail' object is not initialized.")
        return False

    try:
        # Render the email body from the template
        html_body = render_template(template_name, **template_context)
        
        msg = Message(
            subject,
            sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@example.com'),
            recipients=[to_email] if isinstance(to_email, str) else to_email
        )
        msg.html = html_body
        
        mail.send(msg)
        current_app.logger.info(f"Email sent successfully to {to_email} with subject: '{subject}'")
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send email to {to_email} with subject '{subject}': {e}", exc_info=True)
        return False

# --- Data Formatting Utilities ---

def format_currency(value, currency_symbol='$', decimal_places=2):
    """
    Formats a numeric value as a currency string.

    Args:
        value (float or int): The numeric value to format.
        currency_symbol (str): The symbol to prepend (e.g., '$', '€').
        decimal_places (int): The number of decimal places to include.

    Returns:
        str: The formatted currency string.
    """
    if value is None:
        return f"{currency_symbol}0.00"
    try:
        # Using f-string for formatting, e.g., "${:,.2f}".format(value)
        # For more advanced internationalization, consider Flask-Babel.
        return f"{currency_symbol}{value:,.{decimal_places}f}"
    except (TypeError, ValueError) as e:
        current_app.logger.warning(f"Failed to format currency value '{value}': {e}")
        return f"{currency_symbol}N/A"

def format_percentage(value, decimal_places=2):
    """
    Formats a numeric value as a percentage string.

    Args:
        value (float or int): The numeric value to format (e.g., 0.75 for 75%).
        decimal_places (int): The number of decimal places to include.

    Returns:
        str: The formatted percentage string.
    """
    if value is None:
        return "0.00%"
    try:
        return f"{value * 100:,.{decimal_places}f}%"
    except (TypeError, ValueError) as e:
        current_app.logger.warning(f"Failed to format percentage value '{value}': {e}")
        return "N/A%"

def format_date(date_obj, fmt='%Y-%m-%d'):
    """
    Formats a datetime.date or datetime.datetime object into a string.

    Args:
        date_obj (datetime.date or datetime.datetime): The date object to format.
        fmt (str): The format string (e.g., '%Y-%m-%d', '%b %d, %Y').

    Returns:
        str: The formatted date string, or 'N/A' if the object is invalid.
    """
    if not isinstance(date_obj, (datetime.date, datetime.datetime)):
        return 'N/A'
    try:
        return date_obj.strftime(fmt)
    except Exception as e:
        current_app.logger.warning(f"Failed to format date '{date_obj}' with format '{fmt}': {e}")
        return 'N/A'

def format_datetime(datetime_obj, fmt='%Y-%m-%d %H:%M:%S'):
    """
    Formats a datetime.datetime object into a string.

    Args:
        datetime_obj (datetime.datetime): The datetime object to format.
        fmt (str): The format string (e.g., '%Y-%m-%d %H:%M:%S', '%b %d, %Y %I:%M %p').

    Returns:
        str: The formatted datetime string, or 'N/A' if the object is invalid.
    """
    if not isinstance(datetime_obj, datetime.datetime):
        return 'N/A'
    try:
        return datetime_obj.strftime(fmt)
    except Exception as e:
        current_app.logger.warning(f"Failed to format datetime '{datetime_obj}' with format '{fmt}': {e}")
        return 'N/A'

def slugify(text):
    """
    Converts a string into a URL-friendly slug.

    Args:
        text (str): The input string.

    Returns:
        str: The slugified string.
    """
    if not isinstance(text, str):
        return ""
    
    text = text.lower()
    # Replace non-alphanumeric characters (except hyphens and spaces) with nothing
    text = re.sub(r'[^\w\s-]', '', text) 
    # Replace spaces and multiple hyphens with a single hyphen
    text = re.sub(r'[\s_-]+', '-', text) 
    # Remove leading/trailing hyphens
    text = text.strip('-') 
    return text

# --- Security Utilities ---

def generate_secure_token(length=32):
    """
    Generates a cryptographically secure random token.

    Args:
        length (int): The desired length of the token in bytes.
                      The resulting hex string will be twice this length.

    Returns:
        str: A hexadecimal string representing the secure token, or None if generation fails.
    """
    try:
        return secrets.token_hex(length)
    except Exception as e:
        current_app.logger.error(f"Failed to generate secure token: {e}", exc_info=True)
        return None

# --- File Export Utilities ---

def generate_csv_response(data, filename="export.csv", headers=None):
    """
    Generates a Flask Response object for downloading data as a CSV file.

    Args:
        data (list of dict or list of list): The data to export.
                                            If list of dicts, keys are used as headers if `headers` is None.
                                            If list of lists, `headers` must be provided.
        filename (str): The desired filename for the downloaded CSV.
        headers (list, optional): A list of strings to use as CSV column headers.
                                  If None and `data` is list of dicts, dict keys are used.

    Returns:
        flask.Response: A Flask response object configured for CSV download.
    """
    if not data:
        data = [] # Ensure data is an iterable even if empty

    output = StringIO()
    writer = csv.writer(output)

    # Determine headers
    if headers:
        writer.writerow(headers)
    elif data and isinstance(data[0], dict):
        # Infer headers from the keys of the first dictionary
        headers = list(data[0].keys())
        writer.writerow(headers)
    else:
        # No headers provided and data is not list of dicts, or data is empty
        # In this case, we proceed without writing a header row.
        pass 

    # Write data rows
    for row in data:
        if isinstance(row, dict):
            # Write values in the order of headers, handling missing keys gracefully
            if headers:
                writer.writerow([row.get(h, '') for h in headers])
            else:
                # If no headers were inferred/provided, just write dict values
                writer.writerow(list(row.values()))
        elif isinstance(row, (list, tuple)):
            writer.writerow(row)
        else:
            current_app.logger.warning(f"Unsupported data row type for CSV export: {type(row)}. Skipping row: {row}")

    output.seek(0)
    
    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response

# --- General Utilities ---

def get_current_utc_timestamp():
    """
    Returns the current UTC datetime object.

    Returns:
        datetime.datetime: A timezone-aware datetime object representing the current UTC time.
    """
    return datetime.datetime.now(datetime.timezone.utc)

def parse_date_string(date_string, formats=None):
    """
    Attempts to parse a date string into a datetime object using a list of possible formats.

    Args:
        date_string (str): The date string to parse.
        formats (list, optional): A list of datetime format strings to try.
                                  Defaults to common formats if None.

    Returns:
        datetime.datetime or None: The parsed datetime object, or None if parsing fails.
    """
    if not isinstance(date_string, str):
        return None

    if formats is None:
        formats = [
            '%Y-%m-%d %H:%M:%S',        # '2023-10-27 15:30:00'
            '%Y-%m-%dT%H:%M:%S',        # '2023-10-27T15:30:00' (ISO without timezone)
            '%Y-%m-%d %H:%M',           # '2023-10-27 15:30'
            '%Y-%m-%d',                 # '2023-10-27'
            '%m/%d/%Y %H:%M:%S',        # '10/27/2023 15:30:00'
            '%m/%d/%Y %H:%M',           # '10/27/2023 15:30'
            '%m/%d/%Y',                 # '10/27/2023'
            '%d-%m-%Y %H:%M:%S',        # '27-10-2023 15:30:00'
            '%d-%m-%Y %H:%M',           # '27-10-2023 15:30'
            '%d-%m-%Y',                 # '27-10-2023'
            '%Y-%m-%dT%H:%M:%S.%fZ',    # ISO with milliseconds and Z for UTC
            '%Y-%m-%dT%H:%M:%S%z',      # ISO with timezone offset
        ]

    for fmt in formats:
        try:
            # For formats with timezone info, strptime might return naive datetime in older Python
            # or timezone-aware in newer versions. For consistency, we might want to normalize to UTC.
            dt_obj = datetime.datetime.strptime(date_string, fmt)
            # If the parsed datetime is naive, assume it's UTC for consistency, or local if preferred.
            # Here, we'll make it timezone-aware UTC if it's naive.
            if dt_obj.tzinfo is None:
                return dt_obj.replace(tzinfo=datetime.timezone.utc)
            return dt_obj
        except ValueError:
            continue
    
    current_app.logger.warning(f"Could not parse date string '{date_string}' with any known format.")
    return None
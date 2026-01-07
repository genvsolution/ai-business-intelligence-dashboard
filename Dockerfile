# Use an official Python runtime as a base image
FROM python:3.9-slim-buster

# Set environment variables for Python to ensure output is not buffered
# and byte-code is not written to disk, improving performance and reducing image size.
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies
# These packages are required for compiling Python packages with C extensions (e.g., psycopg2, numpy, scipy)
# and for interacting with PostgreSQL.
# build-essential: Provides compilers (gcc, g++) and make.
# libpq-dev: PostgreSQL client library development files, needed by psycopg2.
# python3-dev: Header files for Python C extensions.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the Python dependency file
COPY requirements.txt .

# Install Python packages
# --no-cache-dir: Prevents pip from storing downloaded packages, reducing image size.
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data
# 'punkt' for tokenization, 'stopwords' for text processing. Adjust as per actual usage.
# Ensure 'nltk' is in requirements.txt.
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

# Download SpaCy language model
# 'en_core_web_sm' is a small English model. Choose a larger one if needed (e.g., 'en_core_web_md', 'en_core_web_lg').
# Ensure 'spacy' is in requirements.txt.
RUN python -m spacy download en_core_web_sm

# Copy the entire application code into the container
# This copies everything from the current directory (where Dockerfile is) into /app in the container.
COPY . .

# Set the FLASK_APP environment variable
# This tells Flask where to find your application instance (e.g., for 'flask db upgrade' or 'flask run').
# Assuming your Flask app is initialized in 'wsgi.py' and the app instance is named 'app'.
ENV FLASK_APP=wsgi.py

# Copy the startup script and make it executable
# This script will handle pre-application startup tasks like database migrations and then start Gunicorn.
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Create a non-root user and group for security best practices.
# The application will run as 'appuser' instead of 'root'.
RUN adduser --system --group appuser \
    # Change ownership of the /app directory to the new user.
    # This is important if the application needs to write files (e.g., logs, temporary files)
    # within its working directory.
    && chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# Expose the port that Gunicorn will listen on
# This informs Docker that the container listens on the specified network port at runtime.
EXPOSE 5000

# Define the entrypoint for the container
# This ensures that the 'start.sh' script is executed when the container starts.
ENTRYPOINT ["/app/start.sh"]
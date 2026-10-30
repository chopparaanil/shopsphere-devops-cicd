FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Update installed Debian packages
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root application user
RUN useradd --create-home --shell /usr/sbin/nologin appuser

# Install application dependencies
COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt && \
    rm -rf \
    /usr/local/lib/python3.12/site-packages/pip \
    /usr/local/lib/python3.12/site-packages/pip-*.dist-info \
    /usr/local/bin/pip \
    /usr/local/bin/pip3 \
    /usr/local/bin/pip3.12

# Copy application and database initialization script
COPY app/ ./app/
COPY init_db.py .

# Run as non-root user
USER appuser

EXPOSE 7000

# Initialize tables before starting Gunicorn
CMD ["sh", "-c", "python init_db.py && exec gunicorn --bind 0.0.0.0:7000 --workers 2 app.main:app"]
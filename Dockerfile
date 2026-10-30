FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Update installed Debian packages to receive available security fixes
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root application user
RUN useradd --create-home --shell /usr/sbin/nologin appuser

COPY requirements.txt .

# Remove pip from the runtime image after installing dependencies
RUN rm -rf \
    /usr/local/lib/python3.12/site-packages/pip \
    /usr/local/lib/python3.12/site-packages/pip-*.dist-info \
    /usr/local/bin/pip \
    /usr/local/bin/pip3 \
    /usr/local/bin/pip3.12
COPY app/ ./app/

USER appuser

EXPOSE 7000

CMD ["gunicorn", "--bind", "0.0.0.0:7000", "--workers", "2", "app.main:app"]
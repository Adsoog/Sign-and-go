# ==========================================
# Sign & Go - Production Dockerfile
# Multi-user SaaS for Digital Signature (PAdES)
# ==========================================

FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Set work directory
WORKDIR /app

# Install system dependencies (build-essential for cryptography if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . /app/

# Create persistent storage directories
RUN mkdir -p /app/private_storage/certificates \
             /app/private_storage/documents/sources \
             /app/private_storage/documents/signed \
             /app/media \
             /app/staticfiles

# Create non-root system user for security
RUN useradd -u 1000 -U appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose HTTP port
EXPOSE 8000

# Default command: run migrations and start gunicorn
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --threads 2 --timeout 60"]

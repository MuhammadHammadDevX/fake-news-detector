# ====================================================================
# Factify AI — Production Dockerfile
# ====================================================================

FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5002

WORKDIR /app

# Install essential system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy application layers
COPY backend ./backend
COPY frontend ./frontend

# Ensure upload and dataset directories exist
RUN mkdir -p backend/temp_uploads backend/dataset

# Expose application port
EXPOSE 5002

# Container health monitoring
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5002/health || exit 1

# Launch production WSGI server
WORKDIR /app/backend
CMD ["gunicorn", "--bind", "0.0.0.0:5002", "--workers", "4", "--timeout", "120", "wsgi:app"]

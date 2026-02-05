# ============================================
# Content Studio Agent - Production Dockerfile
# Optimized for AWS EC2 t3.medium (2 vCPU, 4 GB RAM)
# ============================================

# --- Stage 1: Builder ---
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better layer caching)
COPY requirements.txt .

# Install Python dependencies into a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn


# --- Stage 2: Production ---
FROM python:3.12-slim AS production

# Labels
LABEL maintainer="Hylancer"
LABEL description="Content Studio Agent - AI-Powered Social Media Content"
LABEL version="1.0.0"

# Environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/opt/venv/bin:$PATH" \
    # Default server config (override with .env or docker-compose)
    HOST=0.0.0.0 \
    PORT=5001 \
    DEBUG=false \
    # Gunicorn settings optimized for t3.medium (2 vCPU, 4 GB)
    GUNICORN_WORKERS=2 \
    GUNICORN_TIMEOUT=300 \
    GUNICORN_KEEPALIVE=5 \
    GUNICORN_MAX_REQUESTS=1000 \
    GUNICORN_MAX_REQUESTS_JITTER=50

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set working directory
WORKDIR /app

# Copy application code
COPY app/ ./app/
COPY agents/ ./agents/
COPY config/ ./config/
COPY memory/ ./memory/
COPY prompts/ ./prompts/
COPY tools/ ./tools/
COPY static/ ./static/
COPY templates/ ./templates/
COPY requirements.txt pyproject.toml ./

# Create directories for runtime data with proper permissions
RUN mkdir -p /app/generated /app/uploads /app/data /app/logs \
    && chown -R appuser:appuser /app

# Copy startup script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Expose port
EXPOSE ${PORT}

# Run as non-root user
USER appuser

# Entrypoint
ENTRYPOINT ["/docker-entrypoint.sh"]

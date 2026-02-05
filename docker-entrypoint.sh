#!/bin/bash
set -e

echo "============================================"
echo "  Content Studio Agent - Starting Up"
echo "============================================"
echo "  Host: ${HOST:-0.0.0.0}"
echo "  Port: ${PORT:-5001}"
echo "  Workers: ${GUNICORN_WORKERS:-2}"
echo "  Timeout: ${GUNICORN_TIMEOUT:-300}s"
echo "  Debug: ${DEBUG:-false}"
echo "============================================"

# Ensure runtime directories exist
mkdir -p /app/generated /app/uploads /app/data /app/logs

# Start Gunicorn with Uvicorn workers
exec gunicorn app.fast_api_app:app \
    --bind "${HOST:-0.0.0.0}:${PORT:-5001}" \
    --workers "${GUNICORN_WORKERS:-2}" \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout "${GUNICORN_TIMEOUT:-300}" \
    --keep-alive "${GUNICORN_KEEPALIVE:-5}" \
    --max-requests "${GUNICORN_MAX_REQUESTS:-1000}" \
    --max-requests-jitter "${GUNICORN_MAX_REQUESTS_JITTER:-50}" \
    --access-logfile /app/logs/access.log \
    --error-logfile /app/logs/error.log \
    --log-level info \
    --capture-output \
    --graceful-timeout 30 \
    --forwarded-allow-ips="*"

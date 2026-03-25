#!/usr/bin/env bash
# ============================================
# CryptoVault Production Server Start Script
# ============================================
#
# Usage:
#   bash production_start.sh
#
# Environment variables:
#   PORT          - Server port (default: 8000)
#   WORKERS       - Number of workers (default: 4)
#   HOST          - Bind host (default: 0.0.0.0)
#   ENVIRONMENT   - development/staging/production
#
# For production deployment on Render.com:
#   Start Command: bash production_start.sh
#
# For Kubernetes/Docker:
#   CMD ["bash", "production_start.sh"]
#
# ============================================

set -e

# Configuration
PORT="${PORT:-8000}"
HOST="${HOST:-0.0.0.0}"
WORKERS="${WORKERS:-4}"
ENVIRONMENT="${ENVIRONMENT:-production}"
LOG_LEVEL="${LOG_LEVEL:-info}"

echo "============================================"
echo "  CryptoVault API Server - Starting"
echo "============================================"
echo "  Environment: ${ENVIRONMENT}"
echo "  Host: ${HOST}:${PORT}"
echo "  Workers: ${WORKERS}"
echo "  Log Level: ${LOG_LEVEL}"
echo "============================================"

# Add backend to Python path
export PYTHONPATH="${PYTHONPATH}:$(dirname "$0")/backend"

# Graceful shutdown handler
trap 'echo "Received shutdown signal. Stopping gracefully..."; kill -TERM $PID; wait $PID' SIGTERM SIGINT

if [ "$ENVIRONMENT" = "development" ]; then
    echo "Starting in development mode with hot reload..."
    cd backend
    uvicorn server:app \
        --host "$HOST" \
        --port "$PORT" \
        --reload \
        --reload-dirs "." \
        --log-level "$LOG_LEVEL" &
    PID=$!
else
    echo "Starting in production mode with Gunicorn + Uvicorn workers..."
    cd backend
    gunicorn server:app \
        --bind "${HOST}:${PORT}" \
        --workers "$WORKERS" \
        --worker-class uvicorn.workers.UvicornWorker \
        --timeout 120 \
        --graceful-timeout 30 \
        --keep-alive 5 \
        --max-requests 10000 \
        --max-requests-jitter 1000 \
        --access-logfile - \
        --error-logfile - \
        --log-level "$LOG_LEVEL" \
        --preload &
    PID=$!
fi

wait $PID

#!/bin/bash
# Production startup script for CryptoVault Backend
# This script loads environment variables and starts the server

set -e  # Exit on any error

echo "🚀 Starting CryptoVault Backend..."

# Change to the script directory
cd "$(dirname "$0")"

# Load environment variables from .env file if it exists
if [ -f ".env" ]; then
    echo "📄 Loading environment from .env file..."
    set -a  # Export all variables
    source .env
    set +a
fi

# Set default PORT if not set
export PORT=${PORT:-8000}
export HOST=${HOST:-0.0.0.0}
export WORKERS=${WORKERS:-1}

echo "🔧 Configuration:"
echo "   Host: $HOST"
echo "   Port: $PORT"
echo "   Workers: $WORKERS"
echo "   Environment: ${ENVIRONMENT:-development}"

# Start the server using the Python startup script
echo "🏃 Starting server..."
exec python start_server.py
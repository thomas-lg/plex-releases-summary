#!/bin/bash
# Start the application in production mode

set -e

cd "$(dirname "$0")/.."

echo "🚀 Starting Plex Releases Summary (Production Mode)"
echo ""
echo "📋 Requirements:"
echo "   - TAUTULLI_URL must be set in docker-compose.yml"
echo "   - TAUTULLI_API_KEY must be set in docker-compose.yml"
echo "   - Secrets file should exist at ./secrets/tautulli_key (if using file-based secrets)"
echo ""

# Check if config directory exists
if [ ! -d "configs" ]; then
    echo "⚠️  Warning: configs/ directory not found. It will be created on first run."
fi

# Check if secrets directory exists (if using file-based secrets)
if [ ! -d "secrets" ]; then
    echo "⚠️  Warning: secrets/ directory not found."
    echo "   Create it with: mkdir -p secrets && echo 'your_api_key' > secrets/tautulli_key"
    echo ""
fi

echo "Starting container..."
docker-compose -f docker-compose.yml up "$@"

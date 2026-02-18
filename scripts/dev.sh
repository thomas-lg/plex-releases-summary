#!/bin/bash
# Start the application in development mode with hot-reload

set -e

cd "$(dirname "$0")/.."

echo "🔧 Starting Plex Releases Summary (Development Mode)"
echo ""

# Check if config-dev.yml exists
if [ ! -f "configs/config-dev.yml" ]; then
    echo "⚠️  configs/config-dev.yml not found."
    echo "   Copying from config.yml..."
    mkdir -p configs
    if [ -f "configs/config.yml" ]; then
        cp configs/config.yml configs/config-dev.yml
    else
        echo "✨ config-dev.yml will be auto-generated on first run from environment variables"
    fi
    echo ""
fi

# Check if docker-compose.dev.local.yml exists
if [ ! -f "docker-compose.dev.local.yml" ]; then
    echo "⚠️  docker-compose.dev.local.yml not found."
    echo "   This file contains your personal development configuration."
    echo ""
    read -p "   Would you like to create it from the example? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp docker-compose.dev.local.yml.example docker-compose.dev.local.yml
        echo "✅ Created docker-compose.dev.local.yml"
        echo "   📝 Edit this file to set your TAUTULLI_URL and TAUTULLI_API_KEY"
        echo ""
        read -p "   Press Enter to continue or Ctrl+C to exit and configure first..."
    else
        echo "❌ Cannot start without docker-compose.dev.local.yml"
        echo "   Copy the example: cp docker-compose.dev.local.yml.example docker-compose.dev.local.yml"
        exit 1
    fi
fi

echo "📋 Using configuration files:"
echo "   - docker-compose.dev.yml (base dev config)"
echo "   - docker-compose.dev.local.yml (your local overrides)"
echo ""

# Ensure host log directory exists and is writable for container user
mkdir -p logs
chmod 775 logs

# If dev script is not run by UID/GID 1000 (container appuser),
# relax permissions so bind-mounted logs stay writable during development.
if [ "$(id -u)" -ne 1000 ] && [ "$(id -g)" -ne 1000 ]; then
    echo "⚠️  logs/ is not owned by UID/GID 1000; applying permissive mode (777) for dev compatibility"
    chmod 777 logs
fi

echo "🔥 Hot-reload enabled - Python files will auto-reload on save"
echo "📊 Logs will stream below..."
echo ""

# Start development environment with local overrides
docker-compose -f docker-compose.dev.yml -f docker-compose.dev.local.yml up --build "$@"

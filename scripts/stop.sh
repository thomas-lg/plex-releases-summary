#!/bin/bash
# Stop all running containers for this project

set -e

cd "$(dirname "$0")/.."

echo "🛑 Stopping all Plex Releases Summary containers..."
echo ""

# Stop production
if docker-compose -f docker-compose.yml ps -q 2>/dev/null | grep -q .; then
    echo "Stopping production containers..."
    docker-compose -f docker-compose.yml down
fi

# Stop development
if docker-compose -f docker-compose.dev.yml ps -q 2>/dev/null | grep -q .; then
    echo "Stopping development containers..."
    docker-compose -f docker-compose.dev.yml -f docker-compose.dev.local.yml down 2>/dev/null || \
    docker-compose -f docker-compose.dev.yml down
fi

# Stop test
if docker-compose -f docker-compose.test.yml ps -q 2>/dev/null | grep -q .; then
    echo "Stopping test containers..."
    docker-compose -f docker-compose.test.yml down
fi

# Check for containers by name
if docker ps -a --filter "name=plex-releases-summary" --format "{{.Names}}" | grep -q .; then
    echo "Stopping containers by name..."
    docker stop $(docker ps -a --filter "name=plex-releases-summary" --format "{{.Names}}") 2>/dev/null || true
fi

echo ""
echo "✅ All containers stopped!"

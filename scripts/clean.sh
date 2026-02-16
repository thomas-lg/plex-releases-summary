#!/bin/bash
# Clean up generated files, caches, and Docker resources

set -e

cd "$(dirname "$0")/.."

echo "🧹 Cleaning up Plex Releases Summary..."
echo ""

# Ask for confirmation
read -p "This will remove test coverage, caches, and stopped containers. Continue? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

# Clean Python caches
echo "Removing Python caches..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true

# Clean coverage reports
if [ -d "htmlcov" ]; then
    echo "Removing coverage reports..."
    rm -rf htmlcov/
fi
if [ -f ".coverage" ]; then
    rm -f .coverage
fi
if [ -f "coverage.xml" ]; then
    rm -f coverage.xml
fi

# Clean Docker resources
echo "Removing stopped containers..."
docker-compose -f docker-compose.yml down 2>/dev/null || true
docker-compose -f docker-compose.dev.yml down 2>/dev/null || true
docker-compose -f docker-compose.test.yml down 2>/dev/null || true

# Remove dangling images (optional)
read -p "Remove unused Docker images for this project? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Removing unused images..."
    docker images "plex-releases-summary*" -q | xargs docker rmi -f 2>/dev/null || true
fi

echo ""
echo "✨ Clean complete!"

#!/bin/sh
# Start the dev compose environment and open a shell in the app container.

set -e

# Require Docker
if ! command -v docker > /dev/null 2>&1; then
    echo "❌ Docker is not installed or not on PATH. Please install Docker to use this script."
    exit 1
fi
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker daemon is not running. Please start Docker and try again."
    exit 1
fi

cd "$(dirname "$0")/.."

# Derive Python version from Dockerfile so dev and prod always match
PYTHON_VERSION=$(grep -m1 '^FROM python:' Dockerfile | sed 's/FROM python://')
export PYTHON_VERSION

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.dev.yml}"
SERVICE="${SERVICE:-app}"

echo "🐳 Starting development container ($SERVICE) using $COMPOSE_FILE"
docker compose -f "$COMPOSE_FILE" up -d --build

if [ "$#" -gt 0 ]; then
    docker compose -f "$COMPOSE_FILE" exec "$SERVICE" "$@"
else
    docker compose -f "$COMPOSE_FILE" exec "$SERVICE" sh
fi

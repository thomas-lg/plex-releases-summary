#!/bin/sh
# Start the dev compose environment and open a shell in the app container.

set -e

cd "$(dirname "$0")/.."

# Derive Python version from Dockerfile so dev and prod always match
PYTHON_VERSION=$(grep -m1 '^FROM python:' Dockerfile | sed 's/FROM python://')
export PYTHON_VERSION

# Export host UID/GID so docker-compose.dev.yml runs the container as the host user,
# ensuring files written inside the container are owned by the same user on the host.
# If the calling user is root (uid=0), fall back to 1000 to avoid running the container as root.
HOST_UID=$(id -u)
HOST_GID=$(id -g)
if [ "$HOST_UID" = "0" ]; then
    HOST_UID=1000
    HOST_GID=1000
fi
export HOST_UID HOST_GID

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.dev.yml}"
SERVICE="${SERVICE:-app}"

echo "🐳 Starting development container ($SERVICE) using $COMPOSE_FILE"
docker compose -f "$COMPOSE_FILE" up -d --build

if [ "$#" -gt 0 ]; then
    docker compose -f "$COMPOSE_FILE" exec "$SERVICE" "$@"
else
    docker compose -f "$COMPOSE_FILE" exec "$SERVICE" sh
fi

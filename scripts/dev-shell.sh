#!/bin/sh
# Start the dev compose environment and open a shell in the app container.

set -e

cd "$(dirname "$0")/.."

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.dev.yml}"
SERVICE="${SERVICE:-app}"

echo "🐳 Starting development container ($SERVICE) using $COMPOSE_FILE"
docker compose -f "$COMPOSE_FILE" up -d --build

if [ "$#" -gt 0 ]; then
    docker compose -f "$COMPOSE_FILE" exec "$SERVICE" "$@"
else
    docker compose -f "$COMPOSE_FILE" exec "$SERVICE" sh
fi

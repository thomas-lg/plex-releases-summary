#!/bin/bash
# View logs from running containers

cd "$(dirname "$0")/.."

# Default to production logs
COMPOSE_FILE="docker-compose.yml"
MODE="production"

# Parse arguments
case "${1:-prod}" in
    prod|production)
        COMPOSE_FILE="docker-compose.yml"
        MODE="production"
        ;;
    dev|development)
        COMPOSE_FILE="docker-compose.dev.yml"
        MODE="development"
        shift
        # Check if dev.local exists and add it
        if [ -f "docker-compose.dev.local.yml" ]; then
            COMPOSE_ARGS="-f docker-compose.dev.yml -f docker-compose.dev.local.yml"
        else
            COMPOSE_ARGS="-f docker-compose.dev.yml"
        fi
        ;;
    test)
        COMPOSE_FILE="docker-compose.test.yml"
        MODE="test"
        ;;
esac

echo "📜 Viewing $MODE logs..."
echo "   (Press Ctrl+C to exit)"
echo ""

if [ -n "$COMPOSE_ARGS" ]; then
    docker-compose $COMPOSE_ARGS logs -f "${@:2}"
else
    docker-compose -f "$COMPOSE_FILE" logs -f "$@"
fi

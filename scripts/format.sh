#!/bin/bash
# Format and auto-fix Python code using tools installed in the development container

set -e

cd "$(dirname "$0")/.."

IMAGE_NAME="plex-releases-summary-dev"
MODE="fix"

if [ "${1:-}" = "--check" ]; then
    MODE="check"
    shift
fi

if [ "$#" -gt 0 ]; then
    TARGETS=("$@")
else
    TARGETS=(src tests)
fi

echo "🎨 Running Python formatting and linting in Docker..."
echo ""
echo "📦 Building development image (contains black/ruff)..."
docker build -f Dockerfile.dev -t "$IMAGE_NAME" .

if [ "$MODE" = "check" ]; then
    echo ""
    echo "🔍 Checking Black formatting on: ${TARGETS[*]}"
    docker run --rm \
        -u "$(id -u):$(id -g)" \
        -v "$PWD:/app" \
        -w /app \
        "$IMAGE_NAME" \
        black --check "${TARGETS[@]}"

    echo ""
    echo "🔍 Checking Ruff lint on: ${TARGETS[*]}"
    docker run --rm \
        -u "$(id -u):$(id -g)" \
        -v "$PWD:/app" \
        -w /app \
        "$IMAGE_NAME" \
        ruff check "${TARGETS[@]}"
else
    echo ""
    echo "🧹 Running Black on: ${TARGETS[*]}"
    docker run --rm \
        -u "$(id -u):$(id -g)" \
        -v "$PWD:/app" \
        -w /app \
        "$IMAGE_NAME" \
        black "${TARGETS[@]}"

    echo ""
    echo "🛠️  Running Ruff auto-fix on: ${TARGETS[*]}"
    docker run --rm \
        -u "$(id -u):$(id -g)" \
        -v "$PWD:/app" \
        -w /app \
        "$IMAGE_NAME" \
        ruff check --fix "${TARGETS[@]}"
fi

echo ""
echo "✅ Done!"

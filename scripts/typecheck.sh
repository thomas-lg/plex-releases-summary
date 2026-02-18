#!/bin/bash
# Type check Python code using tools installed in the development container

set -e

cd "$(dirname "$0")/.."

IMAGE_NAME="plex-releases-summary-dev"

if [ "$#" -gt 0 ]; then
    TARGETS=("$@")
else
    TARGETS=(src)
fi

echo "🔍 Running type checks in Docker..."
echo ""
echo "📦 Building development image (contains mypy)..."
docker build -f Dockerfile.dev -t "$IMAGE_NAME" .

echo ""
echo "🧠 Running mypy on: ${TARGETS[*]}"
docker run --rm \
    -u "$(id -u):$(id -g)" \
    -v "$PWD:/app" \
    -w /app \
    "$IMAGE_NAME" \
    mypy "${TARGETS[@]}"

echo ""
echo "✅ Type checking complete!"

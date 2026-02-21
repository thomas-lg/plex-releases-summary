#!/bin/sh
# Format and auto-fix Python code in the current environment
# Note: Black is the formatter; ruff is used only as a linter (ruff check --fix).
# ruff format is intentionally not enabled to avoid conflicts with Black.

set -e

cd "$(dirname "$0")/.."

MODE="fix"

if [ "${1:-}" = "--check" ]; then
    MODE="check"
    shift
fi

if [ "$#" -eq 0 ]; then
    set -- src tests
fi

TARGETS="$*"

echo "🎨 Running Python formatting and linting..."

if [ "$MODE" = "check" ]; then
    echo ""
    echo "🔍 Checking Black formatting on: $TARGETS"
    black --check "$@"

    echo ""
    echo "🔍 Checking Ruff lint on: $TARGETS"
    ruff check "$@"
else
    echo ""
    echo "🧹 Running Black on: $TARGETS"
    black "$@"

    echo ""
    echo "🛠️  Running Ruff auto-fix on: $TARGETS"
    ruff check --fix "$@"
fi

echo ""
echo "✅ Done!"

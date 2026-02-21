#!/bin/sh
# Type check Python code in the current environment

set -e

cd "$(dirname "$0")/.."

if [ "$#" -eq 0 ]; then
    set -- src
fi

TARGETS="$*"

echo "🔍 Running type checks..."

echo ""
echo "🧠 Running mypy on: $TARGETS"
PYTHONPATH=src mypy "$@"

echo ""
echo "✅ Type checking complete!"

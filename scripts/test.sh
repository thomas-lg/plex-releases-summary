#!/bin/sh
# Run tests in the current environment (devcontainer recommended)

set -e

cd "$(dirname "$0")/.."

echo "🧪 Running tests..."
echo ""

if [ "$#" -gt 0 ]; then
	PYTHONPATH=src pytest "$@"
else
	PYTHONPATH=src pytest --cov=src --cov-branch --cov-report=xml --cov-report=term --cov-report=html
fi

echo ""
echo "✅ Tests complete!"
echo ""
echo "📊 Coverage report generated in htmlcov/"
echo "   To view: open htmlcov/index.html"

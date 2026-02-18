#!/bin/bash
# Run tests in Docker container

set -e

cd "$(dirname "$0")/.."

echo "🧪 Running tests in Docker..."
echo ""

# Build and run tests
docker-compose -f docker-compose.test.yml build

if [ "$#" -gt 0 ]; then
	docker-compose -f docker-compose.test.yml run --rm test pytest "$@"
else
	docker-compose -f docker-compose.test.yml run --rm test
fi

echo ""
echo "✅ Tests complete!"
echo ""
echo "📊 Coverage report generated in htmlcov/"
echo "   To view: open htmlcov/index.html"

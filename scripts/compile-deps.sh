#!/bin/sh
# Regenerate requirements.lock and requirements-dev.lock from their source .txt files.
# Run this after modifying requirements.txt or requirements-dev.txt and commit the result.

set -e

export LC_ALL=C
export LANG=C

cd "$(dirname "$0")/.."

echo "📦 Compiling requirements.lock..."
pip-compile requirements.txt \
    --output-file requirements.lock \
    --annotate \
    --strip-extras \
    --quiet

echo "📦 Compiling requirements-dev.lock..."
pip-compile requirements-dev.txt \
    --output-file requirements-dev.lock \
    --annotate \
    --strip-extras \
    --quiet

echo "✅ Lockfiles updated. Remember to commit requirements.lock and requirements-dev.lock."

#!/bin/sh
set -e

# =============================================================================
# Docker Entrypoint Script for Plex Releases Summary
# =============================================================================
# Handles PUID/PGID permissions and auto-creates config.yml from template.
# =============================================================================

CONFIG_DIR="/app/configs"
CONFIG_FILE="${CONFIG_DIR}/config.yml"
DEFAULT_CONFIG="/app/config.yml.default"

PUID=${PUID:-1000}
PGID=${PGID:-1000}

echo "==> Plex Releases Summary - Starting..."
echo "==> Running with PUID=$PUID, PGID=$PGID"

# Adjust appuser to match PUID/PGID
echo "==> Adjusting appuser to UID=$PUID, GID=$PGID"
groupmod -o -g "$PGID" appuser 2>/dev/null || true
usermod -o -u "$PUID" appuser 2>/dev/null || true

# Ensure config directory exists and fix permissions
echo "==> Ensuring correct permissions on $CONFIG_DIR"
mkdir -p "$CONFIG_DIR"
chown -R -h "$PUID:$PGID" "$CONFIG_DIR"

# Copy default config if not exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "==> Config file not found at $CONFIG_FILE"
    echo "==> Creating default configuration template..."
    cp "$DEFAULT_CONFIG" "$CONFIG_FILE"
    chown "$PUID:$PGID" "$CONFIG_FILE"
    echo "==> IMPORTANT: Set TAUTULLI_URL and TAUTULLI_API_KEY environment variables"
else
    echo "==> Config file found at $CONFIG_FILE"
fi

# Run application as appuser
echo "==> Starting application as appuser..."
exec gosu appuser "$@"

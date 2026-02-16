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

# Validate that a given ID is a numeric value within the range 1–65535.
# Explicitly rejects 0 (root) for security reasons.
validate_id() {
    value="$1"
    name="$2"

    # Must be composed only of digits.
    case "$value" in
        ''|*[!0-9]*)
            echo "ERROR: $name must be a positive integer, got '$value'." >&2
            exit 1
            ;;
    esac

    # Reject root user/group (UID/GID 0) for security reasons
    if [ "$value" -eq 0 ]; then
        echo "ERROR: $name cannot be 0 (root). Running as root is a security risk." >&2
        echo "       Please specify a non-root user/group ID (1-65535)." >&2
        exit 1
    fi

    # Must be within the typical UID/GID range.
    if [ "$value" -lt 1 ] || [ "$value" -gt 65535 ]; then
        echo "ERROR: $name must be between 1 and 65535, got '$value'." >&2
        exit 1
    fi
}

PUID=${PUID:-99}
PGID=${PGID:-100}

validate_id "$PUID" "PUID"
validate_id "$PGID" "PGID"
echo "==> Plex Releases Summary - Starting..."
echo "==> Running with PUID=$PUID, PGID=$PGID"

# Adjust appuser to match PUID/PGID
echo "==> Adjusting appuser to UID=$PUID, GID=$PGID"

if ! groupmod -o -g "$PGID" appuser 2>&1; then
    echo "WARNING: Failed to modify group for appuser (may already be set)" >&2
fi

if ! usermod -o -u "$PUID" appuser 2>&1; then
    echo "WARNING: Failed to modify user for appuser (may already be set)" >&2
fi

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

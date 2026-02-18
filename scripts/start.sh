#!/bin/sh
# Start the app locally (devcontainer/host) with optional env file support

set -e

cd "$(dirname "$0")/.."

ENV_FILE="${ENV_FILE:-.env}"
CONFIG_FILE="configs/config.yml"

if [ -f "$ENV_FILE" ]; then
    case "$ENV_FILE" in
        /*) ENV_FILE_PATH="$ENV_FILE" ;;
        *) ENV_FILE_PATH="./$ENV_FILE" ;;
    esac

    echo "📦 Loading environment variables from $ENV_FILE_PATH"
    set -a
    # shellcheck disable=SC1090
    . "$ENV_FILE_PATH"
    set +a
fi

# Start the app locally (devcontainer/host) with optional env file support

normalize_secret_path() {
    value="$1"
    if [ -z "$value" ]; then
        return
    fi

    case "$value" in
        /*)
            printf '%s' "$value"
            return
            ;;
    esac

    if [ -f "$value" ]; then
        abs_path="$(cd "$(dirname "$value")" && pwd)/$(basename "$value")"
        printf '%s' "$abs_path"
    else
        printf '%s' "$value"
    fi
}

TAUTULLI_API_KEY="$(normalize_secret_path "${TAUTULLI_API_KEY:-}")"
DISCORD_WEBHOOK_URL="$(normalize_secret_path "${DISCORD_WEBHOOK_URL:-}")"
export TAUTULLI_API_KEY DISCORD_WEBHOOK_URL

tautulli_host="$(printf '%s' "${TAUTULLI_URL:-}" | sed -n 's#^[a-zA-Z][a-zA-Z0-9+.-]*://\([^/:]*\).*#\1#p')"
if [ "$tautulli_host" = "tautulli" ] && ! getent hosts tautulli >/dev/null 2>&1; then
    echo "⚠️  TAUTULLI_URL uses host 'tautulli', which usually only resolves inside Docker Compose networks."
    echo "   For local/devcontainer runs, use a host-reachable URL (e.g., http://localhost:8181 or http://host.docker.internal:8181)."
fi

if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Config file not found: $CONFIG_FILE"
    echo "   Create it from the repository template before starting"
    exit 1
fi

if grep -q '\${TAUTULLI_URL}' "$CONFIG_FILE" && [ -z "${TAUTULLI_URL:-}" ]; then
    echo "❌ TAUTULLI_URL is required (or replace \${TAUTULLI_URL} in $CONFIG_FILE with a literal value)"
    exit 1
fi

if grep -q '\${TAUTULLI_API_KEY}' "$CONFIG_FILE" && [ -z "${TAUTULLI_API_KEY:-}" ]; then
    echo "❌ TAUTULLI_API_KEY is required (or replace \${TAUTULLI_API_KEY} in $CONFIG_FILE with a literal value)"
    exit 1
fi

echo "🚀 Starting Plex Releases Summary"
echo "   Config: $CONFIG_FILE"

PYTHONPATH=src python src/app.py

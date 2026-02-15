#!/bin/sh
set -e

# =============================================================================
# Docker Entrypoint Script for Plex Releases Summary
# =============================================================================
# This script ensures a config file exists before starting the application.
# If no config.yml is found in /app/configs/, it copies the default template.
# This is especially useful for Unraid and other Docker deployments where
# the config directory is volume-mapped but initially empty.
# =============================================================================

CONFIG_DIR="/app/configs"
CONFIG_FILE="${CONFIG_DIR}/config.yml"
DEFAULT_CONFIG="/app/config.yml.default" 

echo "==> Plex Releases Summary - Starting..."

# Create config directory if it doesn't exist (shouldn't happen with volume mounts, but be safe)
if [ ! -d "$CONFIG_DIR" ]; then
    echo "==> Creating config directory: $CONFIG_DIR"
    mkdir -p "$CONFIG_DIR"
fi

# Check if config.yml exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "==> Config file not found at $CONFIG_FILE"
    echo "==> Copying default configuration template..."
    
    # Copy default config
    cp "$DEFAULT_CONFIG" "$CONFIG_FILE"
    
    echo "==> Default config created at $CONFIG_FILE"
    echo "==> IMPORTANT: You MUST edit this file and set:"
    echo "    - TAUTULLI_URL environment variable"
    echo "    - TAUTULLI_API_KEY environment variable"
    echo "==> Or edit config.yml directly with your values."
    echo ""
else
    echo "==> Config file found at $CONFIG_FILE"
fi

# Execute the main application
echo "==> Starting Plex Releases Summary application..."
exec "$@"

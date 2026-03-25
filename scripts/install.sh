#!/bin/bash
# Install the AI Infographic Bot launchd schedule.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST_NAME="com.infographicbot.daily.plist"
PLIST_SRC="${SCRIPT_DIR}/${PLIST_NAME}"
PLIST_DST="${HOME}/Library/LaunchAgents/${PLIST_NAME}"

if [ ! -f "$PLIST_SRC" ]; then
    echo "Error: plist not found at $PLIST_SRC"
    exit 1
fi

# Create LaunchAgents dir if needed
mkdir -p "${HOME}/Library/LaunchAgents"

# Unload existing job if present
if [ -f "$PLIST_DST" ]; then
    launchctl unload "$PLIST_DST" 2>/dev/null || true
fi

# Copy and load
cp "$PLIST_SRC" "$PLIST_DST"
launchctl load "$PLIST_DST"

echo "Installed and loaded ${PLIST_NAME}"
echo "The bot will run daily at the configured hour."
echo "To check: launchctl list | grep infographicbot"

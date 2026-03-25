#!/bin/bash
# Uninstall the AI Infographic Bot launchd schedule.
set -euo pipefail

PLIST_NAME="com.infographicbot.daily.plist"
PLIST_DST="${HOME}/Library/LaunchAgents/${PLIST_NAME}"

if [ -f "$PLIST_DST" ]; then
    launchctl unload "$PLIST_DST" 2>/dev/null || true
    rm "$PLIST_DST"
    echo "Unloaded and removed ${PLIST_NAME}"
else
    echo "No launchd job found at ${PLIST_DST} — nothing to remove."
fi

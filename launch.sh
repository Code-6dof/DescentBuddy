#!/usr/bin/env bash
# launch.sh — Run DescentBuddy without installing it.
#
# On Ubuntu 22.04+ and other systems that ship libfuse3 instead of libfuse2,
# double-clicking the AppImage silently does nothing.  This wrapper bypasses
# FUSE entirely by telling the AppImage runtime to extract-and-run from a
# temporary directory instead.
#
# Usage:
#   chmod +x launch.sh
#   ./launch.sh
#
# To install properly (adds to your app menu), use install.sh instead.

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APPIMAGE="$SCRIPT_DIR/DescentBuddy-x86_64.AppImage"

if [ ! -f "$APPIMAGE" ]; then
    echo "ERROR: DescentBuddy-x86_64.AppImage not found next to launch.sh."
    exit 1
fi

chmod +x "$APPIMAGE"
exec env APPIMAGE_EXTRACT_AND_RUN=1 "$APPIMAGE" "$@"

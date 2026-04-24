#!/usr/bin/env bash
# package_windows.sh — Bundle project source into a zip for Windows builds.
# Run on Linux: bash package_windows.sh
# The resulting DescentBuddy-Windows.zip can be sent to a Windows user.
# They unzip it, double-click build_windows.bat, then run dist\DescentBuddy\DescentBuddy.exe.
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUT="$SCRIPT_DIR/DescentBuddy-Windows.zip"

cd "$SCRIPT_DIR"

echo "Packaging Windows source bundle..."

rm -f "$OUT"

zip -r "$OUT" \
    main.py \
    requirements.txt \
    build_windows.bat \
    descentbuddy_windows.spec \
    core/ \
    ui/ \
    data/notifications/ \
    --exclude "*.pyc" \
    --exclude "*/__pycache__/*" \
    --exclude "*/.git/*"

echo "Done: $OUT"
echo "Send this zip to the Windows user."
echo "They unzip it, run build_windows.bat, then run dist\\DescentBuddy\\DescentBuddy.exe"

#!/usr/bin/env bash
# build_appimage.sh — Build DescentBuddy as a Linux AppImage
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="$SCRIPT_DIR/build"
DIST_DIR="$SCRIPT_DIR/dist/descentbuddy"
APPDIR="$SCRIPT_DIR/DescentBuddy.AppDir"
OUTPUT="$SCRIPT_DIR/DescentBuddy-x86_64.AppImage"
APPIMAGETOOL="$BUILD_DIR/appimagetool-x86_64.AppImage"

cd "$SCRIPT_DIR"

echo "──────────────────────────────────────────"
echo "  DescentBuddy — AppImage Builder"
echo "──────────────────────────────────────────"

# ── 1. Generate icon ──────────────────────────
echo "[1/5] Generating icon..."
python3 "$BUILD_DIR/generate_icon.py"

# ── 2. Install/upgrade PyInstaller ───────────
echo "[2/5] Installing PyInstaller..."
python3 -m pip install --quiet --break-system-packages pyinstaller

# ── 3. Run PyInstaller ────────────────────────
echo "[3/5] Running PyInstaller..."
python3 -m PyInstaller descentbuddy.spec --noconfirm --clean

if [ ! -f "$DIST_DIR/descentbuddy" ]; then
    echo "ERROR: PyInstaller did not produce the expected binary."
    exit 1
fi

# ── 4. Assemble AppDir ────────────────────────
echo "[4/5] Assembling AppDir..."
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"

# Copy entire PyInstaller output (executable + _internal/)
cp -r "$DIST_DIR"/. "$APPDIR/usr/bin/"

# Desktop entry
cp "$BUILD_DIR/descentbuddy.desktop" "$APPDIR/descentbuddy.desktop"
cp "$BUILD_DIR/descentbuddy.desktop" "$APPDIR/usr/share/applications/descentbuddy.desktop"

# Icon
cp "$BUILD_DIR/descentbuddy.png" "$APPDIR/descentbuddy.png"
cp "$BUILD_DIR/descentbuddy.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/descentbuddy.png"

# AppRun
cp "$BUILD_DIR/AppRun" "$APPDIR/AppRun"
chmod +x "$APPDIR/AppRun"

# ── 5. Download appimagetool if needed ───────
echo "[5/5] Building AppImage..."
if [ ! -f "$APPIMAGETOOL" ]; then
    echo "  Downloading appimagetool..."
    curl -L --progress-bar \
        -o "$APPIMAGETOOL" \
        "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    chmod +x "$APPIMAGETOOL"
fi

# APPIMAGE_EXTRACT_AND_RUN=1 lets appimagetool run on the build host without FUSE.
# The resulting AppImage uses the standard runtime; end-users on FUSE3-only systems
# (Ubuntu 22.04+) launch it via launch.sh or install.sh, both of which set
# APPIMAGE_EXTRACT_AND_RUN=1 automatically.
ARCH=x86_64 APPIMAGE_EXTRACT_AND_RUN=1 "$APPIMAGETOOL" "$APPDIR" "$OUTPUT"
chmod +x "$OUTPUT"

# Ensure launch.sh is executable so users can run it straight after download
chmod +x "$SCRIPT_DIR/launch.sh"

echo ""
echo "Done: $OUTPUT"
echo ""
echo "Release files to upload to GitHub:"
echo "  $OUTPUT"
echo "  $SCRIPT_DIR/install.sh"
echo "  $SCRIPT_DIR/launch.sh"
echo ""
echo "Linux end-user experience:"
echo "  • Double-click the AppImage — works on FUSE2 and FUSE3 systems (Ubuntu 20.04+)"
echo "  • Or run directly:        ./launch.sh"
echo "  • Or add to app menu:     chmod +x install.sh && ./install.sh"

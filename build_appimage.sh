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

# Run appimagetool (APPIMAGE_EXTRACT_AND_RUN avoids requiring FUSE on the build host)
ARCH=x86_64 APPIMAGE_EXTRACT_AND_RUN=1 "$APPIMAGETOOL" "$APPDIR" "$OUTPUT"
chmod +x "$OUTPUT"

echo ""
echo "Done: $OUTPUT"
echo ""
echo "NOTE: Requires libfuse2 to run by double-click on Ubuntu/Debian."
echo "      Install with: sudo apt install libfuse2"
echo "      Or run without FUSE:  APPIMAGE_EXTRACT_AND_RUN=1 ./$OUTPUT"

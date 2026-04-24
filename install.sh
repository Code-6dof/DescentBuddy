#!/usr/bin/env bash
# install.sh — Install DescentBuddy so it appears in your app launcher
# and can be double-clicked like any other application.
#
# Run from the folder containing DescentBuddy-x86_64.AppImage:
#   chmod +x install.sh && ./install.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APPIMAGE="$SCRIPT_DIR/DescentBuddy-x86_64.AppImage"
ICON_SRC="$SCRIPT_DIR/build/descentbuddy.png"

INSTALL_DIR="$HOME/Applications"
ICON_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"
DESKTOP_DIR="$HOME/.local/share/applications"

if [ ! -f "$APPIMAGE" ]; then
    echo "ERROR: DescentBuddy-x86_64.AppImage not found in $SCRIPT_DIR"
    echo "Download it from the GitHub releases page and place it here, then re-run."
    exit 1
fi

echo "Installing Descent Buddy..."

mkdir -p "$INSTALL_DIR" "$ICON_DIR" "$DESKTOP_DIR"

chmod +x "$APPIMAGE"
cp "$APPIMAGE" "$INSTALL_DIR/DescentBuddy-x86_64.AppImage"

if [ -f "$ICON_SRC" ]; then
    cp "$ICON_SRC" "$ICON_DIR/descentbuddy.png"
fi

cat > "$DESKTOP_DIR/descentbuddy.desktop" << EOF
[Desktop Entry]
Name=Descent Buddy
Exec=env APPIMAGE_EXTRACT_AND_RUN=1 $INSTALL_DIR/DescentBuddy-x86_64.AppImage
Icon=descentbuddy
Type=Application
Categories=Game;
Comment=DXX-Redux Companion Launcher for Descent 1 and 2
Terminal=false
StartupWMClass=DescentBuddy
EOF

if command -v update-desktop-database &>/dev/null; then
    update-desktop-database "$DESKTOP_DIR"
fi

if command -v gtk-update-icon-cache &>/dev/null; then
    gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
fi

echo ""
echo "Done. Descent Buddy is installed."
echo "You can now launch it from your app menu, or run:"
echo "  $INSTALL_DIR/DescentBuddy-x86_64.AppImage"

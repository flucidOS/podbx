#!/usr/bin/env bash
set -e

echo "Installing Podbx..."

echo "Building Podbx base image..."
podman build -t podbx-base:latest -f Containerfile .

# CLI backend
INSTALL_BIN="$HOME/.local/share/podbx/bin"
mkdir -p "$INSTALL_BIN"
install -m 755 bin/podbx-cli "$INSTALL_BIN/podbx-cli"

# Python package — install for real this time
if command -v pipx &>/dev/null; then
    pipx install --editable . --system-site-packages --force
else
    pip install --user --editable . --break-system-packages
fi

# Icon
ICON_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"
mkdir -p "$ICON_DIR"
install -m 644 data/icons/com.flucidos.Podbx.svg "$ICON_DIR/com.flucidos.Podbx.svg"
gtk-update-icon-cache ~/.local/share/icons/hicolor/ 2>/dev/null || true

# Desktop launcher — point at the *installed console script*, not the old file
DESKTOP_DIR="$HOME/.local/share/applications"
mkdir -p "$DESKTOP_DIR"
cat > "$DESKTOP_DIR/com.flucidos.Podbx.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Podbx
Comment=Workspace manager for immutable Linux systems
Exec=$HOME/.local/bin/podbx-gui
Icon=com.flucidos.Podbx.svg
Terminal=false
Categories=Development;System;
StartupWMClass=Podbx
EOF

echo "Desktop entry written to $DESKTOP_DIR/com.flucidos.Podbx.desktop"
echo "Done. Run 'podbx-gui' to start, or launch 'Podbx' from your app menu."

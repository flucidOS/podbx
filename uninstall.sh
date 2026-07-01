#!/usr/bin/env bash
# uninstall.sh — remove Podbx for the current user
set -e

INSTALL_BIN="$HOME/.local/share/podbx"
DESKTOP_FILE="$HOME/.local/share/applications/com.flucidos.Podbx.desktop"
ICON_FILE="$HOME/.local/share/icons/hicolor/scalable/apps/com.flucidos.Podbx.svg"

echo "Uninstalling Podbx..."
echo ""

# ── CLI backend ────────────────────────────────────────────────────────────
if [ -d "$INSTALL_BIN" ]; then
    rm -rf "$INSTALL_BIN"
    echo "  Removed $INSTALL_BIN"
else
    echo "  Skipped: $INSTALL_BIN (not found)"
fi

# ── Desktop entry ──────────────────────────────────────────────────────────
if [ -f "$DESKTOP_FILE" ]; then
    rm -f "$DESKTOP_FILE"
    echo "  Removed $DESKTOP_FILE"
else
    echo "  Skipped: $DESKTOP_FILE (not found)"
fi

# ── Icon ───────────────────────────────────────────────────────────────────
if [ -f "$ICON_FILE" ]; then
    rm -f "$ICON_FILE"
    echo "  Removed $ICON_FILE"
    gtk-update-icon-cache ~/.local/share/icons/hicolor/ 2>/dev/null || true
else
    echo "  Skipped: $ICON_FILE (not found)"
fi

# ── Workspace data (opt-in) ────────────────────────────────────────────────
echo ""
read -rp "Remove workspace projects at ~/Podbx_Projects? [y/N] " CONFIRM
if [[ "$CONFIRM" =~ ^[Yy]$ ]]; then
    if [ -d "$HOME/Podbx_Projects" ]; then
        rm -rf "$HOME/Podbx_Projects"
        echo "  Removed ~/Podbx_Projects"
    else
        echo "  Skipped: ~/Podbx_Projects (not found)"
    fi
else
    echo "  Kept ~/Podbx_Projects untouched."
fi

# ── Distrobox container (opt-in) ───────────────────────────────────────────
echo ""
read -rp "Remove the podbx-os Distrobox container? [y/N] " CONFIRM
if [[ "$CONFIRM" =~ ^[Yy]$ ]]; then
    if command -v distrobox &>/dev/null && distrobox list | grep -qw "podbx-os"; then
        distrobox rm --force podbx-os
        echo "  Removed podbx-os container."
    else
        echo "  Skipped: podbx-os container not found."
    fi
else
    echo "  Kept podbx-os container untouched."
fi

echo ""
echo "Podbx uninstalled."

"""
podbx.config
~~~~~~~~~~~~~
Central configuration and path constants for Podbx.
All path resolution happens here so the rest of the codebase stays clean.
"""

import os

# Runtime paths
PODBOX_DIR   = os.path.expanduser("~/Podbx_Projects")
CLI_PATH     = os.path.expanduser("~/.local/share/podbx/bin/podbx-cli")
DATA_DIR     = os.path.join(os.path.dirname(__file__), "..", "data")

# Container
BASE_CONTAINER     = "podbx-os"
WORKSPACE_METADATA = ".podbx_workspace.json"

# Terminal preference order (first found wins)
TERMINAL_PREFERENCE = [
    "ptyxis",
    "gnome-console",
    "gnome-terminal",
    "konsole",
    "xterm",
]

# Application info
APP_ID      = "com.flucidos.Podbx"
APP_NAME    = "Podbx"
APP_VERSION = "1.0.0"

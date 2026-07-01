"""
podbx.ide.core
~~~~~~~~~~~~~~
Core shared utilities for IDE integration.
"""

import os
import stat
import shlex

from ..config import CLI_PATH

def write_shell_wrapper(workspace_path: str, cli_path: str = CLI_PATH, is_flatpak: bool = False) -> str:
    """
    Create .podbx/podbx-shell.sh — an executable that any IDE can use as
    its custom shell so every terminal tab enters the container.
    Returns the absolute path to the wrapper.
    """
    podbx_dir = os.path.join(workspace_path, ".podbx")
    os.makedirs(podbx_dir, exist_ok=True)

    wrapper = os.path.join(podbx_dir, "podbx-shell.sh")
    
    script_content = f"""#!/usr/bin/env bash
# Podbx shell wrapper

# Dynamically check if we are in a Flatpak sandbox at runtime
if [ -n "$FLATPAK_ID" ]; then
    CMD=("flatpak-spawn" "--host" "--env=TERM=xterm-256color" {shlex.quote(cli_path)} "enter" {shlex.quote(workspace_path)})
else
    CMD=({shlex.quote(cli_path)} "enter" {shlex.quote(workspace_path)})
fi

# Execute the command
"${{CMD[@]}}"
EXIT_CODE=$?

# Keep the terminal open if it crashes so we can read the error!
if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "❌ Podbx shell crashed! (Exit Code: $EXIT_CODE)"
    echo "Command run: ${{CMD[*]}}"
    read -p "Press Enter to close terminal..."
fi
"""
    
    with open(wrapper, "w") as f:
        f.write(script_content)
        
    mode = os.stat(wrapper).st_mode
    os.chmod(wrapper, mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return wrapper

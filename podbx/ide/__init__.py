"""
podbx.ide
~~~~~~~~~
IDE terminal-config injection module.

Writes shell wrappers and per-IDE config so that every integrated terminal
tab opens inside the podbx-os container automatically.
"""

from __future__ import annotations

from ..config import CLI_PATH
from .core import write_shell_wrapper
from .vscode import write_vscode_settings

def inject_ide_terminal_config(
    workspace_path: str,
    flatpak_app_id: str | None = None,
    cli_path: str = CLI_PATH,
) -> str:
    """
    Inject terminal configuration for all supported IDEs so their integrated
    terminals automatically enter the podbx-os container.

    Parameters
    ----------
    workspace_path : str
        Absolute path to the workspace directory.
    flatpak_app_id : str | None
        Flatpak application ID (e.g. ``com.jetbrains.PyCharm``).
        Passed when the IDE is a Flatpak install so the global JetBrains
        config inside ``~/.var/app/`` is also patched.
    cli_path : str
        Path to the podbx-cli executable (defaults to the constant).

    Returns
    -------
    str
        Absolute path to the shell wrapper script.
    """
    is_flatpak = bool(flatpak_app_id)
    wrapper = write_shell_wrapper(workspace_path, cli_path, is_flatpak)
    
    write_vscode_settings(workspace_path, wrapper)
    
    return wrapper

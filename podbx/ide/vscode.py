"""
podbx.ide.vscode
~~~~~~~~~~~~~~~~
VS Code and VSCodium terminal integration.
"""

import os
import json

def write_vscode_settings(workspace_path: str, shell_wrapper: str) -> None:
    """Write / merge .vscode/settings.json with the Podbx terminal profile."""
    vscode_dir = os.path.join(workspace_path, ".vscode")
    os.makedirs(vscode_dir, exist_ok=True)
    settings_path = os.path.join(vscode_dir, "settings.json")

    existing: dict = {}
    if os.path.exists(settings_path):
        try:
            with open(settings_path) as f:
                existing = json.load(f)
        except (json.JSONDecodeError, OSError):
            pass

    existing.update({
        "terminal.integrated.defaultProfile.linux": "Podbx Shell",
        "terminal.integrated.profiles.linux": {
            "Podbx Shell": {
                "path": shell_wrapper,
                "icon": "terminal-linux",
            }
        },
    })

    with open(settings_path, "w") as f:
        json.dump(existing, f, indent=4)

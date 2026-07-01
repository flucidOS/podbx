"""
podbx.workspace
~~~~~~~~~~~~~~~~
Pure-Python workspace management — no GTK dependency.
All filesystem and subprocess operations live here.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Iterator

from .config import CLI_PATH, PODBOX_DIR, TERMINAL_PREFERENCE, WORKSPACE_METADATA


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Workspace:
    """Represents a single Podbx workspace on disk."""
    name: str
    path: str
    status: str = "initialized"
    extra: dict = field(default_factory=dict)
    _actual_meta_path: str | None = None

    # ------------------------------------------------------------------
    # Factories
    # ------------------------------------------------------------------

    @classmethod
    def from_directory(cls, path: str) -> "Workspace | None":
        """
        Load a Workspace from a directory that contains a metadata file.
        Checks the new hidden `.podbx/` location first, then falls back
        to legacy paths so old workspaces don't break.
        Returns None if the directory is not a valid workspace.
        """
        new_meta = os.path.join(path, ".podbx", WORKSPACE_METADATA)
        old_meta = os.path.join(path, WORKSPACE_METADATA)
        old_meta_alt = os.path.join(path, ".podbox_workspace.json")

        meta_path_to_use = None
        if os.path.isfile(new_meta):
            meta_path_to_use = new_meta
        elif os.path.isfile(old_meta):
            meta_path_to_use = old_meta
        elif os.path.isfile(old_meta_alt):
            meta_path_to_use = old_meta_alt

        if not meta_path_to_use:
            return None

        try:
            with open(meta_path_to_use) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            data = {}
        
        name = data.pop("name", os.path.basename(path))
        status = data.pop("status", "initialized")
        
        return cls(
            name=name, 
            path=path, 
            status=status, 
            extra=data, 
            _actual_meta_path=meta_path_to_use
        )

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def metadata_path(self) -> str:
        if self._actual_meta_path:
            return self._actual_meta_path
        return os.path.join(self.path, ".podbx", WORKSPACE_METADATA)


# ---------------------------------------------------------------------------
# Manager
# ---------------------------------------------------------------------------

class WorkspaceManager:
    """High-level API for workspace CRUD and terminal/CLI operations."""

    def __init__(self, base_dir: str = PODBOX_DIR, cli_path: str = CLI_PATH):
        self.base_dir = base_dir
        self.cli_path = cli_path
        os.makedirs(self.base_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def list_workspaces(self) -> list[Workspace]:
        """Return all valid workspaces under base_dir, sorted by name."""
        results: list[Workspace] = []
        try:
            entries = sorted(os.listdir(self.base_dir))
        except OSError:
            return results
        for entry in entries:
            full = os.path.join(self.base_dir, entry)
            if os.path.isdir(full):
                ws = Workspace.from_directory(full)
                if ws is not None:
                    results.append(ws)
        return results

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create(self, name: str) -> Workspace:
        """
        Create a new workspace directory and invoke the CLI backend.
        Raises ValueError if the name is empty or the path already exists.
        """
        name = name.strip()
        if not name:
            raise ValueError("Workspace name must not be empty.")
        path = os.path.join(self.base_dir, name)
        if os.path.exists(path):
            raise FileExistsError(f"A workspace named '{name}' already exists at {path}.")
        
        subprocess.run([self.cli_path, "create", name, path], check=True)
        
        ws = Workspace.from_directory(path)
        if ws is None:
            raise RuntimeError(f"Workspace creation succeeded but metadata is missing at {path}.")
        return ws

    def delete(self, workspace: Workspace) -> None:
        """Delete a workspace directory via the CLI backend."""
        subprocess.run([self.cli_path, "delete", workspace.path], check=True)

    # ------------------------------------------------------------------
    # Terminal launch
    # ------------------------------------------------------------------

    def open_terminal(self, workspace: Workspace) -> None:
        """
        Launch the preferred terminal emulator and enter the workspace.
        Raises RuntimeError if no supported terminal is found.
        """
        terminal = next(
            (t for t in TERMINAL_PREFERENCE if shutil.which(t)), None
        )
        if terminal is None:
            raise RuntimeError(
                "No supported terminal emulator found.\n"
                f"Tried: {', '.join(TERMINAL_PREFERENCE)}"
            )

        cmd = [self.cli_path, "enter", workspace.path]
        launch_map = {
            "ptyxis":         [terminal, "--"] + cmd,
            "gnome-console":  [terminal, "--"] + cmd,
            "gnome-terminal": [terminal, "--"] + cmd,
            "konsole":        [terminal, "-e"] + cmd,
            "xterm":          [terminal, "-e"] + cmd,
        }
        subprocess.Popen(launch_map.get(terminal, [terminal, "--"] + cmd))

"""
Podbx — Workspace Manager for Immutable Linux Systems
======================================================
A Distrobox-backed dev-environment tool in the spirit of Toolbx,
designed for FlucidOS and other immutable distributions.

Public surface
--------------
    from podbx import WorkspaceManager, Workspace
    from podbx.ui import PodbxApp
"""

from .workspace import Workspace, WorkspaceManager
from .ide import inject_ide_terminal_config
from .config import APP_NAME, APP_VERSION

__all__ = [
    "Workspace",
    "WorkspaceManager",
    "inject_ide_terminal_config",
    "APP_NAME",
    "APP_VERSION",
]

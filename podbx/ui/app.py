"""
podbx.ui.app
~~~~~~~~~~~~~
PodbxApp — the Adw.Application subclass.
Wires together the WorkspaceManager, the main window, and global actions.
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, Gtk

from ..config import APP_ID, APP_NAME, APP_VERSION
from ..workspace import WorkspaceManager
from .window import PodbxWindow


class PodbxApp(Adw.Application):
    def __init__(self, manager: WorkspaceManager | None = None):
        super().__init__(application_id=APP_ID)
        self._manager = manager or WorkspaceManager()
        self.connect("activate", self._on_activate)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def _on_activate(self, _app) -> None:
        win = PodbxWindow(manager=self._manager, application=self)
        win.set_icon_name("com.flucidos.Podbx")       # taskbar / Alt-Tab icon
        self._register_actions(win)
        win.present()

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _register_actions(self, win: PodbxWindow) -> None:
        act_about = Gio.SimpleAction.new("about", None)
        act_about.connect("activate", lambda _a, _b: self._show_about(win))
        self.add_action(act_about)

    def _show_about(self, parent: PodbxWindow) -> None:
        # Define the core metadata as a dictionary to pass directly into the constructor
        about_kwargs = {
            "application_name": APP_NAME,
            "application_icon": "com.flucidos.Podbx",
            "version": APP_VERSION,
            "developer_name": "FlucidOS Project",
            "website": "https://www.flucidos.com/projects/podbx",
            "issue_url": "https://github.com/flucidos/podbx/issues",
            "support_url": "https://github.com/flucidos/podbx/discussions",
            "copyright": "© 2026 FlucidOS Project",
            "license_type": Gtk.License.GPL_3_0,
            "comments": "Workspace manager for immutable Linux systems.\nPowered by Distrobox and Podman.",
        }

        # Adw.AboutDialog is available from libadwaita 1.4 (GNOME 46+).
        if hasattr(Adw, "AboutDialog"):
            about = Adw.AboutDialog(**about_kwargs)
            about.set_developers(["FlucidOS Project"])
            about.present(parent)
        else:
            # Fallback for libadwaita < 1.4
            about = Adw.AboutWindow(transient_for=parent, **about_kwargs)
            about.present()


def main_cli():
    """Console-script entry point (see pyproject.toml [project.scripts])."""
    import sys
    app = PodbxApp()
    return app.run(sys.argv)

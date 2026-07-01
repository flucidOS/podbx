"""
podbx.ui.dialogs
~~~~~~~~~~~~~~~~~
Modal dialog windows used by PodbxWindow.

Classes
-------
CreateWorkspaceDialog   — single-field name entry → create workspace
IDEAppChooserDialog     — searchable app list → open workspace in chosen IDE
"""

from __future__ import annotations

import os
import subprocess

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, GLib, Gtk

from ..ide import inject_ide_terminal_config
from ..workspace import Workspace, WorkspaceManager


# ---------------------------------------------------------------------------
# CreateWorkspaceDialog
# ---------------------------------------------------------------------------

class CreateWorkspaceDialog(Adw.Window):
    """
    Dialog for creating a new workspace.
    Header bar carries: [Cancel]  New Workspace  [Create]
    Body: labelled entry field.
    """

    def __init__(self, parent: Adw.ApplicationWindow, manager: WorkspaceManager):
        super().__init__(transient_for=parent, modal=True)
        self._parent = parent
        self._manager = manager

        self.set_title("New Workspace")
        self.set_default_size(400, 150)
        self.set_resizable(False)

        # ── Native Toolbar Layout ───────────────────────────────────────
        toolbar_view = Adw.ToolbarView()
        self.set_content(toolbar_view)

        # ── Header bar ──────────────────────────────────────────────────
        header = Adw.HeaderBar()
        header.set_show_end_title_buttons(False)
        header.set_show_start_title_buttons(False)
        toolbar_view.add_top_bar(header)

        # Cancel Button (Top Left)
        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.connect("clicked", lambda _: self.close())
        header.pack_start(cancel_btn)

        # Create Button (Top Right)
        self._create_btn = Gtk.Button(label="Create")
        self._create_btn.add_css_class("suggested-action")
        self._create_btn.set_sensitive(False)  # disabled until text entered
        self._create_btn.connect("clicked", self._on_create)
        header.pack_end(self._create_btn)

        # ── Body ─────────────────────────────────────────────────────────
        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        body.set_margin_top(24)
        body.set_margin_bottom(24)
        body.set_margin_start(24)
        body.set_margin_end(24)
        toolbar_view.set_content(body)

        label = Gtk.Label(label="Enter a name for your new project workspace:")
        label.set_halign(Gtk.Align.START)
        body.append(label)

        self._entry = Gtk.Entry(placeholder_text="e.g. my_awesome_app")
        self._entry.set_hexpand(True)
        self._entry.connect("activate", self._on_create)
        self._entry.connect("changed", self._on_entry_changed)
        body.append(self._entry)

    # ------------------------------------------------------------------

    def _on_entry_changed(self, entry: Gtk.Entry) -> None:
        """Enable the Create button only when there is non-blank text."""
        self._create_btn.set_sensitive(bool(entry.get_text().strip()))

    def _on_create(self, _widget) -> None:
        name = self._entry.get_text().strip()
        if not name:
            return
        self._entry.set_sensitive(False)
        self._create_btn.set_sensitive(False)
        try:
            self._manager.create(name)
        except (ValueError, FileExistsError, RuntimeError) as exc:
            self._entry.set_sensitive(True)
            self._create_btn.set_sensitive(True)
            err = Adw.AlertDialog(heading="Cannot create workspace", body=str(exc))
            err.add_response("ok", "OK")
            err.present(self)
            return
        self._parent.refresh()
        self.close()


# ---------------------------------------------------------------------------
# IDEAppChooserDialog
# ---------------------------------------------------------------------------

_IDE_KEYWORDS = [
    "code", "vscodium", "pycharm", "idea", "builder",
    "zed", "sublime", "eclipse", "kate", "gedit", "xed",
]


class IDEAppChooserDialog(Adw.Window):
    """Searchable list of installed apps; launches chosen app into the workspace."""

    def __init__(self, parent: Adw.ApplicationWindow, workspace: Workspace):
        super().__init__(transient_for=parent, modal=True)
        self._workspace = workspace

        self.set_title("Open With…")
        self.set_default_size(450, 600)

        # ── Native Toolbar Layout ───────────────────────────────────────
        toolbar_view = Adw.ToolbarView()
        self.set_content(toolbar_view)

        # Header with inline search
        header = Adw.HeaderBar()
        search_entry = Gtk.SearchEntry()
        search_entry.set_hexpand(True)
        search_entry.set_placeholder_text("Search Applications…")
        search_entry.connect("search-changed", self._on_search_changed)
        header.set_title_widget(search_entry)
        toolbar_view.add_top_bar(header)

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.add_css_class("view")
        toolbar_view.set_content(scroll)

        page = Adw.PreferencesPage()
        scroll.set_child(page)

        self._recommended_group = Adw.PreferencesGroup(
            title="Recommended IDEs & Editors"
        )
        page.add(self._recommended_group)

        self._other_group = Adw.PreferencesGroup(title="Other Applications")
        page.add(self._other_group)

        # (row, is_recommended, search_name_lower, GioAppInfo)
        self._app_rows: list[tuple] = []
        self._load_apps()

    # ------------------------------------------------------------------
    # App discovery
    # ------------------------------------------------------------------

    def _load_apps(self) -> None:
        recommended_ids = {
            app.get_id()
            for app in Gio.AppInfo.get_recommended_for_type("text/plain")
            if app.get_id()
        }

        all_apps = sorted(
            Gio.AppInfo.get_all(),
            key=lambda a: (a.get_name() or "").lower(),
        )

        for app in all_apps:
            if not app.should_show():
                continue

            name     = app.get_name() or ""
            app_id   = app.get_id()   or ""
            exec_cmd = (app.get_executable() or "").lower()

            is_recommended = app_id in recommended_ids or any(
                kw in exec_cmd or kw in name.lower() for kw in _IDE_KEYWORDS
            )

            row = Adw.ActionRow(title=GLib.markup_escape_text(name))
            desc = app.get_description()
            if desc:
                row.set_subtitle(GLib.markup_escape_text(desc))
                row.set_subtitle_lines(1)

            icon = app.get_icon()
            if icon:
                valid = True
                if isinstance(icon, Gio.FileIcon):
                    gfile = icon.get_file()
                    if gfile and not gfile.query_exists():
                        valid = False
                if valid:
                    img = Gtk.Image.new_from_gicon(icon)
                    img.set_pixel_size(32)
                    row.add_prefix(img)

            row.set_activatable(True)
            row.connect("activated", lambda _r, a=app: self._on_app_activated(a))

            self._app_rows.append((row, is_recommended, name.lower(), app))

            if is_recommended:
                self._recommended_group.add(row)
            else:
                self._other_group.add(row)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def _on_search_changed(self, entry: Gtk.SearchEntry) -> None:
        query = entry.get_text().lower()
        for row, _rec, search_name, _app in self._app_rows:
            row.set_visible(not query or query in search_name)

    # ------------------------------------------------------------------
    # Launch
    # ------------------------------------------------------------------

    def _on_app_activated(self, app_info: Gio.AppInfo) -> None:
        executable = app_info.get_executable() or ""
        raw_id     = app_info.get_id() or ""
        app_id     = raw_id.removesuffix(".desktop")

        is_flatpak = (
            executable == "/usr/bin/flatpak"
            or os.path.exists(f"/var/lib/flatpak/app/{app_id}")
            or os.path.exists(
                os.path.expanduser(f"~/.local/share/flatpak/app/{app_id}")
            )
        )

        inject_ide_terminal_config(
            self._workspace.path,
            flatpak_app_id=app_id if is_flatpak else None,
        )

        try:
            if is_flatpak and app_id:
                subprocess.Popen(["flatpak", "run", app_id, self._workspace.path])
            else:
                subprocess.Popen([executable, self._workspace.path])
        except Exception as exc:
            print(f"Direct launch failed ({exc}), trying GIO fallback…")
            try:
                app_info.launch([Gio.File.new_for_path(self._workspace.path)], None)
            except Exception as exc2:
                print(f"GIO launch also failed: {exc2}")

        self.close()

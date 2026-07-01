"""
podbox.ui.window
~~~~~~~~~~~~~~~~
PodbxWindow — the main application window.

Setup flow
----------
If podbx-os doesn't exist yet, container creation starts automatically in a
background thread the moment the window is shown. The user sees a clean
animated setup page. Once the container is ready (or already existed), the
window switches to the normal workspace list. Workspace creation and terminal
launch never touch container initialisation — the container is always ready
by the time the user gets there.
"""

import subprocess
import threading
import re

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, GLib, Gtk

from ..config import APP_NAME, BASE_CONTAINER
from ..workspace import Workspace, WorkspaceManager
from .dialogs import CreateWorkspaceDialog, IDEAppChooserDialog


def _container_exists() -> bool:
    try:
        result = subprocess.run(
            ["distrobox", "list"],
            capture_output=True, text=True, timeout=5,
        )
        return BASE_CONTAINER in result.stdout
    except Exception:
        return False


# Status messages shown in sequence while the container is being created.
# Each string is shown for roughly 4 seconds before cycling to the next.
_SETUP_MESSAGES = [
    "Starting container…",
    "Installing basic packages…",
    "Setting up mounts…",
    "Integrating host themes and fonts…",
    "Setting up package manager…",
    "Configuring user environment…",
    "Almost there…",
]


class PodbxWindow(Adw.ApplicationWindow):
    def __init__(self, manager: WorkspaceManager, **kwargs):
        super().__init__(**kwargs)
        self.manager = manager

        self.set_title(APP_NAME)
        self.set_default_size(700, 550)

        # ── Native Toolbar Layout ─────────────────────────────────────
        self.toolbar_view = Adw.ToolbarView()
        self.set_content(self.toolbar_view)

        # ── Header ────────────────────────────────────────────────────
        self._header = Adw.HeaderBar()
        self.toolbar_view.add_top_bar(self._header)

        menu_btn = Gtk.MenuButton(icon_name="open-menu-symbolic")
        self._header.pack_start(menu_btn)
        menu_model = Gio.Menu()
        menu_model.append("About Podbx", "app.about")
        menu_btn.set_menu_model(menu_model)

        # ── Center UI Clamp ───────────────────────────────────────────
        self.clamp = Adw.Clamp()
        self.clamp.set_maximum_size(600)
        self.toolbar_view.set_content(self.clamp)

        # ── Stack ─────────────────────────────────────────────────────
        self._stack = Gtk.Stack()
        self._stack.set_vexpand(True)
        self._stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self._stack.set_transition_duration(400)
        self.clamp.set_child(self._stack)

        self._build_setup_page()
        self._build_main_page()

        # Internal state for background timers
        self._pulse_timer_id   = None
        self._rows: list[Adw.ActionRow] = []

        self._start(skip_welcome=_container_exists())

    # ------------------------------------------------------------------
    # Startup logic
    # ------------------------------------------------------------------

    def _start(self, skip_welcome: bool) -> None:
        if skip_welcome:
            # Container already exists — go straight to the workspace list
            self._show_main()
        else:
            # Show setup page and immediately begin container creation in bg
            self._stack.set_visible_child_name("setup")
            self._start_setup_animation()
            threading.Thread(target=self._run_container_create, daemon=True).start()

    # ------------------------------------------------------------------
    # Page builders
    # ------------------------------------------------------------------

    def _build_setup_page(self) -> None:
        """
        Modern, clean setup page.
        No log dump — just an icon, title, animated status line, and a
        pulsing progress bar.
        """
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        outer.set_valign(Gtk.Align.CENTER)
        outer.set_vexpand(True)
        outer.set_spacing(0)
        outer.set_margin_top(48)
        outer.set_margin_bottom(48)
        outer.set_margin_start(48)
        outer.set_margin_end(48)

        # Icon
        icon = Gtk.Image.new_from_icon_name("system-run-symbolic")
        icon.set_pixel_size(64)
        icon.add_css_class("dim-label")
        icon.set_margin_bottom(24)
        outer.append(icon)

        # Title
        title = Gtk.Label(label="Setting Up Environment")
        title.add_css_class("title-1")
        title.set_halign(Gtk.Align.CENTER)
        outer.append(title)

        # Subtitle — cycles through _SETUP_MESSAGES
        self._setup_status = Gtk.Label(label="Preparing…")
        self._setup_status.add_css_class("dim-label")
        self._setup_status.set_halign(Gtk.Align.CENTER)
        self._setup_status.set_margin_top(8)
        self._setup_status.set_margin_bottom(16)
        outer.append(self._setup_status)

        # Pulsing progress bar
        self._progress = Gtk.ProgressBar()
        self._progress.set_pulse_step(0.03)
        self._progress.set_size_request(320, -1)
        self._progress.set_halign(Gtk.Align.CENTER)
        self._progress.set_margin_bottom(16)
        outer.append(self._progress)

        # Reassurance text
        reassurance = Gtk.Label(label="Don't worry, this is a one-time setup.")
        reassurance.add_css_class("caption")
        reassurance.add_css_class("dim-label")
        reassurance.set_halign(Gtk.Align.CENTER)
        outer.append(reassurance)

        self._stack.add_named(outer, "setup")

    def _build_main_page(self) -> None:
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)

        page = Adw.PreferencesPage()
        scroll.set_child(page)

        self._list_group = Adw.PreferencesGroup(title="Your Workspaces")
        page.add(self._list_group)

        footer_group = Adw.PreferencesGroup()
        footer_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        footer_box.set_margin_top(20)
        footer_box.set_margin_bottom(20)
        footer_group.add(footer_box)
        page.add(footer_group)

        add_btn = Gtk.Button(label="New Workspace")
        add_btn.add_css_class("pill")
        add_btn.add_css_class("suggested-action")
        add_btn.set_halign(Gtk.Align.CENTER)
        add_btn.set_size_request(200, -1)
        add_btn.connect("clicked", self._on_add_clicked)
        footer_box.append(add_btn)

        self._stack.add_named(scroll, "main")

    # ------------------------------------------------------------------
    # Setup animation (main thread timers)
    # ------------------------------------------------------------------

    def _start_setup_animation(self) -> None:
        self._setup_status.set_label("Starting container…")
        # Pulse bar every 60 ms
        self._pulse_timer_id = GLib.timeout_add(60, self._on_pulse_tick)

    def _on_pulse_tick(self) -> bool:
        self._progress.pulse()
        return True  # keep repeating

    def _stop_setup_animation(self) -> None:
        if self._pulse_timer_id is not None:
            GLib.source_remove(self._pulse_timer_id)
            self._pulse_timer_id = None

    def _update_status_label(self, msg: str) -> bool:
        self._setup_status.set_label(msg)
        return False  # Run once per idle trigger

    # ------------------------------------------------------------------
    # Background container creation
    # ------------------------------------------------------------------

    def _run_container_create(self) -> None:
        """Runs in a daemon thread — ensures container exists and is ready."""
        try:
            # 1. Check if container exists
            check_res = subprocess.run(
                ["distrobox", "list", "--no-color"],
                capture_output=True, text=True
            )
            container_exists = BASE_CONTAINER in check_res.stdout

            # 2. Only create if it doesn't exist
            if not container_exists:
                create_res = subprocess.run(
                    ["distrobox", "create", "--name", BASE_CONTAINER, "--image", "podbx-base:latest", "--yes"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                if create_res.returncode != 0:
                    raise RuntimeError("Failed to create container")

            # 3. Always run the 'enter' initialization to ensure mounts/packages are ready
            ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\\[[0-?]*[ -/]*[@-~])")
            process = subprocess.Popen(
                ["distrobox", "enter", BASE_CONTAINER, "--", "true"],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1
            )
            
            for line in process.stdout:
                clean_line = ansi_escape.sub("", line).strip()
                if clean_line:
                    if "..." in clean_line:
                        msg = clean_line.split("...")[0] + "…"
                        GLib.idle_add(self._update_status_label, msg)
                    elif not clean_line.startswith("["):
                        GLib.idle_add(self._update_status_label, clean_line)

            process.wait()
            if process.returncode != 0:
                raise RuntimeError("Failed to initialize container")

            success = True
        except Exception:
            success = False

        GLib.idle_add(self._on_container_ready, success)

    def _on_container_ready(self, success: bool) -> bool:
        """Called on the main thread when distrobox create finishes."""
        self._stop_setup_animation()

        if success:
            self._progress.set_fraction(1.0)
            self._setup_status.set_label("Environment ready!")
            # Brief pause so the user reads "ready", then switch to main
            GLib.timeout_add(800, self._show_main)
        else:
            # Show an error dialog — user can retry by restarting the app
            self._setup_status.set_label("Setup failed.")
            dialog = Adw.AlertDialog(
                heading="Setup Failed",
                body=(
                    "Could not create the podbx-os container.\n"
                    "Make sure Podman and Distrobox are installed, "
                    "then restart Podbx to try again."
                ),
            )
            dialog.add_response("ok", "OK")
            dialog.present(self)

        return False

    # ------------------------------------------------------------------
    # Main page
    # ------------------------------------------------------------------

    def _show_main(self) -> bool:
        """Switch to the workspace list and populate it."""
        self._stack.set_visible_child_name("main")
        self.refresh()
        return False  # stops GLib.timeout_add from repeating

    def refresh(self) -> None:
        for row in self._rows:
            self._list_group.remove(row)
        self._rows.clear()

        workspaces = self.manager.list_workspaces()
        if not workspaces:
            row = Adw.ActionRow(
                title="No workspaces yet",
                subtitle="Click 'New Workspace' to get started.",
            )
            self._list_group.add(row)
            self._rows.append(row)
            return

        for ws in workspaces:
            self._add_workspace_row(ws)

    def _add_workspace_row(self, ws: Workspace) -> None:
        row = Adw.ActionRow(
            title=GLib.markup_escape_text(ws.name),
            subtitle=ws.path,
        )
        row.set_title_lines(1)

        open_with_btn = Gtk.Button(label="Open With")
        open_with_btn.set_valign(Gtk.Align.CENTER)
        open_with_btn.add_css_class("pill")
        open_with_btn.connect("clicked", lambda _b, w=ws: self._on_open_with(w))
        row.add_suffix(open_with_btn)

        terminal_btn = Gtk.Button(label="Open Terminal")
        terminal_btn.set_valign(Gtk.Align.CENTER)
        terminal_btn.add_css_class("flat")
        terminal_btn.connect("clicked", lambda _b, w=ws: self._on_open_terminal(w))
        row.add_suffix(terminal_btn)

        del_btn = Gtk.Button(icon_name="user-trash-symbolic")
        del_btn.set_valign(Gtk.Align.CENTER)
        del_btn.add_css_class("flat")
        del_btn.add_css_class("destructive-action")
        del_btn.connect("clicked", lambda _b, w=ws: self._on_delete(w))
        row.add_suffix(del_btn)

        self._list_group.add(row)
        self._rows.append(row)

    # ------------------------------------------------------------------
    # Signal handlers
    # ------------------------------------------------------------------

    def _on_add_clicked(self, _btn) -> None:
        dialog = CreateWorkspaceDialog(parent=self, manager=self.manager)
        dialog.connect("destroy", lambda _: self.refresh())
        dialog.present()

    def _on_open_with(self, ws: Workspace) -> None:
        IDEAppChooserDialog(parent=self, workspace=ws).present()

    def _on_open_terminal(self, ws: Workspace) -> None:
        try:
            self.manager.open_terminal(ws)
        except RuntimeError as exc:
            self._show_error(str(exc))

    def _on_delete(self, ws: Workspace) -> None:
        self.manager.delete(ws)
        self.refresh()

    def _show_error(self, message: str) -> None:
        dialog = Adw.AlertDialog(heading="Error", body=message)
        dialog.add_response("ok", "OK")
        dialog.present(self)

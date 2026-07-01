# Podbx

<p align="left">
  <strong>Workspace Manager for Immutable Linux Systems</strong>
</p>

Podbx is a GTK4/libadwaita graphical application and CLI backend designed to manage isolated development environments on immutable Linux operating systems. 

Built on top of [Distrobox](https://distrobox.it/) and [Podman](https://podman.io/), Podbx provisions a shared, enriched base operating system container and maps individual project directories ("workspaces") into it. It seamlessly bridges the gap between host tools and containerized environments, ensuring your integrated IDE terminals and workflows feel completely native.

---

## Features

* **Project-Centric Isolation:** Manage distinct workspace directories rather than sharing a single monolithic container home directory.
* **Native GTK4 Interface:** A beautiful, responsive libadwaita frontend that abstracts CLI complexities and handles asynchronous container initialization in the background.
* **Zero-Friction IDE Integration:** Automatically patches local configurations for VS Code, VSCodium. When you open a terminal in your editor, it securely drops you directly into your containerized workspace.
* **Flatpak Awareness:** Intelligently detects if your IDE is running as a Flatpak and automatically generates `flatpak-spawn --host` shell wrappers to bridge the sandbox.
* **User-Space Operation:** No root required. Everything runs entirely in user-space.

---

## Architecture Overview

Podbx is split into two primary layers:

1. **CLI Backend (`bin/podbx-cli`)**: A robust Bash wrapper around `distrobox` and `podman`. It enforces container presence and handles the secure mounting and entry into workspace directories.
2. **Python Frontend (`podbx.ui`)**: A GTK4 application that manages the asynchronous creation of the shared `podbx-base` container, tracks workspace metadata (`.podbx_workspace.json`), and handles the IDE configuration injections.

By default, Podbx uses a `debian:stable-slim` image enriched with a "Just Works" toolkit (`build-essential`, `python3`, `git`, etc.) to prevent developers from needing to bootstrap basic utilities for every new project.

---

## Prerequisites

Podbx needs the following installed **on the host system** (not inside the container):

### Required

- **Podman** — builds and runs the base container image
- **Distrobox** — manages the `podbx-os` container and workspace entry
- **Python 3.11+**
- **GTK4 & libadwaita bindings**
  * `python3-gi`
  * `gir1.2-gtk-4.0`
  * `gir1.2-adw-1`
- **A terminal emulator** — at least one of:
  `ptyxis`, `gnome-console`, `gnome-terminal`, `konsole`, `xterm`
- **pip** or **pipx** — to install the `podbx` Python package (`python3-pip` / `pipx`)

### Optional

- **Flatpak** — only needed if you plan to launch a Flatpak-installed IDE (e.g. PyCharm via Flatpak) through "Open With"; Podbx auto-detects Flatpak apps and wraps terminal entry with `flatpak-spawn --host`


### Debian/Ubuntu install command

```bash
sudo apt install podman python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 python3-pip pipx
```

Distrobox isn't packaged everywhere — install via their [official script](https://github.com/89luca89/distrobox/blob/main/install.md):

```bash
curl -s https://raw.githubusercontent.com/89luca89/distrobox/main/install | sh -s -- --prefix ~/.local
```

### Python package dependencies

None — `podbx` has zero third-party PyPI dependencies (``pyproject.toml`` declares ``dependencies = []``). GTK/Adwaita bindings must come from your distro's system packages, since ``PyGObject`` isn't pip-installable in a clean way alongside GTK4 system libraries.

**Build-time only:** `setuptools>=68`, `wheel` (used by pip/pipx during install, not needed at runtime).

---

## Installation

Podbx is designed to be installed at the user level. 

Clone the repository and run the provided installation script:

```bash
git clone [https://github.com/flucidos/podbx.git](https://github.com/flucidos/podbx.git)
cd podbx
./install.sh
```

> [!NOTE]
> ``Pobox`` is the default container option for flucidOS, and hence it is a pre-intalled package in flucidOS.

## What the installer does:

- Builds the podbx-base:latest Podman container image.

- Installs the CLI backend to ``~/.local/share/podbx/bin/``.

- Installs the application icon and .desktop entry to ``~/.local/share/``.

You can now launch Podbx directly from your desktop application launcher.

## Usage
### Graphical Interface
Launch Podbx from your app menu.

- On first launch, the GUI will silently initialize your base container in the background.

- Click New Workspace to create a directory in ``~/Podbx_Projects``.

- Use the Open With button to scan your host system for IDEs and launch them directly into the containerized context.

### Command Line Interface
Power users can bypass the GUI and use the CLI directly. Ensure ``~/.local/share/podbx/bin/`` is in your $PATH, or run it via absolute path:

```Bash
# Create a new workspace directory and metadata file
podbx-cli create my_project ~/Podbx_Projects/my_project

# Enter the workspace (drops you into a containerized bash shell)
podbx-cli enter ~/Podbx_Projects/my_project

# Delete the workspace directory from the host
podbx-cli delete ~/Podbx_Projects/my_project
```
## How IDE Integration Works
The hardest part of containerized development is ensuring your editor's integrated terminal works correctly. Podbx solves this automatically.

When you launch an IDE via the Podbx GUI:

- It creates a ``.podbx/podbx-shell.sh`` executable script inside your project folder.

- It writes or patches the local IDE configuration (e.g., ``.vscode/settings.json``) to set the default terminal profile to this new script.

- Every time you open a terminal tab in your IDE, the script executes, transparently entering the Distrobox container before presenting the prompt.

## Uninstallation
To completely remove Podbx and clean up system links, run the uninstall script from the source directory:

```Bash
./uninstall.sh
```
The script will prompt you before deleting your workspace data in ``~/Podbx_Projects`` or the podbx-os container.

---
## Road Map
### To Do:
- [ ] Write Test Cases 
- [ ] Write documentation
- [ ] Set up CI/CD pipeline

### IDEs Implemented:
- [X] VS-Code/VS-Codium

### IDEs to integrate:
- [ ] Eclipse IDE
- [ ] Apache NetBeans
- [ ] JetBrains Family
- [ ] Qt Creator
- [ ] KDevelop
- [ ] Geany
- [ ] Kate


---
## License
Podbx is licensed under the **GPL-3.0**, see [LICENSE](LICENSE)

*© 2026 FlucidOS Project*.

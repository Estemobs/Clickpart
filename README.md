# Clickpak

**Universal graphical installer for Linux: double-click .flatpakref, .AppImage, .pkg.tar.zst and more to install them.**

[![License: GPL-3.0](https://img.shields.io/badge/License-GPL%203.0-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![GTK4](https://img.shields.io/badge/GTK-4-green.svg)](https://gtk.org/)

Clickpak is a lightweight GUI wrapper around native Linux installation commands. It registers as the default handler for package file types, so you can simply double-click any supported file to install it — no terminal required.

## Features

- **Zero-configuration**: Works out of the box on Arch, EndeavourOS, Manjaro, and other distributions
- **Multi-format support**: Handles 10+ package formats (see table below)
- **Transparent**: Shows the exact command that will be executed before running it
- **Safe by default**: Requires confirmation for every installation
- **Lightweight**: Single Python script + GTK4, no Electron, no daemon
- **Native integration**: Uses `polkit` for privilege elevation, standard `.desktop`/MIME associations

## Supported Formats

| Format | Command | Root Required | Since |
|--------|---------|---------------|-------|
| `.pkg.tar.zst` / `.pkg.tar.xz` | `pacman -U` | Yes (polkit) | v0.1 |
| `.flatpakref` / `.flatpak` | `flatpak install` | No (user) | v0.1 |
| `.AppImage` | Copy to `~/Applications`, create `.desktop` & icon | No | v0.1 |
| `.snap` | `snap install --dangerous` | Yes | v0.3 |
| `.vsix` | `code --install-extension` | No | v0.4 |
| `.shell-extension.zip` | `gnome-extensions install` | No | v0.4 |
| `.run` / `.sh` | Execute with warning | Variable | v0.4 |
| `.exe` / `.msi` | Via Wine or Bottles | No | v0.5 |
| `.jar` | `java -jar` | No | v0.5 |
| `PKGBUILD` (dir/archive) | `makepkg -si` | Yes | v0.3 |
| `.tar.gz` / `.zip` / etc. | Heuristic (see docs) | No | v0.6 |

## Installation

### Arch Linux / EndeavourOS / Manjaro (AUR)

```bash
# Stable release
yay -S clickpak

# Git version
yay -S clickpak-git
```

### From Source

```bash
git clone https://github.com/clickpak/clickpak
cd clickpak
pip install -r requirements.txt  # or use your distro's packages
python3 src/main.py --help
```

### Requirements

- Python 3.10+
- GTK4 + libadwaita
- python-gobject
- python-magic (libmagic)
- flatpak, pacman, polkit (for respective backends)

## Usage

Simply double-click any supported file in your file manager, or run from terminal:

```bash
clickpak package.pkg.tar.zst
clickpak app.flatpakref
clickpak application.AppImage
```

### Configuration

On first run, Clickpak will ask to become the default handler for supported file types.

Settings are stored in `~/.config/clickpak/config.toml`:

```toml
[general]
app_dir = "~/Applications"
silent_formats = ["flatpakref", "flatpak", "appimage"]
confirm_by_default = true

[formats]
pacman = { enabled = true, silent = false }
flatpakref = { enabled = true, silent = true }
appimage = { enabled = true, silent = true }
# ... etc
```

## Security

Clickpak follows security best practices:

- **Confirmation by default** — you always see what will run
- **No shell interpolation** — commands passed as argument lists, preventing injection
- **Polkit integration** — standard authentication dialog, no `sudo` in GUI
- **Full audit log** — every installation logged to `~/.local/state/clickpak/history.log`
- **Warning for risky formats** — `.run`, `.sh`, `.exe` show prominent warnings

## Why Not Flatpak?

Clickpak **cannot be distributed as a Flatpak** because the sandbox prevents it from calling system package managers (`pacman`, `snap`, etc.) or writing to host directories like `/usr` or `~/Applications`. This is a fundamental architectural constraint — Clickpak must run on the host.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add a backend in `src/backends/` (see `BASE_BACKEND.md`)
4. Submit a PR

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

GPL-3.0-or-later — see [LICENSE](LICENSE) for details.

## Acknowledgments

Inspired by [Bauh](https://github.com/vinifmor/bauh), [Gear Lever](https://github.com/mjakeman/gear-lever), [AppImageLauncher](https://github.com/TheAssassin/AppImageLauncher), and the Unix philosophy: *do one thing well*.
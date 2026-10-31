# Clickpart

**Universal graphical installer for Linux: install .flatpakref, .AppImage, .pkg.tar.zst and more effortlessly.**

![Clickpart in action](docs/screenshots/main.png)

Clickpart is a lightweight, fast, and native GUI installer for Linux, built with Tauri and Rust. It registers as the default handler for package file types, allowing you to install supported files with a simple double-click.

## Features

- **Native Performance**: Built with Rust/Tauri for minimal footprint.
- **Smart Detection**: Automatically detects your distribution and prioritizes supported formats.
- **Multi-format support**: Handles 10+ package formats (see table below).
- **Safe by default**: Requires confirmation for every installation.
- **Polkit Integration**: Uses system policies for privilege elevation, no `sudo` in GUI.
- **Distro-Aware**: Tailors UI/UX based on detected system tools (Arch/pacman, etc.).

## Supported Formats

| Format | Command | Root Required |
|--------|---------|---------------|
| `.pkg.tar.zst` | `pacman -U` | Yes (polkit) |
| `.flatpakref` / `.flatpak` | `flatpak install` | No (user) |
| `.AppImage` | Copy + Desktop integration | No |
| `.tar.gz` / `.zip` | Heuristic extraction | No |
| `PKGBUILD` | `makepkg -si` | Yes |
| ... | ... | ... |

## Installation

### From AppImage
Download the latest `.AppImage` from the [Releases page](https://github.com/estemobs/Clickpart/releases), make it executable, and run it.

### From Source
1. Ensure Rust, Tauri CLI, and Node.js are installed.
2. `git clone https://github.com/estemobs/Clickpart`
3. `cd Clickpart`
4. `npm install`
5. `npm run build`

## Usage

Once installed, Clickpart registers itself as the default handler for the supported file types. You can simply double-click any of these files in your file manager to install them.

![Installation dialog](docs/screenshots/install.png)

## Security

Clickpart follows security best practices:

- **Confirmation by default** — you always see what will run.
- **No shell interpolation** — commands passed as argument lists, preventing injection.
- **Polkit integration** — standard authentication dialog, no `sudo` in GUI.
- **Full audit log** — every installation is logged.

## Why Not Flatpak?

Clickpart **cannot be distributed as a Flatpak** because the sandbox prevents it from calling system package managers (`pacman`, etc.) or writing to host directories. This is a fundamental architectural constraint — Clickpart must run on the host.

## License

GPL-3.0-or-later — see [LICENSE](LICENSE) for details.

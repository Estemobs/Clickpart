# Changelog

All notable changes to Clickpak will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/lang/fr/).

## [0.1.0] - 2026-10-28

### Added
- Initial prototype: Python + GTK4 + libadwaita
- Format detection by extension, MIME type, and content inspection
- Backends for `.pkg.tar.zst`, `.flatpakref`, `.AppImage`
- Confirmation dialog with command preview
- Progress dialog with real-time output
- Configuration via TOML (`~/.config/clickpak/config.toml`)
- History logging (`~/.local/state/cickpak/history.log`)
- Desktop integration (`.desktop`, MIME associations)
- Polkit policy file (`org.clickpak.policy`)
- AUR package (`packaging/arch/PKGBUILD`)
- English (`README.md`) and French (`README.fr.md`) documentation
- `CONTRIBUTING.md` and `CODE_OF_CONDUCT.md`
- GPL-3.0 license

### Security
- Confirmation required by default
- No shell interpolation (commands as argument lists)
- Polkit elevation instead of `sudo`
- Full audit trail
- Prominent warnings for `.run`, `.sh`, `.exe`

[0.1.0]: https://github.com/clickpak/clickpak/releases/tag/v0.1.0
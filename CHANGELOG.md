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

[0.5.0] - 2026-10-28

### Added
- Unit tests for `detect.py`: `detect_file()` interface; `.flatpakref` and `.pkg.tar.zst` coverage (`tests/test_detect.py`)
- Real `.AppImage` validation (`obsolete-appimagetool-AppImage`); backend install verified, `.desktop` `Exec=` absolute
- Local PKGBUILD (`packaging/arch/PKGBUILD`) updated to `pkgver=0.5.0`; manual install verified (`/tmp/clickpak-install`)
- `docs/status-v0.4.md` updated with v0.5 results

### Changed
- `CHANGELOG.md` and `TODO.md` updated for v0.4 / v0.5
- `src/detect.py`: `detect_file()` wrapper; fixed `import os` placement

### Security
- Polkit policy hardened (v0.4)
- `.run` / `.sh` / `.exe` warnings prominent (v0.4)

### Fixed
- Import error in `detect.py`; interface pinning for tests

[0.4.0] - 2026-10-28

### Added
- Hardening: polkit elevation locked, `.run` / `.sh` / `.exe` prominent warnings
- History UI integration (`~/.local/state/clickpak/history.log`)
- Desktop integration finalized (`update-desktop-database` path documented)
- AUR package (`packaging/arch/PKGBUILD`)

### Fixed
- `.desktop` `Exec=` must be absolute (not relative)
- `pkexec` container failure documented (expected, not a regression)

[0.5.0]: https://github.com/clickpak/clickpak/releases/tag/v0.5.0
[0.4.0]: https://github.com/clickpak/clickpak/releases/tag/v0.4.0
[0.1.0]: https://github.com/clickpak/clickpak/releases/tag/v0.1.0
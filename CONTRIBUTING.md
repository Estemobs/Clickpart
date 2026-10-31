# Contributing to Clickpart

Thank you for your interest in contributing to Clickpart! This document outlines the process for contributing.

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## How to Contribute

### Reporting Bugs

1. Check if the issue already exists in [GitHub Issues](https://github.com/clickpart/clickpart/issues)
2. Create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Your distribution, desktop environment, Clickpart version
   - Relevant log output (`~/.local/state/clickpart/history.log`)

### Suggesting Features

Open an issue with the "enhancement" label describing:
- The problem you're trying to solve
- Your proposed solution
- Any alternatives considered

### Adding a New Backend

This is the most common contribution! Each format = one backend file.

1. Create `src/backends/yourformat.py` following the template:

```python
from . import BaseBackend
from pathlib import Path
from typing import List

class YourFormatBackend(BaseBackend):
    format_type = "yourformat"      # Unique identifier
    format_name = "Your Format"     # Human-readable name
    extensions = [".yourformat"]    # File extensions
    
    def can_handle(self, path: Path) -> bool:
        return path.name.lower().endswith(".yourformat")
    
    def describe(self, path: Path) -> str:
        return f"Your format package: {path.name}"
    
    def get_install_command(self, path: Path) -> List[str]:
        return ["your-install-command", str(path)]
    
    def requires_root(self) -> bool:
        return False  # or True
```

2. Register it in `src/backends/__init__.py` by adding to the `BACKENDS` list

3. Add the MIME type to `data/clickpart.desktop` if needed

4. Add a test file in `tests/test_yourformat.py`

5. Update the formats table in `README.md` and `README.fr.md`

### Code Style

- Python: Follow PEP 8, use type hints
- Run `ruff check .` and `ruff format .` before committing
- GTK4: Follow GNOME HIG guidelines

### Testing

```bash
# Run unit tests
python -m pytest tests/

# Manual test on Arch VM
makepkg -si  # from packaging/arch/
```

### Pull Request Process

1. Fork the repo and create a branch from `main`
2. Make your changes with clear, atomic commits
3. Update documentation if needed
4. Ensure tests pass
5. Open a PR with a clear description

## Development Setup

```bash
git clone https://github.com/clickpart/clickpart
cd clickpart
python3 -m venv venv
source venv/bin/activate
pip install -e .  # or install deps manually
```

## Architecture Overview

```
src/
├── main.py              # Entry point
├── detect.py            # Format detection
├── config.py            # TOML configuration
├── backends/
│   ├── __init__.py      # Backend registry
│   ├── pacman.py        # .pkg.tar.*
│   ├── flatpak.py       # .flatpakref, .flatpak
│   ├── appimage.py      # .AppImage
│   └── ...              # One file per format
└── ui/
    ├── confirm_dialog.py   # Installation confirmation
    └── progress_dialog.py  # Real-time output
```

## Questions?

Open a [GitHub Discussion](https://github.com/clickpart/clickpart/discussions) or ask in the issue tracker.
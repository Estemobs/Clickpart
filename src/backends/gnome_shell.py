#!/usr/bin/env python3
"""
GNOME Shell extension backend for .zip files containing extensions.
"""

from pathlib import Path
from typing import List
from . import BaseBackend


class GnomeShellExtensionBackend(BaseBackend):
    format_type = "gnome-shell-extension"
    format_name = "GNOME Shell Extension"
    extensions = [".shell-extension.zip", ".zip"]
    
    def can_handle(self, path: Path) -> bool:
        name = path.name.lower()
        return name.endswith(".shell-extension.zip") or (
            name.endswith(".zip") and self._looks_like_gnome_extension(path)
        )
    
    def _looks_like_gnome_extension(self, path: Path) -> bool:
        """Check if zip contains metadata.json (GNOME extension marker)."""
        import zipfile
        try:
            with zipfile.ZipFile(path, 'r') as zf:
                return any('metadata.json' in n for n in zf.namelist())
        except Exception:
            return False
    
    def describe(self, path: Path) -> str:
        return f"GNOME Shell Extension: {path.name}"
    
    def get_install_command(self, path: Path) -> List[str]:
        return ["gnome-extensions", "install", "--force", str(path)]
    
    def requires_root(self) -> bool:
        return False
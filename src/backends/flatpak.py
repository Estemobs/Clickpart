#!/usr/bin/env python3
"""
Flatpak backend for .flatpakref and .flatpak files.
"""

from pathlib import Path
from typing import List
from . import BaseBackend


class FlatpakBackend(BaseBackend):
    format_type = "flatpakref"  # handles both .flatpakref and .flatpak
    format_name = "Flatpak Application"
    extensions = [".flatpakref", ".flatpak"]
    
    def can_handle(self, path: Path) -> bool:
        name = path.name.lower()
        return any(name.endswith(ext) for ext in self.extensions)
    
    def describe(self, path: Path) -> str:
        # For .flatpakref, try to parse it
        if path.suffix.lower() == ".flatpakref":
            try:
                content = path.read_text()
                # flatpakref is a simple key=value file
                for line in content.split('\n'):
                    if line.startswith('Name='):
                        return f"Flatpak: {line[5:].strip()}"
                    if line.startswith('Title='):
                        return f"Flatpak: {line[6:].strip()}"
            except Exception:
                pass
        return f"Flatpak application: {path.name}"
    
    def get_install_command(self, path: Path) -> List[str]:
        return ["flatpak", "install", "--user", "--noninteractive", str(path)]
    
    def requires_root(self) -> bool:
        return False  # User installation by default
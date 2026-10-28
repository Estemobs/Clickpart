#!/usr/bin/env python3
"""
Backend for .run and .sh installer scripts.
"""

from pathlib import Path
from typing import List
from . import BaseBackend


class RunScriptBackend(BaseBackend):
    format_type = "run"
    format_name = "Installer Script"
    extensions = [".run", ".sh"]
    
    def can_handle(self, path: Path) -> bool:
        name = path.name.lower()
        return name.endswith(".run") or name.endswith(".sh")
    
    def describe(self, path: Path) -> str:
        return f"Installer script: {path.name}\n⚠️  WARNING: This will execute an arbitrary script. Only run if you trust the source."
    
    def get_install_command(self, path: Path) -> List[str]:
        # Immédiat, sans interpolation shell — mais avec avertissement
        # On passe le chemin directement, pas dans un -c
        return ["/bin/sh", str(path)]
    
    def requires_root(self) -> bool:
        # Could be either, default to False but warn
        return False
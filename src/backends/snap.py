#!/usr/bin/env python3
"""
Snap backend for .snap files.
"""

from pathlib import Path
from typing import List
from . import BaseBackend


class SnapBackend(BaseBackend):
    format_type = "snap"
    format_name = "Snap Package"
    extensions = [".snap"]
    
    def can_handle(self, path: Path) -> bool:
        return path.name.lower().endswith(".snap")
    
    def describe(self, path: Path) -> str:
        return f"Snap package: {path.name}"
    
    def get_install_command(self, path: Path) -> List[str]:
        return ["pkexec", "snap", "install", "--dangerous", str(path)]
    
    def requires_root(self) -> bool:
        return True
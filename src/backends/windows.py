#!/usr/bin/env python3
"""
Windows backend for .exe and .msi files via Wine/Bottles.
"""

from pathlib import Path
from typing import List
from . import BaseBackend
import shutil


class WindowsBackend(BaseBackend):
    format_type = "windows-exe"  # handles both .exe and .msi
    format_name = "Windows Application"
    extensions = [".exe", ".msi"]
    
    def can_handle(self, path: Path) -> bool:
        name = path.name.lower()
        return name.endswith(".exe") or name.endswith(".msi")
    
    def describe(self, path: Path) -> str:
        return f"Windows application: {path.name}"
    
    def get_install_command(self, path: Path) -> List[str]:
        # Prefer Bottles if available, then Wine
        if shutil.which("bottles-cli"):
            return ["bottles-cli", "run", "-b", "default", "-e", str(path)]
        elif shutil.which("wine"):
            if path.name.lower().endswith(".msi"):
                return ["wine", "msiexec", "/i", str(path)]
            return ["wine", str(path)]
        return ["wine", str(path)]
    
    def requires_root(self) -> bool:
        return False
#!/usr/bin/env python3
"""
VS Code extension backend for .vsix files.
"""

from pathlib import Path
from typing import List
from . import BaseBackend


class VSIXBackend(BaseBackend):
    format_type = "vsix"
    format_name = "VS Code Extension"
    extensions = [".vsix"]
    
    def can_handle(self, path: Path) -> bool:
        return path.name.lower().endswith(".vsix")
    
    def describe(self, path: Path) -> str:
        return f"VS Code Extension: {path.name}"
    
    def get_install_command(self, path: Path) -> List[str]:
        # Try code, then code-insiders, then codium
        for cmd in ["code", "code-insiders", "codium"]:
            if shutil.which(cmd):
                return [cmd, "--install-extension", str(path)]
        return ["code", "--install-extension", str(path)]
    
    def requires_root(self) -> bool:
        return False


import shutil
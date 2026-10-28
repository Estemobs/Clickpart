#!/usr/bin/env python3
"""
Pacman backend for .pkg.tar.zst, .pkg.tar.xz, etc.
"""

from pathlib import Path
from typing import List
from . import BaseBackend


class PacmanBackend(BaseBackend):
    format_type = "pacman"
    format_name = "Arch Linux Package"
    extensions = [".pkg.tar.zst", ".pkg.tar.xz", ".pkg.tar.gz", ".pkg.tar"]
    
    def can_handle(self, path: Path) -> bool:
        name = path.name.lower()
        return any(name.endswith(ext) for ext in self.extensions)
    
    def describe(self, path: Path) -> str:
        # Try to extract package info using pacman -Qip
        import subprocess
        try:
            result = subprocess.run(
                ["pacman", "-Qip", str(path)],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                info = {}
                for line in lines:
                    if ':' in line:
                        key, val = line.split(':', 1)
                        info[key.strip()] = val.strip()
                name = info.get('Name', path.name)
                version = info.get('Version', 'unknown')
                desc = info.get('Description', '')
                return f"{name} {version}\n{desc}"
        except Exception:
            pass
        return f"Arch package: {path.name}"
    
    def get_install_command(self, path: Path) -> List[str]:
        return ["pkexec", "pacman", "-U", "--noconfirm", str(path)]
    
    def requires_root(self) -> bool:
        return True
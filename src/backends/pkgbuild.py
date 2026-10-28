#!/usr/bin/env python3
"""
PKGBUILD backend for AUR packages (directories or archives containing PKGBUILD).
"""

import tempfile
import shutil
import tarfile
import zipfile
from pathlib import Path
from typing import List
from . import BaseBackend


class PKGBUILDBackend(BaseBackend):
    format_type = "pkgbuild"
    format_name = "Arch Build Script (PKGBUILD)"
    extensions = []  # Handled by directory detection
    
    def can_handle(self, path: Path) -> bool:
        if path.is_dir():
            return (path / "PKGBUILD").exists()
        # Check archives
        if path.suffix.lower() in ['.tar.gz', '.tar.xz', '.tar.zst', '.tar', '.zip']:
            return self._archive_contains_pkgbuild(path)
        return False
    
    def _archive_contains_pkgbuild(self, path: Path) -> bool:
        try:
            if path.suffix.lower() == '.zip':
                with zipfile.ZipFile(path, 'r') as zf:
                    return any('PKGBUILD' in n for n in zf.namelist())
            else:
                with tarfile.open(path, 'r:*') as tf:
                    return any('PKGBUILD' in m.name for m in tf.getmembers())
        except Exception:
            return False
    
    def describe(self, path: Path) -> str:
        if path.is_dir():
            pkgbuild = path / "PKGBUILD"
        else:
            # Extract to temp and read
            with tempfile.TemporaryDirectory() as tmpdir:
                tmpdir = Path(tmpdir)
                self._extract_archive(path, tmpdir)
                pkgbuild = tmpdir / "PKGBUILD"
                if not pkgbuild.exists():
                    # Look in subdirectories
                    for p in tmpdir.rglob("PKGBUILD"):
                        pkgbuild = p
                        break
        
        if pkgbuild.exists():
            content = pkgbuild.read_text()
            # Parse pkgname and pkgver
            pkgname = "unknown"
            pkgver = "unknown"
            for line in content.split('\n'):
                if line.startswith('pkgname='):
                    pkgname = line.split('=', 1)[1].strip().strip('"\'')
                elif line.startswith('pkgver='):
                    pkgver = line.split('=', 1)[1].strip().strip('"\'')
            return f"AUR package: {pkgname} {pkgver}"
        return f"PKGBUILD archive: {path.name}"
    
    def get_install_command(self, path: Path) -> List[str]:
        # This is complex - we'll handle in install method
        return ["clickpak-makepkg-install", str(path)]
    
    def requires_root(self) -> bool:
        return True  # makepkg -si needs root for install
    
    def _extract_archive(self, path: Path, dest: Path):
        if path.suffix.lower() == '.zip':
            with zipfile.ZipFile(path, 'r') as zf:
                zf.extractall(dest)
        else:
            with tarfile.open(path, 'r:*') as tf:
                tf.extractall(dest)
    
    def install(self, path: Path) -> tuple[bool, str]:
        """Build and install PKGBUILD in a temporary directory."""
        import subprocess
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            build_dir = tmpdir
            
            if path.is_dir():
                # Copy directory contents
                shutil.copytree(path, tmpdir / "src", dirs_exist_ok=True)
                build_dir = tmpdir / "src"
            else:
                # Extract archive
                self._extract_archive(path, tmpdir)
                # Find PKGBUILD directory
                for p in tmpdir.rglob("PKGBUILD"):
                    build_dir = p.parent
                    break
            
            if not (build_dir / "PKGBUILD").exists():
                return False, "PKGBUILD not found"
            
            try:
                # Run makepkg -si
                result = subprocess.run(
                    ["makepkg", "-si", "--noconfirm"],
                    cwd=build_dir,
                    capture_output=True, text=True, timeout=600
                )
                # Gestion des erreurs de dépendances (Phase 3)
                output_text = (result.stdout or "") + (result.stderr or "")
                if result.returncode != 0:
                    low = output_text.lower()
                    if "missing dependencies" in low or "unsatisfied dependencies" in low:
                        output_text += "\n\n💡 Suggestion: install missing dependencies with 'pacman -S <package>' or 'yay -S <package>' before retrying."
                    if "signature" in low and "invalid" in low:
                        output_text += "\n\n⚠️ Signature invalide — vérifiez la source du PKGBUILD."
                return result.returncode == 0, output_text
            except subprocess.TimeoutExpired:
                return False, "Build timed out"
            except Exception as e:
                return False, str(e)
#!/usr/bin/env python3
"""
Archive backend for .tar.gz, .tar.xz, .zip, etc.
Heuristic-based installation as per roadmap.
"""

import os
import shutil
import subprocess
import tarfile
import tempfile
import zipfile
from pathlib import Path
from typing import List
from . import BaseBackend


class ArchiveBackend(BaseBackend):
    format_type = "archive"
    format_name = "Archive (tar.gz, tar.xz, zip, etc.)"
    extensions = [".tar.gz", ".tar.xz", ".tar.zst", ".tar.bz2", ".tar", ".zip", ".deb", ".rpm"]
    
    def can_handle(self, path: Path) -> bool:
        name = path.name.lower()
        return any(name.endswith(ext) for ext in self.extensions)
    
    def describe(self, path: Path) -> str:
        # Try to list contents
        contents = self._list_contents(path)
        if contents:
            preview = "\n".join(contents[:10])
            if len(contents) > 10:
                preview += f"\n... and {len(contents) - 10} more files"
            return f"Archive: {path.name}\nContents:\n{preview}"
        return f"Archive: {path.name}"
    
    def get_install_command(self, path: Path) -> List[str]:
        # Heuristic-based, we'll handle in install method
        return ["clickpak-archive-install", str(path)]
    
    def requires_root(self) -> bool:
        return False
    
    def _list_contents(self, path: Path) -> List[str]:
        try:
            if path.suffix.lower() == '.zip':
                with zipfile.ZipFile(path, 'r') as zf:
                    return zf.namelist()
            else:
                with tarfile.open(path, 'r:*') as tf:
                    return [m.name for m in tf.getmembers()]
        except Exception:
            return []
    
    def _safe_target(self, dest: Path, name: str, linkname: str | None = None) -> None:
        """Reject archive members that would escape ``dest`` (path traversal)."""
        root = dest.resolve()
        target = (root / name).resolve()
        if not target.is_relative_to(root):
            raise ValueError(f"Chemin d'archive non autorisé: {name}")
        if linkname:
            link = (target.parent / linkname) if name else (root / linkname)
            if not link.resolve().is_relative_to(root):
                raise ValueError(f"Lien d'archive non autorisé: {linkname}")

    def _extract_archive(self, path: Path, dest: Path):
        dest = Path(dest)
        if path.suffix.lower() == '.zip':
            with zipfile.ZipFile(path, 'r') as zf:
                for name in zf.namelist():
                    self._safe_target(dest, name)
                zf.extractall(dest)
        else:
            with tarfile.open(path, 'r:*') as tf:
                members = []
                for member in tf.getmembers():
                    self._safe_target(dest, member.name)
                    if member.issym():
                        self._safe_target(dest, member.name, member.linkname)
                    elif member.islnk():
                        root = dest.resolve()
                        link = (root / member.linkname).resolve()
                        if not link.is_relative_to(root):
                            raise ValueError(f"Lien d'archive non autorisé: {member.linkname}")
                    if member.isdev() or member.isfifo():
                        raise ValueError(f"Type de fichier d'archive non autorisé: {member.name}")
                    members.append(member)
                kwargs = {"filter": "data"} if hasattr(tarfile, "data_filter") else {}
                tf.extractall(dest, members=members, **kwargs)
    
    def install(self, path: Path) -> tuple[bool, str]:
        """
        Heuristic installation as per roadmap:
        1. Contains PKGBUILD -> makepkg -si
        2. Contains .desktop + executable -> extract to ~/.local/opt/, create menu entry
        3. Contains install.sh/Makefile -> show content, ask for explicit confirmation
        4. Otherwise -> offer to extract only
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            self._extract_archive(path, tmpdir)
            
            # 1. Check for PKGBUILD
            for pkgbuild in tmpdir.rglob("PKGBUILD"):
                return self._install_pkgbuild(pkgbuild.parent)
            
            # 2. Check for .desktop + executable
            desktop_files = list(tmpdir.rglob("*.desktop"))
            executables = [f for f in tmpdir.rglob("*") if f.is_file() and os.access(f, os.X_OK)]
            
            if desktop_files and executables:
                return self._install_desktop_app(tmpdir, desktop_files[0], executables[0], path.stem)
            
            # 3. Check for install.sh or Makefile
            install_scripts = list(tmpdir.rglob("install.sh")) + list(tmpdir.rglob("Makefile"))
            if install_scripts:
                script_content = install_scripts[0].read_text()
                return False, f"Found install script ({install_scripts[0].name}). Content:\n{script_content[:2000]}\n\nPlease review and run manually if you trust it."
            
            # 4. Default: extract only
            extract_dir = Path.home() / "Downloads" / path.stem
            shutil.copytree(tmpdir, extract_dir, dirs_exist_ok=True)
            return True, f"Extracted to {extract_dir}"
    
    def _install_pkgbuild(self, build_dir: Path) -> tuple[bool, str]:
        try:
            result = subprocess.run(
                ["makepkg", "-si", "--noconfirm"],
                cwd=build_dir,
                capture_output=True, text=True, timeout=600
            )
            return result.returncode == 0, result.stdout + result.stderr
        except Exception as e:
            return False, str(e)
    
    def _install_desktop_app(self, src_dir: Path, desktop_file: Path, executable: Path, name: str) -> tuple[bool, str]:
        try:
            # Install to ~/.local/opt/<name>/
            opt_dir = Path.home() / ".local" / "opt" / name
            opt_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy all extracted files
            for item in src_dir.iterdir():
                if item.is_dir():
                    shutil.copytree(item, opt_dir / item.name, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, opt_dir / item.name)
            
            # Fix executable path in .desktop file
            desktop_content = desktop_file.read_text()
            lines = desktop_content.split('\n')
            new_lines = []
            for line in lines:
                if line.startswith('Exec='):
                    # Replace with the actual executable path
                    exec_path = opt_dir / executable.relative_to(src_dir)
                    new_lines.append(f'Exec={exec_path}')
                elif line.startswith('Icon=') and not line.startswith('Icon=http'):
                    # Handle relative icon paths
                    icon_name = line.split('=', 1)[1]
                    icon_path = src_dir / icon_name
                    if icon_path.exists():
                        # Copy icon to local icons
                        icon_dest = Path.home() / ".local" / "share" / "icons" / "hicolor" / "256x256" / "apps" / f"{name}.png"
                        icon_dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(icon_path, icon_dest)
                        new_lines.append(f'Icon={name}')
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
            
            desktop_content = '\n'.join(new_lines)
            
            # Write .desktop file to applications directory
            apps_dir = Path.home() / ".local" / "share" / "applications"
            apps_dir.mkdir(parents=True, exist_ok=True)
            dest_desktop = apps_dir / f"{name}.desktop"
            dest_desktop.write_text(desktop_content)
            dest_desktop.chmod(0o644)
            
            # Update desktop database
            subprocess.run(["update-desktop-database", str(apps_dir)], capture_output=True)
            
            return True, f"Installed to {opt_dir}, menu entry created"
        except Exception as e:
            return False, str(e)
#!/usr/bin/env python3
"""
Format detection for Clickpak.
Detects file type from extension, MIME type, and content inspection.
"""

import mimetypes
import magic
from pathlib import Path
from typing import Optional

# Initialize mimetypes
mimetypes.init()

# Mapping of extensions to format types
EXTENSION_MAP = {
    # Arch packages
    ".pkg.tar.zst": "pacman",
    ".pkg.tar.xz": "pacman",
    ".pkg.tar.gz": "pacman",
    ".pkg.tar": "pacman",
    
    # Flatpak
    ".flatpakref": "flatpakref",
    ".flatpak": "flatpak",
    
    # AppImage
    ".appimage": "appimage",
    
    # Snap
    ".snap": "snap",
    
    # VS Code extensions
    ".vsix": "vsix",
    
    # GNOME Shell extensions
    ".shell-extension.zip": "gnome-shell-extension",
    
    # Installers
    ".run": "run",
    ".sh": "shell-script",
    
    # Windows
    ".exe": "windows-exe",
    ".msi": "windows-msi",
    
    # Java
    ".jar": "jar",
    
    # Archives
    ".tar.gz": "tar-gz",
    ".tar.xz": "tar-xz",
    ".tar.zst": "tar-zst",
    ".tar.bz2": "tar-bz2",
    ".tar": "tar",
    ".zip": "zip",
    ".deb": "deb",
    ".rpm": "rpm",
}

# MIME type to format mapping
MIME_MAP = {
    "application/x-flatpakref": "flatpakref",
    "application/x-flatpak": "flatpak",
    "application/x-iso9660-appimage": "appimage",
    "application/vnd.snap": "snap",
    "application/vnd.visualstudio.code.extension": "vsix",
    "application/x-shellscript": "shell-script",
    "application/x-executable": "appimage",  # AppImages are often detected as executables
    "application/java-archive": "jar",
    "application/x-deb": "deb",
    "application/x-rpm": "rpm",
    "application/gzip": "tar-gz",
    "application/x-xz": "tar-xz",
    "application/zstd": "tar-zst",
    "application/x-bzip2": "tar-bz2",
    "application/x-tar": "tar",
    "application/zip": "zip",
}


class FormatDetector:
    def __init__(self):
        self.magic = magic.Magic(mime=True)
    
    def detect(self, path: Path) -> Optional[str]:
        """
        Detect the format of a file.
        Returns the format type string or None if unknown.
        """
        # First try by extension (most reliable for our use cases)
        format_type = self._detect_by_extension(path)
        if format_type:
            return format_type
        
        # Then try by MIME type
        format_type = self._detect_by_mime(path)
        if format_type:
            return format_type
        
        # For AppImages, check if it's an executable with AppImage magic
        if self._is_appimage(path):
            return "appimage"
        
        # For PKGBUILD directories
        if path.is_dir() and (path / "PKGBUILD").exists():
            return "pkgbuild"
        
        return None
    
    def _detect_by_extension(self, path: Path) -> Optional[str]:
        """Detect format by file extension."""
        # Check full suffixes first (e.g., .pkg.tar.zst)
        name = path.name.lower()
        for ext, fmt in EXTENSION_MAP.items():
            if name.endswith(ext):
                return fmt
        
        # Fall back to single extension
        suffix = path.suffix.lower()
        return EXTENSION_MAP.get(suffix)
    
    def _detect_by_mime(self, path: Path) -> Optional[str]:
        """Detect format by MIME type."""
        try:
            mime_type = self.magic.from_file(str(path))
            return MIME_MAP.get(mime_type)
        except Exception:
            return None
    
    def _is_appimage(self, path: Path) -> bool:
        """Check if file is an AppImage by reading its magic bytes."""
        try:
            if not path.is_file() or not os.access(path, os.X_OK):
                return False
            with open(path, "rb") as f:
                header = f.read(8)
                # AppImage magic: "AI\x02" or check for squashfs
                return header.startswith(b"AI\x02") or header[:4] == b"hsqs"
        except Exception:
            return False


import os
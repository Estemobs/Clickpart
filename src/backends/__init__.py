#!/usr/bin/env python3
"""
Backends package for Clickpak.
Each backend handles a specific package format.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional


class BaseBackend(ABC):
    """Base class for all installation backends."""
    
    @property
    @abstractmethod
    def format_name(self) -> str:
        """Human-readable format name."""
        pass
    
    @abstractmethod
    def can_handle(self, path: Path) -> bool:
        """Check if this backend can handle the given file."""
        pass
    
    @abstractmethod
    def describe(self, path: Path) -> str:
        """Return a human-readable description of what will be installed."""
        pass
    
    @abstractmethod
    def get_install_command(self, path: Path) -> List[str]:
        """Return the command to execute for installation."""
        pass
    
    @abstractmethod
    def requires_root(self) -> bool:
        """Whether this installation requires root privileges."""
        pass


# Import all backends
from .pacman import PacmanBackend
from .flatpak import FlatpakBackend
from .appimage import AppImageBackend
from .snap import SnapBackend
from .vsix import VSIXBackend
from .gnome_shell import GnomeShellExtensionBackend
from .run_script import RunScriptBackend
from .jar import JarBackend
from .windows import WindowsBackend
from .pkgbuild import PKGBUILDBackend
from .archive import ArchiveBackend

# Registry of available backends
BACKENDS = [
    PacmanBackend(),
    FlatpakBackend(),
    AppImageBackend(),
    SnapBackend(),
    VSIXBackend(),
    GnomeShellExtensionBackend(),
    RunScriptBackend(),
    JarBackend(),
    WindowsBackend(),
    PKGBUILDBackend(),
    ArchiveBackend(),
]


def get_backend(format_type: str) -> Optional[BaseBackend]:
    """Get backend instance for a format type."""
    for backend in BACKENDS:
        if backend.format_type == format_type:
            return backend
    return None


def get_backend_for_file(path: Path) -> Optional[BaseBackend]:
    """Find a backend that can handle the given file."""
    for backend in BACKENDS:
        if backend.can_handle(path):
            return backend
    return None
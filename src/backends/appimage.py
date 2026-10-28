#!/usr/bin/env python3
"""
AppImage backend for .AppImage files.
Extracts icon, creates .desktop file, and installs to ~/Applications.
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import List
from . import BaseBackend


class AppImageBackend(BaseBackend):
    format_type = "appimage"
    format_name = "AppImage"
    extensions = [".appimage", ".AppImage"]
    
    def can_handle(self, path: Path) -> bool:
        name = path.name.lower()
        return any(name.endswith(ext.lower()) for ext in self.extensions)
    
    def describe(self, path: Path) -> str:
        # Try to get info from AppImage
        try:
            result = subprocess.run(
                [str(path), "--appimage-help"],
                capture_output=True, text=True, timeout=5
            )
            # Just return the filename for now
        except Exception:
            pass
        return f"AppImage application: {path.name}"
    
    def get_install_command(self, path: Path) -> List[str]:
        # This is a complex operation, we'll handle it in the install method
        # Return a placeholder command for display
        return ["clickpak-appimage-install", str(path)]
    
    def requires_root(self) -> bool:
        return False
    
    def install(self, path: Path, app_dir: Path = None) -> tuple[bool, str]:
        """
        Install AppImage: make executable, copy to ~/Applications, 
        extract icon, create .desktop file.
        """
        if app_dir is None:
            app_dir = Path.home() / "Applications"
        
        app_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Make executable
            path.chmod(0o755)
            
            # Copy to Applications directory
            dest = app_dir / path.name
            shutil.copy2(path, dest)
            dest.chmod(0o755)
            
            # Extract icon and create .desktop file
            self._create_desktop_entry(dest, app_dir)
            
            # Update desktop database
            subprocess.run(["update-desktop-database", str(Path.home() / ".local" / "share" / "applications")], 
                         capture_output=True)
            
            return True, f"Installed to {dest}"
        except Exception as e:
            return False, str(e)
    
    def _create_desktop_entry(self, appimage_path: Path, app_dir: Path):
        """Extract icon and create .desktop file."""
        import tempfile
        
        desktop_dir = Path.home() / ".local" / "share" / "applications"
        desktop_dir.mkdir(parents=True, exist_ok=True)
        
        # Try to extract icon and desktop file from AppImage
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            try:
                # Try to mount and extract
                result = subprocess.run(
                    [str(appimage_path), "--appimage-extract"],
                    cwd=tmpdir, capture_output=True, timeout=30
                )
                
                # Look for .desktop file and icon
                desktop_files = list(tmpdir.rglob("*.desktop"))
                icon_files = list(tmpdir.rglob("*.png")) + list(tmpdir.rglob("*.svg")) + list(tmpdir.rglob("*.xpm"))
                
                if desktop_files:
                    desktop_content = desktop_files[0].read_text()
                    # Modify Exec line to point to our copied AppImage
                    lines = desktop_content.split('\n')
                    new_lines = []
                    for line in lines:
                        if line.startswith('Exec='):
                            new_lines.append(f'Exec={appimage_path}')
                        elif line.startswith('TryExec='):
                            new_lines.append(f'TryExec={appimage_path}')
                        else:
                            new_lines.append(line)
                    desktop_content = '\n'.join(new_lines)
                else:
                    # Create a basic .desktop file
                    name = appimage_path.stem
                    desktop_content = f"""[Desktop Entry]
Type=Application
Name={name}
Exec={appimage_path}
Icon={name}
Categories=Utility;
"""
                
                # Save .desktop file
                desktop_file = desktop_dir / f"{appimage_path.stem}.desktop"
                desktop_file.write_text(desktop_content)
                desktop_file.chmod(0o644)
                
                # Copy icon if found
                if icon_files:
                    icon_dest = Path.home() / ".local" / "share" / "icons" / "hicolor" / "256x256" / "apps"
                    icon_dest.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(icon_files[0], icon_dest / f"{appimage_path.stem}.png")
                    
            except Exception:
                # Fallback: create basic desktop entry
                name = appimage_path.stem
                desktop_content = f"""[Desktop Entry]
Type=Application
Name={name}
Exec={appimage_path}
Icon=application-x-executable
Categories=Utility;
"""
                desktop_file = desktop_dir / f"{appimage_path.stem}.desktop"
                desktop_file.write_text(desktop_content)
                desktop_file.chmod(0o644)
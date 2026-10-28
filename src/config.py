#!/usr/bin/env python3
"""
Configuration management for Clickpak.
Uses TOML for config file.
"""

import os
import tomli
import tomli_w
from pathlib import Path
from typing import Dict, Any, Optional


DEFAULT_CONFIG = {
    "general": {
        "app_dir": str(Path.home() / "Applications"),
        "silent_formats": ["flatpakref", "flatpak", "appimage"],
        "confirm_by_default": True,
        "show_notifications": True,
    },
    "formats": {
        "pacman": {"enabled": True, "silent": False},
        "flatpakref": {"enabled": True, "silent": True},
        "flatpak": {"enabled": True, "silent": True},
        "appimage": {"enabled": True, "silent": True},
        "snap": {"enabled": True, "silent": False},
        "vsix": {"enabled": True, "silent": True},
        "gnome-shell-extension": {"enabled": True, "silent": True},
        "run": {"enabled": True, "silent": False},
        "shell-script": {"enabled": True, "silent": False},
        "windows-exe": {"enabled": True, "silent": False},
        "windows-msi": {"enabled": True, "silent": False},
        "jar": {"enabled": True, "silent": True},
        "pkgbuild": {"enabled": True, "silent": False},
        "archive": {"enabled": True, "silent": False},
    },
    "advanced": {
        "polkit_action": "org.clickpak.install",
        "log_retention_days": 30,
        "max_log_size_mb": 10,
    }
}


class Config:
    def __init__(self):
        self.config_dir = Path.home() / ".config" / "clickpak"
        self.config_file = self.config_dir / "config.toml"
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load config from file, merging with defaults."""
        config = DEFAULT_CONFIG.copy()
        
        if self.config_file.exists():
            try:
                with open(self.config_file, "rb") as f:
                    user_config = tomli.load(f)
                # Deep merge
                self._deep_merge(config, user_config)
            except Exception as e:
                print(f"Warning: Failed to load config: {e}")
        
        return config
    
    def _deep_merge(self, base: dict, override: dict):
        """Recursively merge override into base."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def save(self):
        """Save config to file."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "wb") as f:
            tomli_w.dump(self.config, f)
    
    def is_enabled(self, format_type: str) -> bool:
        """Check if a format is enabled."""
        return self.config.get("formats", {}).get(format_type, {}).get("enabled", True)
    
    def is_silent(self, format_type: str) -> bool:
        """Check if silent mode is enabled for a format."""
        return self.config.get("formats", {}).get(format_type, {}).get("silent", False)
    
    def set_silent(self, format_type: str, silent: bool):
        """Set silent mode for a format."""
        if "formats" not in self.config:
            self.config["formats"] = {}
        if format_type not in self.config["formats"]:
            self.config["formats"][format_type] = {}
        self.config["formats"][format_type]["silent"] = silent
        self.save()
    
    def set_enabled(self, format_type: str, enabled: bool):
        """Enable/disable a format."""
        if "formats" not in self.config:
            self.config["formats"] = {}
        if format_type not in self.config["formats"]:
            self.config["formats"][format_type] = {}
        self.config["formats"][format_type]["enabled"] = enabled
        self.save()
    
    def get_app_dir(self) -> Path:
        """Get the AppImage applications directory."""
        return Path(self.config.get("general", {}).get("app_dir", str(Path.home() / "Applications")))
    
    def get_all_formats(self) -> Dict[str, Dict[str, Any]]:
        """Get all format configurations."""
        return self.config.get("formats", {})
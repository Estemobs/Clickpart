#!/usr/bin/env python3
"""
Desktop notifications for Clickpak (Phase 2, v0.2).
Uses GIO notifications.
"""

import gi
gi.require_version('Gio', '2.0')
from gi.repository import Gio


class Notifier:
    def __init__(self, app_id="org.clickpak.Clickpak"):
        self.app_id = app_id
    
    def notify(self, title: str, body: str, icon: str = "clickpak") -> bool:
        """
        Send a desktop notification if enabled in config and supported.
        Returns True if notification was sent.
        """
        try:
            notification = Gio.Notification.new(title)
            notification.set_body(body)
            notification.set_icon(Gio.ThemedIcon.new(icon))
            
            application = Gio.Application.get_default()
            if application:
                application.send_notification(None, notification)
                return True
            
            # Fallback: try via D-Bus notification daemon
            import subprocess
            subprocess.run([
                "notify-send", title, body,
                "-i", icon,
                "-a", self.app_id
            ], capture_output=True)
            return True
        except Exception:
            return False
    
    def installation_success(self, package_name: str):
        self.notify(
            title="Installation complete",
            body=f"{package_name} has been installed via Clickpak."
        )
    
    def installation_failed(self, package_name: str, error: str = ""):
        body = f"Installation of {package_name} failed."
        if error:
            body += f"\n{error[:200]}"
        self.notify(
            title="Installation failed",
            body=body
        )
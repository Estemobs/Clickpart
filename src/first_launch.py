#!/usr/bin/env python3
"""
First-launch assistant for Clickpak (Phase 2).
Asks user to register Clickpak as default handler for supported formats.
"""

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Gio
from pathlib import Path
import subprocess


class FirstLaunchAssistant:
    def __init__(self, config):
        self.config = config
        self.completed = False
    
    def run(self) -> bool:
        """Show assistant and return True if user completed it."""
        # Check if already completed
        marker = Path.home() / ".local" / "state" / "clickpak" / ".first_launch_done"
        if marker.exists():
            return False  # Already done, don't show
        
        # Show simple GTK dialog
        app = Gtk.Application.new("org.clickpak.FirstLaunch", GLib.ApplicationFlags.FLAGS_NONE)
        app.connect("activate", self._on_activate)
        app.run([])
        
        if self.completed:
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text("done\n")
        
        return self.completed
    
    def _on_activate(self, app):
        window = Gtk.Window(title="Welcome to Clickpak", application=app)
        window.set_default_size(500, 300)
        
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.set_margin_top(24)
        content.set_margin_bottom(24)
        content.set_margin_start(24)
        content.set_margin_end(24)
        
        title = Gtk.Label(label="Welcome to Clickpak")
        title.add_css_class("title-2")
        content.append(title)
        
        desc = Gtk.Label(label="Clickpak can be your default app for package files.\nWould you like to register it now?")
        desc.set_wrap(True)
        content.append(desc)
        
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        btn_box.set_halign(Gtk.Align.CENTER)
        
        yes_btn = Gtk.Button(label="Yes, set as default")
        yes_btn.add_css_class("suggested-action")
        yes_btn.connect("clicked", lambda _: self._register_defaults(window))
        btn_box.append(yes_btn)
        
        no_btn = Gtk.Button(label="Skip")
        no_btn.connect("clicked", lambda _: self._skip(window))
        btn_box.append(no_btn)
        
        content.append(btn_box)
        
        window.set_child(content)
        window.present()
    
    def _register_defaults(self, window):
        # Run xdg-mime for supported MIME types
        desktop_file = Path(__file__).parent.parent.parent / "data" / "clickpak.desktop"
        if desktop_file.exists():
            subprocess.run(["xdg-mime", "default", "clickpak.desktop"] + [
                "application/x-flatpakref", "application/x-flatpak",
                "application/x-iso9660-appimage", "application/vnd.snap"
            ], capture_output=True)
        
        self.completed = True
        window.close()
    
    def _skip(self, window):
        self.completed = False
        window.close()
#!/usr/bin/env python3
"""
Confirmation dialog for Clickpak.
Shows package info, command to be run, and Install/Cancel buttons.
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib
from typing import List, Optional


class ConfirmDialog:
    def __init__(
        self,
        file_path: str,
        format_type: str,
        description: str,
        command: List[str],
        requires_root: bool
    ):
        self.file_path = file_path
        self.format_type = format_type
        self.description = description
        self.command = command
        self.requires_root = requires_root
        self.response = None
        self.window = None
    
    def run(self) -> str:
        """Run the dialog and return 'install' or 'cancel'."""
        # Create application
        app = Adw.Application.new("org.clickpak.Confirm", GLib.ApplicationFlags.FLAGS_NONE)
        app.connect("activate", self._on_activate)
        app.run([])
        return self.response or "cancel"
    
    def _on_activate(self, app):
        self.window = Adw.Window(title="Confirm Installation", application=app)
        self.window.set_default_size(500, 400)
        self.window.set_resizable(False)
        
        # Main content
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.set_margin_top(24)
        content.set_margin_bottom(24)
        content.set_margin_start(24)
        content.set_margin_end(24)
        
        # Header
        header = Adw.HeaderBar()
        header.set_title_widget(Gtk.Label(label="Confirm Installation"))
        content.append(header)
        
        # File info
        file_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        file_box.add_css_class("card")
        
        file_name = Gtk.Label(label=self.file_path.split('/')[-1])
        file_name.add_css_class("title-2")
        file_name.set_halign(Gtk.Align.START)
        file_name.set_max_width_chars(50)
        file_name.set_ellipsize(3)  # PANGO_ELLIPSIZE_END
        file_box.append(file_name)
        
        format_label = Gtk.Label(label=f"Format: {self.format_type}")
        format_label.set_halign(Gtk.Align.START)
        format_label.add_css_class("dim-label")
        file_box.append(format_label)
        
        content.append(file_box)
        
        # Description
        desc_frame = Gtk.Frame()
        desc_frame.set_label("Description")
        desc_label = Gtk.Label(label=self.description)
        desc_label.set_wrap(True)
        desc_label.set_max_width_chars(60)
        desc_label.set_halign(Gtk.Align.START)
        desc_label.set_valign(Gtk.Align.START)
        desc_label.set_margin_top(12)
        desc_label.set_margin_bottom(12)
        desc_label.set_margin_start(12)
        desc_label.set_margin_end(12)
        desc_frame.set_child(desc_label)
        content.append(desc_frame)
        
        # Command to run
        cmd_frame = Gtk.Frame()
        cmd_frame.set_label("Command to execute")
        cmd_text = " ".join(self.command)
        cmd_label = Gtk.Label(label=cmd_text)
        cmd_label.set_wrap(True)
        cmd_label.set_max_width_chars(60)
        cmd_label.set_halign(Gtk.Align.START)
        cmd_label.add_css_class("monospace")
        cmd_label.set_margin_top(12)
        cmd_label.set_margin_bottom(12)
        cmd_label.set_margin_start(12)
        cmd_label.set_margin_end(12)
        cmd_frame.set_child(cmd_label)
        content.append(cmd_frame)
        
        # Root warning
        if self.requires_root:
            warning = Adw.Banner()
            warning.set_title("Administrator privileges required")
            warning.set_revealed(True)
            warning.add_css_class("warning")
            content.append(warning)
        
        # Buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_margin_top(12)
        
        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.connect("clicked", lambda _: self._respond("cancel"))
        button_box.append(cancel_btn)
        
        install_btn = Gtk.Button(label="Install")
        install_btn.add_css_class("suggested-action")
        install_btn.connect("clicked", lambda _: self._respond("install"))
        button_box.append(install_btn)
        
        content.append(button_box)
        
        self.window.set_content(content)
        self.window.present()
    
    def _respond(self, response: str):
        self.response = response
        if self.window:
            self.window.close()
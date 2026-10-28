#!/usr/bin/env python3
"""
Progress dialog for Clickpak installation.
Shows real-time output and handles cancellation.
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio
from typing import List, Tuple
import subprocess
import threading


class ProgressDialog:
    def __init__(
        self,
        title: str,
        command: List[str],
        requires_root: bool
    ):
        self.title = title
        self.command = command
        self.requires_root = requires_root
        self.success = False
        self.output = ""
        self.window = None
        self.process = None
        self.cancelled = False
    
    def run(self) -> Tuple[bool, str]:
        """Run the installation and return (success, output)."""
        app = Adw.Application.new("org.clickpak.Progress", GLib.ApplicationFlags.FLAGS_NONE)
        app.connect("activate", self._on_activate)
        app.run([])
        return self.success, self.output
    
    def _on_activate(self, app):
        self.window = Adw.Window(title=self.title, application=app)
        self.window.set_default_size(600, 400)
        self.window.set_resizable(True)
        self.window.connect("close-request", self._on_close_request)
        
        # Main content
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Header bar
        header = Adw.HeaderBar()
        header.set_title_widget(Gtk.Label(label=self.title))
        content.append(header)
        
        # Terminal-like output
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        self.text_view = Gtk.TextView()
        self.text_view.set_editable(False)
        self.text_view.set_monospace(True)
        self.text_view.set_left_margin(12)
        self.text_view.set_right_margin(12)
        self.text_view.set_top_margin(12)
        self.text_view.set_bottom_margin(12)
        self.text_view.add_css_class("monospace")
        
        # Set up text buffer with tags for coloring
        self.buffer = self.text_view.get_buffer()
        self.tag_stdout = self.buffer.create_tag("stdout", foreground="#cccccc")
        self.tag_stderr = self.buffer.create_tag("stderr", foreground="#ff6b6b")
        self.tag_info = self.buffer.create_tag("info", foreground="#4ec9b0")
        self.tag_success = self.buffer.create_tag("success", foreground="#4ec9b0", weight=700)
        self.tag_error = self.buffer.create_tag("error", foreground="#ff6b6b", weight=700)
        
        scrolled.set_child(self.text_view)
        content.append(scrolled)
        
        # Cancel button
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_margin_top(12)
        button_box.set_margin_bottom(12)
        button_box.set_margin_start(12)
        button_box.set_margin_end(12)
        
        self.cancel_btn = Gtk.Button(label="Cancel")
        self.cancel_btn.connect("clicked", self._on_cancel)
        button_box.append(self.cancel_btn)
        
        self.close_btn = Gtk.Button(label="Close")
        self.close_btn.add_css_class("suggested-action")
        self.close_btn.set_visible(False)
        self.close_btn.connect("clicked", lambda _: self.window.close())
        button_box.append(self.close_btn)
        
        content.append(button_box)
        
        self.window.set_content(content)
        self.window.present()
        
        # Start installation
        self._append_text(f"$ {' '.join(self.command)}\n", "info")
        self._start_installation()
    
    def _on_close_request(self, window):
        if self.process and self.process.poll() is None:
            # Process still running, ask to cancel
            self._on_cancel(None)
            return True  # Prevent closing
        return False
    
    def _on_cancel(self, button):
        if self.process and self.process.poll() is None:
            self.cancelled = True
            self.process.terminate()
            self._append_text("\n[Installation cancelled by user]\n", "error")
            self._finish_ui(success=False)
    
    def _start_installation(self):
        """Start the installation in a background thread."""
        thread = threading.Thread(target=self._run_installation, daemon=True)
        thread.start()
    
    def _run_installation(self):
        try:
            # Prepare command - handle pkexec for root
            cmd = self.command.copy()
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
            )
            
            # Read output line by line
            while True:
                if self.cancelled:
                    break
                
                stdout_line = self.process.stdout.readline()
                stderr_line = self.process.stderr.readline()
                
                if stdout_line == '' and stderr_line == '' and self.process.poll() is not None:
                    break
                
                if stdout_line:
                    GLib.idle_add(self._append_text, stdout_line, "stdout")
                if stderr_line:
                    GLib.idle_add(self._append_text, stderr_line, "stderr")
            
            returncode = self.process.wait()
            self.success = (returncode == 0)
            
            if self.success:
                GLib.idle_add(self._append_text, "\n[Installation completed successfully]\n", "success")
            else:
                GLib.idle_add(self._append_text, f"\n[Installation failed with exit code {returncode}]\n", "error")
            
        except Exception as e:
            self.success = False
            GLib.idle_add(self._append_text, f"\n[Error: {e}]\n", "error")
        
        GLib.idle_add(self._finish_ui, self.success)
    
    def _append_text(self, text: str, tag: str = None):
        """Append text to the text view."""
        end_iter = self.buffer.get_end_iter()
        if tag:
            self.buffer.insert_with_tags(end_iter, text, getattr(self, f"tag_{tag}"))
        else:
            self.buffer.insert(end_iter, text)
        
        # Auto-scroll to bottom
        mark = self.buffer.create_mark(None, self.buffer.get_end_iter(), True)
        self.text_view.scroll_mark_onscreen(mark)
        return False  # Remove idle handler
    
    def _finish_ui(self, success: bool):
        """Update UI when installation finishes."""
        self.cancel_btn.set_visible(False)
        self.close_btn.set_visible(True)
        self.close_btn.grab_focus()
        return False


def run_command_with_progress(title: str, command: List[str], requires_root: bool = False) -> Tuple[bool, str]:
    """Convenience function to run a command with progress dialog."""
    dialog = ProgressDialog(title, command, requires_root)
    return dialog.run()
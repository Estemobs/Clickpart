#!/usr/bin/env python3
"""
History view — Phase 4 v0.4.
Visualise les installations passées depuis history.log.
"""

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
from pathlib import Path


class HistoryWindow:
    def __init__(self):
        self.window = None
        self.history_file = Path.home() / ".local" / "state" / "clickpak" / "history.log"
    
    def open(self):
        app = Gtk.Application.new("org.clickpak.History", GLib.ApplicationFlags.FLAGS_NONE)
        app.connect("activate", self._on_activate)
        app.run([])
    
    def _on_activate(self, app):
        self.window = Gtk.Window(title="Clickpak — Historique", application=app)
        self.window.set_default_size(700, 500)
        
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.set_margin_top(12)
        content.set_margin_bottom(12)
        content.set_margin_start(12)
        content.set_margin_end(12)
        
        header = Gtk.Label(label="Installations passées")
        header.add_css_class("title-2")
        content.append(header)
        
        # ListBox with rows
        listbox = Gtk.ListBox()
        listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        listbox.set_vexpand(True)
        
        if self.history_file.exists():
            lines = self.history_file.read_text().strip().split("\n")
            for line in lines[-50:]:  # Dernières 50 lignes
                if not line.strip():
                    continue
                row = Gtk.ListBoxRow()
                lbl = Gtk.Label(label=line[:200])
                lbl.set_wrap(True)
                lbl.set_xalign(0)
                lbl.set_margin_top(4)
                lbl.set_margin_bottom(4)
                lbl.set_margin_start(8)
                lbl.set_margin_end(8)
                row.set_child(lbl)
                listbox.append(row)
        else:
            lbl = Gtk.Label(label="Aucune installation enregistrée.")
            lbl.set_margin_top(20)
            listbox.append(Gtk.ListBoxRow(child=lbl))
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_child(listbox)
        content.append(scrolled)
        
        self.window.set_child(content)
        self.window.present()
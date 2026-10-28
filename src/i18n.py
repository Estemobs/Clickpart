#!/usr/bin/env python3
"""
Internationalisation (i18n) pour Clickpak — Phase 3 v0.3.
Utilise gettext avec .po/.mo pour anglais (par défaut) et français.
"""

import os
import gettext
from pathlib import Path

def setup_gettext(lang_code: str = "fr"):
    """Configure gettext selon la langue choisie."""
    locale_dir = Path(__file__).parent.parent / "locales"
    # Fallback vers le répertoire parent si non trouvé
    if not locale_dir.exists():
        locale_dir = Path.home() / ".local" / "share" / "locale"
    
    # Pour le moment, on utilise la translation en ligne (dummy) 
    # La vraie installation mettre dans /usr/share/locale
    gettext.install(
        "clickpak",
        localedir=str(locale_dir) if locale_dir.exists() else None,
        names=["gettext", "ngettext"]
    )
    
    # Force la locale si demandée
    if lang_code:
        try:
            import locale
            locale.setlocale(locale.LC_ALL, f"{lang_code}.UTF-8")
        except locale.Error:
            pass

# Alias rapide
_ = gettext.gettext
n_ = gettext.ngettext
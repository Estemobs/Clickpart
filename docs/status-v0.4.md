# Clickpart — État des lieux v0.4 / v0.5

- Version : v0.4 (commit `0c8f726`) → v0.5 (commit `1f8239a`)
- Structure : src/ (main, detect, backends, ui), tests/, data/, packaging/arch/

## v0.4 — Fait
- Detection + GUI GTK4, polkit durci, `.run` alertes, historique UI
- Desktop integration (`Exec=` absolu vérifié)
- AUR PKGBUILD (`pkgver=0.4.0` base)
- `docs/status-v0.4.md` créé

## v0.5 — Fait / Partiel (BASE `1f8239a`)
- [x] Unit tests `detect.py` (`tests/test_detect.py`) — PASS (`detect_file` interface, `.flatpakref`, `.pkg.tar.zst`)
- [x] `src/detect.py` — `detect_file()` wrapper; import `os` corrigé
- [~] AppImage réel — téléchargé (`obsolete-appimagetool-AppImage`), backend install OK, `.desktop` `Exec=` absolu; `main.py` bloqué par `Adw` manquant (environnement Debian, non régressif)
- [~] PKGBUILD local — `pkgver=0.5.0`, tarball local, install manuel `/tmp/clickpart-install` OK; `makepkg` impossible (pas d'Arch)
- [x] Docs / changelog — `CHANGELOG.md`, `TODO.md`, `docs/status-v0.4.md` mis à jour
- [x] Task 4 (ce document) — commit + rapport

## Ouvert / Suivant
- Rotation `history.log` (v0.2 retardé → v0.6)
- Test `flatpak` sans `flatpak` installé (fallback propre)
- `update-desktop-database` sur cible Arch
- End-to-end GUI validation (`libadwaita` `/ Adw` installé)
- `hello-world.AppImage` URL documentée si asset plus simple requis

## Review src/ (v0.5)
- Backends modulaires, logique propre
- `detect_file()` interface fixée pour tests
- Besoin : tests sur backends (AppImage, flatpak, pkg.tar.zst)
- Besoin : `__init__.py` au package root si wrapper module `python3 -m clickpart.main`

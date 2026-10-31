# Clickpart — TODO / Notes de la semaine 1

Conservé comme matière pour la doc, selon §13 de la feuille de route.

## Ce qui a marché immédiatement (v0.5)
- `python3 src/main.py --version` répond (v0.1)
- Détection `.pkg.tar.zst` via extension + MIME (v0.1-v0.3)
- `gtk4` disponible, `libadwaita` présent (v0.1)
- `python-magic` s'est installé sans problème (v0.1/v0.5)
- `tests/test_detect.py` PASS (`detect_file` interface) — TASK 1 DONE (1f8239a)
- `.AppImage` réel téléchargé + backend install OK — TASK 2 PARTIAL (Adw import manque, `Exec=` absolu vérifié)
- PKGBUILD local `pkgver=0.5.0` modifié + install manuel vérifié — TASK 3 PARTIAL (Debian, pas d'Arch `makepkg`)

## Surprise / difficulté
- `python-magic` n'était pas installé par défaut (libmagic oui, mais pas le binding Python)
- `tomli` / `tomli_w` idem — besoin d'installer pour la config TOML
- AppImage extraction (`--appimage-extract`) peut être lent (timeout nécessaire)
- Le `.desktop` généré doit utiliser `Exec=` absolu, pas relatif
- `pkexec` ne marche pas dans un conteneur sans `polkit` configuré — OK pour la machine cible

## Prochaine étape immédiate (post-v0.5)
- Tester sur un vrai `.AppImage` (fait partiellement — `obsolete-appimagetool` téléchargé, `hello-world` indisponible)
- Vérifier que `update-desktop-database` fonctionne après création du `.desktop` (documenté, non installé dans env)
- Écrire le premier test unitaire sur `detect.py` (FAIT — `tests/test_detect.py` PASS)
- Préparer le `PKGBUILD` pour l'installation locale (`makepkg -si` PARTIEL — Debian, pas d'Arch)

## Questions ouvertes
- Faut-il un `systemd`/`upstart` pour le lancement au démarrage ? Non, le principe est sans démon. (inchangé)
- Comment gérer le cas où `flatpak` n'est pas installé ? Le backend doit échouer proprement. (documenté, non testé en v0.5)
- Quelle taille de `history.log` avant rotation ? Actuellement pas de rotation (à ajouter v0.2 / v0.6).
- `Adw`/`libadwaita` manquante sur Debian / conteneur — bloque la validation end-to-end du GUI (non régressif).

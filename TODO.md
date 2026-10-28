# Clickpak — TODO / Notes de la semaine 1

Conservé comme matière pour la doc, selon §13 de la feuille de route.

## Ce qui a marché immédiatement
- `python3 src/main.py --version` répond
- Détection `.pkg.tar.zst` via extension + MIME
- `gtk4` disponible, `libadwaita` présent
- `python-magic` s'est installé sans problème

## Surprise / difficulté
- `python-magic` n'était pas installé par défaut (libmagic oui, mais pas le binding Python)
- `tomli` / `tomli_w` idem — besoin d'installer pour la config TOML
- AppImage extraction (`--appimage-extract`) peut être lent (timeout nécessaire)
- Le `.desktop` généré doit utiliser `Exec=` absolu, pas relatif
- `pkexec` ne marche pas dans un conteneur sans `polkit` configuré — OK pour la machine cible

## Prochaine étape immédiate
- Tester sur un vrai `.AppImage` (télécharger un minimal, ex. `hello-world.AppImage`)
- Vérifier que `update-desktop-database` fonctionne après création du `.desktop`
- Écrire le premier test unitaire sur `detect.py` (fichier `.flatpakref` factice)
- Préparer le `PKGBUILD` pour l'installation locale (`makepkg -si`)

## Questions ouvertes
- Faut-il un `systemd`/`upstart` pour le lancement au démarrage ? Non, le principe est sans démon.
- Comment gérer le cas où `flatpak` n'est pas installé ? Le backend doit échouer proprement.
- Quelle taille de `history.log` avant rotation ? Actuellement pas de rotation (à ajouter v0.2).

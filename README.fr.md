# Clickpart

**Installeur graphique universel pour Linux : double-cliquez sur .flatpakref, .AppImage, .pkg.tar.zst et plus pour les installer.**

[![License: GPL-3.0](https://img.shields.io/badge/License-GPL%203.0-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![GTK4](https://img.shields.io/badge/GTK-4-green.svg)](https://gtk.org/)

Clickpart est une surcouche graphique légère autour des commandes d'installation natives de Linux. Il s'enregistre comme gestionnaire par défaut pour les types de fichiers de paquet, vous permettant d'installer n'importe quel fichier supporté par simple double-clic — sans terminal.

## Fonctionnalités

- **Zéro configuration** : Fonctionne immédiatement sur Arch, EndeavourOS, Manjaro et autres distributions
- **Support multi-format** : Gère 10+ formats de paquets (voir tableau ci-dessous)
- **Transparent** : Affiche la commande exacte qui sera exécutée avant de la lancer
- **Sûr par défaut** : Demande confirmation pour chaque installation
- **Léger** : Un script Python + GTK4, pas d'Electron, pas de démon
- **Intégration native** : Utilise `polkit` pour l'élévation de privilèges, associations `.desktop`/MIME standard

## Formats Supportés

| Format | Commande | Root Requis | Depuis |
|--------|----------|-------------|--------|
| `.pkg.tar.zst` / `.pkg.tar.xz` | `pacman -U` | Oui (polkit) | v0.1 |
| `.flatpakref` / `.flatpak` | `flatpak install` | Non (utilisateur) | v0.1 |
| `.AppImage` | Copie dans `~/Applications`, crée `.desktop` et icône | Non | v0.1 |
| `.snap` | `snap install --dangerous` | Oui | v0.3 |
| `.vsix` | `code --install-extension` | Non | v0.4 |
| `.shell-extension.zip` | `gnome-extensions install` | Non | v0.4 |
| `.run` / `.sh` | Exécution avec avertissement | Variable | v0.4 |
| `.exe` / `.msi` | Via Wine ou Bottles | Non | v0.5 |
| `.jar` | `java -jar` | Non | v0.5 |
| `PKGBUILD` (dossier/archive) | `makepkg -si` | Oui | v0.3 |
| `.tar.gz` / `.zip` / etc. | Heuristique (voir docs) | Non | v0.6 |

## Installation

### Arch Linux / EndeavourOS / Manjaro (AUR)

```bash
# Version stable
yay -S clickpart

# Version git
yay -S clickpart-git
```

### Depuis les Sources

```bash
git clone https://github.com/clickpart/clickpart
cd clickpart
pip install -r requirements.txt  # ou utilisez les paquets de votre distribution
python3 src/main.py --help
```

### Dépendances

- Python 3.10+
- GTK4 + libadwaita
- python-gobject
- python-magic (libmagic)
- flatpak, pacman, polkit (pour les backends respectifs)

## Utilisation

Double-cliquez simplement sur n'importe quel fichier supporté dans votre gestionnaire de fichiers, ou lancez depuis le terminal :

```bash
clickpart paquet.pkg.tar.zst
clickpart app.flatpakref
clickpart application.AppImage
```

### Configuration

Au premier lancement, Clickpart propose de devenir le gestionnaire par défaut pour les types de fichiers supportés.

Les réglages sont stockés dans `~/.config/clickpart/config.toml` :

```toml
[general]
app_dir = "~/Applications"
silent_formats = ["flatpakref", "flatpak", "appimage"]
confirm_by_default = true

[formats]
pacman = { enabled = true, silent = false }
flatpakref = { enabled = true, silent = true }
appimage = { enabled = true, silent = true }
# ... etc
```

## Sécurité

Clickpart suit les meilleures pratiques de sécurité :

- **Confirmation par défaut** — vous voyez toujours ce qui va s'exécuter
- **Pas d'interpolation shell** — commandes passées comme listes d'arguments, prévenant l'injection
- **Intégration Polkit** — boîte de dialogue d'authentification standard, pas de `sudo` dans la GUI
- **Journal d'audit complet** — chaque installation loguée dans `~/.local/state/clickpart/history.log`
- **Avertissements pour formats risqués** — `.run`, `.sh`, `.exe` affichent des alertes visibles

## Pourquoi Pas Flatpak ?

Clickpart **ne peut pas être distribué en Flatpak** car la sandbox l'empêcherait d'appeler les gestionnaires de paquets système (`pacman`, `snap`, etc.) ou d'écrire dans les répertoires hôtes comme `/usr` ou `~/Applications`. C'est une contrainte architecturale fondamentale — Clickpart doit s'exécuter sur l'hôte.

## Contribuer

1. Forkez le dépôt
2. Créez une branche de fonctionnalité
3. Ajoutez un backend dans `src/backends/` (voir `BASE_BACKEND.md`)
4. Soumettez une PR

Voir [CONTRIBUTING.md](CONTRIBUTING.md) pour les détails.

## Licence

GPL-3.0-or-later — voir [LICENSE](LICENSE) pour les détails.

## Remerciements

Inspiré par [Bauh](https://github.com/vinifmor/bauh), [Gear Lever](https://github.com/mjakeman/gear-lever), [AppImageLauncher](https://github.com/TheAssassin/AppImageLauncher), et la philosophie Unix : *faire une chose et la faire bien*.
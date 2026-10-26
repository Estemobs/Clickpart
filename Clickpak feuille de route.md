# Clickpak : feuille de route

*Un installeur graphique universel pour Linux : tu double-cliques, ça s'installe.*

## 1. Vision

Clickpak est un petit gestionnaire d'ouverture de fichiers pour Linux. Il s'enregistre comme application par défaut pour les formats d'installation (`.flatpakref`, `.AppImage`, `.pkg.tar.zst`, etc.). Quand tu double-cliques sur un fichier, il détecte le format, affiche (ou non) une fenêtre de confirmation, puis exécute **exactement la commande que tu taperais dans un terminal**. Il ne réinvente aucun gestionnaire de paquets : c'est une surcouche graphique fine.

**Principes directeurs**

- **Pas de magie** : chaque action = une commande standard, visible dans un journal.
- **Léger** : un binaire, pas de démon permanent, pas d'Electron.
- **Natif** : paquet Arch/AUR d'abord, pas de dépendance à un runtime lourd.
- **Sûr par défaut** : confirmation demandée, élévation de droits via polkit.
- **Modulaire** : un format = un *backend* ajoutable facilement.

## 2. Nom et référencement GitHub

**Nom retenu : Clickpak** (*click* + *pak*, comme *package*). Court, prononçable, évoque le double-clic.

**Alternatives** si le nom est pris : `Instapak`, `Unipak`, `Dblinstall`. Avant de te lancer, vérifie : le nom du dépôt sur GitHub, le nom du paquet sur l'AUR, et une recherche web rapide pour éviter les confusions.

**Nom du dépôt** : `clickpak`

**Description GitHub (une ligne, riche en mots-clés)** :

> Universal graphical installer for Linux: double-click .flatpakref, .AppImage, .pkg.tar.zst and more to install them. Lightweight GUI wrapper around native install commands.

**Topics GitHub à ajouter** : `linux`, `package-installer`, `installer`, `flatpak`, `appimage`, `arch-linux`, `pacman`, `aur`, `gtk4`, `polkit`, `xdg-mime`, `desktop-integration`, `file-association`.

**Bonnes pratiques de référencement**

- README en anglais en premier (avec une version française `README.fr.md`), titre et premier paragraphe contenant « Linux », « installer », « double-click ».
- Captures d'écran et un GIF de démonstration en haut du README.
- Tags de version propres (`v0.1.0`…) et *Releases* GitHub avec notes.
- Licence claire (voir plus bas), `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`.
- Un site de doc minimal (GitHub Pages) plus tard.

## 3. Périmètre

**Dans le périmètre**

- Détecter le type d'un fichier (extension **et** type MIME / contenu).
- Proposer une interface de confirmation (ou installation silencieuse si l'utilisateur le choisit).
- Lancer la commande d'installation appropriée et afficher la progression et les erreurs.
- Une fenêtre de configuration : formats pris en charge, comportement par défaut, association de fichiers.
- Intégration au menu pour les formats portables (AppImage).

**Hors périmètre (au moins pour la v1)**

- Remplacer pacman, Flatpak ou un store graphique.
- Gérer les mises à jour ou la désinstallation de façon complète (une vue « installé via Clickpak » viendra plus tard).
- Résoudre les dépendances à la place du gestionnaire de paquets.
- Garantir que n'importe quel `.tar.gz` s'installe (heuristique en best effort).

## 4. Formats pris en charge

| Format | Commande exécutée | Droits root | Phase |
| --- | --- | --- | --- |
| `.pkg.tar.zst` / `.pkg.tar.xz` | `pacman -U <fichier>` | oui (polkit) | v0.1 |
| `.flatpakref` / `.flatpak` | `flatpak install <fichier>` | non (utilisateur) | v0.1 |
| `.AppImage` | `chmod +x`, copie dans `~/Applications`, création du `.desktop` et de l'icône | non | v0.1 |
| `PKGBUILD` (dossier ou archive AUR) | `makepkg -si` (dans un dossier temporaire) | partiel (installation) | v0.3 |
| `.snap` | `snap install --dangerous <fichier>` | oui | v0.3 |
| `.vsix` | `code --install-extension <fichier>` | non | v0.4 |
| Extension GNOME Shell (`.zip`) | `gnome-extensions install <fichier>` | non | v0.4 |
| `.run` / `.sh` (installeurs autonomes) | `chmod +x` puis exécution, avec avertissement fort | variable | v0.4 |
| `.exe` / `.msi` | ouverture via Wine ou Bottles | non | v0.5 |
| `.jar` | `java -jar <fichier>` | non | v0.5 |
| `.tar.gz` / `.tar.xz` | heuristique (voir §7) | non | v0.6 |
| `.deb` / `.rpm` | via `debtap` (conversion), **désactivé par défaut** | oui | v1.x (optionnel) |

## 5. Architecture

### 5.1 Choix techniques

| Choix | Recommandation | Pourquoi |
| --- | --- | --- |
| Langage | **Rust** (cible), ou **Python** pour un prototype rapide | Rust : binaire léger, sûr. Python : itération rapide pour valider l'idée. |
| Interface | **GTK4 + libadwaita** (via `gtk4-rs`) ; Qt en option plus tard | Rendu moderne, intégré à GNOME ; fonctionne correctement ailleurs. |
| Élévation de droits | **polkit** (`pkexec`) | Fenêtre de mot de passe standard, pas de `sudo` dans une GUI. |
| Association de fichiers | Fichier `.desktop` avec `MimeType=` + `xdg-mime default` | Mécanisme standard freedesktop. |
| Config | Fichier TOML dans `~/.config/clickpak/config.toml` | Lisible, éditable à la main. |
| Journal | `~/.local/state/clickpak/history.log` | Traçabilité de chaque installation. |

**Conseil de démarrage** : fais un prototype Python + GTK4 en un week-end pour valider l'ergonomie, puis réécris le cœur en Rust si le projet prend.

### 5.2 Composants

1. **Détecteur de format** : à partir d'un chemin, retourne un type (extension, type MIME via `libmagic`/`shared-mime-info`, inspection du contenu au besoin).
2. **Backends** : une interface commune (trait en Rust) avec `can_handle(file)`, `describe(file)` (nom, version, source), `install(file, options)` et `required_privileges()`. Un backend par format.
3. **Exécuteur** : lance la commande en sous-processus, relaie la sortie en temps réel vers l'interface, gère l'annulation et les codes d'erreur.
4. **Interface de confirmation** : petite fenêtre (nom du paquet, source, commande qui sera lancée, bouton Installer / Annuler).
5. **Interface de configuration** : cases à cocher par format, mode par défaut (demander / silencieux), dossier AppImage, journal.
6. **Intégrateur de bureau** : crée les `.desktop` et icônes (AppImage), enregistre les associations MIME.
7. **Journal** : historique des installations avec la commande exacte lancée.

### 5.3 Flux d'une installation

1. Double-clic sur un fichier, le système lance `clickpak %f`.
2. Clickpak détecte le format et choisit le backend.
3. Selon la config : fenêtre de confirmation, ou installation directe pour les formats autorisés en mode silencieux.
4. Élévation de droits via polkit si nécessaire.
5. Exécution, progression affichée, notification de fin (« Installé, retrouve-le dans ton menu »).
6. Écriture dans le journal.

### 5.4 Structure du dépôt

```
clickpak/
├── src/
│   ├── main.rs
│   ├── detect.rs
│   ├── backends/
│   │   ├── mod.rs
│   │   ├── pacman.rs
│   │   ├── flatpak.rs
│   │   ├── appimage.rs
│   │   └── ...
│   ├── ui/
│   └── config.rs
├── data/
│   ├── clickpak.desktop
│   ├── clickpak.metainfo.xml
│   ├── icons/
│   └── polkit/
├── packaging/
│   ├── arch/PKGBUILD
│   └── flatpak/ (plus tard, voir §9)
├── tests/
├── docs/
├── README.md
├── README.fr.md
├── CONTRIBUTING.md
├── LICENSE
└── CHANGELOG.md
```

## 6. Sécurité

C'est le point le plus important : Clickpak lance des installations, parfois en root.

- **Confirmation par défaut** : un paquet peut exécuter des scripts en root à l'installation, donc l'utilisateur doit voir ce qui va se passer.
- **Mode silencieux réservé aux formats sandboxés** (Flatpak, AppImage) tant que l'utilisateur ne l'active pas explicitement pour les autres.
- **Afficher la commande exacte** qui sera exécutée.
- **Vérifications** : signature quand elle existe (paquets pacman signés), avertissement pour les fichiers non signés ou provenant de sources inconnues.
- **Pas de `shell=true`** : arguments passés en liste, jamais interpolés dans une chaîne shell (protection contre l'injection via un nom de fichier malicieux).
- **Polkit** : action dédiée, la plus restreinte possible, plutôt qu'un `pkexec` générique.
- **Journal complet** pour audit.
- **Avertissement renforcé** pour `.run`, `.sh`, `.exe` : ce sont des exécutables arbitraires.

## 7. Cas particulier : `.tar.gz`

Une archive ne contient pas d'instructions d'installation. Heuristique proposée, du plus sûr au moins sûr :

1. Contient un `PKGBUILD` : proposer `makepkg -si`.
2. Contient un fichier `.desktop` et un exécutable : extraire dans `~/.local/opt/<nom>/`, créer le lien et l'entrée de menu.
3. Contient un `install.sh` ou `Makefile` : **ne pas l'exécuter automatiquement** ; afficher le contenu et demander une validation explicite.
4. Autre cas : proposer simplement « Extraire ici » et expliquer pourquoi l'installation n'est pas possible automatiquement.

## 8. Feuille de route par versions

### Phase 0 : Cadrage (1 week-end)

- [ ] Vérifier le nom (GitHub, AUR, web) et créer le dépôt.
- [ ] Rechercher les projets existants proches (Bauh, Gear Lever, AppImageLauncher, etc.) et lister ce qui manque.
- [ ] Choisir la licence (GPL-3.0 ou MIT/Apache-2.0 selon l'esprit voulu).
- [ ] Rédiger un README de vision et 5 maquettes d'écrans (papier ou Figma).
- [ ] Choisir Python ou Rust pour le prototype.

### Phase 1 : Prototype v0.1 « Ça marche sur ma machine » (2 à 3 semaines)

- [ ] Détection du format (extensions + MIME).
- [ ] Backends : `.pkg.tar.zst`, `.flatpakref`/`.flatpak`, `.AppImage`.
- [ ] Fenêtre de confirmation GTK4 minimale (nom, commande, Installer/Annuler).
- [ ] Élévation via `pkexec` pour pacman.
- [ ] Fichier `.desktop` avec les `MimeType` et enregistrement via `xdg-mime`.
- [ ] Journal texte des installations.
- [ ] Premier `PKGBUILD` local pour l'installer proprement.

**Critère de réussite** : sur ta machine Arch, un double-clic sur chacun des trois formats installe l'application et elle apparaît dans le menu.

### Phase 2 : v0.2 « Utilisable par d'autres » (3 semaines)

- [ ] Fenêtre de configuration : cases à cocher des formats, choix confirmation / silencieux par format.
- [ ] Assistant au premier lancement (« Veux-tu que Clickpak soit l'application par défaut pour ces formats ? »).
- [ ] Affichage de la progression en temps réel et gestion propre des erreurs (message clair + sortie brute dépliable).
- [ ] Notifications de bureau à la fin de l'installation.
- [ ] Intégration AppImage complète (icône extraite, `.desktop` généré, dossier configurable).
- [ ] Détection des fichiers déjà installés (proposer « Réinstaller » plutôt que d'échouer).
- [ ] Tests unitaires sur la détection et les backends (avec commandes simulées).
- [ ] Publication sur l'**AUR** (`clickpak` et `clickpak-git`).

### Phase 3 : v0.3 « Plus de formats Arch » (3 semaines)

- [ ] Backend `PKGBUILD` / AUR (`makepkg -si` dans un dossier temporaire, avec avertissement sur la confiance du contenu).
- [ ] Backend `.snap`.
- [ ] Gestion des erreurs de dépendances (message lisible avec suggestion).
- [ ] Internationalisation (gettext) : anglais et français.
- [ ] Premières captures d'écran et GIF pour le README.

### Phase 4 : v0.4 « Les bonus » (3 semaines)

- [ ] `.vsix`, extensions GNOME Shell, `.run`/`.sh` (avec alertes fortes).
- [ ] Mode silencieux configurable par format.
- [ ] Action polkit dédiée et durcie.
- [ ] Vue « Historique » dans l'interface (ce qui a été installé, quand, avec quelle commande).

### Phase 5 : v0.5 « Compatibilité Windows et Java » (2 semaines)

- [ ] `.exe` / `.msi` via Wine ou Bottles (détection de ce qui est installé).
- [ ] `.jar` via Java.
- [ ] Menu clic droit « Ouvrir avec Clickpak » pour les formats non associés par défaut.

### Phase 6 : v0.6 « L'archive qui résiste » (2 à 3 semaines)

- [ ] Heuristique `.tar.gz` / `.tar.xz` (§7).
- [ ] Aperçu du contenu de l'archive avant installation.
- [ ] Intégration au menu pour les applications extraites.

### Phase 7 : v1.0 « Stable » (3 à 4 semaines)

- [ ] Audit de sécurité interne (injection de commandes, chemins, permissions, journal).
- [ ] Tests d'intégration sur plusieurs environnements (GNOME, KDE, XFCE) et sur Arch, EndeavourOS, Manjaro.
- [ ] Documentation complète (utilisateur et contributeur).
- [ ] Site de doc simple (GitHub Pages).
- [ ] Politique de versionnage (SemVer) et `CHANGELOG.md` à jour.
- [ ] Annonces : r/archlinux, r/linux, forums Arch, Mastodon, Hacker News (*Show HN*).

### Après la v1.0 : idées de backlog

- Support Qt/KDE natif (ou thème adaptatif).
- Support d'autres distributions : `.deb` via `apt`/`dpkg`, `.rpm` via `dnf` (backends natifs sur ces distros).
- Mode « ligne de commande » : `clickpak install fichier`.
- Désinstallation et vue « applications installées via Clickpak ».
- Vérification de signatures et empreintes (SHA256 saisi ou lu depuis la page de téléchargement).
- Système de plugins pour des backends communautaires.
- Intégration navigateur (ouvrir directement après téléchargement).

## 9. Distribution

- **AUR** en priorité (`clickpak`, `clickpak-bin`, `clickpak-git`).
- **Paquets natifs** pour d'autres distributions une fois le projet stable (`.deb`, `.rpm`, via CI).
- **Attention** : Clickpak **ne peut pas être distribué en Flatpak** de façon utile, car la sandbox l'empêcherait d'appeler `pacman` ou d'écrire librement sur le système hôte. C'est une contrainte de conception à garder en tête et à expliquer dans le README.
- **Releases GitHub** : binaires statiques et sources signées.

## 10. Qualité, tests et CI

- **CI GitHub Actions** : formatage (`rustfmt`), lint (`clippy`), tests unitaires, construction du paquet Arch dans un conteneur.
- **Tests des backends** avec des commandes simulées (aucune installation réelle en CI).
- **Tests manuels** documentés sur machine virtuelle Arch fraîche avant chaque release.
- **Jeu de fichiers d'essai** : un `.pkg.tar.zst` inoffensif, un `.flatpakref` de test, un AppImage minimal.

## 11. Communauté et visibilité

- Un **README soigné** : GIF de démo, installation en 3 lignes, tableau des formats.
- Des **issues étiquetées** `good first issue` pour attirer les contributeurs.
- Un **backend = un fichier** : documenter précisément comment en ajouter un.
- **Discussions GitHub** activées pour les retours d'utilisateurs.
- Post de lancement sur les forums Arch et Reddit une fois la v0.2 solide (pas avant : mieux vaut un projet fonctionnel qu'une annonce trop tôt).

## 12. Risques et parades

| Risque | Parade |
| --- | --- |
| Faille de sécurité via un fichier malveillant | Confirmation par défaut, pas de shell, journal, action polkit restreinte |
| Un projet similaire existe déjà | Phase 0 : recherche approfondie ; sinon, se différencier (multi-formats, config simple) |
| Gestion trop différente selon les environnements de bureau | Tester GNOME et KDE dès la v0.2 |
| Mainteneur unique qui s'essouffle | Architecture modulaire, doc contributeur, issues bien découpées |
| Dérive du périmètre (« gestionnaire de logiciels complet ») | S'en tenir au principe : *ouvrir un fichier → l'installer* |
| `.tar.gz` impossible à fiabiliser | Heuristique prudente, et l'assumer comme *best effort* |

## 13. Premiers pas : la semaine 1

1. Vérifier la disponibilité du nom *Clickpak* (GitHub, AUR, web).
2. Créer le dépôt, ajouter licence, README de vision, topics et description.
3. Écrire un script minimal qui détecte l'extension d'un fichier et affiche une fenêtre GTK « Installer ce fichier ? ».
4. Brancher le backend `.flatpakref` (le plus simple, sans root).
5. Rédiger le fichier `.desktop` et tester `xdg-mime default` sur ton Arch.
6. Ajouter le backend `.pkg.tar.zst` avec `pkexec`.
7. Noter dans un `TODO.md` tout ce qui t'a surpris : c'est la matière de ta doc.

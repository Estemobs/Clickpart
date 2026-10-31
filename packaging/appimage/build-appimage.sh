#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Clickpart — construction d'une AppImage autonome avec linuxdeploy
#            et le plugin linuxdeploy-plugin-gtk (GTK 3 / WebKitGTK).
#
# Usage :
#   ./packaging/appimage/build-appimage.sh              # build + AppImage
#   ./packaging/appimage/build-appimage.sh --rebuild    # force cargo build
#   ./packaging/appimage/build-appimage.sh --no-download
#   CLICKPART_BUNDLE_GTK=0 ./packaging/appimage/build-appimage.sh
#       -> n'embarque pas GTK (utilise le GTK du système)
#
# Sortie : dist/Clickpart-<version>-x86_64.AppImage
# ---------------------------------------------------------------------------
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APP_ID="org.clickpart.Clickpart"
APP_NAME="Clickpart"
ARCH="$(uname -m)"
WORK="$ROOT/packaging/appimage"
TOOLS="$WORK/.tools"
APPDIR="$WORK/AppDir"
DIST="$ROOT/dist"
BIN="$ROOT/src-tauri/target/release/clickpart"

VERSION="$(sed -n 's/^[[:space:]]*"version":[[:space:]]*"\([^"]*\)".*/\1/p' "$ROOT/package.json" | head -n1)"
VERSION="${VERSION:-0.6.0}"

REBUILD=0
DOWNLOAD=1
for arg in "$@"; do
  case "$arg" in
    --rebuild) REBUILD=1 ;;
    --no-download) DOWNLOAD=0 ;;
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
    *) echo "Option inconnue : $arg" >&2; exit 2 ;;
  esac
done

log()  { printf '\033[1;34m[clickpart]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[clickpart]\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31m[clickpart]\033[0m %s\n' "$*" >&2; exit 1; }

need() { command -v "$1" >/dev/null 2>&1 || die "Commande requise introuvable : $1"; }

need curl
need file
need tar

# ---------------------------------------------------------------------------
# 1. Compilation du binaire Tauri
# ---------------------------------------------------------------------------
if [[ $REBUILD -eq 1 || ! -x "$BIN" ]]; then
  log "Compilation du binaire Tauri (release)…"
  need cargo
  ( cd "$ROOT" && cargo build --release --manifest-path src-tauri/Cargo.toml )
else
  log "Binaire existant réutilisé : $BIN"
fi

[[ -x "$BIN" ]] || die "Binaire introuvable : $BIN"

# ---------------------------------------------------------------------------
# 2. Outils linuxdeploy
# ---------------------------------------------------------------------------
mkdir -p "$TOOLS" "$DIST"

LD="$TOOLS/linuxdeploy-$ARCH.AppImage"
GTK_PLUGIN="$TOOLS/linuxdeploy-plugin-gtk.sh"

if [[ $DOWNLOAD -eq 1 ]]; then
  if [[ ! -x "$LD" ]]; then
    log "Téléchargement de linuxdeploy…"
    curl -fsSL -o "$LD" \
      "https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-$ARCH.AppImage"
    chmod +x "$LD"
  fi

  if [[ ! -x "$GTK_PLUGIN" ]]; then
    log "Téléchargement de linuxdeploy-plugin-gtk…"
    curl -fsSL -o "$GTK_PLUGIN" \
      "https://raw.githubusercontent.com/linuxdeploy/linuxdeploy-plugin-gtk/master/linuxdeploy-plugin-gtk.sh"
    chmod +x "$GTK_PLUGIN"
  fi
fi

[[ -x "$LD" ]] || die "linuxdeploy absent (relancez sans --no-download)"
[[ -x "$GTK_PLUGIN" ]] || die "linuxdeploy-plugin-gtk absent (relancez sans --no-download)"

# Le plugin GTK cherche les bibliothèques récursivement dans /usr/lib. Sur
# certaines machines, des copies parasites (ex. /usr/lib/vmware/lib) cassent le
# déploiement. On limite la recherche à deux niveaux (suffisant pour Arch et
# pour les distributions multiarch).
if grep -q 'find "$directory" \\( -type l -o -type f \\)' "$GTK_PLUGIN"; then
  sed -i 's|find "$directory" \\( -type l -o -type f \\) -name "$library"|find "$directory" -maxdepth 2 \\( -type l -o -type f \\) -name "$library"|' "$GTK_PLUGIN"
  log "Plugin GTK ajusté (recherche limitée à 2 niveaux)."
fi

# linuxdeploy est lui-même une AppImage : on évite FUSE en l'extrayant.
export APPIMAGE_EXTRACT_AND_RUN=1
export PATH="$TOOLS:$PATH"

# ---------------------------------------------------------------------------
# 3. AppDir
# ---------------------------------------------------------------------------
log "Préparation de l'AppDir…"
rm -rf "$APPDIR"
mkdir -p \
  "$APPDIR/usr/bin" \
  "$APPDIR/usr/share/applications" \
  "$APPDIR/usr/share/icons/hicolor/256x256/apps" \
  "$APPDIR/usr/share/metainfo"

install -m 0755 "$BIN" "$APPDIR/usr/bin/clickpart"
install -m 0644 "$WORK/$APP_ID.desktop" "$APPDIR/usr/share/applications/$APP_ID.desktop"
install -m 0644 "$ROOT/src-tauri/icons/clickpart-128x128@2x.png" \
  "$APPDIR/usr/share/icons/hicolor/256x256/apps/$APP_ID.png"
if [[ -f "$ROOT/data/clickpart.metainfo.xml" ]]; then
  install -m 0644 "$ROOT/data/clickpart.metainfo.xml" \
    "$APPDIR/usr/share/metainfo/$APP_ID.metainfo.xml"
fi

# ---------------------------------------------------------------------------
# 4. linuxdeploy + plugin GTK
# ---------------------------------------------------------------------------
LD_ARGS=(
  --appdir "$APPDIR"
  --desktop-file "$APPDIR/usr/share/applications/$APP_ID.desktop"
  --icon-file "$APPDIR/usr/share/icons/hicolor/256x256/apps/$APP_ID.png"
  --output appimage
)

if [[ "${CLICKPART_BUNDLE_GTK:-1}" != "0" ]]; then
  log "Déploiement GTK 3 via linuxdeploy-plugin-gtk…"
  export DEPLOY_GTK_VERSION=3
  export LINUXDEPLOY_PLUGIN_GTK="$GTK_PLUGIN"
  LD_ARGS+=(--plugin gtk)
else
  warn "Plugin GTK désactivé (CLICKPART_BUNDLE_GTK=0) : GTK du système utilisé."
fi

log "Exécution de linuxdeploy…"
( cd "$WORK" && "$LD" "${LD_ARGS[@]}" )

# WebKitGTK ne peut pas être embarqué correctement par linuxdeploy (processus
# auxiliaires + données dans /usr/lib/webkit2gtk-4.1). On le retire de l'AppDir
# pour que l'AppImage utilise le WebKitGTK du système (présent sur Arch).
shopt -s nullglob
REMOVED=0
for f in "$APPDIR"/usr/lib/libwebkit2gtk-*.so* "$APPDIR"/usr/lib/libjavascriptcoregtk-*.so*; do
  rm -f "$f"
  REMOVED=$((REMOVED + 1))
done
shopt -u nullglob
if [[ $REMOVED -gt 0 ]]; then
  warn "WebKitGTK retiré de l'AppImage ($REMOVED fichiers) : dépendance système requise."
fi

# ---------------------------------------------------------------------------
# 5. Récupération du résultat
# ---------------------------------------------------------------------------
BUILT="$(ls -1t "$WORK"/Clickpart*.AppImage "$WORK"/*.AppImage 2>/dev/null | head -n1 || true)"
[[ -n "${BUILT:-}" && -f "$BUILT" ]] || die "Aucune AppImage produite par linuxdeploy."

OUT="$DIST/Clickpart-$VERSION-$ARCH.AppImage"
mv -f "$BUILT" "$OUT"
chmod +x "$OUT"

log "AppImage prête : $OUT"
log "Taille : $(du -h "$OUT" | cut -f1)"
echo
echo "Test rapide :"
echo "  \"$OUT\" --appimage-extract-and-run"
echo "Installation locale :"
echo "  mkdir -p ~/.local/bin && cp \"$OUT\" ~/.local/bin/clickpart.AppImage"

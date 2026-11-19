#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use serde::{Deserialize, Serialize};
use std::fs;
use std::io::{BufRead, BufReader, Read, Write};
use std::os::unix::fs::PermissionsExt;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::sync::{Arc, Mutex};
use std::time::Duration;
use tauri::{AppHandle, Emitter};

// ---------------------------------------------------------------------------
// Modeles partages avec le frontend
// ---------------------------------------------------------------------------

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct FileInfo {
    pub path: String,
    pub name: String,
    pub size: u64,
    pub format: String,
    pub label: String,
    pub description: String,
    pub needs_root: bool,
    pub supported: bool,
    pub distro_compatible: bool,
    pub distro_notes: Option<String>,
}

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct InstallResult {
    pub success: bool,
    pub message: String,
    pub details: String,
}

#[derive(Serialize, Clone, Debug)]
pub struct InstalledApp {
    pub name: String,
    pub exec: String,
    pub desktop: String,
    pub location: String,
}

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct HistoryEntry {
    pub timestamp: String,
    pub file: String,
    pub format: String,
    pub status: String,
    pub message: String,
}

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct Config {
    pub confirm_before_install: bool,
    pub open_log_automatically: bool,
    pub preferred_scope: String,
    #[serde(default)]
    pub check_update: bool,
    #[serde(default)]
    pub update_frequency: String,
    #[serde(default)]
    pub update_source: String,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            confirm_before_install: true,
            open_log_automatically: true,
            preferred_scope: "user".into(),
            check_update: true,
            update_frequency: "weekly".into(),
            update_source: "https://api.github.com/repos/Estemobs/Clickpart/releases/latest".into(),
        }
    }
}

#[derive(Serialize, Clone, Debug)]
struct LogLine {
    stream: String,
    line: String,
}

#[derive(Serialize, Clone, Debug)]
pub struct ToolInfo {
    pub name: String,
    pub available: bool,
    pub relevant: bool,
}

#[derive(Serialize, Clone, Debug)]
pub struct SystemInfo {
    pub distro: String,
    pub distro_family: String,
    pub kernel: String,
    pub tools: Vec<ToolInfo>,
}

// ---------------------------------------------------------------------------
// Helpers chemins / environnement
// ---------------------------------------------------------------------------

fn home() -> PathBuf {
    PathBuf::from(std::env::var("HOME").unwrap_or_else(|_| "/tmp".into()))
}

fn xdg_dir(var: &str, fallback: &str) -> PathBuf {
    match std::env::var(var) {
        Ok(v) if !v.is_empty() => PathBuf::from(v),
        _ => home().join(fallback),
    }
}

fn config_file() -> PathBuf {
    xdg_dir("XDG_CONFIG_HOME", ".config")
        .join("clickpart")
        .join("config.json")
}

fn history_file() -> PathBuf {
    xdg_dir("XDG_STATE_HOME", ".local/state")
        .join("clickpart")
        .join("history.json")
}

fn applications_dir() -> PathBuf {
    xdg_dir("XDG_DATA_HOME", ".local/share").join("applications")
}

fn icons_dir() -> PathBuf {
    xdg_dir("XDG_DATA_HOME", ".local/share")
        .join("icons")
        .join("hicolor")
        .join("256x256")
        .join("apps")
}

fn has_cmd(name: &str) -> bool {
    if let Ok(path) = std::env::var("PATH") {
        for dir in path.split(':') {
            let candidate = Path::new(dir).join(name);
            if candidate.is_file() {
                if let Ok(meta) = fs::metadata(&candidate) {
                    if meta.permissions().mode() & 0o111 != 0 {
                        return true;
                    }
                }
            }
        }
    }
    false
}

fn sanitize(name: &str) -> String {
    name.chars()
        .map(|c| {
            if c.is_ascii_alphanumeric() || c == '.' || c == '-' || c == '_' || c == '+' {
                c
            } else {
                '_'
            }
        })
        .collect()
}

fn shell_quote(s: &str) -> String {
    format!("'{}'", s.replace('\'', "'\\''"))
}

// ---------------------------------------------------------------------------
// Execution de processus avec streaming
// ---------------------------------------------------------------------------

fn pump<R: Read>(reader: R, stream: &'static str, app: &AppHandle, tail: Arc<Mutex<Vec<String>>>) {
    let buffered = BufReader::new(reader);
    for line in buffered.lines() {
        match line {
            Ok(l) => {
                let _ = app.emit(
                    "install-log",
                    LogLine {
                        stream: stream.to_string(),
                        line: l.clone(),
                    },
                );
                if let Ok(mut t) = tail.lock() {
                    t.push(l);
                    if t.len() > 80 {
                        t.remove(0);
                    }
                }
            }
            Err(_) => break,
        }
    }
}

fn phase(app: &AppHandle, message: &str) {
    let _ = app.emit("install-phase", message.to_string());
    let _ = app.emit(
        "install-log",
        LogLine {
            stream: "phase".into(),
            line: format!("▶ {}", message),
        },
    );
}

fn run_stream(
    app: &AppHandle,
    program: &str,
    args: &[String],
    cwd: Option<&Path>,
) -> Result<(i32, String), String> {
    let mut cmd = Command::new(program);
    cmd.args(args)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .stdin(Stdio::null());
    if let Some(dir) = cwd {
        cmd.current_dir(dir);
    }

    let _ = app.emit(
        "install-log",
        LogLine {
            stream: "cmd".into(),
            line: format!("$ {} {}", program, args.join(" ")),
        },
    );

    let mut child = cmd
        .spawn()
        .map_err(|e| format!("Impossible de lancer « {} » : {}", program, e))?;

    let stdout = child.stdout.take();
    let stderr = child.stderr.take();
    let tail = Arc::new(Mutex::new(Vec::new()));

    let mut handles = Vec::new();
    if let Some(out) = stdout {
        let t = tail.clone();
        let a = app.clone();
        handles.push(std::thread::spawn(move || pump(out, "stdout", &a, t)));
    }
    if let Some(err) = stderr {
        let t = tail.clone();
        let a = app.clone();
        handles.push(std::thread::spawn(move || pump(err, "stderr", &a, t)));
    }

    let status = child
        .wait()
        .map_err(|e| format!("Erreur pendant l'attente de « {} » : {}", program, e))?;

    for h in handles {
        let _ = h.join();
    }

    let code = status.code().unwrap_or(-1);
    let text = tail
        .lock()
        .map(|t| t.join("\n"))
        .unwrap_or_else(|_| String::new());

    Ok((code, text))
}

fn spawn_detached(program: &str, args: &[String]) -> Result<(), String> {
    Command::new(program)
        .args(args)
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .stdin(Stdio::null())
        .spawn()
        .map(|_| ())
        .map_err(|e| format!("Impossible de lancer « {} » : {}", program, e))
}

// ---------------------------------------------------------------------------
// Detection de format avec compatibilité par distribution
// ---------------------------------------------------------------------------

fn detect_inner(path: &str, is_arch: bool, is_debian: bool, is_fedora: bool) -> Result<FileInfo, String> {
    let p = Path::new(path);
    let meta = fs::metadata(p).map_err(|e| format!("Fichier introuvable : {}", e))?;
    let name = p
        .file_name()
        .map(|n| n.to_string_lossy().to_string())
        .unwrap_or_else(|| path.to_string());

    let lower = name.to_lowercase();
    let is_dir = meta.is_dir();

    let (format, label, description, needs_root, supported, compatible, notes) = if is_dir {
        if p.join("PKGBUILD").is_file() {
            (
                "pkgbuild",
                "Dossier PKGBUILD",
                "Compile le paquet avec makepkg puis l'installe avec pacman.",
                true,
                true,
                is_arch,
                if is_arch { None } else { Some("PKGBUILD uniquement pour Arch-based".into()) },
            )
        } else {
            (
                "unknown",
                "Dossier",
                "Ce dossier ne contient pas de PKGBUILD.",
                false,
                false,
                false,
                None,
            )
        }
    } else if lower == "pkgbuild" || lower.starts_with("pkgbuild") {
        (
            "pkgbuild",
            "Fichier PKGBUILD",
            "Compile le paquet avec makepkg puis l'installe avec pacman.",
            true,
            true,
            is_arch,
            if is_arch { None } else { Some("PKGBUILD uniquement pour Arch-based".into()) },
        )
    } else if lower.ends_with(".pkg.tar.zst")
        || lower.ends_with(".pkg.tar.xz")
        || lower.ends_with(".pkg.tar.gz")
        || lower.ends_with(".pkg.tar.bz2")
        || lower.ends_with(".pkg.tar.lz4")
        || lower.ends_with(".pkg.tar.lzo")
    {
        (
            "pacman",
            "Paquet Arch (pacman)",
            "Installe le paquet avec pacman -U (authentification administrateur requise).",
            true,
            true,
            is_arch,
            if is_arch { None } else { Some("pacman uniquement pour Arch-based".into()) },
        )
    } else if lower.ends_with(".appimage") {
        (
            "appimage",
            "AppImage",
            "Copie l'AppImage dans ~/.local/bin et crée une entrée de menu.",
            false,
            true,
            true,
            None,
        )
    } else if lower.ends_with(".flatpakref") {
        (
            "flatpakref",
            "Référence Flatpak",
            "Installe l'application depuis sa référence Flatpak.",
            false,
            true,
            true,
            None,
        )
    } else if lower.ends_with(".flatpak") {
        (
            "flatpak",
            "Bundle Flatpak",
            "Installe le bundle Flatpak local.",
            false,
            true,
            true,
            None,
        )
    } else if lower.ends_with(".tar.zst")
        || lower.ends_with(".tar.xz")
        || lower.ends_with(".tar.gz")
        || lower.ends_with(".tar.bz2")
        || lower.ends_with(".tgz")
        || lower.ends_with(".tbz2")
        || lower.ends_with(".txz")
        || lower.ends_with(".tar")
        || lower.ends_with(".zip")
        || lower.ends_with(".7z")
    {
        (
            "archive",
            "Archive",
            "Extrait l'archive dans ~/.local/opt et crée une entrée de menu si possible.",
            false,
            true,
            true,
            None,
        )
    } else if lower.ends_with(".jar") {
        (
            "jar",
            "Application Java",
            "Lance l'application avec java -jar.",
            false,
            true,
            true,
            None,
        )
    } else if lower.ends_with(".vsix") {
        (
            "vsix",
            "Extension VS Code",
            "Installe l'extension avec code --install-extension.",
            false,
            true,
            true,
            None,
        )
    } else if lower.ends_with(".run") {
        (
            "run",
            "Script d'installation .run",
            "Script interactif : Clickpart ne peut pas le piloter sans terminal.",
            true,
            false,
            true,
            Some("Installation manuelle requise".into()),
        )
    } else if lower.ends_with(".exe") || lower.ends_with(".msi") {
        (
            "windows",
            "Application Windows",
            "Lance l'installeur avec Wine.",
            false,
            true,
            true,
            None,
        )
    } else if lower.ends_with(".deb") {
        (
            "deb",
            "Paquet Debian",
            "Format Debian : non installable directement sur Arch Linux.",
            true,
            false,
            is_debian,
            if is_debian { None } else { Some("Format Debian incompatible avec Arch-based".into()) },
        )
    } else if lower.ends_with(".rpm") {
        (
            "rpm",
            "Paquet RPM",
            "Format RPM : non installable directement sur Arch Linux.",
            true,
            false,
            is_fedora,
            if is_fedora { None } else { Some("Format RPM incompatible avec Fedora/Red Hat-based".into()) },
        )
    } else if lower.ends_with(".snap") {
        (
            "snap",
            "Bundle Snap",
            "Format Snap : non installable directement sur Arch Linux.",
            true,
            false,
            false,
            Some("Format Snap non compatible avec Arch Linux".into()),
        )
    } else {
        (
            "unknown",
            "Format inconnu",
            "Clickpart ne reconnaît pas ce type de fichier.",
            false,
            false,
            false,
            None,
        )
    };

    Ok(FileInfo {
        path: p.to_string_lossy().to_string(),
        name,
        size: if is_dir { 0 } else { meta.len() },
        format: format.into(),
        label: label.into(),
        description: description.into(),
        needs_root,
        supported,
        distro_compatible: compatible,
        distro_notes: notes,
    })
}

#[tauri::command]
fn detect_format(path: String) -> Result<FileInfo, String> {
    let distro_raw = fs::read_to_string("/etc/os-release")
        .ok()
        .and_then(|s| {
            s.lines()
                .find(|l| l.starts_with("PRETTY_NAME="))
                .map(|l| l.trim_start_matches("PRETTY_NAME=").trim_matches('"').to_string())
        })
        .unwrap_or_else(|| "Linux".into());

    let id_like = fs::read_to_string("/etc/os-release")
        .ok()
        .and_then(|s| {
            s.lines()
                .find(|l| l.starts_with("ID_LIKE=") || l.starts_with("ID="))
                .map(|l| l.split('=').nth(1).unwrap_or("").trim_matches('"').to_lowercase())
        })
        .unwrap_or_default();

    let is_arch = distro_raw.to_lowercase().contains("arch")
        || distro_raw.to_lowercase().contains("cachyos")
        || distro_raw.to_lowercase().contains("endeavour")
        || distro_raw.to_lowercase().contains("manjaro")
        || distro_raw.to_lowercase().contains("garuda")
        || id_like.contains("arch");

    let is_debian = distro_raw.to_lowercase().contains("debian")
        || distro_raw.to_lowercase().contains("ubuntu")
        || distro_raw.to_lowercase().contains("mint")
        || distro_raw.to_lowercase().contains("kali")
        || id_like.contains("debian");

    let is_fedora = distro_raw.to_lowercase().contains("fedora")
        || distro_raw.to_lowercase().contains("rhel")
        || distro_raw.to_lowercase().contains("centos")
        || id_like.contains("fedora") || id_like.contains("rhel");

    detect_inner(&path, is_arch, is_debian, is_fedora)
}

#[tauri::command]
fn startup_file() -> Option<String> {
    std::env::args().skip(1).find(|arg| !arg.starts_with('-'))
}

#[tauri::command]
fn system_info() -> SystemInfo {
    let distro_raw = fs::read_to_string("/etc/os-release")
        .ok()
        .and_then(|s| {
            s.lines()
                .find(|l| l.starts_with("PRETTY_NAME="))
                .map(|l| l.trim_start_matches("PRETTY_NAME=").trim_matches('"').to_string())
        })
        .unwrap_or_else(|| "Linux".into());

    let id_like = fs::read_to_string("/etc/os-release")
        .ok()
        .and_then(|s| {
            s.lines()
                .find(|l| l.starts_with("ID_LIKE=") || l.starts_with("ID="))
                .map(|l| l.split('=').nth(1).unwrap_or("").trim_matches('"').to_lowercase())
        })
        .unwrap_or_default();

    let is_arch = distro_raw.to_lowercase().contains("arch")
        || distro_raw.to_lowercase().contains("cachyos")
        || distro_raw.to_lowercase().contains("endeavour")
        || distro_raw.to_lowercase().contains("manjaro")
        || distro_raw.to_lowercase().contains("garuda")
        || id_like.contains("arch");

    let is_debian = distro_raw.to_lowercase().contains("debian")
        || distro_raw.to_lowercase().contains("ubuntu")
        || distro_raw.to_lowercase().contains("mint")
        || distro_raw.to_lowercase().contains("kali")
        || id_like.contains("debian");

    let is_fedora = distro_raw.to_lowercase().contains("fedora")
        || distro_raw.to_lowercase().contains("rhel")
        || distro_raw.to_lowercase().contains("centos")
        || id_like.contains("fedora") || id_like.contains("rhel");

    let kernel = fs::read_to_string("/proc/sys/kernel/osrelease")
        .map(|s| s.trim().to_string())
        .unwrap_or_default();

    let tools = [
        ("pacman", is_arch),
        ("pkexec", true),
        ("flatpak", true),
        ("makepkg", is_arch),
        ("wine", true),
        ("java", true),
        ("code", true),
        ("gnome-extensions", true),
        ("tar", true),
        ("unzip", true),
        ("7z", true),
        ("xdg-open", true),
        ("apt", is_debian),
        ("dnf", is_fedora),
        ("rpm", is_fedora || is_debian),
        ("zypper", false),
    ]
    .iter()
    .map(|(t, relevant)| ToolInfo {
        name: (*t).to_string(),
        available: if *relevant { has_cmd(t) } else { false },
        relevant: *relevant,
    })
    .collect();

    SystemInfo {
        distro: distro_raw,
        distro_family: if is_arch { "arch".into() } else if is_debian { "debian".into() } else if is_fedora { "fedora".into() } else { "other".into() },
        kernel,
        tools,
    }
}

// ---------------------------------------------------------------------------
// Applications installées par Clickpart (~/.local) et désinstallation
// ---------------------------------------------------------------------------

fn desktop_field(content: &str, key: &str) -> Option<String> {
    content
        .lines()
        .find_map(|l| l.strip_prefix(key).map(|v| v.trim().to_string()))
}

fn exec_program(exec: &str) -> Option<String> {
    let s = exec.trim();
    let first = if let Some(rest) = s.strip_prefix('"') {
        rest.split_once('"')?.0
    } else if let Some(rest) = s.strip_prefix('\'') {
        rest.split_once('\'')?.0
    } else {
        s.split_once(char::is_whitespace).map(|(f, _)| f).unwrap_or(s)
    };
    if first.is_empty() {
        None
    } else {
        Some(first.to_string())
    }
}

// Cible supprimable : uniquement ~/.local/bin (fichier) ou ~/.local/opt/<app>.
fn confined_target(exec: &Path, opt: &Path, bin: &Path) -> Option<PathBuf> {
    if exec.starts_with(bin) && exec.is_file() {
        return Some(exec.to_path_buf());
    }
    if let Ok(rel) = exec.strip_prefix(opt) {
        let dir = opt.join(rel.components().next()?.as_os_str());
        if dir != opt && dir.is_dir() {
            return Some(dir);
        }
    }
    None
}

fn remove_path(path: &Path, removed: &mut Vec<String>, failed: &mut Vec<String>) {
    if !path.exists() {
        return;
    }
    let result = if path.is_dir() {
        fs::remove_dir_all(path)
    } else {
        fs::remove_file(path)
    };
    match result {
        Ok(_) => removed.push(path.display().to_string()),
        Err(e) => failed.push(format!("{} : {}", path.display(), e)),
    }
}

#[tauri::command]
fn list_installed() -> Vec<InstalledApp> {
    let opt = home().join(".local/opt");
    let bin = home().join(".local/bin");
    let mut apps = Vec::new();
    let entries = match fs::read_dir(applications_dir()) {
        Ok(e) => e,
        Err(_) => return apps,
    };
    for entry in entries.flatten() {
        let desktop = entry.path();
        if desktop.extension().map(|e| e != "desktop").unwrap_or(true) {
            continue;
        }
        let content = match fs::read_to_string(&desktop) {
            Ok(c) => c,
            Err(_) => continue,
        };
        let exec = match desktop_field(&content, "Exec=").and_then(|v| exec_program(&v)) {
            Some(e) => PathBuf::from(e),
            None => continue,
        };
        let location = match confined_target(&exec, &opt, &bin) {
            Some(l) => l,
            None => continue,
        };
        let name = desktop_field(&content, "Name=").unwrap_or_else(|| {
            desktop
                .file_stem()
                .map(|s| s.to_string_lossy().to_string())
                .unwrap_or_default()
        });
        apps.push(InstalledApp {
            name,
            exec: exec.to_string_lossy().to_string(),
            desktop: desktop.to_string_lossy().to_string(),
            location: location.to_string_lossy().to_string(),
        });
    }
    apps.sort_by(|a, b| a.name.to_lowercase().cmp(&b.name.to_lowercase()));
    apps
}

#[tauri::command]
fn uninstall_app(desktop: String) -> Result<InstallResult, String> {
    let entry = PathBuf::from(&desktop);
    if entry.parent() != Some(applications_dir().as_path())
        || entry.extension().map(|e| e != "desktop").unwrap_or(true)
    {
        return Err("Chemin d'entrée de menu invalide.".into());
    }
    let content = fs::read_to_string(&entry).map_err(|_| "Entrée de menu introuvable.".to_string())?;
    let exec = desktop_field(&content, "Exec=")
        .and_then(|v| exec_program(&v))
        .map(PathBuf::from)
        .ok_or("Impossible de déterminer le programme à désinstaller.")?;
    let target = confined_target(&exec, &home().join(".local/opt"), &home().join(".local/bin"))
        .ok_or("Le programme associé est introuvable (déjà désinstallé ?).")?;

    let mut removed = Vec::new();
    let mut failed = Vec::new();
    remove_path(&target, &mut removed, &mut failed);

    if let Some(icon) = desktop_field(&content, "Icon=") {
        let icon_path = if icon.starts_with('/') {
            PathBuf::from(&icon)
        } else {
            icons_dir().join(format!("{}.png", icon))
        };
        if icon_path.starts_with(icons_dir()) {
            remove_path(&icon_path, &mut removed, &mut failed);
        }
    }
    remove_path(&entry, &mut removed, &mut failed);
    let _ = Command::new("update-desktop-database")
        .arg(applications_dir())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .status();

    let name = desktop_field(&content, "Name=").unwrap_or_else(|| {
        entry
            .file_stem()
            .map(|s| s.to_string_lossy().to_string())
            .unwrap_or_else(|| "Application".into())
    });
    let mut details = if removed.is_empty() {
        "Aucun fichier supprimé.".to_string()
    } else {
        format!("Supprimé :\n{}", removed.join("\n"))
    };
    if !failed.is_empty() {
        details.push_str(&format!("\nÉchecs :\n{}", failed.join("\n")));
    }
    Ok(InstallResult {
        success: failed.is_empty(),
        message: if failed.is_empty() {
            format!("{} désinstallé.", name)
        } else {
            format!("Désinstallation de {} incomplète.", name)
        },
        details,
    })
}

// ---------------------------------------------------------------------------
// Configuration / historique
// ---------------------------------------------------------------------------

#[tauri::command]
fn get_config() -> Config {
    fs::read_to_string(config_file())
        .ok()
        .and_then(|s| serde_json::from_str(&s).ok())
        .unwrap_or_default()
}

#[tauri::command]
fn save_config(config: Config) -> Result<(), String> {
    let file = config_file();
    if let Some(parent) = file.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let json = serde_json::to_string_pretty(&config).map_err(|e| e.to_string())?;
    fs::write(&file, json).map_err(|e| e.to_string())
}

#[tauri::command]
fn get_history() -> Vec<HistoryEntry> {
    fs::read_to_string(history_file())
        .ok()
        .and_then(|s| serde_json::from_str(&s).ok())
        .unwrap_or_default()
}

#[tauri::command]
fn clear_history() -> Result<(), String> {
    let file = history_file();
    if file.exists() {
        fs::remove_file(file).map_err(|e| e.to_string())?;
    }
    Ok(())
}

#[tauri::command]
fn open_url(url: String) -> Result<(), String> {
    std::process::Command::new("xdg-open")
        .arg(&url)
        .spawn()
        .map(|_| ())
        .map_err(|e| format!("Impossible d'ouvrir l'URL : {}", e))
}

/// Telecharge le binaire de la derniere release, remplace l'executable
/// en cours et relance l'application proprement.
#[tauri::command]
fn update_app(api_url: String) -> Result<(), String> {
    // En AppImage, current_exe() pointe vers le montage squashfs (lecture seule) :
    // on remplace le fichier .AppImage lui-même via $APPIMAGE.
    let exe = match std::env::var_os("APPIMAGE").map(PathBuf::from) {
        Some(p) if p.is_file() => p,
        _ => std::env::current_exe().map_err(|e| e.to_string())?,
    };
    let exe_dir = exe.parent().ok_or("Dossier de l'executable introuvable")?;

    // Recuperer les infos de la release (pour trouver l'asset a telecharger)
    let release: serde_json::Value = {
        let resp = ureq::get(&api_url)
            .call()
            .map_err(|e| format!("Impossible de contacter l'API de release : {}", e))?;
        serde_json::from_reader(resp.into_reader()).map_err(|e| e.to_string())?
    };

    let asset_url = release["assets"]
        .as_array()
        .and_then(|arr| {
            arr.iter()
                .find(|a| {
                    a["name"]
                        .as_str()
                        .map_or(false, |n| n.ends_with(".AppImage") || n.ends_with(".AppImage.tar.gz"))
                })
                .or_else(|| arr.first())
                .and_then(|a| a["browser_download_url"].as_str().map(String::from))
        })
        .ok_or("Aucun binaire de mise à jour trouve dans la release")?;

    // Telecharger le nouveau binaire dans un fichier temporaire (meme dossier pour le rename)
    let temp_name = format!(".clickpart-update-{}", std::process::id());
    let temp_path = exe_dir.join(temp_name);
    let resp = ureq::get(&asset_url)
        .call()
        .map_err(|e| format!("Echec du telechargement : {}", e))?;
    let mut reader = resp.into_reader();
    let mut file = std::fs::File::create(&temp_path).map_err(|e| e.to_string())?;
    let mut buffer = [0u8; 8192];
    loop {
        match reader.read(&mut buffer) {
            Ok(0) => break,
            Ok(n) => file.write_all(&buffer[..n]).map_err(|e| e.to_string())?,
            Err(e) => return Err(e.to_string()),
        }
    }
    drop(file);
    let _ = std::fs::set_permissions(&temp_path, std::fs::Permissions::from_mode(0o755));

    // Remplacer l'executable en cours (sur Linux, le fichier ouvert reste valide)
    std::fs::rename(&temp_path, &exe).map_err(|e| format!("Impossible de remplacer l'executable : {}", e))?;

    // Relancer la nouvelle version puis fermer l'instance actuelle
    let exe_for_spawn = exe.clone();
    std::thread::spawn(move || {
        std::thread::sleep(Duration::from_millis(700));
        let _ = std::process::Command::new(exe_for_spawn).spawn();
        std::thread::sleep(Duration::from_millis(300));
        std::process::exit(0);
    });

    Ok(())
}

fn now_string() -> String {
    let output = Command::new("date").arg("+%Y-%m-%d %H:%M:%S").output();
    match output {
        Ok(o) => String::from_utf8_lossy(&o.stdout).trim().to_string(),
        Err(_) => "date inconnue".into(),
    }
}

fn append_history(entry: HistoryEntry) {
    let file = history_file();
    if let Some(parent) = file.parent() {
        let _ = fs::create_dir_all(parent);
    }
    let mut entries = get_history();
    entries.insert(0, entry);
    entries.truncate(100);
    if let Ok(json) = serde_json::to_string_pretty(&entries) {
        let _ = fs::write(file, json);
    }
}

// ---------------------------------------------------------------------------
// Installeurs
// ---------------------------------------------------------------------------

fn install_pacman(app: &AppHandle, path: &str) -> Result<InstallResult, String> {
    if !has_cmd("pkexec") {
        return Err(
            "pkexec est introuvable. Installez polkit ou lancez : sudo pacman -U <fichier>"
                .into(),
        );
    }
    phase(app, "Authentification administrateur (polkit)…");
    let args = vec![
        "pacman".to_string(),
        "-U".to_string(),
        "--noconfirm".to_string(),
        path.to_string(),
    ];
    let (code, tail) = run_stream(app, "pkexec", &args, None)?;
    if code == 0 {
        Ok(InstallResult {
            success: true,
            message: "Paquet installé avec succès.".into(),
            details: tail,
        })
    } else if code == 126 || code == 127 {
        Err("Installation annulée ou authentification refusée.".into())
    } else {
        Ok(InstallResult {
            success: false,
            message: format!("pacman a échoué (code {}).", code),
            details: tail,
        })
    }
}

fn install_appimage(app: &AppHandle, path: &str) -> Result<InstallResult, String> {
    let src = Path::new(path);
    let name = src
        .file_name()
        .map(|n| n.to_string_lossy().to_string())
        .ok_or("Nom de fichier invalide")?;
    let name = sanitize(&name);

    let bin_dir = home().join(".local/bin");
    fs::create_dir_all(&bin_dir).map_err(|e| format!("Impossible de créer ~/.local/bin : {}", e))?;
    let dest = bin_dir.join(&name);

    phase(app, "Copie de l'AppImage dans ~/.local/bin…");
    fs::copy(src, &dest).map_err(|e| format!("Copie impossible : {}", e))?;
    let mut perms = fs::metadata(&dest)
        .map_err(|e| e.to_string())?
        .permissions();
    perms.set_mode(0o755);
    fs::set_permissions(&dest, perms).map_err(|e| e.to_string())?;

    phase(app, "Création de l'entrée de menu…");
    let stem = dest
        .file_stem()
        .map(|s| s.to_string_lossy().to_string())
        .unwrap_or_else(|| "clickpart-app".into());

    let mut icon_line = String::new();
    let tmp = std::env::temp_dir().join(format!("clickpart-icon-{}", std::process::id()));
    let _ = fs::create_dir_all(&tmp);
    let extract = Command::new(&dest)
        .arg("--appimage-extract")
        .arg(".DirIcon")
        .current_dir(&tmp)
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .status();
    if extract.map(|s| s.success()).unwrap_or(false) {
        let extracted = tmp.join("squashfs-root").join(".DirIcon");
        if extracted.is_file() {
            let _ = fs::create_dir_all(icons_dir());
            let icon_dest = icons_dir().join(format!("{}.png", stem));
            if fs::copy(&extracted, &icon_dest).is_ok() {
                icon_line = format!("Icon={}\n", icon_dest.to_string_lossy());
            }
        }
    }
    let _ = fs::remove_dir_all(&tmp);

    if icon_line.is_empty() {
        icon_line = "Icon=application-x-executable\n".into();
    }

    let desktop = format!(
        "[Desktop Entry]\nType=Application\nName={}\nComment=Installé par Clickpart\nExec=\"{}\" %f\n{}Terminal=false\nCategories=Utility;\n",
        stem,
        dest.to_string_lossy(),
        icon_line
    );
    let apps = applications_dir();
    fs::create_dir_all(&apps).map_err(|e| e.to_string())?;
    let desktop_path = apps.join(format!("{}.desktop", stem));
    fs::write(&desktop_path, desktop).map_err(|e| e.to_string())?;
    let _ = Command::new("update-desktop-database")
        .arg(&apps)
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .status();

    Ok(InstallResult {
        success: true,
        message: format!(
            "AppImage installée dans {}. Entrée de menu : {}",
            dest.display(),
            desktop_path.display()
        ),
        details: format!(
            "Binaire : {}\nEntrée : {}\nLancez-la depuis le menu ou avec : {}",
            dest.display(),
            desktop_path.display(),
            shell_quote(&dest.to_string_lossy())
        ),
    })
}

fn install_flatpak(app: &AppHandle, path: &str, scope: &str) -> Result<InstallResult, String> {
    if !has_cmd("flatpak") {
        return Err("flatpak n'est pas installé sur ce système.".into());
    }
    let scope_flag = if scope == "system" { "--system" } else { "--user" };
    phase(app, "Installation Flatpak…");
    let args = vec![
        "install".to_string(),
        scope_flag.to_string(),
        "-y".to_string(),
        "--noninteractive".to_string(),
        path.to_string(),
    ];
    let (code, tail) = run_stream(app, "flatpak", &args, None)?;
    if code == 0 {
        Ok(InstallResult {
            success: true,
            message: "Application Flatpak installée.".into(),
            details: tail,
        })
    } else {
        Ok(InstallResult {
            success: false,
            message: format!("flatpak a échoué (code {}).", code),
            details: tail,
        })
    }
}

fn extract_archive(app: &AppHandle, path: &str, dest: &Path) -> Result<(), String> {
    let lower = path.to_lowercase();
    let dest_s = dest.to_string_lossy().to_string();

    let result = if lower.ends_with(".zip") {
        if !has_cmd("unzip") {
            return Err("unzip est introuvable.".into());
        }
        run_stream(
            app,
            "unzip",
            &["-o".to_string(), path.to_string(), "-d".to_string(), dest_s],
            None,
        )
    } else if lower.ends_with(".7z") {
        if !has_cmd("7z") {
            return Err("7z est introuvable (paquet p7zip).".into());
        }
        run_stream(
            app,
            "7z",
            &["x".to_string(), "-y".to_string(), format!("-o{}", dest_s), path.to_string()],
            None,
        )
    } else {
        run_stream(
            app,
            "tar",
            &[
                "-xf".to_string(),
                path.to_string(),
                "-C".to_string(),
                dest_s,
            ],
            None,
        )
    }?;

    if result.0 == 0 {
        Ok(())
    } else {
        Err(format!("Extraction échouée (code {}).\n{}", result.0, result.1))
    }
}

fn find_desktop_file(root: &Path) -> Option<PathBuf> {
    let mut stack = vec![root.to_path_buf()];
    let mut depth = 0;
    while let Some(dir) = stack.pop() {
        depth += 1;
        if depth > 200 {
            break;
        }
        if let Ok(entries) = fs::read_dir(&dir) {
            for entry in entries.flatten() {
                let p = entry.path();                if p.is_dir() {
                    stack.push(p);
                } else if p.extension().map(|e| e == "desktop").unwrap_or(false) {
                    return Some(p);
                }
            }
        }
    }
    None
}

// Heuristique pour les archives sans .desktop : binaire principal à la racine.
fn find_main_executable(root: &Path) -> Option<PathBuf> {
    let hint = root
        .file_name()
        .map(|n| n.to_string_lossy().to_lowercase())
        .unwrap_or_default();
    let mut candidates: Vec<(String, PathBuf)> = Vec::new();
    for entry in fs::read_dir(root).ok()?.flatten() {
        let path = entry.path();
        let name = match path.file_name() {
            Some(n) => n.to_string_lossy().to_string(),
            None => continue,
        };
        let lower = name.to_lowercase();
        let is_exec = entry
            .metadata()
            .map(|m| m.is_file() && m.permissions().mode() & 0o111 != 0)
            .unwrap_or(false);
        if !is_exec
            || name.starts_with('.')
            || lower.starts_with("lib")
            || lower.ends_with(".so")
            || lower.ends_with(".sh")
        {
            continue;
        }
        candidates.push((lower, path));
    }
    // Le nom le plus proche de celui de l'archive, sinon le plus long.
    candidates.sort_by_key(|(lower, _)| (hint.contains(lower), lower.len()));
    candidates.pop().map(|(_, path)| path)
}

fn find_icon(root: &Path) -> Option<PathBuf> {
    let mut stack = vec![(root.to_path_buf(), 0usize)];
    while let Some((dir, depth)) = stack.pop() {
        if depth > 3 {
            continue;
        }
        let entries = match fs::read_dir(&dir) {
            Ok(e) => e,
            Err(_) => continue,
        };
        for entry in entries.flatten() {
            let path = entry.path();
            if path.is_dir() {
                stack.push((path, depth + 1));
                continue;
            }
            let ext = path
                .extension()
                .map(|e| e.to_string_lossy().to_lowercase())
                .unwrap_or_default();
            if ["png", "svg", "xpm"].contains(&ext.as_str()) {
                return Some(path);
            }
        }
    }
    None
}

fn write_desktop_entry(name: &str, exec: &Path, icon: &str) -> Result<PathBuf, String> {
    let apps = applications_dir();
    fs::create_dir_all(&apps).map_err(|e| e.to_string())?;
    let target = apps.join(format!("{}.desktop", sanitize(name)));
    let content = format!(
        "[Desktop Entry]\nType=Application\nName={}\nComment=Installé par Clickpart\nExec=\"{}\"\nIcon={}\nTerminal=false\nCategories=Utility;\n",
        name,
        exec.to_string_lossy(),
        icon
    );
    fs::write(&target, content).map_err(|e| e.to_string())?;
    let _ = Command::new("update-desktop-database")
        .arg(&apps)
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .status();
    Ok(target)
}

fn install_archive(app: &AppHandle, path: &str) -> Result<InstallResult, String> {
    let src = Path::new(path);
    let stem = src
        .file_name()
        .map(|n| n.to_string_lossy().to_string())
        .unwrap_or_else(|| "archive".into());
    let stem = stem
        .split(".tar")
        .next()
        .unwrap_or(&stem)
        .trim_end_matches(".zip")
        .trim_end_matches(".7z")
        .to_string();
    let stem = sanitize(&stem);

    let dest = home().join(".local/opt").join(&stem);
    fs::create_dir_all(&dest).map_err(|e| e.to_string())?;

    phase(app, "Extraction de l'archive…");
    extract_archive(app, path, &dest)?;

    let mut desktop_msg = String::new();
    if let Some(desktop) = find_desktop_file(&dest) {
        phase(app, "Création de l'entrée de menu…");
        let apps = applications_dir();
        let _ = fs::create_dir_all(&apps);
        let target = apps.join(
            desktop
                .file_name()
                .map(|n| n.to_string_lossy().to_string())
                .unwrap_or_else(|| format!("{}.desktop", stem)),
        );

        let content = fs::read_to_string(&desktop).unwrap_or_default();
        let mut fixed = String::new();
        for line in content.lines() {
            if let Some(exec) = line.strip_prefix("Exec=") {
                let first = exec.split_whitespace().next().unwrap_or("");
                let candidate = dest.join(first);
                if !first.starts_with('/') && candidate.is_file() {
                    fixed.push_str(&format!(
                        "Exec={} {}\n",
                        shell_quote(&candidate.to_string_lossy()),
                        exec.split_whitespace().skip(1).collect::<Vec<_>>().join(" ")
                    ));
                    continue;
                }
            }
            fixed.push_str(line);
            fixed.push('\n');
        }
        if fs::write(&target, fixed).is_ok() {
            let _ = Command::new("update-desktop-database")
                .arg(&apps)
                .stdout(Stdio::null())
                .stderr(Stdio::null())
                .status();
            desktop_msg = format!("\nEntrée de menu : {}", target.display());
        }
    }

    if desktop_msg.is_empty() {
        phase(app, "Création de l'entrée de menu…");
        if let Some(bin) = find_main_executable(&dest) {
            let name = bin
                .file_name()
                .map(|n| n.to_string_lossy().to_string())
                .unwrap_or_else(|| stem.clone());
            let icon = find_icon(&dest)
                .map(|p| p.to_string_lossy().to_string())
                .unwrap_or_else(|| "application-x-executable".into());
            if let Ok(target) = write_desktop_entry(&name, &bin, &icon) {
                desktop_msg = format!("\nEntrée de menu : {}", target.display());
            }
        }
    }

    Ok(InstallResult {
        success: true,
        message: format!("Archive extraite dans {}.{}", dest.display(), desktop_msg),
        details: format!(
            "Dossier : {}\n{}",
            dest.display(),
            if desktop_msg.is_empty() {
                "Aucun exécutable trouvé : lancez le programme manuellement.".to_string()
            } else {
                desktop_msg.clone()
            }
        ),
    })
}

fn install_pkgbuild(app: &AppHandle, path: &str) -> Result<InstallResult, String> {
    if !has_cmd("makepkg") {
        return Err("makepkg est introuvable (paquet base-devel).".into());
    }
    let p = Path::new(path);
    let dir = if p.is_dir() {
        p.to_path_buf()
    } else {
        p.parent().unwrap_or(Path::new(".")).to_path_buf()
    };
    if !dir.join("PKGBUILD").is_file() {
        return Err("Aucun PKGBUILD trouvé dans ce dossier.".into());
    }

    phase(app, "Compilation avec makepkg…");
    let args = vec!["-s".to_string(), "--noconfirm".to_string(), "--needed".to_string()];
    let (code, tail) = run_stream(app, "makepkg", &args, Some(&dir))?;
    if code != 0 {
        return Ok(InstallResult {
            success: false,
            message: format!("makepkg a échoué (code {}).", code),
            details: tail,
        });
    }

    let pkg = fs::read_dir(&dir)
        .ok()
        .into_iter()
        .flatten()
        .flatten()
        .map(|e| e.path())
        .filter(|p| {
            p.file_name()
                .map(|n| n.to_string_lossy().contains(".pkg.tar."))
                .unwrap_or(false)
        })
        .max_by_key(|p| fs::metadata(p).and_then(|m| m.modified()).ok());

    let pkg = match pkg {
        Some(p) => p,
        None => {
            return Ok(InstallResult {
                success: false,
                message: "Aucun paquet produit par makepkg.".into(),
                details: tail,
            })
        }
    };

    if !has_cmd("pkexec") {
        return Ok(InstallResult {
            success: true,
            message: format!("Paquet compilé : {}", pkg.display()),
            details: format!(
                "Compilation OK, mais pkexec est absent. Installez manuellement :\nsudo pacman -U {}",
                shell_quote(&pkg.to_string_lossy())
            ),
        });
    }

    phase(app, "Installation du paquet compilé…");
    let args = vec![
        "pacman".to_string(),
        "-U".to_string(),
        "--noconfirm".to_string(),
        pkg.to_string_lossy().to_string(),
    ];
    let (code, tail2) = run_stream(app, "pkexec", &args, None)?;
    Ok(InstallResult {
        success: code == 0,
        message: if code == 0 {
            "Paquet compilé et installé.".into()
        } else {
            format!("Installation échouée (code {}).", code)
        },
        details: format!("{}\n{}", tail, tail2),
    })
}

fn launch_jar(app: &AppHandle, path: &str) -> Result<InstallResult, String> {
    if !has_cmd("java") {
        return Err("java est introuvable.".into());
    }
    phase(app, "Lancement de l'application Java…");
    spawn_detached("java", &["-jar".to_string(), path.to_string()])?;
    Ok(InstallResult {
        success: true,
        message: "Application Java lancée.".into(),
        details: format!("java -jar {}", shell_quote(path)),
    })
}

fn install_vsix(app: &AppHandle, path: &str) -> Result<InstallResult, String> {
    if !has_cmd("code") {
        return Err("Visual Studio Code (code) est introuvable.".into());
    }
    phase(app, "Installation de l'extension VS Code…");
    let args = vec![
        "--install-extension".to_string(),
        path.to_string(),
        "--force".to_string(),
    ];
    let (code, tail) = run_stream(app, "code", &args, None)?;
    Ok(InstallResult {
        success: code == 0,
        message: if code == 0 {
            "Extension installée.".into()
        } else {
            format!("code a échoué (code {}).", code)
        },
        details: tail,
    })
}

fn launch_wine(app: &AppHandle, path: &str) -> Result<InstallResult, String> {
    if !has_cmd("wine") {
        return Err("wine est introuvable.".into());
    }
    phase(app, "Lancement avec Wine…");
    spawn_detached("wine", &[path.to_string()])?;
    Ok(InstallResult {
        success: true,
        message: "Installeur Windows lancé avec Wine.".into(),
        details: format!("wine {}", shell_quote(path)),
    })
}

#[tauri::command]
async fn install(app: AppHandle, path: String, format: String, scope: String) -> Result<InstallResult, String> {
    let app_for_task = app.clone();
    let path_for_task = path.clone();
    let format_for_task = format.clone();

    let outcome = tauri::async_runtime::spawn_blocking(move || {
        let app = app_for_task;
        match format_for_task.as_str() {
            "pacman" => install_pacman(&app, &path_for_task),
            "appimage" => install_appimage(&app, &path_for_task),
            "flatpakref" | "flatpak" => install_flatpak(&app, &path_for_task, &scope),
            "archive" => install_archive(&app, &path_for_task),
            "pkgbuild" => install_pkgbuild(&app, &path_for_task),
            "jar" => launch_jar(&app, &path_for_task),
            "vsix" => install_vsix(&app, &path_for_task),
            "windows" => launch_wine(&app, &path_for_task),
            "run" => Err(
                "Les scripts .run sont interactifs : lancez-le dans un terminal avec « sh fichier.run »."
                    .to_string(),
            ),
            "deb" => Err("Les paquets .deb ne sont pas installables sur Arch Linux.".to_string()),
            "rpm" => Err("Les paquets .rpm ne sont pas installables sur Arch Linux.".to_string()),
            "snap" => Err("Les paquets .snap ne sont pas installables sur Arch Linux.".to_string()),
            _ => Err("Format non pris en charge.".to_string()),
        }
    })
    .await
    .map_err(|e| format!("Tâche interrompue : {}", e))?;

    let (status, message) = match &outcome {
        Ok(r) if r.success => ("success", r.message.clone()),
        Ok(r) => ("error", r.message.clone()),
        Err(e) => ("error", e.clone()),
    };
    append_history(HistoryEntry {
        timestamp: now_string(),
        file: path.clone(),
        format,
        status: status.into(),
        message,
    });

    outcome
}

// ---------------------------------------------------------------------------
// Entree
// ---------------------------------------------------------------------------

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![
            detect_format,
            startup_file,
            system_info,
            list_installed,
            uninstall_app,
            install,
            get_config,
            save_config,
            get_history,
            clear_history,
            open_url,
            update_app
        ])
        .run(tauri::generate_context!())
        .expect("Erreur au lancement de Clickpart");
}

#[cfg(test)]
mod tests {
    use super::*;

    fn temp_path(name: &str) -> PathBuf {
        std::env::temp_dir().join(format!("clickpart-test-{}-{}", std::process::id(), name))
    }

    #[test]
    fn sanitize_replaces_unsafe_characters() {
        assert_eq!(sanitize("app image/1.0.AppImage"), "app_image_1.0.AppImage");
        assert_eq!(sanitize("déjà-vu+ok"), "d_j_-vu+ok");
    }

    #[test]
    fn detect_appimage_is_supported() {
        let path = temp_path("sample.AppImage");
        fs::write(&path, b"test").unwrap();

        let info = detect_inner(path.to_str().unwrap(), true, false, false).unwrap();

        assert_eq!(info.format, "appimage");
        assert!(info.supported);
        assert!(!info.needs_root);
        assert_eq!(info.size, 4);
        let _ = fs::remove_file(&path);
    }

    #[test]
    fn detect_deb_is_incompatible_on_arch() {
        let path = temp_path("sample.deb");
        fs::write(&path, b"test").unwrap();

        let info = detect_inner(path.to_str().unwrap(), true, false, false).unwrap();

        assert_eq!(info.format, "deb");
        assert!(!info.supported);
        assert!(!info.distro_compatible);
        assert!(info.distro_notes.is_some());
        let _ = fs::remove_file(&path);
    }

    #[test]
    fn detect_pkgbuild_directory() {
        let dir = temp_path("pkgbuild-dir");
        fs::create_dir_all(&dir).unwrap();
        fs::write(dir.join("PKGBUILD"), b"pkgname=test").unwrap();

        let info = detect_inner(dir.to_str().unwrap(), true, false, false).unwrap();

        assert_eq!(info.format, "pkgbuild");
        assert!(info.supported);
        assert!(info.needs_root);
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn find_main_executable_prefers_name_matching_archive() {
        let dir = temp_path("unigetui-1.0");
        fs::create_dir_all(dir.join("Assets")).unwrap();
        for (name, mode) in [("uniget", 0o755), ("UniGetUI", 0o755), ("libSkiaSharp.so", 0o755), ("readme.txt", 0o644)] {
            let p = dir.join(name);
            fs::write(&p, b"x").unwrap();
            fs::set_permissions(&p, fs::Permissions::from_mode(mode)).unwrap();
        }

        let found = find_main_executable(&dir).unwrap();
        assert_eq!(found.file_name().unwrap(), "UniGetUI");

        fs::remove_file(dir.join("UniGetUI")).unwrap();
        assert_eq!(find_main_executable(&dir).unwrap().file_name().unwrap(), "uniget");
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn find_icon_finds_nested_image() {
        let dir = temp_path("icon-nested");
        fs::create_dir_all(dir.join("Assets")).unwrap();
        fs::write(dir.join("Assets/logo.png"), b"x").unwrap();

        assert_eq!(find_icon(&dir).unwrap(), dir.join("Assets/logo.png"));
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn exec_program_handles_quotes_and_field_codes() {
        assert_eq!(
            exec_program("\"/home/u/.local/bin/My App\" %f").as_deref(),
            Some("/home/u/.local/bin/My App")
        );
        assert_eq!(exec_program("'/opt/x/y' --flag").as_deref(), Some("/opt/x/y"));
        assert_eq!(exec_program("/usr/bin/foo --bar").as_deref(), Some("/usr/bin/foo"));
        assert_eq!(desktop_field("[Desktop Entry]\nName=MyApp\n", "Name=").as_deref(), Some("MyApp"));
    }

    #[test]
    fn confined_target_only_allows_clickpart_paths() {
        let root = temp_path("confined");
        let opt = root.join(".local/opt");
        let bin = root.join(".local/bin");
        fs::create_dir_all(opt.join("MyApp")).unwrap();
        fs::create_dir_all(&bin).unwrap();
        let app_bin = bin.join("myapp");
        fs::write(&app_bin, b"x").unwrap();

        assert_eq!(confined_target(&app_bin, &opt, &bin), Some(app_bin));
        assert_eq!(
            confined_target(&opt.join("MyApp/MyApp"), &opt, &bin),
            Some(opt.join("MyApp"))
        );
        assert_eq!(confined_target(Path::new("/usr/bin/ls"), &opt, &bin), None);
        let _ = fs::remove_dir_all(&root);
    }

    #[test]
    fn detect_unknown_extension() {
        let path = temp_path("sample.unknown");
        fs::write(&path, b"test").unwrap();

        let info = detect_inner(path.to_str().unwrap(), true, false, false).unwrap();

        assert_eq!(info.format, "unknown");
        assert!(!info.supported);
        let _ = fs::remove_file(&path);
    }
}

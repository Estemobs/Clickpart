# Task 4 Report — Update docs / changelog (Clickpart v0.5)

- Plan: Clickpart v0.5 (docs/superpowers/plans/2026-10-28-clickpart-v0.5.md)
- Date: 2026-10-28
- Constraint: Python 3, GPL-3; no destructive ops.

## BASE
`1f8239ad69132425096e562caebad35217dda90e` (HEAD before this task; matches task-2 / task-3 reports)

## Changes / actions
- Updated `CHANGELOG.md`: added `[0.4.0]` (polkit durci, `.run` alertes, historique UI, AUR PKGBUILD) and `[0.5.0]` (tests detect.py, AppImage validation, PKGBUILD local, docs update) with links.
- Updated `TODO.md`: marked "ce qui a marché" with v0.5 results (task 1 PASS, task 2 PARTIAL, task 3 PARTIAL); updated prochaine étape and questions ouvertes with `Adw`/containeur note.
- Updated `docs/status-v0.4.md`: expanded to v0.4/v0.5 state, results (tests PASS, AppImage validated partial, PKGBUILD partial), open follow-up (history rotation, flatpak fallback, `update-desktop-database`, end-to-end GUI).
- Committed: `73005a7`.

## Status
COMPLETE — docs / changelog updated; commit made; no destructive operations.

## Results
- CHANGELOG: v0.4 and v0.5 sections present with Added/Changed/Security/Fixed and release links.
- TODO: completed items clearly tagged; next steps reflect actual state (AppImage partial, PKGBUILD partial due to Debian/missing Arch toolchain).
- docs/status-v0.4.md: version notes from 0c8f726 → 1f8239a; checkboxes for task 1/2/3/4; review notes for src/.

## Concerns / follow-up
- `docs/` directory had `docs/superpowers/` and `docs/status-v0.4.md` already tracked; edit recreated `docs/status-v0.4.md` (same path) — fine, no data loss.
- `gitea-mcp/` untracked subdirectory caused `git add -A` failure; resolved by adding only target files explicitly.
- No changes to source code; pure documentation task.

## Commit
- Before: `1f8239ad69132425096e562caebad35218dda90e`
- After: `73005a7`

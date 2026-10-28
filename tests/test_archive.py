import io
import sys
import tarfile
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from backends.archive import ArchiveBackend  # noqa: E402


def test_desktop_install_updates_desktop_database(monkeypatch, tmp_path):
    """The desktop entry install must not fail on a missing module import."""
    import subprocess

    calls = []

    def fake_run(args, **kwargs):
        calls.append((args, kwargs))
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    executable = src_dir / "app"
    executable.write_text("#!/bin/sh\n")
    executable.chmod(0o755)
    desktop = src_dir / "app.desktop"
    desktop.write_text("[Desktop Entry]\nExec=app\n")

    ok, message = ArchiveBackend()._install_desktop_app(src_dir, desktop, executable, "testapp")

    assert ok, message
    assert calls, "update-desktop-database should have been called"
    assert calls[0][0] == ["update-desktop-database", str(tmp_path / ".local/share/applications")]


def test_extract_rejects_tar_path_traversal(tmp_path):
    archive = tmp_path / "evil.tar"
    with tarfile.open(archive, "w") as tf:
        info = tarfile.TarInfo("../escape.txt")
        data = b"owned"
        info.size = len(data)
        tf.addfile(info, io.BytesIO(data))

    dest = tmp_path / "dest"
    dest.mkdir()

    with pytest.raises(ValueError):
        ArchiveBackend()._extract_archive(archive, dest)

    assert not (tmp_path / "escape.txt").exists()


def test_extract_rejects_zip_path_traversal(tmp_path):
    archive = tmp_path / "evil.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr(zipfile.ZipInfo("../escape.txt"), b"owned")

    dest = tmp_path / "dest"
    dest.mkdir()

    with pytest.raises(ValueError):
        ArchiveBackend()._extract_archive(archive, dest)

    assert not (tmp_path / "escape.txt").exists()


def test_extract_accepts_normal_archive(tmp_path):
    archive = tmp_path / "ok.tar"
    with tarfile.open(archive, "w") as tf:
        info = tarfile.TarInfo("ok.txt")
        data = b"hello"
        info.size = len(data)
        tf.addfile(info, io.BytesIO(data))

    dest = tmp_path / "dest"
    dest.mkdir()
    ArchiveBackend()._extract_archive(archive, dest)

    assert (dest / "ok.txt").read_bytes() == b"hello"

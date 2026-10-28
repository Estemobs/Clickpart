#!/usr/bin/env python3
"""Tests for format detection (Task 1)."""
import sys
sys.path.insert(0, "src")

from pathlib import Path
import tempfile
import os

from detect import detect_file, FormatDetector


def test_detect_file_flatpakref():
    with tempfile.NamedTemporaryFile(suffix=".flatpakref", delete=False) as f:
        f.write(b"[Flatpak Ref]\nName=test\n")
        path = f.name
    try:
        result = detect_file(path)
        assert isinstance(result, dict), "detect_file must return dict"
        assert result["format"] == "flatpakref", f"Expected flatpakref, got {result['format']}"
        assert result["detected"] is True
        assert result["path"] == str(Path(path).resolve())
        print("PASS: detect_file .flatpakref")
    finally:
        os.unlink(path)


def test_detect_file_pkg_tar_zst():
    with tempfile.NamedTemporaryFile(suffix=".pkg.tar.zst", delete=False) as f:
        f.write(b"fake package content")
        path = f.name
    try:
        result = detect_file(path)
        assert isinstance(result, dict), "detect_file must return dict"
        assert result["format"] == "pacman", f"Expected pacman, got {result['format']}"
        assert result["detected"] is True
        print("PASS: detect_file .pkg.tar.zst")
    finally:
        os.unlink(path)


def test_detect_file_unknown():
    with tempfile.NamedTemporaryFile(suffix=".unknownxyz", delete=False) as f:
        f.write(b"nope")
        path = f.name
    try:
        result = detect_file(path)
        assert result["format"] is None or result["format"] == "unknownxyz"
        assert isinstance(result, dict)
        print("PASS: detect_file unknown")
    finally:
        os.unlink(path)


if __name__ == "__main__":
    test_detect_file_flatpakref()
    test_detect_file_pkg_tar_zst()
    test_detect_file_unknown()
    print("\nAll task-1 detect tests passed.")

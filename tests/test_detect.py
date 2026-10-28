#!/usr/bin/env python3
"""Tests for format detection."""

import sys
sys.path.insert(0, "src")

from pathlib import Path
import tempfile
import os

from detect import FormatDetector


def test_detect_by_extension():
    det = FormatDetector()
    with tempfile.NamedTemporaryFile(suffix=".pkg.tar.zst", delete=False) as f:
        f.write(b"fake package content")
        path = Path(f.name)
    
    result = det.detect(path)
    assert result == "pacman", f"Expected pacman, got {result}"
    
    path.unlink()
    print("PASS: detect_by_extension .pkg.tar.zst")


def test_detect_flatpakref():
    det = FormatDetector()
    with tempfile.NamedTemporaryFile(suffix=".flatpakref", delete=False) as f:
        f.write(b"[Flatpak Ref]\nName=test\n")
        path = Path(f.name)
    
    result = det.detect(path)
    assert result == "flatpakref", f"Expected flatpakref, got {result}"
    
    path.unlink()
    print("PASS: detect_flatpakref")


def test_appimage_by_extension():
    det = FormatDetector()
    with tempfile.NamedTemporaryFile(suffix=".AppImage", delete=False) as f:
        # Write minimal AppImage magic header
        f.write(b"AI\x02\x00\x00\x00")
        path = Path(f.name)
    
    result = det.detect(path)
    # Should detect as appimage either by extension or magic
    assert result in ("appimage", "appimage"), f"Expected appimage, got {result}"
    
    path.unlink()
    print("PASS: appimage_by_extension")


if __name__ == "__main__":
    test_detect_by_extension()
    test_detect_flatpakref()
    test_appimage_by_extension()
    print("\nAll detect tests passed.")

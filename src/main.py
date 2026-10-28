#!/usr/bin/env python3
"""
Clickpak - Universal graphical installer for Linux
Double-click .flatpakref, .AppImage, .pkg.tar.zst and more to install them.
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from detect import FormatDetector
from backends import get_backend
from ui.confirm_dialog import ConfirmDialog
from ui.progress_dialog import ProgressDialog
from config import Config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Clickpak:
    def __init__(self):
        self.config = Config()
        self.detector = FormatDetector()
        self.history_file = Path.home() / ".local" / "state" / "clickpak" / "history.log"
        self.history_file.parent.mkdir(parents=True, exist_ok=True)

    def log_installation(self, file_path: str, format_type: str, command: list, success: bool, output: str):
        """Log installation attempt to history file."""
        import datetime
        timestamp = datetime.datetime.now().isoformat()
        with open(self.history_file, "a") as f:
            f.write(f"[{timestamp}] {file_path} | {format_type} | {'SUCCESS' if success else 'FAILED'} | {' '.join(command)}\n")
            if output:
                f.write(f"  Output: {output[:500]}\n")

    def run(self, file_path: str) -> int:
        """Main entry point for installing a file."""
        path = Path(file_path).resolve()
        
        if not path.exists():
            logger.error(f"File not found: {path}")
            return 1

        # Detect format
        format_type = self.detector.detect(path)
        if not format_type:
            logger.error(f"Unsupported file format: {path}")
            return 1

        logger.info(f"Detected format: {format_type} for {path}")

        # Get backend
        backend = get_backend(format_type)
        if not backend:
            logger.error(f"No backend for format: {format_type}")
            return 1

        # Get description and command
        description = backend.describe(path)
        command = backend.get_install_command(path)
        requires_root = backend.requires_root()

        logger.info(f"Install command: {' '.join(command)}")

        # Check if silent mode is enabled for this format
        silent = self.config.is_silent(format_type)
        
        if not silent:
            # Show confirmation dialog
            dialog = ConfirmDialog(
                file_path=str(path),
                format_type=format_type,
                description=description,
                command=command,
                requires_root=requires_root
            )
            response = dialog.run()
            if response != "install":
                logger.info("Installation cancelled by user")
                return 0

        # Run installation with progress dialog
        progress = ProgressDialog(
            title=f"Installing {path.name}",
            command=command,
            requires_root=requires_root
        )
        success, output = progress.run()

        # Log the installation
        self.log_installation(str(path), format_type, command, success, output)

        if success:
            logger.info("Installation successful")
            return 0
        else:
            logger.error(f"Installation failed: {output}")
            return 1


def main():
    parser = argparse.ArgumentParser(description="Clickpak - Universal graphical installer for Linux")
    parser.add_argument("file", nargs="?", help="File to install")
    parser.add_argument("--config", action="store_true", help="Open configuration window")
    parser.add_argument("--version", action="store_true", help="Show version")
    args = parser.parse_args()

    if args.version:
        print("Clickpak 0.1.0")
        return 0

    app = Clickpak()

    if args.config:
        # TODO: Open config window
        print("Configuration window not yet implemented")
        return 0

    if not args.file:
        parser.print_help()
        return 1

    return app.run(args.file)


if __name__ == "__main__":
    sys.exit(main())
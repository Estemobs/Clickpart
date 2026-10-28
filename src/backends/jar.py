#!/usr/bin/env python3
"""
JAR backend for .jar files.
"""

from pathlib import Path
from typing import List
from . import BaseBackend


class JarBackend(BaseBackend):
    format_type = "jar"
    format_name = "Java Application"
    extensions = [".jar"]
    
    def can_handle(self, path: Path) -> bool:
        return path.name.lower().endswith(".jar")
    
    def describe(self, path: Path) -> str:
        return f"Java application: {path.name}"
    
    def get_install_command(self, path: Path) -> List[str]:
        return ["java", "-jar", str(path)]
    
    def requires_root(self) -> bool:
        return False
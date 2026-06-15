"""
Per-OS default filesystem locations for PostMule.

Windows keeps its existing locations (%APPDATA% for config search,
%PROGRAMDATA%\\PostMule for the install/data directory) so existing
installs are unaffected. macOS and Linux get equivalent platform-native
defaults instead of the Windows-only paths previously hardcoded in
cli.py and pipeline.py.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "PostMule"


def user_config_dir() -> Path:
    """Per-OS directory to search for config.yaml on a standard install."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA")
        return Path(base) / APP_NAME if base else Path.home() / "AppData" / "Roaming" / APP_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    base = os.environ.get("XDG_CONFIG_HOME")
    return Path(base) / APP_NAME if base else Path.home() / ".config" / APP_NAME


def default_install_dir() -> Path:
    """Per-OS default install/data directory (config, credentials, logs, files)."""
    if sys.platform == "win32":
        base = os.environ.get("PROGRAMDATA", "C:\\ProgramData")
        return Path(base) / APP_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    base = os.environ.get("XDG_DATA_HOME")
    return Path(base) / APP_NAME if base else Path.home() / ".local" / "share" / APP_NAME

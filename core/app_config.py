"""Persistence for DescentBuddy application preferences.

Settings are stored as JSON in the platform user config directory.
The config file is created on first save; missing keys return their defaults.
"""

import json
import os
import sys
from pathlib import Path


def _config_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path.home() / ".config"
    return base / "descentbuddy"


_CONFIG_FILE = _config_dir() / "config.json"


def load_config() -> dict:
    if not _CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_config(data: dict) -> None:
    _CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    _CONFIG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

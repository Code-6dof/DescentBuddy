"""Detect the version of a DXX-Redux executable."""

import os
import re
import subprocess
import sys
from pathlib import Path

# Patterns that DXX-Redux / DXX-Rebirth-family ports emit on --version
_VERSION_PATTERNS = [
    re.compile(r"[Dd][1-2][Xx][-\s][\w]+\s+([\d.]+[\w-]*)"),
    re.compile(r"version\s+([\d.]+[\w.-]*)", re.IGNORECASE),
    re.compile(r"([\d]+\.[\d]+\.[\d]+[\w.-]*)"),
]


def detect_version(executable_path: str) -> str:
    """Return a version string for the given DXX-Redux executable.

    Returns 'Unknown' if detection fails.
    """
    path = Path(executable_path)
    if not path.is_file():
        return "File not found"

    # Try running with --version flag
    env = os.environ.copy()
    # AppImages require FUSE to mount; APPIMAGE_EXTRACT_AND_RUN bypasses that
    if path.suffix.lower() == ".appimage":
        env["APPIMAGE_EXTRACT_AND_RUN"] = "1"

    if sys.platform != "win32":
        # Prevent the game from opening a window during version detection.
        # SDL checks SDL_VIDEODRIVER first; setting it to "dummy" keeps it
        # headless.  Clearing DISPLAY/WAYLAND_DISPLAY adds a second layer of
        # protection for non-SDL display init.
        env["SDL_VIDEODRIVER"] = "dummy"
        env["DISPLAY"] = ""
        env["WAYLAND_DISPLAY"] = ""

    for flag in ("--version", "-version", "-v"):
        try:
            result = subprocess.run(
                [str(path), flag],
                capture_output=True,
                text=True,
                timeout=10,
                env=env,
            )
            output = (result.stdout + result.stderr).strip()
            if output:
                version = _parse_version(output)
                if version:
                    return version
        except (subprocess.TimeoutExpired, OSError, PermissionError):
            continue

    # Fallback: scan binary for embedded version strings
    return _scan_binary(path)


def _parse_version(text: str) -> str:
    """Extract a version token from free-form text."""
    for pattern in _VERSION_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(1)
    # Return first non-empty line as last resort
    first_line = text.splitlines()[0].strip() if text else ""
    return first_line[:64] if first_line else ""


def _scan_binary(path: Path) -> str:
    """Scan the binary file for an embedded version string."""
    try:
        data = path.read_bytes()
        # Look for null-terminated ASCII version patterns in the binary
        pattern = re.compile(rb"(\d+\.\d+\.\d+[\w.\-]*)")
        matches = pattern.findall(data)
        for raw in matches:
            candidate = raw.decode("ascii", errors="ignore")
            # Filter out unlikely matches (too long, or all zeros)
            if 3 <= len(candidate) <= 20 and not candidate.startswith("0.0.0"):
                return candidate
    except (OSError, PermissionError):
        pass
    return "Unknown"

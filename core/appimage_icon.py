"""AppImage icon extraction utilities."""

import os
import subprocess
import tempfile
from pathlib import Path


def extract_appimage_icon(appimage_path: str, dest_dir: str) -> str | None:
    """Extract the primary icon PNG from an AppImage into dest_dir.

    Uses --appimage-extract with APPIMAGE_EXTRACT_AND_RUN=1 so no FUSE is needed.
    Returns the absolute path to the best icon PNG, or None on failure.
    """
    path = Path(appimage_path)
    if not (path.is_file() and path.suffix.lower() == ".appimage"):
        return None

    env = os.environ.copy()
    env["APPIMAGE_EXTRACT_AND_RUN"] = "1"

    # Extract the icons directory — this contains real files, not broken symlinks
    try:
        subprocess.run(
            [str(path), "--appimage-extract", "usr/share/icons"],
            capture_output=True,
            timeout=20,
            env=env,
            cwd=dest_dir,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None

    icons_root = Path(dest_dir) / "squashfs-root" / "usr" / "share" / "icons"
    if not icons_root.is_dir():
        return None

    # Prefer the largest available size (pick highest numeric dir name)
    best: Path | None = None
    best_size = 0
    for png in sorted(icons_root.rglob("*.png")):
        # Favour higher-resolution icons by parsing the size component from the path
        # e.g. hicolor/128x128/apps/foo.png → 128
        parts = png.parts
        size = 0
        for part in parts:
            if "x" in part:
                try:
                    size = int(part.split("x")[0])
                    break
                except ValueError:
                    pass
        if size > best_size or best is None:
            best_size = size
            best = png

    return str(best) if best else None


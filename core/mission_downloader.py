"""Installs DXMA mission archives into the local missions directory.

Install priority:
  1. Local archive (the user's dxma-files.zip) — zero network cost.
  2. Direct download URL from the DXMA server.

A mission zip contains HOG, MSN/MN2, and optionally TXT/image files.
All recognized files are extracted flat into missions_dir (no subdirectory).
"""

import io
import urllib.request
import zipfile
from pathlib import Path

_ARCHIVE_PATH_PREFIX = "https://sectorgame.com/dxma/files/"
_RECOGNIZED_SUFFIXES = {".hog", ".msn", ".mn2", ".txt"}
_TIMEOUT = 30


def _zip_internal_path(direct_download_url: str) -> str | None:
    """Convert a direct download URL to its path inside the local archive zip.

    Example:
      https://sectorgame.com/dxma/files/f/34/2076/tegralb.zip
      -> f/34/2076/tegralb.zip
    """
    if not direct_download_url.startswith(_ARCHIVE_PATH_PREFIX):
        return None
    return direct_download_url[len(_ARCHIVE_PATH_PREFIX):]


def _extract_mission_zip(zip_bytes: bytes, missions_dir: Path) -> list[Path]:
    """Extract mission files from a downloaded inner zip into missions_dir.

    Returns the list of paths that were written.
    """
    missions_dir.mkdir(parents=True, exist_ok=True)
    installed: list[Path] = []

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as inner:
        for member in inner.infolist():
            member_path = Path(member.filename)
            if member.is_dir():
                continue
            if member_path.suffix.lower() not in _RECOGNIZED_SUFFIXES:
                continue
            dest = missions_dir / member_path.name
            dest.write_bytes(inner.read(member.filename))
            installed.append(dest)

    return installed


def install_from_local_archive(
    local_archive_path: Path,
    direct_download_url: str,
    missions_dir: Path,
) -> tuple[bool, str]:
    """Extract a mission from the local dxma-files.zip archive.

    Returns (success, message).
    """
    zip_key = _zip_internal_path(direct_download_url)
    if not zip_key:
        return False, "URL does not match local archive path pattern."

    if not local_archive_path.exists():
        return False, f"Local archive not found: {local_archive_path.name}"

    try:
        with zipfile.ZipFile(local_archive_path) as outer:
            names = outer.namelist()
            if zip_key not in names:
                return False, f"Mission not found in local archive ({zip_key})."
            inner_bytes = outer.read(zip_key)
    except (zipfile.BadZipFile, KeyError, OSError) as exc:
        return False, f"Could not read local archive: {exc}"

    try:
        installed = _extract_mission_zip(inner_bytes, missions_dir)
    except (zipfile.BadZipFile, OSError) as exc:
        return False, f"Could not extract mission files: {exc}"

    if not installed:
        return False, "No recognized mission files found in the archive."

    return True, str(missions_dir)


def install_from_web(
    download_url: str,
    missions_dir: Path,
) -> tuple[bool, str]:
    """Download a mission zip from DXMA and extract it.

    Follows redirects automatically. Returns (success, message).
    """
    try:
        req = urllib.request.Request(
            download_url, headers={"User-Agent": "DescentBuddy/1.0"}
        )
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            zip_bytes = resp.read()
    except OSError as exc:
        return False, f"Download failed: {exc}"

    try:
        installed = _extract_mission_zip(zip_bytes, missions_dir)
    except (zipfile.BadZipFile, OSError) as exc:
        return False, f"Could not extract mission files: {exc}"

    if not installed:
        return False, "No recognized mission files found in the downloaded archive."

    return True, str(missions_dir)


def _resolve_direct_url(mission_id: int) -> str:
    """Fetch the mission page to find the direct download URL."""
    page_url = f"https://sectorgame.com/dxma/mission?m={mission_id}"
    try:
        req = urllib.request.Request(
            page_url, headers={"User-Agent": "DescentBuddy/1.0"}
        )
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except OSError:
        return ""
    import re
    match = re.search(
        r'href="(/dxma/files/[^"]+\.(?:zip|rar|7z))"', html, re.IGNORECASE
    )
    if not match:
        return ""
    return f"https://sectorgame.com{match.group(1)}"


def install_mission(
    entry: dict,
    missions_dir: Path,
    local_archive_path: Path | None,
) -> tuple[bool, str]:
    """Install a mission, preferring the local archive over a network download.

    Returns (success, message).
    """
    direct_url = entry.get("direct_download_url", "")
    download_url = entry.get("download_url", "")

    if local_archive_path and direct_url:
        zip_key = _zip_internal_path(direct_url)
        if zip_key:
            ok, msg = install_from_local_archive(local_archive_path, direct_url, missions_dir)
            if ok:
                return True, msg

    if direct_url:
        return install_from_web(direct_url, missions_dir)

    if not direct_url:
        direct_url = _resolve_direct_url(entry["id"])

    if direct_url:
        return install_from_web(direct_url, missions_dir)

    if download_url:
        return install_from_web(download_url, missions_dir)

    return False, "No download URL available for this mission."


def load_mission_image_bytes(archive_path: Path, mission_id: int) -> bytes | None:
    """Return raw bytes for the mission screenshot stored in the local archive.

    Images are stored at img/1/{mission_id}/{filename} inside dxma-files.zip.
    Returns None if no image is found or the archive cannot be read.
    """
    prefix = f"img/1/{mission_id}/"
    try:
        with zipfile.ZipFile(archive_path) as outer:
            candidates = [
                n for n in outer.namelist()
                if n.startswith(prefix) and not n.endswith("/")
            ]
            if not candidates:
                return None
            data = outer.read(candidates[0])
            return data if data else None
    except (KeyError, zipfile.BadZipFile, OSError):
        return None


def fetch_mission_image_from_web(mission_id: int, image_url: str = "") -> bytes | None:
    """Download the mission screenshot from sectorgame.com/dxma.

    Uses image_url if provided; otherwise fetches the mission page to find it.
    Returns raw image bytes, or None on failure.
    """
    if not image_url:
        page_url = f"https://sectorgame.com/dxma/mission?m={mission_id}"
        try:
            req = urllib.request.Request(
                page_url, headers={"User-Agent": "DescentBuddy/1.0"}
            )
            with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
                html = resp.read().decode("utf-8", errors="replace")
        except OSError:
            return None
        import re
        match = re.search(r'href="(/dxma/files/img/[^"]+)"', html)
        if not match:
            return None
        image_url = f"https://sectorgame.com{match.group(1)}"

    try:
        req = urllib.request.Request(
            image_url, headers={"User-Agent": "DescentBuddy/1.0"}
        )
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            return resp.read()
    except OSError:
        return None

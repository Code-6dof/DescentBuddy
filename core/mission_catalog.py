"""Manages the local DXMA mission catalog.

The catalog is seeded from data/missions_catalog.csv on first run and stored
as JSON at ~/.config/descentbuddy/missions_catalog.json. Each entry records
mission metadata and whether it is currently installed locally.

Update checks scrape the DXMA listing page for mission IDs greater than the
highest known ID. Only Descent 1 missions are tracked.
"""

import csv
import html
import json
import re
import sys
import urllib.request
from pathlib import Path

_CATALOG_FILE = Path.home() / ".config" / "descentbuddy" / "missions_catalog.json"
_CSV_SEED = Path(__file__).parent.parent / "data" / "missions_catalog.csv"

_DXMA_BASE = "https://sectorgame.com/dxma"
_LISTING_URL = f"{_DXMA_BASE}/"

_MISSION_LINK_RE = re.compile(r'href="[^"]*mission\?m=(\d+)"')
_AUTHOR_RE = re.compile(r'href="[^"]*authors/(\d+)"[^>]*>([^<]+)<')
_TITLE_RE = re.compile(r'<h1[^>]*>([^<]+)<')
_META_RE = re.compile(r'<th[^>]*>([^<]+)</th>\s*<td[^>]*>([^<]+)</td>', re.DOTALL)
_DOWNLOAD_LINK_RE = re.compile(r'href="([^"]*download\?m=\d+)"')
_DIRECT_LINK_RE = re.compile(r'href="([^"]*dxma/files/[^"]+\.(?:zip|rar|7z))"')
_IMG_LINK_RE = re.compile(r'href="(/dxma/files/img/[^"]+)"')
_TABLE_ROW_RE = re.compile(
    r'<tr[^>]*>(.*?)</tr>', re.DOTALL | re.IGNORECASE
)
_TD_RE = re.compile(r'<td[^>]*>(.*?)</td>', re.DOTALL | re.IGNORECASE)
_HREF_RE = re.compile(r'href="([^"]*)"')
_STRIP_TAGS_RE = re.compile(r'<[^>]+>')


def _strip_tags(text: str) -> str:
    return html.unescape(_STRIP_TAGS_RE.sub("", text)).strip()


def load_catalog() -> dict:
    """Return the catalog as a dict keyed by mission ID (int).

    Seeds from the bundled CSV on first run.
    """
    if _CATALOG_FILE.exists():
        try:
            raw = json.loads(_CATALOG_FILE.read_text(encoding="utf-8"))
            return {int(k): v for k, v in raw.items()}
        except (json.JSONDecodeError, OSError):
            pass

    return _seed_from_csv()


def save_catalog(catalog: dict) -> None:
    _CATALOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    serializable = {str(k): v for k, v in catalog.items()}
    _CATALOG_FILE.write_text(
        json.dumps(serializable, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _seed_from_csv() -> dict:
    catalog: dict = {}
    if not _CSV_SEED.exists():
        return catalog
    with _CSV_SEED.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("download_status") != "success":
                continue
            mission_id = int(row["id"])
            catalog[mission_id] = {
                "id": mission_id,
                "title": row["title"],
                "mode": row["mode"],
                "game": row["game"],
                "date": row["date"],
                "author": row["author"],
                "mission_url": row.get("mission_url", ""),
                "download_url": row["download_url"],
                "direct_download_url": row["direct_download_url"],
                "installed": False,
                "installed_path": None,
            }
    save_catalog(catalog)
    return catalog


def get_d1_missions(catalog: dict) -> list:
    """Return all D1 missions sorted by date descending."""
    d1 = [entry for entry in catalog.values() if entry.get("game") == "D1"]
    return sorted(d1, key=lambda e: e.get("date", ""), reverse=True)


def get_d2_missions(catalog: dict) -> list:
    """Return all D2 missions sorted by date descending."""
    d2 = [entry for entry in catalog.values() if entry.get("game") == "D2"]
    return sorted(d2, key=lambda e: e.get("date", ""), reverse=True)


def mark_installed(catalog: dict, mission_id: int, installed_path: str) -> None:
    if mission_id in catalog:
        catalog[mission_id]["installed"] = True
        catalog[mission_id]["installed_path"] = installed_path


def mark_not_installed(catalog: dict, mission_id: int) -> None:
    if mission_id in catalog:
        catalog[mission_id]["installed"] = False
        catalog[mission_id]["installed_path"] = None


def scan_installed(catalog: dict, missions_dir: Path) -> int:
    """Cross-reference missions_dir filenames against catalog entries.

    Returns the count of newly detected installed missions.
    """
    if not missions_dir.exists():
        return 0

    existing_stems = {
        p.stem.lower()
        for p in missions_dir.rglob("*")
        if p.suffix.lower() in {".hog", ".msn", ".mn2"}
    }

    newly_found = 0
    for mission_id, entry in catalog.items():
        if entry.get("installed"):
            continue
        direct_url = entry.get("direct_download_url", "")
        if not direct_url:
            continue
        zip_name = Path(direct_url).stem.lower()
        if zip_name in existing_stems:
            mark_installed(catalog, mission_id, str(missions_dir))
            newly_found += 1

    return newly_found


def _fetch_text(url: str, timeout: int = 10) -> str | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "DescentBuddy/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception:
        return None


def _parse_listing_page(html_text: str) -> list[tuple[int, str, str, str, str]]:
    """Parse a DXMA listing page into (id, title, game, mode, author) tuples."""
    results = []
    for row_match in _TABLE_ROW_RE.finditer(html_text):
        row_html = row_match.group(1)
        cells = _TD_RE.findall(row_html)
        if len(cells) < 5:
            continue

        mode_text = _strip_tags(cells[0])
        game_text = _strip_tags(cells[1])
        title_cell = cells[2]
        date_text = _strip_tags(cells[3])
        author_text = _strip_tags(cells[4])

        if mode_text not in ("SP", "MP", "CTF"):
            continue

        link_match = _HREF_RE.search(title_cell)
        if not link_match:
            continue
        id_match = re.search(r'[?&]m=(\d+)', link_match.group(1))
        if not id_match:
            continue

        mission_id = int(id_match.group(1))
        title_text = _strip_tags(title_cell)
        results.append((mission_id, title_text, game_text, mode_text, author_text))

    return results


def _fetch_mission_page(mission_id: int) -> dict | None:
    """Fetch the DXMA mission page and extract metadata."""
    url = f"{_DXMA_BASE}/mission?m={mission_id}"
    html_text = _fetch_text(url)
    if not html_text:
        return None

    direct_match = _DIRECT_LINK_RE.search(html_text)
    direct_url = direct_match.group(1) if direct_match else ""
    if not direct_url.startswith("http"):
        direct_url = f"https://sectorgame.com{direct_url}" if direct_url else ""

    img_match = _IMG_LINK_RE.search(html_text)
    image_url = f"https://sectorgame.com{img_match.group(1)}" if img_match else ""

    return {
        "mission_url": f"{_DXMA_BASE}/mission?m={mission_id}",
        "download_url": f"{_DXMA_BASE}/download?m={mission_id}",
        "direct_download_url": direct_url,
        "image_url": image_url,
    }


def fetch_new_d1_missions(catalog: dict) -> list[dict]:
    """Scrape DXMA for D1 missions with IDs not present in the catalog.

    Walks listing pages newest-first, stopping once all IDs on a page are known.
    Returns a list of new entry dicts ready to be added to the catalog.
    """
    new_entries: list[dict] = []
    page = 1
    known_ids = set(catalog.keys())

    while True:
        url = f"{_LISTING_URL}?page={page}"
        html_text = _fetch_text(url)
        if not html_text:
            break

        rows = _parse_listing_page(html_text)
        if not rows:
            break

        all_known = True
        for mission_id, title, game, mode, author in rows:
            if mission_id not in known_ids:
                all_known = False
                if game.strip().upper() == "D1":
                    page_data = _fetch_mission_page(mission_id)
                    entry = {
                        "id": mission_id,
                        "title": title,
                        "mode": mode,
                        "game": "D1",
                        "date": "",
                        "author": author,
                        "mission_url": f"{_DXMA_BASE}/mission?m={mission_id}",
                        "download_url": f"{_DXMA_BASE}/download?m={mission_id}",
                        "direct_download_url": (
                            page_data["direct_download_url"] if page_data else ""
                        ),
                        "image_url": (
                            page_data["image_url"] if page_data else ""
                        ),
                        "installed": False,
                        "installed_path": None,
                    }
                    new_entries.append(entry)
                    known_ids.add(mission_id)

        if all_known:
            break

        page += 1
        if page > 20:
            break

    return new_entries


def fetch_new_d2_missions(catalog: dict) -> list[dict]:
    """Scrape DXMA for D2 missions with IDs not present in the catalog.

    Walks listing pages newest-first, stopping once all IDs on a page are known.
    Returns a list of new entry dicts ready to be added to the catalog.
    """
    new_entries: list[dict] = []
    page = 1
    known_ids = set(catalog.keys())

    while True:
        url = f"{_LISTING_URL}?page={page}"
        html_text = _fetch_text(url)
        if not html_text:
            break

        rows = _parse_listing_page(html_text)
        if not rows:
            break

        all_known = True
        for mission_id, title, game, mode, author in rows:
            if mission_id not in known_ids:
                all_known = False
                if game.strip().upper() == "D2":
                    page_data = _fetch_mission_page(mission_id)
                    entry = {
                        "id": mission_id,
                        "title": title,
                        "mode": mode,
                        "game": "D2",
                        "date": "",
                        "author": author,
                        "mission_url": f"{_DXMA_BASE}/mission?m={mission_id}",
                        "download_url": f"{_DXMA_BASE}/download?m={mission_id}",
                        "direct_download_url": (
                            page_data["direct_download_url"] if page_data else ""
                        ),
                        "image_url": (
                            page_data["image_url"] if page_data else ""
                        ),
                        "installed": False,
                        "installed_path": None,
                    }
                    new_entries.append(entry)
                    known_ids.add(mission_id)

        if all_known:
            break

        page += 1
        if page > 20:
            break

    return new_entries


def add_entries(catalog: dict, entries: list[dict]) -> None:
    for entry in entries:
        catalog[entry["id"]] = entry

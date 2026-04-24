"""Scanner for locally installed Descent 1 mission files.

DXX-Redux loads missions from a missions/ directory (or the game data root).
A mission is identified by a .HOG file. The .MSN or .MN2 file provides the
mission definition (level order, name). Supporting files (.txt, images) share
the same stem as the HOG file and are grouped together.

Missions may live directly in the scanned directory or inside one level of
subdirectory.
"""

from dataclasses import dataclass, field
from pathlib import Path

_HOG_SUFFIX = ".hog"
_MISSION_SUFFIXES = {".msn", ".mn2"}
_INFO_SUFFIXES = {".txt"}
_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}
_ALL_TRACKED = _MISSION_SUFFIXES | _INFO_SUFFIXES | _IMAGE_SUFFIXES


@dataclass
class MissionEntry:
    name: str
    hog_file: Path
    mission_file: Path | None
    info_file: Path | None
    image_file: Path | None
    extra_files: list[Path] = field(default_factory=list)

    @property
    def directory(self) -> Path:
        return self.hog_file.parent

    @property
    def is_complete(self) -> bool:
        return self.hog_file.exists() and self.mission_file is not None


def scan_missions_directory(directory: Path) -> list[MissionEntry]:
    """Return a list of missions found in *directory*.

    Scans the directory itself and any immediate subdirectories (one level
    deep). Each .HOG file is treated as the root of one mission entry.
    """
    if not directory.is_dir():
        return []

    hog_files: list[Path] = []

    for item in directory.iterdir():
        if item.is_file() and item.suffix.lower() == _HOG_SUFFIX:
            hog_files.append(item)
        elif item.is_dir():
            for sub_item in item.iterdir():
                if sub_item.is_file() and sub_item.suffix.lower() == _HOG_SUFFIX:
                    hog_files.append(sub_item)

    entries = [_build_entry(hog) for hog in sorted(hog_files, key=lambda p: p.stem.lower())]
    return entries


def _build_entry(hog_file: Path) -> MissionEntry:
    stem = hog_file.stem.lower()
    parent = hog_file.parent

    mission_file: Path | None = None
    info_file: Path | None = None
    image_file: Path | None = None
    extra: list[Path] = []

    for sibling in parent.iterdir():
        if not sibling.is_file():
            continue
        if sibling == hog_file:
            continue
        suffix = sibling.suffix.lower()
        sibling_stem = sibling.stem.lower()

        if sibling_stem != stem:
            extra.append(sibling)
            continue

        if suffix in _MISSION_SUFFIXES:
            mission_file = sibling
        elif suffix in _INFO_SUFFIXES:
            info_file = sibling
        elif suffix in _IMAGE_SUFFIXES:
            image_file = sibling

    return MissionEntry(
        name=hog_file.stem,
        hog_file=hog_file,
        mission_file=mission_file,
        info_file=info_file,
        image_file=image_file,
        extra_files=extra,
    )

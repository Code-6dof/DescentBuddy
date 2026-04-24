"""Game type detection and game-specific path resolution for Descent 1 and Descent 2."""

from enum import Enum
from pathlib import Path


class Game(Enum):
    D1 = "d1"
    D2 = "d2"


def detect_game(exe_path: str) -> Game:
    """Return D2 if the executable stem contains 'd2x', otherwise D1."""
    name = Path(exe_path).stem.lower()
    if "d2x" in name:
        return Game.D2
    return Game.D1


def display_name(game: Game) -> str:
    return "Descent II" if game == Game.D2 else "Descent"


def data_dir(game: Game) -> Path:
    """Return the user home data directory for this game on Linux."""
    folder = ".d2x-redux" if game == Game.D2 else ".d1x-redux"
    return Path.home() / folder


def ini_prefix(game: Game) -> str:
    return "d2x" if game == Game.D2 else "d1x"


def ini_names(game: Game) -> list[str]:
    """Return [active_ini, default_ini] filenames in priority order."""
    prefix = ini_prefix(game)
    return [f"{prefix}.ini", f"{prefix}-default.ini"]


def mission_extensions(game: Game) -> tuple[str, ...]:
    """Return the file extensions that identify installed missions."""
    if game == Game.D2:
        return (".hog", ".mn2")
    return (".hog", ".mn1")


def config_key(game: Game, field: str) -> str:
    """Return the config dict key for a game-specific setting.

    Example: config_key(Game.D1, "gamelog_path") -> "gamelog_path_d1"
    """
    return f"{field}_{game.value}"

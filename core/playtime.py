"""Persistent playtime tracking per game.

Total seconds are stored in config.json under the keys
'playtime_seconds_d1' and 'playtime_seconds_d2'.
"""

from core.app_config import load_config, save_config


def get_total_seconds(game_key: str) -> int:
    """Return the accumulated playtime in seconds for the given game ('d1' or 'd2')."""
    return int(load_config().get(f"playtime_seconds_{game_key}", 0))


def add_seconds(game_key: str, seconds: int) -> int:
    """Add seconds to the stored total and return the new total."""
    if seconds <= 0:
        return get_total_seconds(game_key)
    config = load_config()
    key = f"playtime_seconds_{game_key}"
    total = int(config.get(key, 0)) + seconds
    config[key] = total
    save_config(config)
    return total


def format_playtime(total_seconds: int) -> str:
    """Return a human-readable playtime string, e.g. '42 hrs 7 mins'."""
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    if hours == 0:
        return f"{minutes} min" if minutes != 1 else "1 min"
    if minutes == 0:
        return f"{hours} hrs"
    return f"{hours} hrs  {minutes} min"

"""Discord Rich Presence integration via pypresence.

To enable, set DISCORD_APP_ID to your application's client ID from
https://discord.com/developers/applications (create an application, enable
Rich Presence, and upload art assets with the key "descentbuddy").

If pypresence is not installed or Discord is not running, all calls are
silent no-ops. The rest of the app is never aware of the failure.

On Linux, alternative Discord clients (Goofcord, Vesktop, Flatpak Discord, etc.)
place their IPC socket in non-standard locations. This module detects those
and creates a symlink at the path pypresence expects.
"""

import os
import sys
from pathlib import Path

DISCORD_APP_ID = "1497108822651703326"

try:
    from pypresence import Presence
    _pypresence_available = True
except ImportError:
    _pypresence_available = False


def _find_ipc_socket() -> Path | None:
    """Return the discord-ipc-0 socket path, searching alternative locations on Linux."""
    runtime = Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp"))
    standard = runtime / "discord-ipc-0"
    if standard.exists():
        return standard

    uid = os.getuid()
    candidates = [
        runtime / ".flatpak" / "io.github.milkshiift.GoofCord" / "xdg-run" / "discord-ipc-0",
        runtime / ".flatpak" / "com.discordapp.Discord" / "xdg-run" / "discord-ipc-0",
        Path(f"/run/user/{uid}/.flatpak/io.github.milkshiift.GoofCord/xdg-run/discord-ipc-0"),
        Path(f"/run/user/{uid}/.flatpak/com.discordapp.Discord/xdg-run/discord-ipc-0"),
        runtime / "snap.discord" / "discord-ipc-0",
        Path("/tmp/discord-ipc-0"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _ensure_ipc_symlink() -> bool:
    """Create a symlink at the standard IPC path if the socket lives elsewhere.

    Returns True if the standard path is accessible (either directly or via symlink).
    """
    if sys.platform == "win32":
        return True
    runtime = Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp"))
    standard = runtime / "discord-ipc-0"
    if standard.exists():
        return True
    actual = _find_ipc_socket()
    if actual is None:
        return False
    try:
        standard.symlink_to(actual)
    except OSError:
        pass
    return standard.exists()


class _DiscordPresence:
    def __init__(self) -> None:
        self._rpc = None
        self._connected = False

    def _try_connect(self) -> bool:
        if not _pypresence_available or not DISCORD_APP_ID:
            return False
        _ensure_ipc_symlink()
        try:
            self._rpc = Presence(DISCORD_APP_ID)
            self._rpc.connect()
            self._connected = True
            return True
        except Exception:
            self._rpc = None
            self._connected = False
            return False

    def update(self, game_name: str, start_timestamp: float) -> None:
        from core.app_config import load_config
        if not load_config().get("discord_presence_enabled", True):
            return
        if not self._connected:
            self._try_connect()
        if not self._connected:
            return
        try:
            self._rpc.update(
                details=game_name,
                state="In game",
                start=int(start_timestamp),
                large_image="descentbuddy",
                large_text="DescentBuddy",
            )
        except Exception:
            self._connected = False
            self._rpc = None

    def clear(self) -> None:
        if not self._connected or self._rpc is None:
            return
        try:
            self._rpc.clear()
            self._rpc.close()
        except Exception:
            pass
        self._rpc = None
        self._connected = False


_instance = _DiscordPresence()


def update_presence(game_name: str, start_timestamp: float) -> None:
    """Set Rich Presence to show the given game as actively running."""
    _instance.update(game_name, start_timestamp)


def clear_presence() -> None:
    """Remove Rich Presence (call when the game process stops)."""
    _instance.clear()

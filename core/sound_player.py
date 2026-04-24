"""Plays notification sounds using Qt multimedia.

The sounds directory is data/notifications/ relative to the project root
(or sys._MEIPASS when frozen by PyInstaller).
"""

import sys
from pathlib import Path

from PyQt6.QtCore import QUrl
try:
    from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
    _MULTIMEDIA_AVAILABLE = True
except ImportError:
    _MULTIMEDIA_AVAILABLE = False

_LABEL_MAP = {
    "dragon-studio-chime-notification-444815": "Chime",
    "dragon-studio-new-notification-3-398649": "Ping 1",
    "dragon-studio-notification-ping-372479": "Ping 2",
    "dragon-studio-notification-sound-effect-372475": "Alert",
    "u_4quckyrjhw-notification-sound-349341": "Blip",
    "universfield-new-notification-010-352755": "Notification 1",
    "universfield-new-notification-020-352772": "Notification 2",
    "universfield-new-notification-040-493469": "Notification 3",
    "universfield-new-notification-056-494256": "Notification 4",
    "universfield-new-notification-064-494547": "Notification 5",
    "universfield-new-notification-09-352705": "Notification 6",
    "universfield-positive-notification-alert-351299": "Positive Alert",
}

_player: QMediaPlayer | None = None
_audio_output: QAudioOutput | None = None


def sounds_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "data" / "notifications"
    return Path(__file__).parent.parent / "data" / "notifications"


def list_sounds() -> list[tuple[str, str]]:
    """Return list of (stem, label) pairs for available notification sounds, with None first."""
    result: list[tuple[str, str]] = [("none", "None")]
    d = sounds_dir()
    if d.exists():
        for f in sorted(d.glob("*.mp3")):
            label = _LABEL_MAP.get(f.stem, f.stem.replace("-", " ").title())
            result.append((f.stem, label))
    return result


def default_sound() -> str:
    """Return the stem of the first available sound, or 'none' if there are none."""
    sounds = list_sounds()
    for stem, _ in sounds:
        if stem != "none":
            return stem
    return "none"


def play_notification_sound(stem: str) -> None:
    """Play the sound file identified by stem. No-op for 'none' or missing files."""
    global _player, _audio_output
    if not _MULTIMEDIA_AVAILABLE:
        return
    if not stem or stem == "none":
        return
    path = sounds_dir() / f"{stem}.mp3"
    if not path.exists():
        return
    if _player is None:
        _audio_output = QAudioOutput()
        _player = QMediaPlayer()
        _player.setAudioOutput(_audio_output)
    _player.setSource(QUrl.fromLocalFile(str(path)))
    _player.play()

"""Application settings dialog."""

import os
import struct
import sys
from pathlib import Path

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.app_config import load_config, save_config, config_file_path


def _config_file_display() -> str:
    """Return a human-readable config file path for display."""
    return str(config_file_path())
from ui.theme import THEME_LABELS, apply_theme, get_active_theme, list_theme_keys


# ---------------------------------------------------------------------------
# Autostart helpers (Linux ~/.config/autostart)
# ---------------------------------------------------------------------------

def _autostart_path() -> Path:
    return Path.home() / ".config" / "autostart" / "descentbuddy.desktop"


def _autostart_enabled() -> bool:
    return _autostart_path().exists()


def _set_autostart(enabled: bool) -> None:
    path = _autostart_path()
    if enabled:
        exe = os.environ.get("APPIMAGE") or os.path.abspath(sys.argv[0])
        content = (
            "[Desktop Entry]\n"
            "Name=DescentBuddy\n"
            f"Exec={exe}\n"
            "Type=Application\n"
            "Hidden=false\n"
            "X-GNOME-Autostart-enabled=true\n"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    else:
        path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Steam non-Steam game helpers (binary VDF)
# ---------------------------------------------------------------------------

def _vdf_str(key: str, value: str) -> bytes:
    return b"\x01" + key.encode() + b"\x00" + value.encode() + b"\x00"


def _vdf_int(key: str, value: int) -> bytes:
    return b"\x02" + key.encode() + b"\x00" + struct.pack("<I", value)


def _build_steam_shortcut(index: int, name: str, exe: str, start_dir: str) -> bytes:
    entry = b"\x00" + str(index).encode() + b"\x00"
    entry += _vdf_str("appname", name)
    entry += _vdf_str("Exe", f'"{exe}"')
    entry += _vdf_str("StartDir", f'"{start_dir}"')
    entry += _vdf_str("icon", "")
    entry += _vdf_str("ShortcutPath", "")
    entry += _vdf_str("LaunchOptions", "")
    entry += _vdf_int("IsHidden", 0)
    entry += _vdf_int("AllowDesktopConfig", 1)
    entry += _vdf_int("AllowOverlay", 1)
    entry += _vdf_int("openvr", 0)
    entry += _vdf_int("Devkit", 0)
    entry += _vdf_str("DevkitGameID", "")
    entry += _vdf_int("LastPlayTime", 0)
    entry += b"\x00tags\x00\x08"
    entry += b"\x08"
    return entry


def _steam_shortcut_files() -> list[Path]:
    for root in [
        Path.home() / ".local/share/Steam/userdata",
        Path.home() / ".steam/steam/userdata",
    ]:
        if root.exists():
            return [
                d / "config" / "shortcuts.vdf"
                for d in root.iterdir()
                if d.is_dir() and d.name.isdigit()
            ]
    return []


def _add_to_steam(exe: str) -> tuple[bool, str]:
    start_dir = str(Path(exe).parent)
    files = _steam_shortcut_files()
    if not files:
        return False, "Steam installation not found."

    already = []
    added: list[str] = []
    for path in files:
        account = path.parent.parent.name
        if path.exists():
            data = path.read_bytes()
            # Already added with this exact exe — skip
            if exe.encode() in data:
                already.append(account)
                continue
            index = data.count(b"\x01Exe\x00")
            entry = _build_steam_shortcut(index, "DescentBuddy", exe, start_dir)
            new_data = (
                data[:-2] + entry + b"\x08\x08"
                if data.endswith(b"\x08\x08")
                else data + entry + b"\x08\x08"
            )
            path.with_suffix(".vdf.bak").write_bytes(data)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            new_data = (
                b"\x00shortcuts\x00"
                + _build_steam_shortcut(0, "DescentBuddy", exe, start_dir)
                + b"\x08\x08"
            )
        path.write_bytes(new_data)
        added.append(account)

    if not added:
        if already:
            return False, "Already added to Steam with this executable."
        return False, "No Steam accounts found to update."
    msg = f"Added to Steam (account: {', '.join(added)}). Restart Steam to see it."
    if already:
        msg += f" (Already present for: {', '.join(already)}.)"
    return True, msg


# ---------------------------------------------------------------------------
# Dialog
# ---------------------------------------------------------------------------

_STATUS_ITEMS = ["Online", "Busy", "Do Not Disturb", "Invisible"]
_STATUS_KEYS = ["online", "busy", "dnd", "invisible"]


class AppSettingsDialog(QDialog):
    display_name_changed = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(560)
        self.setMinimumHeight(500)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll_content = QWidget()
        scroll_content.setObjectName("panel")

        inner = QVBoxLayout(scroll_content)
        inner.setContentsMargins(40, 36, 40, 36)
        inner.setSpacing(0)

        title = QLabel("SETTINGS")
        title.setObjectName("panel-title")
        inner.addWidget(title)

        inner.addSpacing(28)

        # ── General ──────────────────────────────────────────────────
        self._add_section_label("GENERAL", inner)
        inner.addSpacing(10)

        self._autostart_check = QCheckBox("Start DescentBuddy when PC starts")
        self._autostart_check.setChecked(_autostart_enabled())
        self._autostart_check.toggled.connect(self._on_autostart_toggled)
        inner.addWidget(self._autostart_check)

        inner.addSpacing(10)

        steam_row = QHBoxLayout()
        self._steam_btn = QPushButton("Add to Steam as Non-Steam Game")
        self._steam_btn.clicked.connect(self._on_add_to_steam)
        steam_row.addWidget(self._steam_btn)
        steam_row.addSpacing(12)
        self._steam_status = QLabel("")
        self._steam_status.setObjectName("section-label")
        self._steam_status.setWordWrap(True)
        steam_row.addWidget(self._steam_status, 1)
        inner.addLayout(steam_row)

        inner.addSpacing(28)
        self._add_divider(inner)
        inner.addSpacing(24)

        # ── Appearance ───────────────────────────────────────────────
        self._add_section_label("APPEARANCE", inner)
        inner.addSpacing(10)

        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel("Default theme"))
        theme_row.addSpacing(16)
        self._theme_combo = QComboBox()
        for key in list_theme_keys():
            self._theme_combo.addItem(THEME_LABELS.get(key, key), key)
        active = get_active_theme()
        keys = list_theme_keys()
        if active in keys:
            self._theme_combo.setCurrentIndex(keys.index(active))
        self._theme_combo.setFixedWidth(160)
        self._theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        theme_row.addWidget(self._theme_combo)
        theme_row.addStretch()
        inner.addLayout(theme_row)

        inner.addSpacing(28)
        self._add_divider(inner)
        inner.addSpacing(24)

        # ── Game ─────────────────────────────────────────────────────
        self._add_section_label("GAME", inner)
        inner.addSpacing(10)

        game_row = QHBoxLayout()
        game_row.addWidget(QLabel("Default game"))
        game_row.addSpacing(16)
        self._game_combo = QComboBox()
        self._game_combo.addItem("Descent 1", "d1")
        self._game_combo.addItem("Descent 2", "d2")
        default_game = load_config().get("default_game", "d1")
        self._game_combo.setCurrentIndex(0 if default_game == "d1" else 1)
        self._game_combo.setFixedWidth(160)
        self._game_combo.currentIndexChanged.connect(self._on_game_changed)
        game_row.addWidget(self._game_combo)
        game_row.addStretch()
        inner.addLayout(game_row)

        inner.addSpacing(28)
        self._add_divider(inner)
        inner.addSpacing(24)

        # ── Community ─────────────────────────────────────────────────
        self._add_section_label("COMMUNITY", inner)
        inner.addSpacing(10)

        status_row = QHBoxLayout()
        status_row.addWidget(QLabel("Default status"))
        status_row.addSpacing(16)
        self._default_status_combo = QComboBox()
        for label, key in zip(_STATUS_ITEMS, _STATUS_KEYS):
            self._default_status_combo.addItem(label, key)
        default_status = load_config().get("default_status", "online")
        if default_status in _STATUS_KEYS:
            self._default_status_combo.setCurrentIndex(_STATUS_KEYS.index(default_status))
        self._default_status_combo.setFixedWidth(160)
        self._default_status_combo.currentIndexChanged.connect(self._on_default_status_changed)
        status_row.addWidget(self._default_status_combo)
        status_row.addStretch()
        inner.addLayout(status_row)

        inner.addSpacing(16)

        sound_row = QHBoxLayout()
        sound_row.addWidget(QLabel("Notification sound"))
        sound_row.addSpacing(16)
        self._sound_combo = QComboBox()
        from core.sound_player import default_sound, list_sounds
        sounds = list_sounds()
        for stem, label in sounds:
            self._sound_combo.addItem(label, stem)
        stems = [s for s, _ in sounds]
        current_sound = load_config().get("notification_sound") or default_sound()
        if current_sound in stems:
            self._sound_combo.setCurrentIndex(stems.index(current_sound))
        self._sound_combo.setFixedWidth(180)
        self._sound_combo.currentIndexChanged.connect(self._on_sound_changed)
        sound_row.addWidget(self._sound_combo)
        sound_row.addSpacing(8)
        preview_btn = QPushButton("Preview")
        preview_btn.setFixedWidth(70)
        preview_btn.clicked.connect(self._preview_sound)
        sound_row.addWidget(preview_btn)
        sound_row.addStretch()
        inner.addLayout(sound_row)

        inner.addSpacing(16)

        dn_lbl = QLabel("Display name")
        inner.addWidget(dn_lbl)
        inner.addSpacing(6)

        dn_row = QHBoxLayout()
        self._dn_edit = QLineEdit()
        self._dn_edit.setPlaceholderText(
            "Name shown to others online (leave blank to use your account name)"
        )
        self._dn_edit.setMaxLength(32)
        self._dn_edit.setText(load_config().get("community_display_name", ""))
        self._dn_edit.returnPressed.connect(self._apply_display_name)
        dn_row.addWidget(self._dn_edit, 1)
        dn_set_btn = QPushButton("Set")
        dn_set_btn.setFixedWidth(60)
        dn_set_btn.clicked.connect(self._apply_display_name)
        dn_row.addWidget(dn_set_btn)
        inner.addLayout(dn_row)

        inner.addSpacing(4)
        self._dn_status = QLabel("")
        self._dn_status.setObjectName("section-label")
        inner.addWidget(self._dn_status)

        inner.addSpacing(28)
        self._add_divider(inner)
        inner.addSpacing(24)

        # ── Data ─────────────────────────────────────────────────────
        self._add_section_label("DATA", inner)
        inner.addSpacing(10)

        reset_row = QHBoxLayout()
        self._reset_btn = QPushButton("Reset Config File")
        self._reset_btn.clicked.connect(self._on_reset_config)
        reset_row.addWidget(self._reset_btn)
        reset_row.addSpacing(12)
        self._reset_status = QLabel(
            f"Clears all settings and saved paths. Config is stored at:\n"
            f"{_config_file_display()}"
        )
        self._reset_status.setObjectName("version-label")
        self._reset_status.setWordWrap(True)
        reset_row.addWidget(self._reset_status, 1)
        inner.addLayout(reset_row)

        inner.addStretch()

        scroll = QScrollArea()
        scroll.setWidget(scroll_content)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer.addWidget(scroll, 1)

        close_row = QHBoxLayout()
        close_row.setContentsMargins(20, 10, 20, 14)
        close_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setFixedWidth(80)
        close_btn.clicked.connect(self.accept)
        close_row.addWidget(close_btn)
        outer.addLayout(close_row)

    def _add_section_label(self, text: str, layout: QVBoxLayout) -> None:
        lbl = QLabel(text)
        lbl.setObjectName("section-label")
        layout.addWidget(lbl)

    def _add_divider(self, layout: QVBoxLayout) -> None:
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(divider)

    def _on_autostart_toggled(self, enabled: bool) -> None:
        _set_autostart(enabled)

    def _on_add_to_steam(self) -> None:
        # If running as an AppImage the env var is set; otherwise ask the user to
        # locate the AppImage they built so Steam gets the right executable.
        appimage_env = os.environ.get("APPIMAGE", "")
        if appimage_env and Path(appimage_env).is_file():
            exe_path = appimage_env
        else:
            # Look for the built AppImage next to the project root as a default
            project_root = Path(__file__).parent.parent
            default = project_root / "DescentBuddy-x86_64.AppImage"
            start = str(default) if default.exists() else str(Path.home())
            chosen, _ = QFileDialog.getOpenFileName(
                self,
                "Select DescentBuddy AppImage",
                start,
                "AppImage (*.AppImage);;All files (*)",
            )
            if not chosen:
                return
            exe_path = chosen

        self._steam_btn.setEnabled(False)
        self._steam_status.setText("Adding...")
        try:
            ok, msg = _add_to_steam(exe_path)
            self._steam_status.setText(msg)
        except Exception as exc:
            self._steam_status.setText(f"Error: {exc}")
        self._steam_btn.setEnabled(True)

    def _on_theme_changed(self, index: int) -> None:
        key = self._theme_combo.itemData(index)
        apply_theme(QApplication.instance(), key)
        cfg = load_config()
        cfg["theme"] = key
        save_config(cfg)

    def _on_game_changed(self, index: int) -> None:
        cfg = load_config()
        cfg["default_game"] = self._game_combo.itemData(index)
        save_config(cfg)

    def _on_default_status_changed(self, index: int) -> None:
        cfg = load_config()
        cfg["default_status"] = self._default_status_combo.itemData(index)
        save_config(cfg)

    def _on_sound_changed(self, index: int) -> None:
        cfg = load_config()
        cfg["notification_sound"] = self._sound_combo.itemData(index)
        save_config(cfg)

    def _preview_sound(self) -> None:
        from core.sound_player import play_notification_sound
        play_notification_sound(self._sound_combo.currentData())

    def _apply_display_name(self) -> None:
        name = self._dn_edit.text().strip()
        cfg = load_config()
        cfg["community_display_name"] = name
        save_config(cfg)
        self._dn_status.setText(f"Set to: {name}" if name else "Using account name.")
        self.display_name_changed.emit(name)

    def _on_reset_config(self) -> None:
        from PyQt6.QtWidgets import QMessageBox
        result = QMessageBox.warning(
            self,
            "Reset Config File",
            "This will delete your config file, removing all saved paths, settings, "
            "and play time records.\n\nThe application will close. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
        )
        if result != QMessageBox.StandardButton.Yes:
            return
        try:
            config_file_path().unlink(missing_ok=True)
        except OSError as exc:
            self._reset_status.setText(f"Error: {exc}")
            return
        QApplication.instance().quit()

"""Launch panel — two stacked game cards, one for Descent 1 and one for Descent 2."""

import os
import sys
import tempfile
import time
from pathlib import Path

from PyQt6.QtCore import QByteArray, QFileInfo, Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QCursor, QFont, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QFileDialog,
    QFileIconProvider,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from core.app_config import load_config, save_config
from core.appimage_icon import extract_appimage_icon
from core.game_detector import Game, detect_game, display_name
from core.game_launcher import GameLauncher
from core.playtime import add_seconds, format_playtime, get_total_seconds
from core.version_detector import detect_version
from ui.panels.settings_panel import SettingsDialog

_ICON_SIZE = 72
_CONFIG_KEY = {Game.D1: "exe_path_d1", Game.D2: "exe_path_d2"}


def _format_size(bytes_: int) -> str:
    value = float(bytes_)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024:
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} GB"


class _VersionThread(QThread):
    result = pyqtSignal(str)

    def __init__(self, path: str, parent=None) -> None:
        super().__init__(parent)
        self._path = path

    def run(self) -> None:
        self.result.emit(detect_version(self._path))


class _ClickableLabel(QLabel):
    """QLabel that emits clicked when left-clicked."""

    clicked = pyqtSignal()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class _GameCard(QWidget):
    """Self-contained launch card for one game (D1 or D2)."""

    game_applied = pyqtSignal(str)

    def __init__(self, game: Game, parent=None) -> None:
        super().__init__(parent)

        self._game = game
        self._exe_path: str = ""
        self._exe_configured = False
        self._launcher = GameLauncher()
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(1000)
        self._poll_timer.timeout.connect(self._poll_process)
        self._icon_provider = QFileIconProvider()
        self._settings_dialog: SettingsDialog | None = None
        self._version_threads: list[QThread] = []
        self._session_start: float = 0.0
        self._session_timer = QTimer(self)
        self._session_timer.setInterval(1000)
        self._session_timer.timeout.connect(self._tick_session)

        self._build_ui()
        self._restore_saved_path()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        title_row = QHBoxLayout()
        title_row.setSpacing(0)

        game_label = QLabel(display_name(self._game).upper())
        game_label.setObjectName("section-label")
        title_row.addWidget(game_label)
        title_row.addStretch()
        root.addLayout(title_row)

        root.addSpacing(10)

        card_row = QHBoxLayout()
        card_row.setSpacing(16)
        card_row.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Select column — always visible, to the left of the icon
        select_col = QVBoxLayout()
        select_col.setContentsMargins(0, 0, 0, 0)
        select_col.setSpacing(0)
        select_col.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._select_btn = QPushButton("Select")
        self._select_btn.setObjectName("select-btn")
        self._select_btn.setCheckable(True)
        self._select_btn.setFixedWidth(84)
        self._select_btn.clicked.connect(self._on_select_clicked)
        select_col.addWidget(self._select_btn)
        select_col.addStretch()

        card_row.addLayout(select_col)

        self._icon_label = _ClickableLabel()
        self._icon_label.setFixedSize(_ICON_SIZE, _ICON_SIZE)
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._render_blank_icon()
        card_row.addWidget(self._icon_label, 0, Qt.AlignmentFlag.AlignTop)

        meta_col = QVBoxLayout()
        meta_col.setSpacing(4)
        meta_col.setContentsMargins(0, 4, 0, 0)

        self._filename_label = QLabel("No executable selected")
        self._filename_label.setObjectName("filename-main")
        meta_col.addWidget(self._filename_label)

        self._version_label = QLabel("")
        self._version_label.setObjectName("version-label")
        self._version_label.setVisible(False)
        meta_col.addWidget(self._version_label)

        self._size_label = QLabel("")
        self._size_label.setObjectName("version-label")
        self._size_label.setVisible(False)
        meta_col.addWidget(self._size_label)

        self._playtime_label = QLabel("")
        self._playtime_label.setObjectName("version-label")
        self._playtime_label.setVisible(False)
        meta_col.addWidget(self._playtime_label)

        meta_col.addStretch()
        card_row.addLayout(meta_col, 1)

        action_col = QVBoxLayout()
        action_col.setSpacing(6)
        action_col.setContentsMargins(0, 4, 0, 0)
        action_col.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

        self._action_btn = QPushButton("LAUNCH")
        self._action_btn.setObjectName("launch-btn")
        self._action_btn.setFixedWidth(140)
        self._action_btn.setEnabled(False)
        self._action_btn.clicked.connect(self._on_action_btn_clicked)
        action_col.addWidget(self._action_btn, 0, Qt.AlignmentFlag.AlignRight)

        self._status_label = QLabel("")
        self._status_label.setObjectName("status-label")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        action_col.addWidget(self._status_label, 0, Qt.AlignmentFlag.AlignRight)

        action_col.addStretch()
        card_row.addLayout(action_col, 0)

        root.addLayout(card_row)

    # ------------------------------------------------------------------
    # Icon helpers
    # ------------------------------------------------------------------

    def _render_blank_icon(self) -> None:
        self._icon_label.setPixmap(self._make_letter_icon("?", "#3a3530"))
        self._icon_label.setCursor(Qt.CursorShape.ArrowCursor)
        self._icon_label.setToolTip("")

    def _enable_icon_click(self) -> None:
        self._icon_label.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._icon_label.setToolTip("Click to configure")
        try:
            self._icon_label.clicked.disconnect()
        except (RuntimeError, TypeError):
            pass
        self._icon_label.clicked.connect(self._open_settings)

    def _make_letter_icon(self, letter: str, color: str = "#e85c00") -> QPixmap:
        px = QPixmap(_ICON_SIZE, _ICON_SIZE)
        px.fill(Qt.GlobalColor.transparent)
        painter = QPainter(px)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor("#1a1a1a"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, _ICON_SIZE, _ICON_SIZE, 10, 10)
        painter.setPen(QColor(color))
        painter.setFont(QFont("DejaVu Sans", 28, QFont.Weight.Bold))
        painter.drawText(px.rect(), Qt.AlignmentFlag.AlignCenter, letter)
        painter.end()
        return px

    def _load_icon(self, path: str) -> None:
        p = Path(path)
        if p.suffix.lower() == ".appimage":
            icon_bytes = None
            with tempfile.TemporaryDirectory() as tmpdir:
                icon_path = extract_appimage_icon(path, tmpdir)
                if icon_path:
                    try:
                        icon_bytes = Path(icon_path).read_bytes()
                    except OSError:
                        pass
            if icon_bytes:
                px = QPixmap()
                if px.loadFromData(QByteArray(icon_bytes), "PNG") and not px.isNull():
                    px = px.scaled(
                        _ICON_SIZE, _ICON_SIZE,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                    self._icon_label.setPixmap(px)
                    self._icon_label.update()
                    return

        px = self._icon_provider.icon(QFileInfo(path)).pixmap(_ICON_SIZE, _ICON_SIZE)
        if not px.isNull():
            self._icon_label.setPixmap(px)
            self._icon_label.update()
            return

        self._icon_label.setPixmap(self._make_letter_icon(p.name[0].upper()))
        self._icon_label.update()

    # ------------------------------------------------------------------
    # State management
    # ------------------------------------------------------------------

    def _enter_loaded_state(self, path: str) -> None:
        p = Path(path)
        self._exe_configured = True
        self._filename_label.setText(p.name)
        self._version_label.setText("Version: Detecting...")
        self._version_label.setVisible(True)
        self._size_label.setText(f"Size: {_format_size(os.path.getsize(path))}")
        self._size_label.setVisible(True)
        self._playtime_label.setText(self._playtime_text())
        self._playtime_label.setVisible(True)
        self._action_btn.setEnabled(True)
        self._set_status("idle", "Ready")
        self._enable_icon_click()
        thread = _VersionThread(path, self)
        thread.result.connect(lambda v: self._version_label.setText(f"Version: {v}"))
        thread.finished.connect(lambda: self._prune_version_thread(thread))
        self._version_threads.append(thread)
        thread.start()
        QTimer.singleShot(0, lambda: self._load_icon(path))

    def _prune_version_thread(self, thread: QThread) -> None:
        if thread in self._version_threads:
            self._version_threads.remove(thread)

    def _enter_empty_state(self) -> None:
        self._exe_configured = False
        self._filename_label.setText("No executable selected")
        self._version_label.setVisible(False)
        self._size_label.setVisible(False)
        self._playtime_label.setVisible(False)
        self._action_btn.setEnabled(False)
        self._set_status("idle", "")
        self._render_blank_icon()

    def _apply_exe_path(self, path: str) -> None:
        if not path or not Path(path).is_file():
            self._enter_empty_state()
            return

        detected = detect_game(path)
        if detected != self._game:
            self._set_status("error", f"Not a {display_name(self._game)} executable")
            return

        self._exe_path = path
        self._enter_loaded_state(path)

        config = load_config()
        config[_CONFIG_KEY[self._game]] = path
        save_config(config)

        self.game_applied.emit(self._game.value)

        if self._settings_dialog is not None:
            self._settings_dialog.exe_path_changed.disconnect(self._apply_exe_path)
            self._settings_dialog = None

    def _restore_saved_path(self) -> None:
        config = load_config()
        saved = config.get(_CONFIG_KEY[self._game], "")

        if not saved:
            old_key = config.get("exe_path", "")
            if old_key and Path(old_key).is_file():
                try:
                    if detect_game(old_key) == self._game:
                        saved = old_key
                        config[_CONFIG_KEY[self._game]] = saved
                        save_config(config)
                except Exception:
                    pass

        if saved and Path(saved).is_file():
            self._exe_path = saved
            self._enter_loaded_state(saved)

    def has_exe(self) -> bool:
        return self._exe_configured

    def flush_session(self) -> None:
        """Save any accumulated session time immediately (e.g. on app quit)."""
        if self._session_start > 0:
            elapsed = int(time.monotonic() - self._session_start)
            self._session_start = 0.0
            self._session_timer.stop()
            if elapsed > 0:
                add_seconds(self._game.value, elapsed)

    def set_selected(self, active: bool) -> None:
        self._select_btn.setChecked(active)
        self._select_btn.setText("Selected" if active else "Select")

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_select_clicked(self) -> None:
        """If an exe is already configured, make this game active. Otherwise open the picker."""
        if self._exe_configured:
            self.game_applied.emit(self._game.value)
        else:
            self._pick_exe()

    def _pick_exe(self) -> None:
        if sys.platform == "win32":
            file_filter = "DXX-Redux Executable (*.exe);;All Files (*)"
        else:
            file_filter = "DXX-Redux AppImage (*.AppImage);;All Files (*)"
        start = str(Path(self._exe_path).parent) if self._exe_path else str(Path.home())
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Game Executable", start, file_filter,
        )
        if path:
            self._apply_exe_path(path)

    def _on_action_btn_clicked(self) -> None:
        if self._launcher.is_running():
            self._launcher.stop()
            self._set_status_idle()
        else:
            self._start_game()

    def _open_settings(self) -> None:
        if self._settings_dialog is None:
            self._settings_dialog = SettingsDialog(self)
            self._settings_dialog.exe_path_changed.connect(self._apply_exe_path)
        self._settings_dialog.open_for(self._game, self._exe_path)
        self._settings_dialog.exec()

    def _start_game(self) -> None:
        try:
            self._launcher.launch(self._exe_path)
        except (FileNotFoundError, RuntimeError, OSError) as exc:
            self._set_status("error", f"Error: {exc}")
            return
        self._session_start = time.monotonic()
        self._session_timer.start()
        self._action_btn.setText("STOP")
        self._action_btn.setEnabled(True)
        self._select_btn.setEnabled(False)
        self._set_status("running", "Running")
        self._poll_timer.start()
        QTimer.singleShot(800, self._check_launch_survived)

    def _check_launch_survived(self) -> None:
        if not self._launcher.is_running():
            self._poll_timer.stop()
            self._set_status("error", "Game exited immediately — check executable or FUSE support")
            self._set_status_idle()

    def _poll_process(self) -> None:
        if not self._launcher.is_running():
            self._poll_timer.stop()
            self._set_status_idle()

    def _set_status_idle(self) -> None:
        self._poll_timer.stop()
        if self._session_start > 0:
            elapsed = int(time.monotonic() - self._session_start)
            self._session_start = 0.0
            self._session_timer.stop()
            add_seconds(self._game.value, elapsed)
            self._playtime_label.setText(self._playtime_text())
        self._action_btn.setText("LAUNCH")
        self._action_btn.setEnabled(True)
        self._select_btn.setEnabled(True)
        self._set_status("idle", "Ready")

    def _tick_session(self) -> None:
        if self._session_start > 0:
            elapsed = int(time.monotonic() - self._session_start)
            total = get_total_seconds(self._game.value) + elapsed
            session_str = f"{elapsed // 60}:{elapsed % 60:02d}"
            self._playtime_label.setText(f"Play time: {format_playtime(total)}  (session: {session_str})")

    def _playtime_text(self) -> str:
        total = get_total_seconds(self._game.value)
        if total == 0:
            return "Play time: 0 min"
        return f"Play time: {format_playtime(total)}"

    def _set_status(self, state: str, text: str) -> None:
        mapping = {
            "idle": "status-label",
            "running": "status-running",
            "error": "status-error",
        }
        self._status_label.setObjectName(mapping.get(state, "status-label"))
        self._status_label.setText(text)
        self._status_label.setStyle(self._status_label.style())


class LaunchPanel(QWidget):
    """Panel containing one game card for Descent 1 and one for Descent 2."""

    exe_path_changed = pyqtSignal(str)
    game_changed = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("panel")
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 36, 40, 36)
        root.setSpacing(0)

        title = QLabel("LAUNCH")
        title.setObjectName("panel-title")
        root.addWidget(title)

        root.addSpacing(28)

        divider_top = QFrame()
        divider_top.setFrameShape(QFrame.Shape.HLine)
        root.addWidget(divider_top)

        root.addSpacing(24)

        self._d1_card = _GameCard(Game.D1, self)
        self._d1_card.game_applied.connect(self.game_changed)
        self._d1_card.game_applied.connect(self.exe_path_changed)
        self._d1_card.game_applied.connect(self._on_card_selected)
        root.addWidget(self._d1_card)

        root.addSpacing(20)

        divider_mid = QFrame()
        divider_mid.setFrameShape(QFrame.Shape.HLine)
        root.addWidget(divider_mid)

        root.addSpacing(20)

        self._d2_card = _GameCard(Game.D2, self)
        self._d2_card.game_applied.connect(self.game_changed)
        self._d2_card.game_applied.connect(self.exe_path_changed)
        self._d2_card.game_applied.connect(self._on_card_selected)
        root.addWidget(self._d2_card)

        root.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

    def _on_card_selected(self, game_value: str) -> None:
        self._d1_card.set_selected(game_value == Game.D1.value)
        self._d2_card.set_selected(game_value == Game.D2.value)

    def save_active_sessions(self) -> None:
        """Flush any in-progress session time to config (called on app quit)."""
        self._d1_card.flush_session()
        self._d2_card.flush_session()

    def emit_current_game(self) -> None:
        """Re-emit game state for whichever games have executables configured."""
        preferred = load_config().get("default_game", "d1")
        ordered = (
            (self._d1_card, self._d2_card)
            if preferred == "d1"
            else (self._d2_card, self._d1_card)
        )
        for card in ordered:
            if card.has_exe():
                self._on_card_selected(card._game.value)
                self.game_changed.emit(card._game.value)
                break

"""Netlog panel — live viewer for DXX-Redux multiplayer session audit log."""

import re
from pathlib import Path

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QFontDatabase
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.app_config import load_config

_LIVE_INTERVAL_MS = 1500

_GAME_START = re.compile(
    r"starting netgame|netgame started|joining game|game started|net game|"
    r"connected to server|hosting game|new game",
    re.IGNORECASE,
)

_GAME_END = re.compile(
    r"game over|netgame ended|game ended|leaving game|disconnected from|"
    r"connection closed|host quit|server closed",
    re.IGNORECASE,
)


def _parse_netgames(text: str) -> list[dict]:
    """Split netlog into game sessions, newest first.

    Each entry is a dict with:
      lines: list[str]  — all lines belonging to this session
      complete: bool    — True if an end-of-game marker was found
    """
    lines = text.splitlines()
    sessions: list[dict] = []
    current: list[str] = []
    in_session = False
    complete = False

    for line in lines:
        if _GAME_START.search(line):
            if in_session and current:
                sessions.append({"lines": current, "complete": complete})
            current = [line]
            in_session = True
            complete = False
        elif _GAME_END.search(line) and in_session:
            current.append(line)
            complete = True
        else:
            current.append(line)

    if current:
        sessions.append({"lines": current, "complete": complete or not in_session})

    sessions.reverse()
    return sessions


class NetlogPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("panel")
        self._sessions: list[dict] = []
        self._last_mtime: float = 0.0
        self._game: str = "d1"
        self._live_timer = QTimer(self)
        self._live_timer.setInterval(_LIVE_INTERVAL_MS)
        self._live_timer.timeout.connect(self._poll_file)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 36, 40, 36)
        layout.setSpacing(0)

        header_row = QHBoxLayout()
        header_row.setSpacing(0)

        title = QLabel("NETLOG")
        title.setObjectName("panel-title")
        header_row.addWidget(title)

        header_row.addStretch()

        self._live_indicator = QLabel("LIVE")
        self._live_indicator.setObjectName("live-indicator")
        self._live_indicator.setVisible(False)
        header_row.addWidget(self._live_indicator)

        layout.addLayout(header_row)

        subtitle = QLabel("Multiplayer session audit log")
        subtitle.setObjectName("section-label")
        layout.addWidget(subtitle)

        layout.addSpacing(16)

        controls = QHBoxLayout()
        controls.setSpacing(8)

        sessions_label = QLabel("Sessions:")
        sessions_label.setObjectName("section-label")
        controls.addWidget(sessions_label)

        self._session_count = QSpinBox()
        self._session_count.setRange(1, 20)
        self._session_count.setValue(5)
        self._session_count.setFixedWidth(64)
        self._session_count.valueChanged.connect(self._render)
        controls.addWidget(self._session_count)

        controls.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setFixedWidth(90)
        refresh_btn.clicked.connect(self._load_and_render)
        controls.addWidget(refresh_btn)

        layout.addLayout(controls)

        layout.addSpacing(12)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(divider)

        layout.addSpacing(6)

        self._status_label = QLabel("")
        self._status_label.setObjectName("section-label")
        layout.addWidget(self._status_label)

        layout.addSpacing(4)

        self._content_area = QTextEdit()
        self._content_area.setReadOnly(True)
        self._content_area.setFont(
            QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        )
        self._content_area.setObjectName("gamelog-content")
        layout.addWidget(self._content_area, stretch=1)

    def _netlog_path(self) -> Path | None:
        path = load_config().get(f"netlog_path_{self._game}", "")
        return Path(path) if path else None

    def on_game_changed(self, game_key: str) -> None:
        self._game = game_key
        self._last_mtime = 0.0
        self._load_and_render()

    def _load_and_render(self) -> None:
        path = self._netlog_path()

        if path is None:
            self._status_label.setText("No netlog path configured — set it in Settings.")
            self._content_area.clear()
            self._sessions = []
            self._live_indicator.setVisible(False)
            return

        if not path.exists():
            self._status_label.setText(
                f"File not found: {path.name} — join a netgame once to generate it."
            )
            self._content_area.clear()
            self._sessions = []
            self._live_indicator.setVisible(False)
            return

        try:
            mtime = path.stat().st_mtime
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            self._status_label.setText(f"Could not read netlog: {exc}")
            self._content_area.clear()
            self._sessions = []
            self._live_indicator.setVisible(False)
            return

        self._last_mtime = mtime
        self._sessions = _parse_netgames(text)
        self._live_indicator.setVisible(True)
        self._render()

    def _poll_file(self) -> None:
        path = self._netlog_path()
        if path is None or not path.exists():
            return
        try:
            mtime = path.stat().st_mtime
        except OSError:
            return
        if mtime != self._last_mtime:
            self._load_and_render()

    def _render(self) -> None:
        count = self._session_count.value()
        shown = self._sessions[:count]

        if not shown:
            if not self._sessions:
                return
            self._status_label.setText("No session data found in netlog.")
            self._content_area.clear()
            return

        total = len(self._sessions)
        self._status_label.setText(
            f"Showing {len(shown)} of {total} netgame session(s) — newest first."
        )

        scrollbar = self._content_area.verticalScrollBar()
        at_bottom = scrollbar.value() >= scrollbar.maximum() - 4

        parts: list[str] = []
        for i, session in enumerate(shown):
            status = "COMPLETED" if session["complete"] else "IN PROGRESS / INCOMPLETE"
            parts.append("=" * 60)
            parts.append(f"  NETGAME {i + 1}  [{status}]")
            parts.append("=" * 60)
            non_empty = [line for line in session["lines"] if line.strip()]
            parts.extend(non_empty)
            parts.append("")

        self._content_area.setPlainText("\n".join(parts))

        if at_bottom:
            scrollbar.setValue(scrollbar.maximum())

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._load_and_render()
        self._live_timer.start()

    def hideEvent(self, event) -> None:
        super().hideEvent(event)
        self._live_timer.stop()

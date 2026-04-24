"""Recent panel — gamelog viewer and netlog viewer with a tab toggle."""

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

_SESSION_START = re.compile(r"^(D[1-9]X|DXX|Descent\s+\d)", re.IGNORECASE)

_GAME_PATTERNS = [
    re.compile(r"kill|died|death|fragged|destroyed", re.IGNORECASE),
    re.compile(r"picked up|got the |grabbed ", re.IGNORECASE),
    re.compile(r"entered|joined|left the game|disconnected|connected", re.IGNORECASE),
    re.compile(r"^\[.+?\]", re.IGNORECASE),
    re.compile(r"\bscore\b|\bkills\b|\bdeaths\b|\blevel\s+\d", re.IGNORECASE),
    re.compile(r"\bshield\b|\benergy\b|\bpowerup\b|\bbonus\b", re.IGNORECASE),
    re.compile(r"missile|laser|cannon|weapon|vulcan|plasma|phoenix", re.IGNORECASE),
]

_DEBUG_PATTERNS = [
    re.compile(r"\berror\b|\bwarning\b|\bassert\b|\bfailed\b", re.IGNORECASE),
    re.compile(r"\bcrash\b|\bexception\b|\bsegfault\b|\babort\b", re.IGNORECASE),
    re.compile(r"\bdebug\b|\bverbose\b|\btrace\b", re.IGNORECASE),
    re.compile(r"opengl|gl error|gl_|memory|malloc|alloc", re.IGNORECASE),
]

_NETGAME_START = re.compile(
    r"starting netgame|netgame started|joining game|game started|net game|"
    r"connected to server|hosting game|new game",
    re.IGNORECASE,
)

_NETGAME_END = re.compile(
    r"game over|netgame ended|game ended|leaving game|disconnected from|"
    r"connection closed|host quit|server closed",
    re.IGNORECASE,
)


def _parse_gamelog_sessions(text: str) -> list[list[str]]:
    lines = text.splitlines()
    sessions: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if _SESSION_START.match(line) and current:
            sessions.append(current)
            current = [line]
        else:
            current.append(line)
    if current:
        sessions.append(current)
    sessions.reverse()
    return sessions


def _parse_netlog_sessions(text: str) -> list[dict]:
    lines = text.splitlines()
    sessions: list[dict] = []
    current: list[str] = []
    in_session = False
    complete = False
    for line in lines:
        if _NETGAME_START.search(line):
            if in_session and current:
                sessions.append({"lines": current, "complete": complete})
            current = [line]
            in_session = True
            complete = False
        elif _NETGAME_END.search(line) and in_session:
            current.append(line)
            complete = True
        else:
            current.append(line)
    if current:
        sessions.append({"lines": current, "complete": complete or not in_session})
    sessions.reverse()
    return sessions


def _apply_filter(lines: list[str], mode: str) -> list[str]:
    if mode == "raw":
        return lines
    patterns = _GAME_PATTERNS if mode == "game" else _DEBUG_PATTERNS
    return [line for line in lines if any(p.search(line) for p in patterns)]


class RecentPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("panel")
        self._game: str = "d1"
        self._mode: str = "gamelog"

        self._gamelog_sessions: list[list[str]] = []
        self._gamelog_mtime: float = 0.0
        self._filter_mode = "raw"
        self._filter_buttons: dict[str, QPushButton] = {}

        self._netlog_sessions: list[dict] = []
        self._netlog_mtime: float = 0.0

        self._live_timer = QTimer(self)
        self._live_timer.setInterval(_LIVE_INTERVAL_MS)
        self._live_timer.timeout.connect(self._poll_files)

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 36, 40, 36)
        layout.setSpacing(0)

        header_row = QHBoxLayout()
        header_row.setSpacing(0)

        title = QLabel("RECENT")
        title.setObjectName("panel-title")
        header_row.addWidget(title)

        header_row.addStretch()

        self._mode_btns: dict[str, QPushButton] = {}
        for label, mode in (("GAMELOG", "gamelog"), ("NETLOG", "netlog")):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setChecked(mode == "gamelog")
            btn.setObjectName("filter-btn-active" if mode == "gamelog" else "filter-btn")
            btn.setFixedWidth(88)
            btn.clicked.connect(lambda _, m=mode: self._switch_mode(m))
            self._mode_btns[mode] = btn
            header_row.addSpacing(6)
            header_row.addWidget(btn)

        layout.addLayout(header_row)

        self._subtitle = QLabel("Latest game session log entries")
        self._subtitle.setObjectName("section-label")
        layout.addWidget(self._subtitle)

        layout.addSpacing(16)

        controls = QHBoxLayout()
        controls.setSpacing(8)

        sessions_label = QLabel("Sessions:")
        sessions_label.setObjectName("section-label")
        controls.addWidget(sessions_label)

        self._session_count = QSpinBox()
        self._session_count.setRange(1, 20)
        self._session_count.setValue(3)
        self._session_count.setFixedWidth(64)
        self._session_count.valueChanged.connect(self._render)
        controls.addWidget(self._session_count)

        controls.addSpacing(12)

        for label, mode in (("RAW", "raw"), ("GAME", "game"), ("DEBUG", "debug")):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setChecked(mode == "raw")
            btn.setObjectName("filter-btn-active" if mode == "raw" else "filter-btn")
            btn.setFixedWidth(72)
            btn.clicked.connect(lambda checked, m=mode: self._set_filter(m))
            self._filter_buttons[mode] = btn
            controls.addWidget(btn)

        self._live_indicator = QLabel("LIVE")
        self._live_indicator.setObjectName("live-indicator")
        self._live_indicator.setVisible(False)
        controls.addWidget(self._live_indicator)

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

    def _switch_mode(self, mode: str) -> None:
        self._mode = mode
        for m, btn in self._mode_btns.items():
            is_active = m == mode
            btn.setChecked(is_active)
            btn.setObjectName("filter-btn-active" if is_active else "filter-btn")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        in_netlog = mode == "netlog"
        self._subtitle.setText(
            "Multiplayer session audit log — DROPPED, kills, events"
            if in_netlog
            else "Latest game session log entries"
        )
        for btn in self._filter_buttons.values():
            btn.setVisible(not in_netlog)
        self._live_indicator.setVisible(in_netlog and bool(self._netlog_sessions))
        self._session_count.setValue(5 if in_netlog else 3)
        self._content_area.clear()
        self._load_and_render()

    def _gamelog_path(self) -> Path | None:
        path = load_config().get(f"gamelog_path_{self._game}", "")
        return Path(path) if path else None

    def _netlog_path(self) -> Path | None:
        path = load_config().get(f"netlog_path_{self._game}", "")
        return Path(path) if path else None

    def _set_filter(self, mode: str) -> None:
        self._filter_mode = mode
        for m, btn in self._filter_buttons.items():
            is_active = m == mode
            btn.setChecked(is_active)
            btn.setObjectName("filter-btn-active" if is_active else "filter-btn")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self._render()

    def on_game_changed(self, game_key: str) -> None:
        self._game = game_key
        self._gamelog_mtime = 0.0
        self._netlog_mtime = 0.0
        self._load_and_render()

    def _load_and_render(self) -> None:
        if self._mode == "netlog":
            self._load_netlog()
        else:
            self._load_gamelog()
        self._render()

    def _load_gamelog(self) -> None:
        path = self._gamelog_path()
        if path is None:
            self._status_label.setText("No gamelog path configured — set it in Settings.")
            self._content_area.clear()
            self._gamelog_sessions = []
            return
        if not path.exists():
            self._status_label.setText(
                f"File not found: {path.name} — start the game once to generate it."
            )
            self._content_area.clear()
            self._gamelog_sessions = []
            return
        try:
            mtime = path.stat().st_mtime
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            self._status_label.setText(f"Could not read gamelog: {exc}")
            self._content_area.clear()
            self._gamelog_sessions = []
            return
        self._gamelog_mtime = mtime
        self._gamelog_sessions = _parse_gamelog_sessions(text)

    def _load_netlog(self) -> None:
        path = self._netlog_path()
        if path is None:
            self._status_label.setText("No netlog path configured — set it in Settings.")
            self._content_area.clear()
            self._netlog_sessions = []
            self._live_indicator.setVisible(False)
            return
        if not path.exists():
            self._status_label.setText(
                f"File not found: {path.name} — join a netgame once to generate it."
            )
            self._content_area.clear()
            self._netlog_sessions = []
            self._live_indicator.setVisible(False)
            return
        try:
            mtime = path.stat().st_mtime
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            self._status_label.setText(f"Could not read netlog: {exc}")
            self._content_area.clear()
            self._netlog_sessions = []
            self._live_indicator.setVisible(False)
            return
        self._netlog_mtime = mtime
        self._netlog_sessions = _parse_netlog_sessions(text)
        self._live_indicator.setVisible(True)

    def _poll_files(self) -> None:
        if self._mode == "netlog":
            path = self._netlog_path()
            if path and path.exists():
                try:
                    mtime = path.stat().st_mtime
                except OSError:
                    return
                if mtime != self._netlog_mtime:
                    self._load_and_render()
        else:
            path = self._gamelog_path()
            if path and path.exists():
                try:
                    mtime = path.stat().st_mtime
                except OSError:
                    return
                if mtime != self._gamelog_mtime:
                    self._load_and_render()

    def _render(self) -> None:
        if self._mode == "netlog":
            self._render_netlog()
        else:
            self._render_gamelog()

    def _render_gamelog(self) -> None:
        count = self._session_count.value()
        shown = self._gamelog_sessions[:count]
        if not shown:
            if not self._gamelog_sessions:
                return
            self._status_label.setText("No session data found in gamelog.")
            self._content_area.clear()
            return
        total = len(self._gamelog_sessions)
        mode_label = {"raw": "RAW", "game": "GAME", "debug": "DEBUG"}[self._filter_mode]
        self._status_label.setText(
            f"Showing {len(shown)} of {total} session(s) — newest first — {mode_label}"
        )
        scrollbar = self._content_area.verticalScrollBar()
        at_bottom = scrollbar.value() >= scrollbar.maximum() - 4
        parts: list[str] = []
        for i, session_lines in enumerate(shown):
            parts.append("=" * 60)
            parts.append(f"  SESSION {i + 1}")
            parts.append("=" * 60)
            filtered = _apply_filter(
                [line for line in session_lines if line.strip()],
                self._filter_mode,
            )
            parts.extend(filtered)
            parts.append("")
        self._content_area.setPlainText("\n".join(parts))
        if at_bottom:
            scrollbar.setValue(scrollbar.maximum())

    def _render_netlog(self) -> None:
        count = self._session_count.value()
        shown = self._netlog_sessions[:count]
        if not shown:
            if not self._netlog_sessions:
                return
            self._status_label.setText("No netgame data found in netlog.")
            self._content_area.clear()
            return
        total = len(self._netlog_sessions)
        self._status_label.setText(
            f"Showing {len(shown)} of {total} netgame session(s) — newest first"
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

"""Tracker panel — retro-tracker.game-server.cc live and archive views."""

from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout, QWidget

_TRACKER_LIVE = "https://retro-tracker.game-server.cc/"
_TRACKER_ARCHIVE = "https://retro-tracker.game-server.cc/archive/"


class StatsPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("panel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._browser = QWebEngineView(self)
        self._browser.load(QUrl(_TRACKER_LIVE))

        toolbar = self._build_toolbar()
        layout.addWidget(toolbar)

        divider = QWidget()
        divider.setFixedHeight(1)
        divider.setStyleSheet("background-color: #1f1f1f;")
        layout.addWidget(divider)

        layout.addWidget(self._browser, stretch=1)

    def _build_toolbar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(40)
        bar.setStyleSheet("background-color: #0a0a0a; border: none;")

        row = QHBoxLayout(bar)
        row.setContentsMargins(12, 0, 12, 0)
        row.setSpacing(10)

        self._live_btn = QPushButton("Live")
        self._live_btn.setFixedHeight(26)
        self._live_btn.setCheckable(True)
        self._live_btn.setChecked(True)
        self._live_btn.clicked.connect(self._go_live)
        row.addWidget(self._live_btn)

        self._archive_btn = QPushButton("Archive")
        self._archive_btn.setFixedHeight(26)
        self._archive_btn.setCheckable(True)
        self._archive_btn.setChecked(False)
        self._archive_btn.clicked.connect(self._go_archive)
        row.addWidget(self._archive_btn)

        row.addStretch()

        reload_btn = QPushButton("Reload")
        reload_btn.setFixedHeight(26)
        reload_btn.clicked.connect(self._browser.reload)
        row.addWidget(reload_btn)

        return bar

    def _go_live(self) -> None:
        self._live_btn.setChecked(True)
        self._archive_btn.setChecked(False)
        self._browser.load(QUrl(_TRACKER_LIVE))

    def _go_archive(self) -> None:
        self._live_btn.setChecked(False)
        self._archive_btn.setChecked(True)
        self._browser.load(QUrl(_TRACKER_ARCHIVE))

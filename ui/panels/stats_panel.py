"""Tracker panel — links to retro-tracker.game-server.cc."""

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

_TRACKER_LIVE = "https://retro-tracker.game-server.cc/"
_TRACKER_ARCHIVE = "https://retro-tracker.game-server.cc/archive/"


class StatsPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("panel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 36, 40, 36)
        layout.setSpacing(0)

        title = QLabel("TRACKER")
        title.setObjectName("panel-title")
        layout.addWidget(title)

        subtitle = QLabel("MULTIPLAYER SERVER BROWSER")
        subtitle.setObjectName("section-label")
        layout.addWidget(subtitle)

        layout.addSpacing(32)

        live_btn = QPushButton("Open Live Tracker")
        live_btn.setObjectName("about-link-btn")
        live_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(_TRACKER_LIVE)))
        layout.addWidget(live_btn)

        layout.addSpacing(12)

        archive_btn = QPushButton("Open Archive")
        archive_btn.setObjectName("about-link-btn")
        archive_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(_TRACKER_ARCHIVE)))
        layout.addWidget(archive_btn)

        layout.addStretch()

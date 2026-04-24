"""Wiki panel — links to descentnexus.com."""

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

_WIKI_HOME = "https://descentnexus.com/"


class WikiPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("panel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 36, 40, 36)
        layout.setSpacing(0)

        title = QLabel("WIKI")
        title.setObjectName("panel-title")
        layout.addWidget(title)

        subtitle = QLabel("DESCENT NEXUS COMMUNITY WIKI")
        subtitle.setObjectName("section-label")
        layout.addWidget(subtitle)

        layout.addSpacing(32)

        open_btn = QPushButton("Open Descent Nexus")
        open_btn.setObjectName("about-link-btn")
        open_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(_WIKI_HOME)))
        layout.addWidget(open_btn)

        layout.addStretch()

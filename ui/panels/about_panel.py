"""About panel."""

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout, QWidget

APP_VERSION = "b1.0"
DXXREDUX_URL = "https://github.com/dxx-redux/dxx-redux"


class AboutPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("panel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 36, 40, 36)
        layout.setSpacing(0)

        title = QLabel("DESCENTBUDDY")
        title.setObjectName("panel-title")
        layout.addWidget(title)

        version = QLabel(f"Version {APP_VERSION}")
        version.setObjectName("version-label")
        layout.addWidget(version)

        layout.addSpacing(28)

        byline = QLabel("Made by Code -- a Project D initiative.")
        byline.setObjectName("about-byline")
        layout.addWidget(byline)

        layout.addSpacing(8)

        desc = QLabel(
            "Descent Buddy wraps DXX-Redux to give Descent 1 and 2 players "
            "a modern companion: mission management, session tracking, community "
            "status, and more -- without touching the game itself."
        )
        desc.setObjectName("about-desc")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        layout.addSpacing(32)

        divider = QFrame()
        divider.setObjectName("about-divider")
        divider.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(divider)

        layout.addSpacing(24)

        port_label = QLabel("BUILT ON")
        port_label.setObjectName("section-label")
        layout.addWidget(port_label)

        layout.addSpacing(8)

        link_btn = QPushButton("DXX-Redux on GitHub")
        link_btn.setObjectName("about-link-btn")
        link_btn.setMinimumWidth(200)
        link_btn.setToolTip(DXXREDUX_URL)
        link_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(DXXREDUX_URL)))
        layout.addWidget(link_btn)

        layout.addStretch()

        footer = QLabel("Not affiliated with Parallax Software or Interplay Productions.")
        footer.setObjectName("version-label")
        footer.setWordWrap(True)
        layout.addWidget(footer)

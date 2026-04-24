"""About panel."""

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

APP_VERSION = "0.1.0"
DXXREDUX_URL = "https://github.com/dxx-redux/dxx-redux"


class AboutPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("panel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 36, 40, 36)
        layout.setSpacing(8)

        title = QLabel("ABOUT")
        title.setObjectName("panel-title")
        layout.addWidget(title)

        layout.addSpacing(24)

        app_name = QLabel("DescentBuddy")
        app_name.setObjectName("panel-title")
        app_name.setStyleSheet("font-size: 28px; letter-spacing: 3px;")
        layout.addWidget(app_name)

        version_lbl = QLabel(f"Version {APP_VERSION}")
        version_lbl.setObjectName("version-label")
        layout.addWidget(version_lbl)

        layout.addSpacing(20)

        desc = QLabel(
            "A companion launcher for Descent 1 via DXX-Redux.\n"
            "Supports version detection, mission management,\n"
            "stats tracking, and more — coming soon."
        )
        desc.setObjectName("section-label")
        desc.setStyleSheet("font-size: 13px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        layout.addSpacing(24)

        port_label = QLabel("Game Port")
        port_label.setObjectName("section-label")
        layout.addWidget(port_label)

        link_btn = QPushButton("DXX-Redux on GitHub →")
        link_btn.setFixedWidth(220)
        link_btn.setToolTip(DXXREDUX_URL)
        link_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(DXXREDUX_URL)))
        layout.addWidget(link_btn)

        layout.addStretch()

        footer = QLabel("Not affiliated with Parallax Software or Interplay Productions.")
        footer.setObjectName("version-label")
        footer.setWordWrap(True)
        layout.addWidget(footer)

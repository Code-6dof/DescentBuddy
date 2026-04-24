"""Navigation sidebar widget."""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QListWidget, QListWidgetItem
from PyQt6.QtCore import Qt


# Navigation labels in order — each corresponds to one stacked panel
_NAV_ITEMS = [
    "LAUNCH",
    "RECENT",
    "NETLOG",
    "MISSIONS",
    "DEMOS",
    "COMMUNITY",
    "RDL",
    "WIKI",
    "TRACKER",
]


class Sidebar(QListWidget):
    """Left-hand navigation list.

    Emits ``panel_changed(index)`` when the user selects a different item.
    """

    panel_changed = pyqtSignal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(190)
        self.setSpacing(2)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        for label in _NAV_ITEMS:
            self.addItem(QListWidgetItem(label))

        self.setCurrentRow(0)
        self.currentRowChanged.connect(self.panel_changed)

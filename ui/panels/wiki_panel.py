"""Wiki panel — embedded browser for descentnexus.com."""

from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

_WIKI_HOME = "https://descentnexus.com/"


class WikiPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("panel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._browser = QWebEngineView(self)
        self._browser.load(QUrl(_WIKI_HOME))

        toolbar = self._build_toolbar()
        layout.addWidget(toolbar)

        divider = QWidget()
        divider.setObjectName("browser-divider")
        divider.setFixedHeight(1)
        layout.addWidget(divider)

        layout.addWidget(self._browser, stretch=1)

    def _build_toolbar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("browser-toolbar")
        bar.setFixedHeight(40)

        row = QHBoxLayout(bar)
        row.setContentsMargins(12, 0, 12, 0)
        row.setSpacing(10)

        back_btn = QPushButton("<")
        back_btn.setFixedWidth(30)
        back_btn.setFixedHeight(26)
        back_btn.setToolTip("Back")
        back_btn.clicked.connect(lambda: self._browser.back())
        row.addWidget(back_btn)

        forward_btn = QPushButton(">")
        forward_btn.setFixedWidth(30)
        forward_btn.setFixedHeight(26)
        forward_btn.setToolTip("Forward")
        forward_btn.clicked.connect(lambda: self._browser.forward())
        row.addWidget(forward_btn)

        reload_btn = QPushButton("Reload")
        reload_btn.setFixedHeight(26)
        reload_btn.clicked.connect(self._browser.reload)
        row.addWidget(reload_btn)

        url_label = QLabel(_WIKI_HOME)
        url_label.setObjectName("browser-url")
        url_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row.addWidget(url_label, stretch=1)

        home_btn = QPushButton("Home")
        home_btn.setFixedHeight(26)
        home_btn.clicked.connect(lambda: self._browser.load(QUrl(_WIKI_HOME)))
        row.addWidget(home_btn)

        return bar

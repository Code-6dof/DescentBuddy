"""RDL panel — embedded browser locked to rdl.descentnexus.com with persistent session."""

import os
import sys
from pathlib import Path

from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

_RDL_BASE = "https://rdl.descentnexus.com"
_ALLOWED_HOST = "rdl.descentnexus.com"


def _profile_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path.home() / ".config"
    return base / "descentbuddy" / "rdl_profile"


_PROFILE_DIR = _profile_dir()


class _RdlPage(QWebEnginePage):
    """WebEnginePage that restricts navigation to rdl.descentnexus.com."""

    def acceptNavigationRequest(
        self, url: QUrl, nav_type: QWebEnginePage.NavigationType, is_main_frame: bool
    ) -> bool:
        if not is_main_frame:
            return True
        if url.host() == _ALLOWED_HOST:
            return True
        return False


class RdlPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("panel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        toolbar = self._build_toolbar()
        layout.addWidget(toolbar)

        divider = QWidget()
        divider.setObjectName("browser-divider")
        divider.setFixedHeight(1)
        layout.addWidget(divider)

        _PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        self._profile = QWebEngineProfile("rdl_session", self)
        self._profile.setPersistentStoragePath(str(_PROFILE_DIR))
        self._profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies
        )

        self._page = _RdlPage(self._profile, self)

        self._browser = QWebEngineView(self)
        self._browser.setPage(self._page)
        self._browser.setZoomFactor(0.75)
        self._browser.load(QUrl(_RDL_BASE))
        layout.addWidget(self._browser, stretch=1)

        self._page.titleChanged.connect(self._on_title_changed)

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
        back_btn.clicked.connect(self._go_back)
        row.addWidget(back_btn)

        forward_btn = QPushButton(">")
        forward_btn.setFixedWidth(30)
        forward_btn.setFixedHeight(26)
        forward_btn.setToolTip("Forward")
        forward_btn.clicked.connect(self._go_forward)
        row.addWidget(forward_btn)

        reload_btn = QPushButton("Reload")
        reload_btn.setFixedHeight(26)
        reload_btn.clicked.connect(self._browser_reload)
        row.addWidget(reload_btn)

        url_label = QLabel(_RDL_BASE)
        url_label.setObjectName("browser-url")
        url_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row.addWidget(url_label, stretch=1)

        home_btn = QPushButton("Home")
        home_btn.setFixedHeight(26)
        home_btn.clicked.connect(self._go_home)
        row.addWidget(home_btn)

        self._back_btn = back_btn
        self._forward_btn = forward_btn

        return bar

    def _go_back(self) -> None:
        self._browser.back()

    def _go_forward(self) -> None:
        self._browser.forward()

    def _browser_reload(self) -> None:
        self._browser.reload()

    def _go_home(self) -> None:
        self._browser.load(QUrl(_RDL_BASE))

    def navigate(self, url: str) -> None:
        """Load a URL in the embedded browser. Must be on rdl.descentnexus.com."""
        self._browser.load(QUrl(url))

    def _on_title_changed(self, title: str) -> None:
        pass

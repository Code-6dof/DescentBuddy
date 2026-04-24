"""Main application window."""

import sys
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ui.sidebar import Sidebar
from ui.panels.launch_panel import LaunchPanel
from ui.panels.recent_panel import RecentPanel
from ui.panels.missions_panel import MissionsPanel
from ui.panels.demos_panel import DemosPanel
from ui.panels.community_panel import CommunityPanel
from ui.panels.rdl_panel import RdlPanel
from ui.panels.wiki_panel import WikiPanel
from ui.panels.stats_panel import StatsPanel
from ui.panels.about_panel import AboutPanel
from ui.notification_inbox import NotificationInbox


class MainWindow(QMainWindow):
    """Top-level window: header bar + sidebar + stacked content panels."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("DescentBuddy")
        self.setMinimumSize(860, 560)
        self.resize(1000, 640)

        central = QWidget()
        self.setCentralWidget(central)

        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Header bar ────────────────────────────────────────────────
        header = self._build_header()
        outer.addWidget(header)

        # ── Body: sidebar + content ───────────────────────────────────
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        self._sidebar = Sidebar()
        body.addWidget(self._sidebar)

        self._stack = QStackedWidget()
        self._stack.setObjectName("panel")

        self._panels = [
            LaunchPanel(),
            RecentPanel(),
            MissionsPanel(),
            DemosPanel(),
            CommunityPanel(),
            RdlPanel(),
            WikiPanel(),
            StatsPanel(),
        ]
        for panel in self._panels:
            self._stack.addWidget(panel)

        launch_panel: LaunchPanel = self._panels[0]
        recent_panel: RecentPanel = self._panels[1]
        missions_panel: MissionsPanel = self._panels[2]
        demos_panel: DemosPanel = self._panels[3]
        community_panel: CommunityPanel = self._panels[4]

        launch_panel.game_changed.connect(recent_panel.on_game_changed)
        launch_panel.game_changed.connect(missions_panel.on_game_changed)
        launch_panel.game_changed.connect(demos_panel.on_game_changed)

        QTimer.singleShot(0, launch_panel.emit_current_game)
        QTimer.singleShot(2000, missions_panel.start_background_update)
        self._community_panel = community_panel

        community_panel.user_signed_in.connect(self._notification_inbox.set_user)
        community_panel.user_signed_out.connect(self._notification_inbox.clear_user)
        self._notification_inbox.open_url_in_rdl.connect(self._open_url_in_rdl)

        self._rdl_panel: RdlPanel = self._panels[5]

        app = QApplication.instance()
        assert app is not None
        app.aboutToQuit.connect(community_panel.go_offline)
        app.aboutToQuit.connect(launch_panel.save_active_sessions)

        body.addWidget(self._stack, stretch=1)

        body_widget = QWidget()
        body_widget.setLayout(body)
        outer.addWidget(body_widget, stretch=1)

        self._missions_panel = missions_panel
        self._sidebar.panel_changed.connect(self._stack.setCurrentIndex)
        self._sidebar.panel_changed.connect(self._on_panel_changed)

    def _on_panel_changed(self, index: int) -> None:
        if index == 2:
            self._missions_panel.start_background_update()

    def _open_url_in_rdl(self, url: str) -> None:
        self._rdl_panel.navigate(url)
        self._sidebar.setCurrentRow(5)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("app-header")
        header.setFixedHeight(52)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(0)

        logo_main = QLabel("DESCENT")
        logo_main.setObjectName("header-logo-main")
        layout.addWidget(logo_main)

        logo_accent = QLabel("BUDDY")
        logo_accent.setObjectName("header-logo-accent")
        layout.addWidget(logo_accent)

        layout.addStretch(1)

        icon_label = QLabel()
        icon_label.setObjectName("header-center-icon")
        icon_label.setFixedSize(26, 26)
        if hasattr(sys, "_MEIPASS"):
            icon_path = Path(sys._MEIPASS) / "descentbuddy.png"
        else:
            icon_path = Path(__file__).parent.parent / "build" / "descentbuddy.png"
        if icon_path.exists():
            pixmap = QPixmap(str(icon_path)).scaled(
                26, 26, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            icon_label.setPixmap(pixmap)
        layout.addWidget(icon_label)

        layout.addSpacing(8)

        tagline = QLabel("A Project D initiative by Code")
        tagline.setObjectName("header-tagline")
        layout.addWidget(tagline)

        layout.addStretch(1)

        self._notification_inbox = NotificationInbox()
        layout.addWidget(self._notification_inbox)
        layout.addSpacing(12)

        account_btn = QPushButton("Account")
        account_btn.setObjectName("account-btn")

        account_menu = QMenu(account_btn)
        settings_action = account_menu.addAction("Settings")
        account_menu.addSeparator()
        about_action = account_menu.addAction("About DescentBuddy")
        account_menu.addSeparator()
        sign_out_action = account_menu.addAction("Sign Out of Community")
        settings_action.triggered.connect(self._show_settings_dialog)
        about_action.triggered.connect(self._show_about_dialog)
        sign_out_action.triggered.connect(self._sign_out_account)
        account_btn.setMenu(account_menu)

        layout.addWidget(account_btn)

        return header

    def _show_settings_dialog(self) -> None:
        from ui.app_settings_dialog import AppSettingsDialog
        dialog = AppSettingsDialog(self)
        dialog.display_name_changed.connect(self._community_panel.set_display_name)
        dialog.exec()

    def _show_about_dialog(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("About DescentBuddy")
        dialog.setMinimumWidth(500)
        dialog.setMinimumHeight(400)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(0, 0, 0, 0)
        about = AboutPanel(dialog)
        layout.addWidget(about)
        dialog.exec()

    def _sign_out_account(self) -> None:
        self._community_panel.sign_out()

"""Community panel — see who is online and manage your presence."""

import sys

from PyQt6.QtCore import Qt, QRect, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.app_config import load_config, save_config
from core.firebase_auth import (
    clear_session,
    fetch_rdladder_username_public,
    get_db_token,
    load_session,
    sign_in,
)
from core.presence_service import (
    delete_presence,
    fetch_all_presence,
    write_member,
    write_presence,
)

_STATUS_LABELS = {
    "online": "Online",
    "busy": "Busy",
    "dnd": "Do Not Disturb",
}

_STATUS_COLORS = {
    "online": "#3cb371",
    "busy": "#e85c00",
    "dnd": "#cc1a00",
    "invisible": "#4a4540",
}

_COMBO_ITEMS = ["Online", "Busy", "Do Not Disturb", "Invisible"]
_COMBO_KEYS = ["online", "busy", "dnd", "invisible"]

_HEARTBEAT_MS = 60_000
_PRESENCE_FETCH_MS = 30_000


def _make_avatar_pixmap(initial: str, color: str) -> QPixmap:
    size = 48
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QBrush(QColor(color)))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(0, 0, size, size)
    font = QFont()
    font.setPixelSize(22)
    font.setBold(True)
    painter.setFont(font)
    painter.setPen(QColor("#ffffff"))
    painter.drawText(QRect(0, 0, size, size), Qt.AlignmentFlag.AlignCenter, initial.upper())
    painter.end()
    return pixmap


class _SignInThread(QThread):
    success = pyqtSignal(dict)
    failure = pyqtSignal(str)

    def __init__(self, email: str, password: str, parent=None) -> None:
        super().__init__(parent)
        self._email = email
        self._password = password

    def run(self) -> None:
        try:
            self.success.emit(sign_in(self._email, self._password))
        except Exception as exc:
            self.failure.emit(str(exc))


class _TokenThread(QThread):
    done = pyqtSignal(str)

    def run(self) -> None:
        self.done.emit(get_db_token() or "")


class _FetchPresenceThread(QThread):
    result = pyqtSignal(list)

    def run(self) -> None:
        self.result.emit(fetch_all_presence())


class _WritePresenceThread(QThread):
    token_expired = pyqtSignal()

    def __init__(self, uid: str, username: str, status: str, db_token: str, parent=None) -> None:
        super().__init__(parent)
        self._uid = uid
        self._username = username
        self._status = status
        self._db_token = db_token

    def run(self) -> None:
        ok = write_presence(self._uid, self._username, self._status, self._db_token)
        if not ok:
            self.token_expired.emit()


class _DeletePresenceThread(QThread):
    def __init__(self, uid: str, db_token: str, parent=None) -> None:
        super().__init__(parent)
        self._uid = uid
        self._db_token = db_token

    def run(self) -> None:
        delete_presence(self._uid, self._db_token)


class _WriteMemberThread(QThread):
    def __init__(self, uid: str, username: str, db_token: str, parent=None) -> None:
        super().__init__(parent)
        self._uid = uid
        self._username = username
        self._db_token = db_token

    def run(self) -> None:
        write_member(self._uid, self._username, self._db_token)


class _UsernameRefreshThread(QThread):
    done = pyqtSignal(str)

    def __init__(self, uid: str, parent=None) -> None:
        super().__init__(parent)
        self._uid = uid

    def run(self) -> None:
        self.done.emit(fetch_rdladder_username_public(self._uid) or "")


class _InviteThread(QThread):
    def __init__(self, target_uid: str, sender_name: str, id_token: str, parent=None) -> None:
        super().__init__(parent)
        self._target_uid = target_uid
        self._sender_name = sender_name
        self._id_token = id_token

    def run(self) -> None:
        from core.notification_service import send_invitation
        send_invitation(self._target_uid, self._sender_name, self._id_token)


class _IdTokenRefreshThread(QThread):
    done = pyqtSignal(str)

    def __init__(self, refresh_token: str, parent=None) -> None:
        super().__init__(parent)
        self._refresh_token = refresh_token

    def run(self) -> None:
        from core.firebase_auth import get_fresh_id_token
        self.done.emit(get_fresh_id_token(self._refresh_token) or "")


class CommunityPanel(QWidget):
    user_signed_in = pyqtSignal(str, str)   # uid, id_token
    user_signed_out = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("panel")

        self._session: dict | None = None
        self._db_token: str | None = None
        self._current_status = "online"
        self._threads: list[QThread] = []
        self._display_name: str = load_config().get("community_display_name", "")

        self._heartbeat_timer = QTimer(self)
        self._heartbeat_timer.setInterval(_HEARTBEAT_MS)
        self._heartbeat_timer.timeout.connect(self._heartbeat)

        self._presence_timer = QTimer(self)
        self._presence_timer.setInterval(_PRESENCE_FETCH_MS)
        self._presence_timer.timeout.connect(self._fetch_players)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._stack = QStackedWidget()
        self._stack.addWidget(self._build_login_page())
        self._stack.addWidget(self._build_community_page())
        root.addWidget(self._stack)

        self._try_restore_session()

    # ------------------------------------------------------------------
    # Page builders
    # ------------------------------------------------------------------

    def _build_login_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("panel")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 36, 40, 36)
        layout.setSpacing(0)

        title = QLabel("COMMUNITY")
        title.setObjectName("panel-title")
        layout.addWidget(title)

        layout.addSpacing(6)

        subtitle = QLabel("Sign in with your RDL Ladder account to see who is online")
        subtitle.setObjectName("section-label")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        layout.addSpacing(32)

        email_label = QLabel("EMAIL")
        email_label.setObjectName("section-label")
        layout.addWidget(email_label)
        layout.addSpacing(6)

        self._email_edit = QLineEdit()
        self._email_edit.setPlaceholderText("your@email.com")
        layout.addWidget(self._email_edit)

        layout.addSpacing(16)

        pw_label = QLabel("PASSWORD")
        pw_label.setObjectName("section-label")
        layout.addWidget(pw_label)
        layout.addSpacing(6)

        self._pw_edit = QLineEdit()
        self._pw_edit.setPlaceholderText("Password")
        self._pw_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._pw_edit.returnPressed.connect(self._start_sign_in)
        layout.addWidget(self._pw_edit)

        layout.addSpacing(20)

        self._sign_in_btn = QPushButton("Sign In")
        self._sign_in_btn.setFixedWidth(120)
        self._sign_in_btn.clicked.connect(self._start_sign_in)
        layout.addWidget(self._sign_in_btn)

        layout.addSpacing(10)

        self._login_error = QLabel("")
        self._login_error.setObjectName("login-error")
        self._login_error.setWordWrap(True)
        self._login_error.hide()
        layout.addWidget(self._login_error)

        layout.addStretch()
        return page

    def _build_community_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("panel")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 36, 40, 36)
        layout.setSpacing(0)

        # Header: title left, avatar + username + status + sign-out right
        header_row = QHBoxLayout()
        header_row.setSpacing(0)

        title = QLabel("COMMUNITY")
        title.setObjectName("panel-title")
        header_row.addWidget(title, 0, Qt.AlignmentFlag.AlignBottom)
        header_row.addStretch()

        self._avatar_label = QLabel()
        self._avatar_label.setFixedSize(48, 48)
        header_row.addWidget(self._avatar_label, 0, Qt.AlignmentFlag.AlignVCenter)

        header_row.addSpacing(10)

        self._username_label = QLabel("")
        self._username_label.setObjectName("community-username")
        header_row.addWidget(self._username_label, 0, Qt.AlignmentFlag.AlignVCenter)

        header_row.addSpacing(16)

        self._status_combo = QComboBox()
        for item in _COMBO_ITEMS:
            self._status_combo.addItem(item)
        self._status_combo.setFixedWidth(160)
        self._status_combo.currentIndexChanged.connect(self._on_status_changed)
        header_row.addWidget(self._status_combo, 0, Qt.AlignmentFlag.AlignVCenter)

        header_row.addSpacing(12)

        self._sign_out_btn = QPushButton("Sign Out")
        self._sign_out_btn.setFixedWidth(80)
        self._sign_out_btn.clicked.connect(self._sign_out)
        header_row.addWidget(self._sign_out_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        layout.addLayout(header_row)
        layout.addSpacing(20)

        divider1 = QFrame()
        divider1.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(divider1)

        layout.addSpacing(10)

        self._display_name_label = QLabel("")
        self._display_name_label.setObjectName("section-label")
        layout.addWidget(self._display_name_label)

        layout.addSpacing(10)

        divider_players = QFrame()
        divider_players.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(divider_players)

        layout.addSpacing(14)

        players_header = QHBoxLayout()
        self._players_label = QLabel("ONLINE PLAYERS")
        self._players_label.setObjectName("section-label")
        players_header.addWidget(self._players_label)
        players_header.addStretch()
        self._fetch_status = QLabel("")
        self._fetch_status.setObjectName("fetch-status")
        players_header.addWidget(self._fetch_status)
        layout.addLayout(players_header)

        layout.addSpacing(8)

        self._table = QTableWidget()
        self._table.setObjectName("mission-table")
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels(["", "PLAYER", ""])
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.setColumnWidth(0, 28)
        self._table.setColumnWidth(2, 70)
        self._table.horizontalHeader().setStretchLastSection(False)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._table.setShowGrid(False)
        layout.addWidget(self._table, stretch=1)

        layout.addSpacing(8)

        self._bottom_status = QLabel("")
        self._bottom_status.setObjectName("section-label")
        layout.addWidget(self._bottom_status)

        layout.addSpacing(20)

        discord_divider = QFrame()
        discord_divider.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(discord_divider)

        layout.addSpacing(14)

        discord_heading = QLabel("DISCORD")
        discord_heading.setObjectName("section-label")
        layout.addWidget(discord_heading)

        layout.addSpacing(8)

        discord_row = QHBoxLayout()
        discord_row.setSpacing(8)

        discord_label = QLabel("Show Rich Presence while playing")
        discord_label.setToolTip(
            "When enabled, your Discord status will show which game you are playing\n"
            "while a game is running through DescentBuddy."
        )
        discord_row.addWidget(discord_label, 1)

        self._discord_checkbox = QCheckBox()
        self._discord_checkbox.setChecked(
            load_config().get("discord_presence_enabled", True)
        )
        self._discord_checkbox.stateChanged.connect(self._on_discord_toggled)
        discord_row.addWidget(self._discord_checkbox)

        layout.addLayout(discord_row)

        if sys.platform != "win32":
            layout.addSpacing(8)
            note = QLabel(
                "Linux setup: Discord must expose its IPC socket at "
                "$XDG_RUNTIME_DIR/discord-ipc-0.\n"
                "Flatpak/Goofcord users: run once in a terminal --\n"
                "  ln -sf $XDG_RUNTIME_DIR/.flatpak/<app-id>/xdg-run/discord-ipc-0 "
                "$XDG_RUNTIME_DIR/discord-ipc-0\n"
                "Replace <app-id> with com.discordapp.Discord or "
                "io.github.milkshiift.GoofCord as appropriate.\n"
                "For Goofcord, also enable arRPC in its settings."
            )
            note.setObjectName("section-label")
            note.setWordWrap(True)
            layout.addWidget(note)

        layout.addStretch()
        return page

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------

    def _on_discord_toggled(self, state: int) -> None:
        enabled = bool(state)
        config = load_config()
        config["discord_presence_enabled"] = enabled
        save_config(config)
        if not enabled:
            from core.discord_presence import clear_presence
            clear_presence()

    def _try_restore_session(self) -> None:
        session = load_session()
        if session:
            self._session = session
            self._get_db_token()

    def _get_db_token(self) -> None:
        thread = _TokenThread(self)
        thread.done.connect(self._on_token_fetched)
        thread.finished.connect(lambda: self._prune_thread(thread))
        self._threads.append(thread)
        thread.start()

    def _on_token_fetched(self, token: str) -> None:
        if token:
            self._db_token = token
        self._refresh_username_then_enter()

    def _refresh_username_then_enter(self) -> None:
        thread = _UsernameRefreshThread(self._session["uid"], self)
        thread.done.connect(self._on_username_refreshed)
        thread.finished.connect(lambda: self._prune_thread(thread))
        self._threads.append(thread)
        thread.start()

    def _on_username_refreshed(self, username: str) -> None:
        if username and username != self._session.get("username"):
            self._session["username"] = username
            from core.firebase_auth import _save_session
            _save_session(self._session)
        if not self._session.get("idToken") and self._session.get("refreshToken"):
            self._refresh_id_token_then_enter()
        else:
            self._enter_community_view()

    def _refresh_id_token_then_enter(self) -> None:
        thread = _IdTokenRefreshThread(self._session["refreshToken"], self)
        thread.done.connect(self._on_id_token_refreshed)
        thread.finished.connect(lambda: self._prune_thread(thread))
        self._threads.append(thread)
        thread.start()

    def _on_id_token_refreshed(self, id_token: str) -> None:
        if id_token:
            self._session["idToken"] = id_token
        self._enter_community_view()

    def _enter_community_view(self) -> None:
        username = self._session["username"]
        initial = username[0] if username else "?"
        default_status = load_config().get("default_status", "online")
        default_index = _COMBO_KEYS.index(default_status) if default_status in _COMBO_KEYS else 0
        color = _STATUS_COLORS.get(_COMBO_KEYS[default_index], "#4a4540")
        self._avatar_label.setPixmap(_make_avatar_pixmap(initial, color))
        self._username_label.setText(username)

        self._status_combo.blockSignals(True)
        self._status_combo.setCurrentIndex(default_index)
        self._status_combo.blockSignals(False)
        self._current_status = _COMBO_KEYS[default_index]
        self._stack.setCurrentIndex(1)

        self._update_display_name_label()

        if self._db_token:
            self._write_member_now()
            if self._current_status != "invisible":
                self._write_presence_now()
                self._heartbeat_timer.start()

        self._fetch_players()
        self._presence_timer.start()
        self.user_signed_in.emit(
            self._session["uid"], self._session.get("idToken", "")
        )

    def _start_sign_in(self) -> None:
        email = self._email_edit.text().strip()
        password = self._pw_edit.text()
        if not email or not password:
            self._show_login_error("Enter your email and password.")
            return
        self._sign_in_btn.setEnabled(False)
        self._sign_in_btn.setText("Signing in...")
        self._login_error.hide()

        thread = _SignInThread(email, password, self)
        thread.success.connect(self._on_sign_in_success)
        thread.failure.connect(self._on_sign_in_failure)
        thread.finished.connect(lambda: self._prune_thread(thread))
        self._threads.append(thread)
        thread.start()

    def _on_sign_in_success(self, session: dict) -> None:
        self._session = session
        self._sign_in_btn.setEnabled(True)
        self._sign_in_btn.setText("Sign In")
        self._get_db_token()

    def _on_sign_in_failure(self, error: str) -> None:
        self._sign_in_btn.setEnabled(True)
        self._sign_in_btn.setText("Sign In")
        self._show_login_error(error)

    def _show_login_error(self, msg: str) -> None:
        self._login_error.setText(msg)
        self._login_error.show()

    def _sign_out(self) -> None:
        self._heartbeat_timer.stop()
        self._presence_timer.stop()
        if self._session and self._db_token and self._current_status != "invisible":
            thread = _DeletePresenceThread(self._session["uid"], self._db_token, self)
            thread.finished.connect(lambda: self._prune_thread(thread))
            self._threads.append(thread)
            thread.start()
        self._session = None
        self._db_token = None
        clear_session()
        self._stack.setCurrentIndex(0)
        self.user_signed_out.emit()

    def sign_out(self) -> None:
        """Sign out of the community session. Safe to call when not signed in."""
        if self._session:
            self._sign_out()

    # ------------------------------------------------------------------
    # Presence
    # ------------------------------------------------------------------

    def _heartbeat(self) -> None:
        if self._session and self._db_token and self._current_status != "invisible":
            display = self._display_name or self._session["username"]
            thread = _WritePresenceThread(
                self._session["uid"],
                display,
                self._current_status,
                self._db_token,
                self,
            )
            thread.token_expired.connect(self._on_token_expired)
            thread.finished.connect(lambda: self._prune_thread(thread))
            self._threads.append(thread)
            thread.start()

    def _write_presence_now(self) -> None:
        if not self._session or not self._db_token:
            return
        display = self._display_name or self._session["username"]
        thread = _WritePresenceThread(
            self._session["uid"],
            display,
            self._current_status,
            self._db_token,
            self,
        )
        thread.token_expired.connect(self._on_token_expired)
        thread.finished.connect(lambda: self._prune_thread(thread))
        self._threads.append(thread)
        thread.start()

    def _write_member_now(self) -> None:
        if not self._session or not self._db_token:
            return
        thread = _WriteMemberThread(
            self._session["uid"],
            self._session["username"],
            self._db_token,
            self,
        )
        thread.finished.connect(lambda: self._prune_thread(thread))
        self._threads.append(thread)
        thread.start()

    def _on_token_expired(self) -> None:
        self._db_token = None
        thread = _TokenThread(self)
        thread.done.connect(self._on_token_refreshed)
        thread.finished.connect(lambda: self._prune_thread(thread))
        self._threads.append(thread)
        thread.start()

    def _on_token_refreshed(self, token: str) -> None:
        if token:
            self._db_token = token
            self._write_presence_now()

    def _on_status_changed(self, index: int) -> None:
        new_status = _COMBO_KEYS[index]
        if new_status == self._current_status:
            return
        old_status = self._current_status
        self._current_status = new_status

        if self._session:
            initial = self._session["username"][0] if self._session["username"] else "?"
            self._avatar_label.setPixmap(
                _make_avatar_pixmap(initial, _STATUS_COLORS.get(new_status, "#4a4540"))
            )

        if new_status == "invisible":
            self._heartbeat_timer.stop()
            if self._session and self._db_token:
                thread = _DeletePresenceThread(self._session["uid"], self._db_token, self)
                thread.finished.connect(self._fetch_players)
                thread.finished.connect(lambda: self._prune_thread(thread))
                self._threads.append(thread)
                thread.start()
        else:
            if old_status == "invisible":
                self._heartbeat_timer.start()
            self._write_presence_now()
            QTimer.singleShot(1500, self._fetch_players)

    # ------------------------------------------------------------------
    # Player list
    # ------------------------------------------------------------------

    def _fetch_players(self) -> None:
        self._fetch_status.setText("Refreshing...")
        thread = _FetchPresenceThread(self)
        thread.result.connect(self._on_players_fetched)
        thread.finished.connect(lambda: self._prune_thread(thread))
        self._threads.append(thread)
        thread.start()

    def _on_players_fetched(self, players: list) -> None:
        self._fetch_status.setText("")
        own_uid = self._session["uid"] if self._session else None

        sorted_players = sorted(
            players,
            key=lambda p: (0 if p["uid"] == own_uid else 1, p["username"].lower()),
        )

        self._players_label.setText(f"ONLINE PLAYERS ({len(sorted_players)})")
        self._table.setRowCount(len(sorted_players))

        for row, player in enumerate(sorted_players):
            status = player["status"]
            color = _STATUS_COLORS.get(status, "#3a3530")
            status_label = _STATUS_LABELS.get(status, status.title())

            dot = QTableWidgetItem("●")
            dot.setForeground(QColor(color))
            dot.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            dot.setToolTip(status_label)
            dot.setFlags(dot.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self._table.setItem(row, 0, dot)

            name_text = player["username"]
            if player["uid"] == own_uid:
                name_text += " (you)"
            name_item = QTableWidgetItem(name_text)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self._table.setItem(row, 1, name_item)

            if player["uid"] != own_uid:
                invite_btn = QPushButton("Invite")
                invite_btn.setFixedWidth(58)
                invite_btn.clicked.connect(
                    lambda checked, uid=player["uid"], uname=player["username"], btn=invite_btn:
                        self._send_invite(uid, uname, btn)
                )
                self._table.setCellWidget(row, 2, invite_btn)

            self._table.setRowHeight(row, 32)

        if len(sorted_players) == 0:
            self._bottom_status.setText("No one else is online right now.")
        else:
            self._bottom_status.setText("")

    def set_display_name(self, name: str) -> None:
        self._display_name = name
        self._update_display_name_label()
        if self._session and self._db_token and self._current_status != "invisible":
            self._write_presence_now()

    def _update_display_name_label(self) -> None:
        if self._display_name:
            self._display_name_label.setText(f"Shown as: {self._display_name}")
        else:
            self._display_name_label.setText("")

    def _send_invite(self, target_uid: str, target_username: str, btn: QPushButton) -> None:
        if not self._session:
            return
        id_token = self._session.get("idToken", "")
        if not id_token:
            return
        btn.setEnabled(False)
        btn.setText("Sent")
        sender = self._display_name or self._session.get("username", "Someone")
        thread = _InviteThread(target_uid, sender, id_token, self)
        thread.finished.connect(lambda: self._prune_thread(thread))
        self._threads.append(thread)
        thread.start()

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def go_offline(self) -> None:
        """Call on app quit to remove presence from Firestore."""
        self._heartbeat_timer.stop()
        self._presence_timer.stop()
        if self._session and self._db_token and self._current_status != "invisible":
            delete_presence(self._session["uid"], self._db_token)

    def _prune_thread(self, thread: QThread) -> None:
        if thread in self._threads:
            self._threads.remove(thread)

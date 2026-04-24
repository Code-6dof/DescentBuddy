"""Notification inbox widget for the application header bar.

Polls the rdladder userNotifications collection for the signed-in user and
shows unread count on the button. Clicking opens a popup listing notifications.
"""

from datetime import datetime, timezone

from PyQt6.QtCore import QThread, QTimer, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.notification_service import (
    fetch_user_notifications,
    mark_all_notifications_read,
)

_POLL_INTERVAL_MS = 120_000  # 2 minutes
_RDL_BASE_URL = "https://rdl.descentnexus.com"


def _relative_time(timestamp_str: str) -> str:
    if not timestamp_str:
        return ""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        seconds = int((datetime.now(timezone.utc) - dt).total_seconds())
        if seconds < 60:
            return "just now"
        if seconds < 3600:
            return f"{seconds // 60}m ago"
        if seconds < 86400:
            return f"{seconds // 3600}h ago"
        return f"{seconds // 86400}d ago"
    except Exception:
        return ""


class _FetchThread(QThread):
    result = pyqtSignal(list)

    def __init__(self, uid: str, id_token: str | None, parent=None) -> None:
        super().__init__(parent)
        self._uid = uid
        self._id_token = id_token

    def run(self) -> None:
        self.result.emit(fetch_user_notifications(self._uid, self._id_token))


class _MarkReadThread(QThread):
    def __init__(self, notifications: list, id_token: str, parent=None) -> None:
        super().__init__(parent)
        self._notifications = notifications
        self._id_token = id_token

    def run(self) -> None:
        mark_all_notifications_read(self._notifications, self._id_token)


class _NotificationPopup(QFrame):
    mark_requested = pyqtSignal(list)
    url_clicked = pyqtSignal(str)

    def __init__(
        self,
        notifications: list[dict],
        id_token: str | None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent, Qt.WindowType.Popup)
        self.setObjectName("notification-popup")
        self.setFixedWidth(400)
        self._id_token = id_token
        self._notifications = notifications

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        popup_header = QWidget()
        popup_header.setObjectName("notification-popup-header")
        header_layout = QHBoxLayout(popup_header)
        header_layout.setContentsMargins(16, 10, 16, 10)
        header_title = QLabel("NOTIFICATIONS")
        header_title.setObjectName("section-label")
        header_layout.addWidget(header_title)
        header_layout.addStretch()
        outer.addWidget(popup_header)

        divider_top = QFrame()
        divider_top.setFrameShape(QFrame.Shape.HLine)
        outer.addWidget(divider_top)

        scroll_content = QWidget()
        self._rows_layout = QVBoxLayout(scroll_content)
        self._rows_layout.setContentsMargins(0, 0, 0, 0)
        self._rows_layout.setSpacing(0)
        self._populate()
        self._rows_layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidget(scroll_content)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setMaximumHeight(420)
        outer.addWidget(scroll)

        divider_bottom = QFrame()
        divider_bottom.setFrameShape(QFrame.Shape.HLine)
        outer.addWidget(divider_bottom)

        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(16, 8, 16, 8)
        footer_layout.addStretch()

        unread = [n for n in self._notifications if not n.get("read")]
        if unread and id_token:
            mark_btn = QPushButton("Mark all read")
            mark_btn.setFixedWidth(110)
            mark_btn.clicked.connect(self._on_mark_all_read)
            footer_layout.addWidget(mark_btn)
            footer_layout.addSpacing(8)

        close_btn = QPushButton("Close")
        close_btn.setFixedWidth(70)
        close_btn.clicked.connect(self.close)
        footer_layout.addWidget(close_btn)

        outer.addLayout(footer_layout)

    def _populate(self) -> None:
        if not self._notifications:
            empty = QLabel("No notifications.")
            empty.setObjectName("section-label")
            empty.setContentsMargins(16, 20, 16, 20)
            self._rows_layout.addWidget(empty)
            return

        for i, notif in enumerate(self._notifications):
            self._rows_layout.addWidget(self._make_row(notif))
            if i < len(self._notifications) - 1:
                divider = QFrame()
                divider.setFrameShape(QFrame.Shape.HLine)
                self._rows_layout.addWidget(divider)

    def _make_row(self, notif: dict) -> QWidget:
        row = QWidget()
        row.setObjectName("notif-row-unread" if not notif.get("read") else "notif-row")
        layout = QVBoxLayout(row)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(4)

        title_row = QHBoxLayout()
        title_lbl = QLabel(notif.get("title", ""))
        title_lbl.setObjectName("notif-title")
        title_row.addWidget(title_lbl)
        title_row.addStretch()
        age_lbl = QLabel(_relative_time(notif.get("created_at", "")))
        age_lbl.setObjectName("notif-age")
        title_row.addWidget(age_lbl)
        layout.addLayout(title_row)

        msg_lbl = QLabel(notif.get("message", ""))
        msg_lbl.setObjectName("notif-message")
        msg_lbl.setWordWrap(True)
        layout.addWidget(msg_lbl)

        link = notif.get("link", "")
        if link:
            full_url = link if link.startswith("http") else f"{_RDL_BASE_URL}/{link}"
            link_btn = QPushButton("Open in RDL")
            link_btn.setObjectName("link-btn")
            link_btn.setFixedWidth(130)
            link_btn.clicked.connect(
                lambda checked, url=full_url: self.url_clicked.emit(url)
            )
            layout.addWidget(link_btn)

        return row

    def _on_mark_all_read(self) -> None:
        unread = [n for n in self._notifications if not n.get("read")]
        self.mark_requested.emit(unread)
        self.close()


class NotificationInbox(QWidget):
    """Header bar inbox button — shows unread badge and opens notification popup."""

    open_url_in_rdl = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._btn = QPushButton("Inbox")
        self._btn.setObjectName("inbox-btn")
        self._btn.clicked.connect(self._open_popup)
        layout.addWidget(self._btn)

        self._uid: str | None = None
        self._id_token: str | None = None
        self._notifications: list[dict] = []
        self._threads: list[QThread] = []
        self._prev_unread_count: int = 0

        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(_POLL_INTERVAL_MS)
        self._poll_timer.timeout.connect(self._fetch)

        self._popup: "_NotificationPopup | None" = None

    def set_user(self, uid: str, id_token: str = "") -> None:
        self._uid = uid
        self._id_token = id_token or None
        self._fetch()
        self._poll_timer.start()

    def clear_user(self) -> None:
        self._uid = None
        self._id_token = None
        self._notifications = []
        self._prev_unread_count = 0
        self._poll_timer.stop()
        self._update_button()

    def _fetch(self) -> None:
        if not self._uid:
            return
        thread = _FetchThread(self._uid, self._id_token, self)
        thread.result.connect(self._on_fetched)
        thread.finished.connect(lambda t=thread: self._prune_thread(t))
        self._threads.append(thread)
        thread.start()

    def _prune_thread(self, thread: QThread) -> None:
        if thread in self._threads:
            self._threads.remove(thread)

    def _on_fetched(self, notifications: list) -> None:
        self._notifications = notifications
        unread = sum(1 for n in notifications if not n.get("read"))
        if unread > self._prev_unread_count:
            from core.app_config import load_config
            from core.sound_player import default_sound, play_notification_sound
            stem = load_config().get("notification_sound") or ""
            if not stem or stem == "none":
                stem = default_sound()
            play_notification_sound(stem)
        self._prev_unread_count = unread
        self._update_button()

    def _update_button(self) -> None:
        unread = sum(1 for n in self._notifications if not n.get("read"))
        if unread:
            self._btn.setText(f"Inbox  {unread}")
            self._btn.setObjectName("inbox-btn-unread")
        else:
            self._btn.setText("Inbox")
            self._btn.setObjectName("inbox-btn")
        self._btn.style().unpolish(self._btn)
        self._btn.style().polish(self._btn)

    def _open_popup(self) -> None:
        self._popup = _NotificationPopup(self._notifications, self._id_token)
        self._popup.mark_requested.connect(self._on_mark_requested)
        self._popup.url_clicked.connect(self._on_url_clicked)
        self._popup.adjustSize()
        pos = self._btn.mapToGlobal(self._btn.rect().bottomRight())
        self._popup.move(pos.x() - self._popup.width(), pos.y() + 4)
        self._popup.show()

    def _on_url_clicked(self, url: str) -> None:
        self.open_url_in_rdl.emit(url)
        if self._popup:
            self._popup.close()

    def _on_mark_requested(self, notifications: list) -> None:
        if not self._id_token or not notifications:
            return
        thread = _MarkReadThread(notifications, self._id_token, self)
        thread.finished.connect(self._fetch)
        thread.finished.connect(lambda t=thread: self._prune_thread(t))
        self._threads.append(thread)
        thread.start()

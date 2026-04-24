"""Missions panel — browse, filter, and install community missions from DXMA."""

import sys
from pathlib import Path

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QPixmap
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.app_config import load_config
from core.mission_catalog import (
    add_entries,
    fetch_new_d1_missions,
    fetch_new_d2_missions,
    get_d1_missions,
    get_d2_missions,
    load_catalog,
    mark_installed,
    save_catalog,
    scan_installed,
)
from core.mission_downloader import (
    fetch_mission_image_from_web,
    install_mission,
    load_mission_image_bytes,
)

_COL_STATUS = 0
_COL_TITLE = 1
_COL_AUTHOR = 2
_COL_MODE = 3
_COL_DATE = 4
_COL_COUNT = 5

_COLOR_INSTALLED = QColor("#3ccc3c")
_COLOR_NEW = QColor("#e85c00")
_COLOR_DIM = QColor("#7a7060")

_IMAGE_W = 300
_IMAGE_H = 225


class _UpdateThread(QThread):
    new_missions_found = pyqtSignal(list)
    check_complete = pyqtSignal()

    def __init__(self, catalog: dict, game: str, parent=None) -> None:
        super().__init__(parent)
        self._catalog = catalog
        self._game = game

    def run(self) -> None:
        if self._game == "d2":
            new = fetch_new_d2_missions(self._catalog)
        else:
            new = fetch_new_d1_missions(self._catalog)
        self.new_missions_found.emit(new)
        self.check_complete.emit()


class _InstallThread(QThread):
    install_complete = pyqtSignal(int, bool, str)

    def __init__(self, entry: dict, missions_dir: Path, archive, parent=None) -> None:
        super().__init__(parent)
        self._entry = entry
        self._missions_dir = missions_dir
        self._archive = archive

    def run(self) -> None:
        ok, msg = install_mission(self._entry, self._missions_dir, self._archive)
        self.install_complete.emit(self._entry["id"], ok, msg)


class _ImageLoadThread(QThread):
    image_ready = pyqtSignal(bytes)

    def __init__(self, mission_id: int, image_url: str, parent=None) -> None:
        super().__init__(parent)
        self._mission_id = mission_id
        self._image_url = image_url

    def run(self) -> None:
        data = fetch_mission_image_from_web(self._mission_id, self._image_url)
        if data:
            self.image_ready.emit(data)


class _MissionDetailDialog(QDialog):
    def __init__(self, entry: dict, archive_path, missions_dir, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(entry.get("title", "Mission Details"))
        self.setMinimumWidth(620)
        self.setModal(True)
        self.install_was_requested = False
        self._image_thread = None
        self._build_ui(entry, archive_path, missions_dir)

    def _build_ui(self, entry: dict, archive_path, missions_dir) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(14)

        content = QHBoxLayout()
        content.setSpacing(20)
        content.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._image_label = QLabel()
        self._image_label.setFixedSize(_IMAGE_W, _IMAGE_H)
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setObjectName("mission-image")

        img_loaded = False
        if archive_path and Path(archive_path).exists():
            img_bytes = load_mission_image_bytes(Path(archive_path), entry["id"])
            if img_bytes:
                img_loaded = self._set_image(img_bytes)

        if not img_loaded:
            self._image_label.setText("Loading...")
            image_url = entry.get("image_url", "")
            self._image_thread = _ImageLoadThread(entry["id"], image_url)
            self._image_thread.image_ready.connect(self._on_image_ready)
            self._image_thread.finished.connect(self._on_image_thread_done)
            self._image_thread.start()

        content.addWidget(self._image_label)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        title_label = QLabel(entry.get("title", ""))
        title_label.setObjectName("panel-title")
        title_label.setWordWrap(True)
        info_layout.addWidget(title_label)

        info_layout.addSpacing(6)

        if entry.get("installed"):
            status_text = "Installed"
        elif entry.get("_new"):
            status_text = "NEW"
        else:
            status_text = "Available"

        date_str = entry.get("date", "")
        if date_str and " " in date_str:
            date_str = date_str.split(" ")[0]

        fields = [
            ("Author", entry.get("author", "")),
            ("Mode", entry.get("mode", "")),
            ("Date", date_str),
            ("Status", status_text),
        ]
        if missions_dir:
            fields.append(("Install to", str(missions_dir)))

        for field_name, value in fields:
            row = QHBoxLayout()
            row.setSpacing(8)
            key_label = QLabel(f"{field_name}:")
            key_label.setObjectName("section-label")
            key_label.setFixedWidth(70)
            val_label = QLabel(value)
            val_label.setWordWrap(True)
            row.addWidget(key_label)
            row.addWidget(val_label, 1)
            info_layout.addLayout(row)

        mission_url = f"https://sectorgame.com/dxma/mission?m={entry['id']}"
        info_layout.addSpacing(4)
        link_label = QLabel(
            f'<a href="{mission_url}" style="color:#e07030;">'
            f"View on sectorgame.com/dxma</a>"
        )
        link_label.setOpenExternalLinks(True)
        info_layout.addWidget(link_label)

        info_layout.addStretch()
        content.addLayout(info_layout, 1)

        layout.addLayout(content)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(divider)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        if not entry.get("installed"):
            install_btn = QPushButton("Install")
            install_btn.setFixedWidth(100)
            install_btn.clicked.connect(self._on_install_clicked)
            btn_row.addWidget(install_btn)
            btn_row.addSpacing(8)

        close_btn = QPushButton("Close")
        close_btn.setFixedWidth(80)
        close_btn.clicked.connect(self.reject)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

    def _on_install_clicked(self) -> None:
        self.install_was_requested = True
        self.accept()

    def _set_image(self, img_bytes: bytes) -> bool:
        pixmap = QPixmap()
        pixmap.loadFromData(img_bytes)
        if pixmap.isNull():
            return False
        scaled = pixmap.scaled(
            _IMAGE_W,
            _IMAGE_H,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._image_label.setPixmap(scaled)
        return True

    def _on_image_ready(self, img_bytes: bytes) -> None:
        self._set_image(img_bytes)

    def _on_image_thread_done(self) -> None:
        if not self._image_label.pixmap() or self._image_label.pixmap().isNull():
            self._image_label.setText("No image")

    def closeEvent(self, event) -> None:
        if self._image_thread is not None:
            self._image_thread.blockSignals(True)
            self._image_thread.image_ready.disconnect()
            self._image_thread.finished.disconnect()
        super().closeEvent(event)


class MissionsPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("panel")
        self._catalog: dict = {}
        self._displayed_missions: list[dict] = []
        self._update_thread = None
        self._install_threads: list = []
        self._filter_mode = "ALL"
        self._search_text = ""
        self._game: str = "d1"
        self._dialog_open = False
        self._image_threads: list = []
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 36, 40, 36)
        layout.setSpacing(0)

        header_row = QHBoxLayout()

        title = QLabel("MISSIONS")
        title.setObjectName("panel-title")
        header_row.addWidget(title)

        header_row.addStretch()

        self._update_status = QLabel("")
        self._update_status.setObjectName("section-label")
        header_row.addWidget(self._update_status)

        check_btn = QPushButton("Check for Updates")
        check_btn.clicked.connect(self._start_update_check)
        header_row.addSpacing(8)
        header_row.addWidget(check_btn)

        layout.addLayout(header_row)

        subtitle = QLabel("Community missions from sectorgame.com/dxma")
        subtitle.setObjectName("section-label")
        layout.addWidget(subtitle)

        layout.addSpacing(14)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(6)

        self._mode_btns: dict[str, QPushButton] = {}
        for label, mode in (("ALL", "ALL"), ("SP", "SP"), ("MP", "MP")):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setChecked(mode == "ALL")
            btn.setObjectName("filter-btn-active" if mode == "ALL" else "filter-btn")
            btn.setFixedWidth(56)
            btn.clicked.connect(lambda _, m=mode: self._set_mode_filter(m))
            self._mode_btns[mode] = btn
            filter_row.addWidget(btn)

        filter_row.addSpacing(10)

        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText("Search title or author...")
        self._search_box.setFixedWidth(220)
        self._search_box.textChanged.connect(self._on_search_changed)
        filter_row.addWidget(self._search_box)

        filter_row.addStretch()

        self._catalog_status = QLabel("")
        self._catalog_status.setObjectName("section-label")
        filter_row.addWidget(self._catalog_status)

        layout.addLayout(filter_row)

        layout.addSpacing(10)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(divider)

        self._table = QTableWidget()
        self._table.setColumnCount(_COL_COUNT)
        self._table.setHorizontalHeaderLabels(["Status", "Title", "Author", "Mode", "Date"])
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setShowGrid(False)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(False)
        self._table.setObjectName("mission-table")

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, header.ResizeMode.Fixed)
        header.setSectionResizeMode(1, header.ResizeMode.Stretch)
        header.setSectionResizeMode(2, header.ResizeMode.Fixed)
        header.setSectionResizeMode(3, header.ResizeMode.Fixed)
        header.setSectionResizeMode(4, header.ResizeMode.Fixed)
        self._table.setColumnWidth(0, 90)
        self._table.setColumnWidth(2, 140)
        self._table.setColumnWidth(3, 52)
        self._table.setColumnWidth(4, 110)

        self._table.cellClicked.connect(self._on_row_clicked)

        layout.addWidget(self._table, stretch=1)

        layout.addSpacing(6)

        self._bottom_status = QLabel("Loading catalog...")
        self._bottom_status.setObjectName("section-label")
        layout.addWidget(self._bottom_status)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._load_catalog()

    def _load_catalog(self) -> None:
        self._catalog = load_catalog()
        config = load_config()
        missions_dir = config.get(f"missions_dir_{self._game}", "")
        if missions_dir:
            newly_found = scan_installed(self._catalog, Path(missions_dir))
            if newly_found:
                save_catalog(self._catalog)
        self._refresh_table()

    def _missions_dir(self):
        path = load_config().get(f"missions_dir_{self._game}", "")
        return Path(path) if path else None

    def _local_archive(self):
        path = load_config().get(f"local_archive_path_{self._game}", "")
        return Path(path) if path else None

    def _set_mode_filter(self, mode: str) -> None:
        self._filter_mode = mode
        for m, btn in self._mode_btns.items():
            is_active = m == mode
            btn.setChecked(is_active)
            btn.setObjectName("filter-btn-active" if is_active else "filter-btn")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self._refresh_table()

    def _on_search_changed(self, text: str) -> None:
        self._search_text = text.lower().strip()
        self._refresh_table()

    def _matches_filters(self, entry: dict) -> bool:
        if self._filter_mode != "ALL" and entry.get("mode") != self._filter_mode:
            return False
        if self._search_text:
            title = entry.get("title", "").lower()
            author = entry.get("author", "").lower()
            if self._search_text not in title and self._search_text not in author:
                return False
        return True

    def _refresh_table(self) -> None:
        if self._game == "d2":
            all_missions = get_d2_missions(self._catalog)
            game_label = "D2"
        else:
            all_missions = get_d1_missions(self._catalog)
            game_label = "D1"

        self._displayed_missions = [m for m in all_missions if self._matches_filters(m)]

        installed_count = sum(1 for m in all_missions if m.get("installed"))
        self._catalog_status.setText(
            f"{installed_count} installed / {len(all_missions)} {game_label} missions"
        )
        self._bottom_status.setText(
            f"Showing {len(self._displayed_missions)} missions  —  click a row for details"
        )

        self._table.setRowCount(len(self._displayed_missions))
        for row, entry in enumerate(self._displayed_missions):
            self._populate_row(row, entry)

    def _populate_row(self, row: int, entry: dict) -> None:
        if entry.get("installed"):
            status_text, status_color = "Installed", _COLOR_INSTALLED
        elif entry.get("_new"):
            status_text, status_color = "NEW", _COLOR_NEW
        else:
            status_text, status_color = "Available", _COLOR_DIM

        status_item = QTableWidgetItem(status_text)
        status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        status_item.setForeground(status_color)
        status_item.setData(Qt.ItemDataRole.UserRole, entry["id"])
        self._table.setItem(row, _COL_STATUS, status_item)

        self._table.setItem(row, _COL_TITLE, QTableWidgetItem(entry.get("title", "")))

        author_item = QTableWidgetItem(entry.get("author", ""))
        author_item.setForeground(_COLOR_DIM)
        self._table.setItem(row, _COL_AUTHOR, author_item)

        mode_item = QTableWidgetItem(entry.get("mode", ""))
        mode_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self._table.setItem(row, _COL_MODE, mode_item)

        date_str = entry.get("date", "")
        if date_str and " " in date_str:
            date_str = date_str.split(" ")[0]
        date_item = QTableWidgetItem(date_str)
        date_item.setForeground(_COLOR_DIM)
        self._table.setItem(row, _COL_DATE, date_item)

        self._table.setRowHeight(row, 30)

    def _on_row_clicked(self, row: int, _col: int) -> None:
        if self._dialog_open or row >= len(self._displayed_missions):
            return
        self._dialog_open = True
        entry = self._displayed_missions[row]
        archive = self._local_archive()
        missions_dir = self._missions_dir()
        dialog = _MissionDetailDialog(entry, archive, missions_dir, self)
        if dialog._image_thread is not None:
            thread = dialog._image_thread
            self._image_threads.append(thread)
            thread.finished.connect(lambda t=thread: self._image_threads.remove(t) if t in self._image_threads else None)
        dialog.exec()
        self._dialog_open = False
        if dialog.install_was_requested:
            self._start_install(entry)

    def _start_install(self, entry: dict) -> None:
        missions_dir = self._missions_dir()
        if not missions_dir:
            QMessageBox.warning(
                self,
                "No Missions Directory",
                "Click the game icon on the Launch panel to open settings and configure the missions directory.",
            )
            return

        archive = self._local_archive()
        self._bottom_status.setText(f"Installing \"{entry['title']}\"...")
        thread = _InstallThread(entry, missions_dir, archive, self)
        thread.install_complete.connect(self._on_install_complete)
        self._install_threads.append(thread)
        thread.start()

    def _on_install_complete(self, mission_id: int, ok: bool, msg: str) -> None:
        self._install_threads = [t for t in self._install_threads if t.isRunning()]
        if ok:
            mark_installed(self._catalog, mission_id, msg)
            save_catalog(self._catalog)
            self._refresh_table()
            self._bottom_status.setText(
                "Mission installed. Click any row for details."
            )
        else:
            self._bottom_status.setText(f"Install failed: {msg}")

    def _start_update_check(self) -> None:
        if self._update_thread and self._update_thread.isRunning():
            return
        if not self._catalog:
            self._catalog = load_catalog()
        self._update_status.setText("Checking...")
        self._update_thread = _UpdateThread(self._catalog, self._game, self)
        self._update_thread.new_missions_found.connect(self._on_new_missions_found)
        self._update_thread.check_complete.connect(self._on_check_complete)
        self._update_thread.start()

    def _on_new_missions_found(self, new_entries: list) -> None:
        if not new_entries:
            return
        for entry in new_entries:
            entry["_new"] = True

        game_label = "D2" if self._game == "d2" else "D1"
        reply = QMessageBox.question(
            self,
            "New Missions Available",
            f"{len(new_entries)} new {game_label} mission(s) found on sectorgame.com/dxma.\n\n"
            "Add them to the catalog?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            add_entries(self._catalog, new_entries)
            save_catalog(self._catalog)
            self._refresh_table()

    def _on_check_complete(self) -> None:
        self._update_status.setText("")

    def start_background_update(self) -> None:
        if not self._catalog:
            self._catalog = load_catalog()
            self._refresh_table()
        self._start_update_check()

    def on_game_changed(self, game_key: str) -> None:
        self._game = game_key
        if self._catalog:
            self._refresh_table()

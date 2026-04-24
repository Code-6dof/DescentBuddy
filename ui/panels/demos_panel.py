"""Demos panel — browse and rename demo recordings from the game's demos directory."""

import subprocess
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.game_detector import Game, data_dir, display_name

# Temp filenames the engine writes when auto-demo is on and the player discards
# the save prompt at level end. Each game has one active slot and one backup.
_AUTO_DEMO_NAMES = {
    Game.D1: {"tmp2.dem", "tmp1.dem"},
    Game.D2: {"tmpdemo.dmo", "tmp2.dem"},
}

_DEMO_EXTENSIONS = {".dem", ".dmo"}


def _demos_dir(game: Game) -> Path:
    """Return the demos/ directory inside the game's user data directory."""
    return data_dir(game) / "demos"


def _is_auto_demo(name: str, game: Game) -> bool:
    return name.lower() in _AUTO_DEMO_NAMES.get(game, set())


def _human_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


class DemosPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("panel")
        self._game = Game.D1
        self._build_ui()
        self._refresh()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 36, 40, 36)
        layout.setSpacing(0)

        # Header row: title left, Refresh + Open Folder right
        header_row = QHBoxLayout()
        header_row.setSpacing(0)

        title = QLabel("DEMOS")
        title.setObjectName("panel-title")
        header_row.addWidget(title)

        header_row.addStretch()

        self._open_folder_btn = QPushButton("Open Folder")
        self._open_folder_btn.clicked.connect(self._open_demos_folder)
        header_row.addWidget(self._open_folder_btn)

        header_row.addSpacing(8)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh)
        header_row.addWidget(refresh_btn)

        layout.addLayout(header_row)
        layout.addSpacing(6)

        self._subtitle = QLabel("")
        self._subtitle.setObjectName("section-label")
        layout.addWidget(self._subtitle)

        layout.addSpacing(14)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(divider)

        layout.addSpacing(14)

        unsaved_label = QLabel("UNSAVED AUTO-DEMOS")
        unsaved_label.setObjectName("section-label")
        layout.addWidget(unsaved_label)

        layout.addSpacing(8)

        # Unsaved auto-demo rename section
        self._unsaved_container = QWidget()
        unsaved_layout = QVBoxLayout(self._unsaved_container)
        unsaved_layout.setContentsMargins(0, 0, 0, 0)
        unsaved_layout.setSpacing(6)

        self._unsaved_status = QLabel("No unsaved auto-demos found.")
        self._unsaved_status.setObjectName("section-label")
        unsaved_layout.addWidget(self._unsaved_status)

        # Rename rows — one per potential unsaved demo slot
        self._rename_rows: list[tuple[QLabel, QLineEdit, QPushButton]] = []
        for _ in range(2):
            row_widget = QWidget()
            row_widget.setObjectName("demo-rename-row")
            row = QHBoxLayout(row_widget)
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(8)

            source_label = QLabel("")
            source_label.setObjectName("source-label")
            source_label.setMinimumWidth(120)
            row.addWidget(source_label)

            new_name_edit = QLineEdit()
            new_name_edit.setPlaceholderText("New name (without extension)")
            new_name_edit.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
            )
            row.addWidget(new_name_edit, 1)

            save_btn = QPushButton("Rename")
            save_btn.setMinimumWidth(76)
            row.addWidget(save_btn)

            unsaved_layout.addWidget(row_widget)
            row_widget.hide()
            self._rename_rows.append((source_label, new_name_edit, save_btn))

        layout.addWidget(self._unsaved_container)

        layout.addSpacing(16)

        # All demos table
        all_label = QLabel("ALL RECORDINGS")
        all_label.setObjectName("section-label")
        layout.addWidget(all_label)

        layout.addSpacing(8)

        self._table = QTableWidget()
        self._table.setObjectName("mission-table")
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels(["NAME", "SIZE", "MODIFIED"])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setColumnWidth(0, 260)
        self._table.setColumnWidth(1, 80)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._table.setShowGrid(False)
        layout.addWidget(self._table, stretch=1)

        layout.addSpacing(8)

        self._footer_status = QLabel("")
        self._footer_status.setObjectName("section-label")
        layout.addWidget(self._footer_status)

    def on_game_changed(self, game_value: str) -> None:
        try:
            self._game = Game(game_value)
        except ValueError:
            return
        self._refresh()

    def _refresh(self) -> None:
        demos_dir = _demos_dir(self._game)
        game_label = display_name(self._game)

        self._subtitle.setText(f"{game_label}  |  {demos_dir}")
        self._open_folder_btn.setEnabled(demos_dir.is_dir())

        if not demos_dir.is_dir():
            self._footer_status.setText(
                f"Demos directory not found: {demos_dir}"
            )
            self._table.setRowCount(0)
            self._unsaved_status.setText("No unsaved auto-demos found.")
            for label, edit, btn in self._rename_rows:
                label.parentWidget().hide()
            return

        all_demos = sorted(
            [p for p in demos_dir.iterdir() if p.suffix.lower() in _DEMO_EXTENSIONS],
            key=lambda p: (not _is_auto_demo(p.name.lower(), self._game), p.name.lower()),
        )

        unsaved = [p for p in all_demos if _is_auto_demo(p.name.lower(), self._game)]
        self._populate_unsaved(unsaved)
        self._populate_table(all_demos)

        count = len(all_demos)
        self._footer_status.setText(
            f"{count} recording{'s' if count != 1 else ''}" if count else "No demos recorded yet."
        )

    def _populate_unsaved(self, files: list[Path]) -> None:
        if not files:
            self._unsaved_status.setText("No unsaved auto-demos found.")
            for label, edit, btn in self._rename_rows:
                label.parentWidget().hide()
            return

        self._unsaved_status.setText(
            "These were auto-recorded but not saved. Rename to keep them."
        )

        for i, (label, edit, btn) in enumerate(self._rename_rows):
            if i < len(files):
                source_path = files[i]
                label.setText(source_path.name)
                edit.clear()
                edit.setPlaceholderText(f"New name for {source_path.name}")
                try:
                    btn.clicked.disconnect()
                except (RuntimeError, TypeError):
                    pass
                btn.clicked.connect(
                    lambda _, src=source_path, name_edit=edit: self._rename_demo(src, name_edit)
                )
                label.parentWidget().show()
            else:
                label.parentWidget().hide()

    def _populate_table(self, files: list[Path]) -> None:
        self._table.setRowCount(len(files))
        for row, path in enumerate(files):
            try:
                stat = path.stat()
                size_text = _human_size(stat.st_size)
                import datetime
                mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
                mtime_text = mtime.strftime("%Y-%m-%d %H:%M")
            except OSError:
                size_text = "?"
                mtime_text = "?"

            is_auto = _is_auto_demo(path.name.lower(), self._game)
            display = f"{path.name}  [unsaved]" if is_auto else path.name

            name_item = QTableWidgetItem(display)
            if is_auto:
                name_item.setForeground(
                    __import__("PyQt6.QtGui", fromlist=["QColor"]).QColor("#e85c00")
                )
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self._table.setItem(row, 0, name_item)

            size_item = QTableWidgetItem(size_text)
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            size_item.setFlags(size_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self._table.setItem(row, 1, size_item)

            mtime_item = QTableWidgetItem(mtime_text)
            mtime_item.setFlags(mtime_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self._table.setItem(row, 2, mtime_item)

            self._table.setRowHeight(row, 28)

    def _rename_demo(self, source: Path, name_edit: QLineEdit) -> None:
        new_stem = name_edit.text().strip()
        if not new_stem:
            self._footer_status.setText("Enter a name before renaming.")
            return
        new_path = source.parent / (new_stem + source.suffix)
        if new_path.exists():
            self._footer_status.setText(f"A file named {new_path.name} already exists.")
            return
        try:
            source.rename(new_path)
            name_edit.clear()
            self._footer_status.setText(f"Renamed to {new_path.name}")
            self._refresh()
        except OSError as exc:
            self._footer_status.setText(f"Rename failed: {exc}")

    def _open_demos_folder(self) -> None:
        subprocess.Popen(["xdg-open", str(_demos_dir(self._game))])

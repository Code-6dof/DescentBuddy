"""DescentBuddy — entry point."""

import sys
from pathlib import Path

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from core.app_config import load_config
from ui.main_window import MainWindow
from ui.theme import apply_theme


def _app_icon() -> QIcon:
    if hasattr(sys, "_MEIPASS"):
        icon_path = Path(sys._MEIPASS) / "descentbuddy.png"
    else:
        icon_path = Path(__file__).parent / "build" / "descentbuddy.png"
    return QIcon(str(icon_path))


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("DescentBuddy")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("DescentBuddy")
    app.setWindowIcon(_app_icon())

    saved_theme = load_config().get("theme", "descent")
    apply_theme(app, saved_theme)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

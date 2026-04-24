"""DescentBuddy — entry point."""

import sys

from PyQt6.QtWidgets import QApplication

from core.app_config import load_config
from ui.main_window import MainWindow
from ui.theme import apply_theme


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("DescentBuddy")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("DescentBuddy")

    saved_theme = load_config().get("theme", "descent")
    apply_theme(app, saved_theme)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

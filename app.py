# Copyright (©) 2026, Alexander Suvorov. All rights reserved.
import sys
from PyQt6.QtWidgets import QApplication

from smart_repository_manager_gui.main_window import MainWindow
from smart_repository_manager_gui.ui.dark_theme import ModernDarkTheme


def main():
    app = QApplication(sys.argv)
    ModernDarkTheme.apply(app)
    window = MainWindow()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

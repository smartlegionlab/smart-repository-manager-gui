# Copyright (©) 2026, Alexander Suvorov. All rights reserved.
import sys
from PyQt6.QtWidgets import QApplication

from core.ui.main_window import MainWindow
from core.ui.dark_theme import ModernDarkTheme


def main():
    app = QApplication(sys.argv)
    ModernDarkTheme.apply(app)
    window = MainWindow()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

# Copyright (©) 2026, Alexander Suvorov. All rights reserved.
from PyQt6.QtGui import QPalette, QColor

class ModernDarkTheme:
    PRIMARY_COLOR = "#0e65e5"
    DARK_BG = "#121212"
    CARD_BG = "#1e1e1e"
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#b0b0b0"
    BORDER_COLOR = "#2d2d2d"
    ROW_EVEN = "#1e1e1e"
    ROW_ODD = "#1a1a1a"
    ROW_SELECTED = "#0e65e5"

    @staticmethod
    def apply(app):
        app.setStyle("Fusion")

        dark_palette = QPalette()
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(ModernDarkTheme.DARK_BG))
        dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(ModernDarkTheme.TEXT_PRIMARY))
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(ModernDarkTheme.CARD_BG))
        dark_palette.setColor(QPalette.ColorRole.Text, QColor(ModernDarkTheme.TEXT_PRIMARY))
        dark_palette.setColor(QPalette.ColorRole.Button, QColor("#252525"))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(ModernDarkTheme.TEXT_PRIMARY))
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(ModernDarkTheme.PRIMARY_COLOR))

        app.setPalette(dark_palette)

        app.setStyleSheet(f"""
            QMainWindow {{
                background-color: {ModernDarkTheme.DARK_BG};
            }}
            QLabel {{
                color: {ModernDarkTheme.TEXT_PRIMARY};
            }}
            QPushButton {{
                background-color: #252525;
                color: white;
                border: 1px solid {ModernDarkTheme.BORDER_COLOR};
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
                min-height: 36px;
            }}
            QPushButton:hover {{
                background-color: #2a2a2a;
            }}
            QStatusBar {{
                background-color: #1e1e1e;
                color: {ModernDarkTheme.TEXT_SECONDARY};
                border-top: 1px solid {ModernDarkTheme.BORDER_COLOR};
            }}
        """)

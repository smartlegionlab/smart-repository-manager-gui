# Copyright (©) 2026, Alexander Suvorov. All rights reserved.
import webbrowser

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QGridLayout, QTextEdit, QGroupBox, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from smart_repository_manager_core.core.models.repository import Repository

from smart_repository_manager_gui.ui.dark_theme import ModernDarkTheme

class RepoDetailDialog(QDialog):
    def __init__(self, repository=None, parent=None):
        super().__init__(parent)
        self.repository = repository or Repository()
        self.setWindowTitle(f"{self.repository.name} - Repository Details")
        self.setMinimumSize(700, 600)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #1a1a1a;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #3a3a3a;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #4a4a4a;
            }
        """)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(10, 10, 10, 10)

        self.create_header_section(content_layout)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(f"background-color: {ModernDarkTheme.BORDER_COLOR}; height: 1px;")
        content_layout.addWidget(separator)

        if self.repository.description:
            self.create_description_section(content_layout)

        self.create_info_section(content_layout)

        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setStyleSheet(f"background-color: {ModernDarkTheme.BORDER_COLOR}; height: 1px;")
        content_layout.addWidget(separator2)

        self.create_stats_section(content_layout)

        content_layout.addStretch()

        self.create_action_buttons(content_layout)

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

    def create_header_section(self, parent_layout):
        header_layout = QVBoxLayout()
        header_layout.setSpacing(10)

        name_label = QLabel(self.repository.name)
        name_font = QFont()
        name_font.setPointSize(18)
        name_font.setBold(True)
        name_label.setFont(name_font)
        name_label.setStyleSheet(f"color: {ModernDarkTheme.PRIMARY_COLOR};")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        full_name_label = QLabel(self.repository.full_name)
        full_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        full_name_label.setStyleSheet(f"color: {ModernDarkTheme.TEXT_SECONDARY}; font-size: 12px;")

        header_layout.addWidget(name_label)
        header_layout.addWidget(full_name_label)

        parent_layout.addLayout(header_layout)

    def create_description_section(self, parent_layout):
        group = QGroupBox("Description")
        group.setStyleSheet(f"""
            QGroupBox {{
                color: {ModernDarkTheme.TEXT_PRIMARY};
                font-weight: bold;
                font-size: 14px;
                border: 1px solid {ModernDarkTheme.BORDER_COLOR};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(15, 25, 15, 15)

        desc_text = QTextEdit()
        desc_text.setPlainText(self.repository.description)
        desc_text.setReadOnly(True)
        desc_text.setMaximumHeight(120)
        desc_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: transparent;
                border: none;
                color: {ModernDarkTheme.TEXT_PRIMARY};
                font-size: 13px;
                line-height: 1.5;
                padding: 0;
            }}
        """)

        layout.addWidget(desc_text)
        group.setLayout(layout)
        parent_layout.addWidget(group)

    def create_info_section(self, parent_layout):
        group = QGroupBox("Repository Information")
        group.setStyleSheet(f"""
            QGroupBox {{
                color: {ModernDarkTheme.TEXT_PRIMARY};
                font-weight: bold;
                font-size: 14px;
                border: 1px solid {ModernDarkTheme.BORDER_COLOR};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
        """)

        layout = QGridLayout()
        layout.setSpacing(12)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 2)

        status_text = "Update Available" if self.repository.need_update else "Up to date"
        status_color = "#4caf50" if self.repository.need_update else "#ff9800"

        local_text = "Local copy exists" if self.repository.local_exists else "Not cloned locally"
        local_color = "#4caf50" if self.repository.local_exists else "#f44336"

        info_data = [
            ("URL:", self.repository.html_url),
            ("Created:", self.repository.created_date),
            ("Last Update:", self.repository.last_update),
            ("Status:", status_text),
            ("Local:", local_text),
            ("Default Branch:", self.repository.default_branch),
            ("License:", self.repository.license_name),
            ("Homepage:", self.repository.homepage or "None")
        ]

        for i, (label_text, value) in enumerate(info_data):
            label = QLabel(label_text)
            label.setStyleSheet(f"color: {ModernDarkTheme.TEXT_SECONDARY}; font-size: 12px;")
            layout.addWidget(label, i, 0)

            value_widget = QLabel(value)
            if label_text == "Status:":
                value_widget.setStyleSheet(f"color: {status_color}; font-size: 12px; font-weight: 500;")
            elif label_text == "Local:":
                value_widget.setStyleSheet(f"color: {local_color}; font-size: 12px; font-weight: 500;")
            else:
                value_widget.setStyleSheet(f"color: {ModernDarkTheme.TEXT_PRIMARY}; font-size: 12px; font-weight: 500;")
            layout.addWidget(value_widget, i, 1)

        group.setLayout(layout)
        parent_layout.addWidget(group)

    def create_stats_section(self, parent_layout):
        group = QGroupBox("Repository Statistics")
        group.setStyleSheet(f"""
            QGroupBox {{
                color: {ModernDarkTheme.TEXT_PRIMARY};
                font-weight: bold;
                font-size: 14px;
                border: 1px solid {ModernDarkTheme.BORDER_COLOR};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
        """)

        layout = QGridLayout()
        layout.setSpacing(12)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 2)

        stats_data = [
            ("Language:", self.repository.language or "Unknown"),
            ("Stars:", str(self.repository.stargazers_count)),
            ("Forks:", str(self.repository.forks_count)),
            ("Watchers:", str(self.repository.watchers_count)),
            ("Open Issues:", str(self.repository.open_issues_count)),
            ("Size:", f"{self.repository.size_mb:.1f} MB"),
            ("Private:", "Yes" if self.repository.private else "No"),
            ("Archived:", "Yes" if self.repository.archived else "No")
        ]

        for i, (label_text, value) in enumerate(stats_data):
            label = QLabel(label_text)
            label.setStyleSheet(f"color: {ModernDarkTheme.TEXT_SECONDARY}; font-size: 12px;")
            layout.addWidget(label, i, 0)

            value_widget = QLabel(value)
            value_widget.setStyleSheet(f"color: {ModernDarkTheme.TEXT_PRIMARY}; font-size: 12px; font-weight: 500;")
            layout.addWidget(value_widget, i, 1)

        group.setLayout(layout)
        parent_layout.addWidget(group)

    def create_action_buttons(self, parent_layout):
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.setSpacing(10)
        buttons_layout.setContentsMargins(0, 20, 0, 0)

        open_btn = QPushButton("🌐 Open in Browser")
        open_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ModernDarkTheme.PRIMARY_COLOR};
                color: white;
                border: none;
                padding: 10px 24px;
                font-size: 13px;
                font-weight: 500;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: #1a75ff;
            }}
        """)
        open_btn.clicked.connect(self.open_in_browser)

        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #2a2a2a;
                color: white;
                border: 1px solid {ModernDarkTheme.BORDER_COLOR};
                padding: 10px 24px;
                font-size: 13px;
                font-weight: 500;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: #333333;
                border-color: #4a4a4a;
            }}
        """)
        close_btn.clicked.connect(self.accept)

        buttons_layout.addWidget(open_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(close_btn)

        parent_layout.addWidget(buttons_widget)

    def open_in_browser(self):
        if hasattr(self.repository, 'html_url') and self.repository.html_url:
            try:
                webbrowser.open(self.repository.html_url)
            except Exception as e:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self,
                    "Browser Error",
                    f"Failed to open browser: {str(e)}\n\n"
                    f"URL: {self.repository.html_url}\n"
                    f"You can manually copy and paste the URL.",
                    QMessageBox.StandardButton.Ok
                )
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "URL Not Available",
                "Repository URL is not available.",
                QMessageBox.StandardButton.Ok
            )

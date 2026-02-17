# Copyright (©) 2026, Alexander Suvorov. All rights reserved.
import webbrowser

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QGridLayout, QTextEdit, QGroupBox, QFrame, QMessageBox, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QAction
from smart_repository_manager_core.core.models.repository import Repository

from smart_repository_manager_gui.ui.dark_theme import ModernDarkTheme
from smart_repository_manager_gui.ui.repo_download_dialog import RepoDownloadDialog


class RepoDetailDialog(QDialog):
    clone_requested = pyqtSignal(object)
    update_requested = pyqtSignal(object)
    reclone_requested = pyqtSignal(object)
    delete_requested = pyqtSignal(object)

    status_updated = pyqtSignal()

    def __init__(self, repository=None, parent=None, app_state=None):
        super().__init__(parent)
        self.repository = repository or Repository()
        self.app_state = app_state
        self.parent_window = parent
        self.setWindowTitle(f"{self.repository.name} - Repository Details")
        self.setMinimumSize(700, 600)
        self.setup_ui()
        self.update_display_info()

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

        self.create_bottom_buttons(content_layout)

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

    def create_header_section(self, parent_layout):
        header_layout = QVBoxLayout()
        header_layout.setSpacing(10)

        self.name_label = QLabel(self.repository.name)
        name_font = QFont()
        name_font.setPointSize(18)
        name_font.setBold(True)
        self.name_label.setFont(name_font)
        self.name_label.setStyleSheet(f"color: {ModernDarkTheme.PRIMARY_COLOR};")
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.full_name_label = QLabel(self.repository.full_name)
        self.full_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.full_name_label.setStyleSheet(f"color: {ModernDarkTheme.TEXT_SECONDARY}; font-size: 12px;")

        header_layout.addWidget(self.name_label)
        header_layout.addWidget(self.full_name_label)

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

        self.desc_text = QTextEdit()
        self.desc_text.setPlainText(self.repository.description)
        self.desc_text.setReadOnly(True)
        self.desc_text.setMaximumHeight(120)
        self.desc_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: transparent;
                border: none;
                color: {ModernDarkTheme.TEXT_PRIMARY};
                font-size: 13px;
                line-height: 1.5;
                padding: 0;
            }}
        """)

        layout.addWidget(self.desc_text)
        group.setLayout(layout)
        parent_layout.addWidget(group)

    def create_info_section(self, parent_layout):
        self.info_group = QGroupBox("Repository Information")
        self.info_group.setStyleSheet(f"""
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

        self.info_layout = QGridLayout()
        self.info_layout.setSpacing(12)
        self.info_layout.setColumnStretch(0, 1)
        self.info_layout.setColumnStretch(1, 2)

        self.info_labels = {}

        info_data = [
            ("URL:", "html_url", self.repository.html_url),
            ("Created:", "created_date", self.repository.created_date),
            ("Last Update:", "last_update", self.repository.last_update),
            ("Status:", "status", "Update Available" if self.repository.need_update else "Up to date"),
            ("Local:", "local", "Local copy exists" if self.repository.local_exists else "Not cloned locally"),
            ("Default Branch:", "default_branch", self.repository.default_branch),
            ("License:", "license_name", self.repository.license_name),
            ("Homepage:", "homepage", self.repository.homepage or "None")
        ]

        for i, (label_text, key, value) in enumerate(info_data):
            label = QLabel(label_text)
            label.setStyleSheet(f"color: {ModernDarkTheme.TEXT_SECONDARY}; font-size: 12px;")
            self.info_layout.addWidget(label, i, 0)

            value_widget = QLabel(value)
            if label_text == "Status:" or label_text == "Local:":
                pass
            else:
                value_widget.setStyleSheet(f"color: {ModernDarkTheme.TEXT_PRIMARY}; font-size: 12px; font-weight: 500;")

            self.info_layout.addWidget(value_widget, i, 1)
            self.info_labels[key] = value_widget

        self.info_group.setLayout(self.info_layout)
        parent_layout.addWidget(self.info_group)

    def create_stats_section(self, parent_layout):
        self.stats_group = QGroupBox("Repository Statistics")
        self.stats_group.setStyleSheet(f"""
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

        self.stats_layout = QGridLayout()
        self.stats_layout.setSpacing(12)
        self.stats_layout.setColumnStretch(0, 1)
        self.stats_layout.setColumnStretch(1, 2)

        self.stats_labels = {}

        stats_data = [
            ("Language:", "language", self.repository.language or "Unknown"),
            ("Stars:", "stargazers_count", str(self.repository.stargazers_count)),
            ("Forks:", "forks_count", str(self.repository.forks_count)),
            ("Watchers:", "watchers_count", str(self.repository.watchers_count)),
            ("Open Issues:", "open_issues_count", str(self.repository.open_issues_count)),
            ("Size:", "size_mb", f"{self.repository.size_mb:.1f} MB"),
            ("Private:", "private", "Yes" if self.repository.private else "No"),
            ("Archived:", "archived", "Yes" if self.repository.archived else "No")
        ]

        for i, (label_text, key, value) in enumerate(stats_data):
            label = QLabel(label_text)
            label.setStyleSheet(f"color: {ModernDarkTheme.TEXT_SECONDARY}; font-size: 12px;")
            self.stats_layout.addWidget(label, i, 0)

            value_widget = QLabel(value)
            value_widget.setStyleSheet(f"color: {ModernDarkTheme.TEXT_PRIMARY}; font-size: 12px; font-weight: 500;")
            self.stats_layout.addWidget(value_widget, i, 1)
            self.stats_labels[key] = value_widget

        self.stats_group.setLayout(self.stats_layout)
        parent_layout.addWidget(self.stats_group)

    def create_bottom_buttons(self, parent_layout):
        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout(bottom_widget)
        bottom_layout.setSpacing(10)
        bottom_layout.setContentsMargins(0, 10, 0, 0)

        self.actions_menu_btn = QPushButton("📁 Repo Actions ▼")
        self.actions_menu_btn.setMinimumWidth(150)
        self.actions_menu_btn.setStyleSheet(f"""
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
            QPushButton::menu-indicator {{ 
                subcontrol-position: right center;
                subcontrol-origin: padding;
                left: 8px;
            }}
        """)

        actions_menu = QMenu(self)

        if not self.repository.local_exists:
            clone_action = QAction("📥 Clone Repository", self)
            clone_action.triggered.connect(self._on_clone_clicked)
            actions_menu.addAction(clone_action)
        else:
            if self.repository.need_update:
                update_action = QAction("🔄 Update Repository", self)
                update_action.triggered.connect(self._on_update_clicked)
                actions_menu.addAction(update_action)

            reclone_action = QAction("🔄 Re-clone", self)
            reclone_action.triggered.connect(self._on_reclone_clicked)
            actions_menu.addAction(reclone_action)

            delete_action = QAction("🗑️ Delete Local", self)
            delete_action.triggered.connect(self._on_delete_clicked)
            actions_menu.addAction(delete_action)

        actions_menu.addSeparator()

        browser_action = QAction("🌐 Open in Browser", self)
        browser_action.triggered.connect(self.open_in_browser)
        actions_menu.addAction(browser_action)

        self.actions_menu_btn.setMenu(actions_menu)

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

        bottom_layout.addWidget(self.actions_menu_btn)
        bottom_layout.addStretch()
        bottom_layout.addWidget(close_btn)

        parent_layout.addWidget(bottom_widget)

    def update_display_info(self):

        status_text = "Update Available" if self.repository.need_update else "Up to date"
        status_color = "#ff9800" if self.repository.need_update else "#4caf50"

        local_text = "Local copy exists" if self.repository.local_exists else "Not cloned locally"
        local_color = "#4caf50" if self.repository.local_exists else "#f44336"

        if 'status' in self.info_labels:
            self.info_labels['status'].setText(status_text)
            self.info_labels['status'].setStyleSheet(f"color: {status_color}; font-size: 12px; font-weight: 500;")

        if 'local' in self.info_labels:
            self.info_labels['local'].setText(local_text)
            self.info_labels['local'].setStyleSheet(f"color: {local_color}; font-size: 12px; font-weight: 500;")

        info_updates = {
            'html_url': self.repository.html_url,
            'created_date': self.repository.created_date,
            'last_update': self.repository.last_update,
            'default_branch': self.repository.default_branch,
            'license_name': self.repository.license_name,
            'homepage': self.repository.homepage or "None"
        }

        for key, value in info_updates.items():
            if key in self.info_labels:
                self.info_labels[key].setText(value)

        stats_updates = {
            'language': self.repository.language or "Unknown",
            'stargazers_count': str(self.repository.stargazers_count),
            'forks_count': str(self.repository.forks_count),
            'watchers_count': str(self.repository.watchers_count),
            'open_issues_count': str(self.repository.open_issues_count),
            'size_mb': f"{self.repository.size_mb:.1f} MB",
            'private': "Yes" if self.repository.private else "No",
            'archived': "Yes" if self.repository.archived else "No"
        }

        for key, value in stats_updates.items():
            if key in self.stats_labels:
                self.stats_labels[key].setText(value)

        self.setWindowTitle(f"{self.repository.name} - Repository Details")

        self.update_actions_menu()

        self.status_updated.emit()

    def update_actions_menu(self):
        actions_menu = QMenu(self)

        if not self.repository.local_exists:
            clone_action = QAction("📥 Clone Repository", self)
            clone_action.triggered.connect(self._on_clone_clicked)
            actions_menu.addAction(clone_action)
        else:
            if self.repository.need_update:
                update_action = QAction("🔄 Update Repository", self)
                update_action.triggered.connect(self._on_update_clicked)
                actions_menu.addAction(update_action)

            reclone_action = QAction("🔄 Re-clone", self)
            reclone_action.triggered.connect(self._on_reclone_clicked)
            actions_menu.addAction(reclone_action)

            delete_action = QAction("🗑️ Delete Local", self)
            delete_action.triggered.connect(self._on_delete_clicked)
            actions_menu.addAction(delete_action)

        actions_menu.addSeparator()

        download_action = QAction("📦 Download repository", self)
        download_action.triggered.connect(self._on_download_clicked)
        actions_menu.addAction(download_action)

        browser_action = QAction("🌐 Open in Browser", self)
        browser_action.triggered.connect(self.open_in_browser)
        actions_menu.addAction(browser_action)

        self.actions_menu_btn.setMenu(actions_menu)

    def _on_download_clicked(self):
        token = self.app_state.get('current_token') if self.app_state else None
        username = self.app_state.get('current_user') if self.app_state else None

        if hasattr(self.parent_window, 'repo_table'):
            selected_repos = self.parent_window.repo_table.get_selected_repositories()
            if len(selected_repos) > 1:
                dialog = RepoDownloadDialog(selected_repos, token, username, self)
                dialog.exec()
                return

        if hasattr(self.parent_window, 'repo_table'):
            selected_repos = self.parent_window.repo_table.get_selected_repositories()
            if len(selected_repos) == 1:
                repo = selected_repos[0]
            else:
                repo = self.repository
        else:
            repo = self.repository

        dialog = RepoDownloadDialog([repo], token, username, self)
        dialog.exec()

    def _on_clone_clicked(self):
        self.clone_requested.emit(self.repository)
        QTimer.singleShot(500, self.update_display_info)

    def _on_update_clicked(self):
        self.update_requested.emit(self.repository)
        QTimer.singleShot(500, self.update_display_info)

    def _on_reclone_clicked(self):
        self.reclone_requested.emit(self.repository)
        QTimer.singleShot(500, self.update_display_info)

    def _on_delete_clicked(self):
        self.delete_requested.emit(self.repository)
        QTimer.singleShot(500, self.update_display_info)

    def open_in_browser(self):
        if hasattr(self.repository, 'html_url') and self.repository.html_url:
            try:
                webbrowser.open(self.repository.html_url)
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Browser Error",
                    f"Failed to open browser: {str(e)}\n\n"
                    f"URL: {self.repository.html_url}\n"
                    f"You can manually copy and paste the URL.",
                    QMessageBox.StandardButton.Ok
                )
        else:
            QMessageBox.warning(
                self,
                "URL Not Available",
                "Repository URL is not available.",
                QMessageBox.StandardButton.Ok
            )

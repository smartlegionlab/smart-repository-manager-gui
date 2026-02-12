# Copyright (©) 2026, Alexander Suvorov. All rights reserved.
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QAbstractItemView,
    QWidget, QMessageBox, QLineEdit
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPixmap, QPainter, QPainterPath

from smart_repository_manager_gui.ui.dark_theme import ModernDarkTheme
from smart_repository_manager_core.services.config_service import ConfigService
from smart_repository_manager_core.services.github_service import GitHubService


class TokenSelectionDialog(QDialog):
    def __init__(self, config_path=None):
        super().__init__()
        self.selected_username = None
        self.user_items = {}

        if config_path:
            self.config_service = ConfigService(config_path)
        else:
            self.config_service = ConfigService(Path.home() / "smart_repository_manager" / "config.json")

        self.setWindowTitle("Select GitHub Account")
        self.setFixedSize(650, 600)
        self._setup_ui()
        self._load_users()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("Select GitHub Account")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color: {ModernDarkTheme.PRIMARY_COLOR};")

        subtitle = QLabel("Choose an existing account or add a new one")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f"color: {ModernDarkTheme.TEXT_SECONDARY}; font-size: 12px;")

        self.user_list = QListWidget()
        self.user_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.user_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {ModernDarkTheme.CARD_BG};
                border: 1px solid {ModernDarkTheme.BORDER_COLOR};
                border-radius: 6px;
                font-size: 13px;
            }}
            QListWidget::item {{
                border-bottom: 1px solid {ModernDarkTheme.BORDER_COLOR};
            }}
            QListWidget::item:selected {{
                background-color: {ModernDarkTheme.PRIMARY_COLOR};
                color: white;
            }}
        """)

        quick_token_widget = QWidget()
        quick_token_layout = QVBoxLayout(quick_token_widget)
        quick_token_layout.setSpacing(8)

        quick_token_label = QLabel("Or enter token directly:")
        quick_token_label.setStyleSheet(f"color: {ModernDarkTheme.TEXT_SECONDARY}; font-size: 12px;")

        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Paste GitHub token here...")
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.token_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {ModernDarkTheme.CARD_BG};
                border: 1px solid {ModernDarkTheme.BORDER_COLOR};
                border-radius: 4px;
                padding: 8px 12px;
                color: {ModernDarkTheme.TEXT_PRIMARY};
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 1px solid {ModernDarkTheme.PRIMARY_COLOR};
            }}
        """)

        quick_token_btn = QPushButton("Add new user")
        quick_token_btn.setMinimumWidth(120)
        quick_token_btn.clicked.connect(self._validate_quick_token)
        quick_token_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ModernDarkTheme.PRIMARY_COLOR};
                color: white;
                font-weight: 500;
                border: none;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: #1a75ff;
            }}
        """)

        quick_token_layout.addWidget(quick_token_label)
        quick_token_layout.addWidget(self.token_input)
        quick_token_layout.addWidget(quick_token_btn)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.delete_btn = QPushButton("Delete Account")
        self.delete_btn.setMinimumWidth(120)
        self.delete_btn.clicked.connect(self._delete_user)
        self.delete_btn.setEnabled(False)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:disabled {
                background-color: #5a6268;
                color: #adb5bd;
            }
        """)

        self.select_btn = QPushButton("Select Account")
        self.select_btn.setMinimumWidth(120)
        self.select_btn.clicked.connect(self._select)
        self.select_btn.setEnabled(False)
        self.select_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #28a745;
                color: white;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #218838;
            }}
            QPushButton:disabled {{
                background-color: #5a6268;
                color: #adb5bd;
            }}
        """)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setMinimumWidth(120)
        self.cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.select_btn)
        button_layout.addWidget(self.cancel_btn)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(self.user_list, 1)
        layout.addWidget(quick_token_widget)
        layout.addLayout(button_layout)

        self.user_list.itemSelectionChanged.connect(self._on_selection_changed)

    def _load_users(self):
        self.user_list.clear()
        self.user_items.clear()

        config = self.config_service.load_config()

        if config.users:
            for i, (username, token) in enumerate(config.users.items()):
                item = QListWidgetItem()
                widget = self._create_user_item(username, i == 0)
                item.setSizeHint(widget.sizeHint())
                self.user_list.addItem(item)
                self.user_list.setItemWidget(item, widget)

                self.user_items[username] = i

        if config.users:
            QTimer.singleShot(50, self._select_active_user)

    def _create_user_item(self, username: str, is_active: bool = False):
        widget = QWidget()
        widget.setFixedHeight(70)
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)

        avatar_label = QLabel()
        avatar_label.setFixedSize(50, 50)

        avatar_pixmap = self._load_user_avatar(username)
        if avatar_pixmap:
            avatar_label.setPixmap(avatar_pixmap)
        else:
            avatar_label.setStyleSheet(f"""
                background-color: #2a2a2a;
                border-radius: 25px;
                border: 2px solid {ModernDarkTheme.BORDER_COLOR};
                color: {ModernDarkTheme.TEXT_SECONDARY};
                font-size: 20px;
                font-weight: bold;
            """)
            initial = username[0].upper() if username else "?"
            avatar_label.setText(initial)
            avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(5)
        text_layout.setContentsMargins(0, 0, 0, 0)

        username_label = QLabel(f"@{username}")
        username_label.setStyleSheet(f"""
            color: {ModernDarkTheme.TEXT_PRIMARY}; 
            font-weight: bold; 
            font-size: 14px;
        """)

        display_name = self._get_user_display_name(username)

        name_label = QLabel(display_name)
        name_label.setStyleSheet(f"""
            color: {ModernDarkTheme.TEXT_SECONDARY}; 
            font-size: 12px;
        """)

        text_layout.addWidget(username_label)
        text_layout.addWidget(name_label)
        text_layout.addStretch()

        layout.addWidget(avatar_label)
        layout.addLayout(text_layout, 1)

        widget.setProperty("username", username)
        return widget

    def _get_user_display_name(self, username: str) -> str:
        try:
            from pathlib import Path
            import json

            user_dir = Path.home() / "smart_repository_manager" / username
            user_data_file = user_dir / "user_data.json"

            if user_data_file.exists():
                with open(user_data_file, 'r', encoding='utf-8') as f:
                    user_data = json.load(f)
                    if user_data and 'name' in user_data and user_data['name']:
                        return user_data['name']
        except:
            pass

        return username.capitalize()

    def _load_user_avatar(self, username: str) -> Optional[QPixmap]:
        try:
            from pathlib import Path

            avatar_path = Path.home() / "smart_repository_manager" / username / "avatar.png"

            if avatar_path.exists():
                pixmap = QPixmap(str(avatar_path))
                if not pixmap.isNull():
                    return self._make_avatar_circular(pixmap, 50)
        except Exception as e:
            print(f"Error loading avatar for {username}: {e}")

        return None

    def _make_avatar_circular(self, pixmap: QPixmap, size: int = 50) -> QPixmap:
        circular_pixmap = QPixmap(size, size)
        circular_pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(circular_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        path = QPainterPath()
        path.addEllipse(0, 0, size, size)
        painter.setClipPath(path)

        scaled_pixmap = pixmap.scaled(size, size,
                                      Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                      Qt.TransformationMode.SmoothTransformation)

        x = (size - scaled_pixmap.width()) // 2
        y = (size - scaled_pixmap.height()) // 2
        painter.drawPixmap(x, y, scaled_pixmap)
        painter.end()

        return circular_pixmap

    def _on_selection_changed(self):
        has_selection = len(self.user_list.selectedItems()) > 0
        self.select_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)

    def _validate_quick_token(self):
        token = self.token_input.text().strip()

        if not token:
            QMessageBox.warning(self, "Error", "Please enter a token")
            return

        if len(token) < 40:
            QMessageBox.warning(self, "Error", "Token is too short")
            return

        try:
            github_service = GitHubService(token)
            valid, user = github_service.validate_token()

            if valid and user:
                self.config_service.add_user(user.username, token)
                self.config_service.set_active_user(user.username)

                self.selected_username = user.username
                QMessageBox.information(
                    self,
                    "Success",
                    f"Token validated for @{user.username}"
                )
                self.accept()
            else:
                QMessageBox.warning(self, "Error", "Invalid token")

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Validation failed: {str(e)}")

    def _select(self):
        selected_items = self.user_list.selectedItems()
        if selected_items:
            selected_item = selected_items[0]
            widget = self.user_list.itemWidget(selected_item)
            if widget:
                self.selected_username = widget.property("username")
                self.config_service.set_active_user(self.selected_username)
                self.accept()

    def _delete_user(self):
        selected_items = self.user_list.selectedItems()
        if not selected_items:
            return

        selected_item = selected_items[0]
        widget = self.user_list.itemWidget(selected_item)
        if not widget:
            return

        username = widget.property("username")
        if not username:
            return

        self._confirm_and_delete(username)

    def _confirm_and_delete(self, username):
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete account @{username}?\n\n"
            f"This will remove:\n"
            f"• GitHub token from configuration\n"
            f"• Cached repository data\n",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        success = self.config_service.remove_user(username)

        if success:
            QMessageBox.information(
                self,
                "Success",
                f"Account @{username} deleted"
            )
            self._load_users()
        else:
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to delete account @{username}"
            )

    def _select_active_user(self):
        config = self.config_service.load_config()
        if config.active_user and config.active_user in self.user_items:
            index = self.user_items[config.active_user]
            item = self.user_list.item(index)
            if item:
                self.user_list.setCurrentItem(item)
                self.user_list.scrollToItem(item)

    def get_selected_user(self):
        return self.selected_username

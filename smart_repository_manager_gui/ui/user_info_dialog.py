# Copyright (©) 2026, Alexander Suvorov. All rights reserved.
from pathlib import Path
import requests
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGroupBox, QGridLayout,
    QWidget, QScrollArea, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor, QPainterPath
from smart_repository_manager_core.services.github_service import GitHubService

from smart_repository_manager_gui.ui.dark_theme import ModernDarkTheme


class UserInfoDialog(QDialog):
    def __init__(self, app_state, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        self.setWindowTitle("GitHub User Information")
        self.setMinimumSize(600, 500)
        self.setup_ui()
        self.load_user_data()

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

        self.create_user_info_section(content_layout)

        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setStyleSheet(f"background-color: {ModernDarkTheme.BORDER_COLOR}; height: 1px;")
        content_layout.addWidget(separator2)

        self.create_stats_section(content_layout)

        content_layout.addStretch()

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setMinimumWidth(120)
        self.refresh_btn.clicked.connect(self.update_refresh_btn)
        self.refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ModernDarkTheme.PRIMARY_COLOR};
                color: white;
                font-weight: 500;
                border: none;
            }}
            QPushButton:hover {{
                background-color: #1a75ff;
            }}
        """)

        close_btn = QPushButton("Close")
        close_btn.setMinimumWidth(120)
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #b0b0b0;
                border: 1px solid #3a3a3a;
            }
            QPushButton:hover {
                background-color: #2a2a2a;
            }
        """)

        button_layout.addWidget(self.refresh_btn)
        button_layout.addWidget(close_btn)

        main_layout.addLayout(button_layout)

    def create_header_section(self, parent_layout):
        header_layout = QVBoxLayout()
        header_layout.setSpacing(10)

        title_label = QLabel("GitHub User Information")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {ModernDarkTheme.PRIMARY_COLOR};")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle_label = QLabel("Your GitHub account details")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet(f"color: {ModernDarkTheme.TEXT_SECONDARY}; font-size: 12px;")

        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)

        parent_layout.addLayout(header_layout)

    def create_user_info_section(self, parent_layout):
        group = QGroupBox("User Profile")
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

        main_layout = QHBoxLayout()

        left_layout = QVBoxLayout()
        left_layout.setSpacing(15)

        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(100, 100)
        self.avatar_label.setStyleSheet("border-radius: 50px; border: 2px solid #3a3a3a;")

        left_layout.addWidget(self.avatar_label)
        left_layout.setAlignment(self.avatar_label, Qt.AlignmentFlag.AlignCenter)

        right_layout = QVBoxLayout()
        right_layout.setSpacing(10)

        self.username_label = QLabel()
        self.username_label.setStyleSheet(
            f"color: {ModernDarkTheme.PRIMARY_COLOR}; font-size: 16px; font-weight: bold;")

        self.name_label = QLabel()
        self.name_label.setStyleSheet(f"color: {ModernDarkTheme.TEXT_PRIMARY}; font-size: 14px;")

        self.bio_label = QLabel()
        self.bio_label.setStyleSheet(f"color: {ModernDarkTheme.TEXT_SECONDARY}; font-size: 12px;")
        self.bio_label.setWordWrap(True)

        right_layout.addWidget(self.username_label)
        right_layout.addWidget(self.name_label)
        right_layout.addWidget(self.bio_label)

        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 2)

        group.setLayout(main_layout)
        parent_layout.addWidget(group)

    def create_stats_section(self, parent_layout):
        group = QGroupBox("Account Statistics")
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

        self.repos_label = QLabel()
        self.public_repos_label = QLabel()
        self.private_repos_label = QLabel()
        self.followers_label = QLabel()
        self.following_label = QLabel()
        self.created_label = QLabel()
        self.location_label = QLabel()
        self.company_label = QLabel()

        labels = [
            ("Total Repositories:", self.repos_label),
            ("Public Repositories:", self.public_repos_label),
            ("Private Repositories:", self.private_repos_label),
            ("Followers:", self.followers_label),
            ("Following:", self.following_label),
            ("Account Created:", self.created_label),
            ("Location:", self.location_label),
            ("Company:", self.company_label)
        ]

        for i, (label_text, widget) in enumerate(labels):
            label = QLabel(label_text)
            label.setStyleSheet(f"color: {ModernDarkTheme.TEXT_SECONDARY}; font-size: 12px;")
            layout.addWidget(label, i, 0)

            widget.setStyleSheet(f"color: {ModernDarkTheme.TEXT_PRIMARY}; font-size: 12px; font-weight: 500;")
            layout.addWidget(widget, i, 1)

        group.setLayout(layout)
        parent_layout.addWidget(group)

    def load_user_data(self):
        user_data = self.app_state.get('user_data')

        if not user_data:
            self.set_default_avatar()
            self.username_label.setText("@no-user")
            self.name_label.setText("No user data available")
            self.bio_label.setText("Please run system checkup first")

            self.repos_label.setText("0")
            self.public_repos_label.setText("0")
            self.private_repos_label.setText("0")
            self.followers_label.setText("0")
            self.following_label.setText("0")
            self.created_label.setText("Unknown")
            self.location_label.setText("Unknown")
            self.company_label.setText("Unknown")
            return

        self.load_avatar(user_data.get('username'))

        self.username_label.setText(f"@{user_data.get('username', 'unknown')}")
        self.name_label.setText(user_data.get('name', 'Not specified'))
        self.bio_label.setText(user_data.get('bio', 'No bio available') or 'No bio available')

        total_repos = len(self.app_state.get('repositories', []))
        private_count = self.app_state.get('total_private', 0)
        public_count = self.app_state.get('total_public', 0)

        self.repos_label.setText(str(total_repos))
        self.public_repos_label.setText(str(public_count))
        self.private_repos_label.setText(str(private_count))
        self.followers_label.setText(str(user_data.get('followers', 0)))
        self.following_label.setText(str(user_data.get('following', 0)))
        self.created_label.setText(user_data.get('created_date', 'Unknown'))
        self.location_label.setText(user_data.get('location', 'Not specified') or 'Not specified')
        self.company_label.setText(user_data.get('company', 'Not specified') or 'Not specified')

    def load_avatar(self, username):
        try:
            user_dir = Path.home() / "smart_repository_manager" / username
            avatar_path = user_dir / "avatar.png"

            if avatar_path.exists():
                pixmap = QPixmap(str(avatar_path))
                if not pixmap.isNull():
                    circular_pixmap = self.make_avatar_circular(pixmap)
                    self.avatar_label.setPixmap(circular_pixmap)
                    return

            user_data = self.app_state.get('user_data')
            if user_data and 'avatar_url' in user_data:
                response = requests.get(user_data['avatar_url'], timeout=10)
                if response.status_code == 200:
                    user_dir.mkdir(parents=True, exist_ok=True)
                    with open(avatar_path, 'wb') as f:
                        f.write(response.content)

                    pixmap = QPixmap()
                    pixmap.loadFromData(response.content)
                    if not pixmap.isNull():
                        circular_pixmap = self.make_avatar_circular(pixmap)
                        self.avatar_label.setPixmap(circular_pixmap)
                        return

            self.set_default_avatar(username[0].upper() if username else "?")

        except Exception as e:
            print(f"Error loading avatar: {e}")
            self.set_default_avatar(username[0].upper() if username else "?")

    def make_avatar_circular(self, pixmap: QPixmap, size: int = 90) -> QPixmap:
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

    def set_default_avatar(self, initial="?"):
        pixmap = QPixmap(100, 100)
        pixmap.fill(QColor(70, 70, 70))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setBrush(QColor(100, 100, 100))
        painter.drawEllipse(0, 0, 100, 100)

        painter.setFont(QFont("Arial", 40, QFont.Weight.Bold))
        painter.setPen(QColor(200, 200, 200))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, initial)

        painter.end()
        self.avatar_label.setPixmap(pixmap)

    def update_refresh_btn(self):
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("Refreshing...")

        QTimer.singleShot(300, self.refresh_user_data)

    def refresh_user_data(self):
        try:
            current_token = self.app_state.get('current_token')
            if not current_token:
                QMessageBox.warning(
                    self,
                    "Warning",
                    "No active token found",
                    QMessageBox.StandardButton.Ok
                )
            else:
                github_service = GitHubService(current_token)
                valid, user = github_service.validate_token()
                if not valid or not user:
                    QMessageBox.warning(
                        self,
                        "Warning",
                        "Failed to validate token",
                        QMessageBox.StandardButton.Ok
                    )
                else:
                    user_data = {
                        'username': user.username,
                        'name': user.name,
                        'bio': user.bio,
                        'public_repos': user.public_repos,
                        'followers': user.followers,
                        'following': user.following,
                        'created_date': user.created_date,
                        'html_url': user.html_url,
                        'location': getattr(user, 'location', None),
                        'company': getattr(user, 'company', None),
                        'avatar_url': getattr(user, 'avatar_url', None)
                    }

                    self.app_state.update(user_data=user_data)
                    self.load_user_data()

                    QMessageBox.information(
                        self,
                        "Success",
                        f"User information refreshed for @{user.username}",
                        QMessageBox.StandardButton.Ok
                    )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to refresh user info: {str(e)}",
                QMessageBox.StandardButton.Ok
            )
        finally:
            self.refresh_btn.setEnabled(True)
            self.refresh_btn.setText("🔄 Refresh")

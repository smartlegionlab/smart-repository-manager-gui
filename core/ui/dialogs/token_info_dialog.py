# Copyright (©) 2026, Alexander Suvorov. All rights reserved.
from datetime import datetime

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGroupBox, QGridLayout,
    QWidget, QScrollArea, QMessageBox,
)

from smart_repository_manager_core.services.github_service import GitHubService
from smart_repository_manager_core.services.config_service import ConfigService

from core.models.state import TokenInfo, RateLimits
from core.ui.dark_theme import ModernDarkTheme


class TokenInfoDialog(QDialog):
    def __init__(self, app_state, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        self.setWindowTitle("GitHub Token Information")
        self.setMinimumSize(600, 500)
        self.setup_ui()
        self.load_token_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea { border: none; background-color: transparent; }
            QScrollBar:vertical { border: none; background: #1a1a1a; width: 10px; margin: 0px; }
            QScrollBar::handle:vertical { background: #3a3a3a; min-height: 20px; border-radius: 5px; }
            QScrollBar::handle:vertical:hover { background: #4a4a4a; }
        """)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(10, 10, 10, 10)

        header_layout = QVBoxLayout()
        header_layout.setSpacing(10)

        title_label = QLabel("GitHub Token Information")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {ModernDarkTheme.PRIMARY_COLOR};")
        title_label.setAlignment(Qt.AlignCenter)

        subtitle_label = QLabel("Token details and API rate limits")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet(f"color: {ModernDarkTheme.TEXT_SECONDARY}; font-size: 12px;")

        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        content_layout.addLayout(header_layout)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet(f"background-color: {ModernDarkTheme.BORDER_COLOR}; height: 1px;")
        content_layout.addWidget(separator)

        token_group = QGroupBox("Token Information")
        token_group.setStyleSheet(f"""
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

        token_layout = QGridLayout()
        token_layout.setSpacing(12)
        token_layout.setColumnStretch(0, 1)
        token_layout.setColumnStretch(1, 2)

        self.token_status_label = QLabel()
        self.token_scopes_label = QLabel()
        self.active_user_label = QLabel()
        self.created_label = QLabel()
        self.last_used_label = QLabel()

        self.token_label = QLabel()
        self.token_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.token_label.setStyleSheet(f"""
            color: {ModernDarkTheme.TEXT_PRIMARY};
            font-size: 12px;
            font-weight: 500;
            font-family: 'Monospace';
            background-color: #2a2a2a;
            padding: 4px 8px;
            border-radius: 4px;
        """)

        labels = [
            ("Token Status:", self.token_status_label),
            ("Scopes:", self.token_scopes_label),
            ("Active User:", self.active_user_label),
            ("Created:", self.created_label),
            ("Last Used:", self.last_used_label),
            ("Token:", self.token_label),
        ]

        for i, (label_text, widget) in enumerate(labels):
            label = QLabel(label_text)
            label.setStyleSheet(f"color: {ModernDarkTheme.TEXT_SECONDARY}; font-size: 12px;")
            token_layout.addWidget(label, i, 0)
            widget.setStyleSheet(f"color: {ModernDarkTheme.TEXT_PRIMARY}; font-size: 12px; font-weight: 500;")
            token_layout.addWidget(widget, i, 1)

        token_group.setLayout(token_layout)
        content_layout.addWidget(token_group)

        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setStyleSheet(f"background-color: {ModernDarkTheme.BORDER_COLOR}; height: 1px;")
        content_layout.addWidget(separator2)

        limits_group = QGroupBox("API Rate Limits")
        limits_group.setStyleSheet(f"""
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

        limits_layout = QGridLayout()
        limits_layout.setSpacing(12)
        limits_layout.setColumnStretch(0, 1)
        limits_layout.setColumnStretch(1, 2)

        self.limit_label = QLabel()
        self.remaining_label = QLabel()
        self.used_label = QLabel()
        self.reset_label = QLabel()
        self.resource_label = QLabel()

        limits_labels = [
            ("Limit:", self.limit_label),
            ("Remaining:", self.remaining_label),
            ("Used:", self.used_label),
            ("Reset Time:", self.reset_label),
            ("Resource:", self.resource_label),
        ]

        for i, (label_text, widget) in enumerate(limits_labels):
            label = QLabel(label_text)
            label.setStyleSheet(f"color: {ModernDarkTheme.TEXT_SECONDARY}; font-size: 12px;")
            limits_layout.addWidget(label, i, 0)
            widget.setStyleSheet(f"color: {ModernDarkTheme.TEXT_PRIMARY}; font-size: 12px; font-weight: 500;")
            limits_layout.addWidget(widget, i, 1)

        limits_group.setLayout(limits_layout)
        content_layout.addWidget(limits_group)
        content_layout.addStretch()

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setMinimumWidth(120)
        self.refresh_btn.clicked.connect(self.update_refresh_btn)
        self.refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ModernDarkTheme.PRIMARY_COLOR};
                color: white;
                font-weight: 500;
                border: none;
            }}
            QPushButton:hover {{ background-color: #1a75ff; }}
        """)

        self.close_btn = QPushButton("Close")
        self.close_btn.setMinimumWidth(120)
        self.close_btn.clicked.connect(self.accept)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #b0b0b0;
                border: 1px solid #3a3a3a;
            }
            QPushButton:hover { background-color: #2a2a2a; }
        """)

        button_layout.addWidget(self.refresh_btn)
        button_layout.addWidget(self.close_btn)
        main_layout.addLayout(button_layout)

    def load_token_data(self):
        try:
            d = self.app_state.data
            token_info: TokenInfo = d.token_info
            rate_limits: RateLimits = d.rate_limits

            if token_info is None:
                self.refresh_token_data()
                return

            self.token_status_label.setText("✅ Valid")
            self.token_status_label.setStyleSheet("color: #4caf50; font-weight: bold;")

            self.token_scopes_label.setText(token_info.scopes or "Not specified")
            username = token_info.username or d.current_user or "Unknown"
            self.active_user_label.setText(f"@{username}")
            self.created_label.setText(token_info.created_at or "Unknown")
            self.last_used_label.setText("Now")
            self.token_label.setText(token_info.token or d.current_token or "")

            if rate_limits:
                self.limit_label.setText(str(rate_limits.limit if rate_limits.limit is not None else "?"))
                remaining = rate_limits.remaining
                self.remaining_label.setText(str(remaining if remaining is not None else "?"))

                if isinstance(remaining, int):
                    if remaining > 1000:
                        self.remaining_label.setStyleSheet("color: #4caf50; font-weight: bold;")
                    elif remaining > 100:
                        self.remaining_label.setStyleSheet("color: #ff9800; font-weight: bold;")
                    else:
                        self.remaining_label.setStyleSheet("color: #f44336; font-weight: bold;")
                else:
                    self.remaining_label.setStyleSheet(
                        f"color: {ModernDarkTheme.TEXT_PRIMARY}; font-weight: 500;")

                self.used_label.setText(str(rate_limits.used or 0))
                self.reset_label.setText(rate_limits.reset_time or "Unknown")
                self.resource_label.setText("core")

        except Exception as e:
            print(f"Error loading token data: {e}")
            self.token_status_label.setText("❌ Error loading data")
            self.token_status_label.setStyleSheet("color: #f44336; font-weight: bold;")

    def update_refresh_btn(self):
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("Refreshing...")
        QTimer.singleShot(300, self.refresh_token_data)

    def refresh_token_data(self):
        try:
            d = self.app_state.data
            current_token = d.current_token
            current_user = d.current_user

            if not current_token:
                config_service = ConfigService()
                config = config_service.load_config()
                if current_user and current_user in config.users:
                    current_token = config.users[current_user]

            if not current_token:
                QMessageBox.warning(self, "Warning", "No active token found", QMessageBox.Ok)
                self.refresh_btn.setEnabled(True)
                self.refresh_btn.setText("Refresh")
                return

            github_service = GitHubService(current_token)
            valid, user = github_service.validate_token()

            if not valid or not user:
                QMessageBox.warning(self, "Warning", "Invalid token", QMessageBox.Ok)
                self.refresh_btn.setEnabled(True)
                self.refresh_btn.setText("Refresh")
                return

            token_obj = github_service.get_token_info()

            token_info = TokenInfo(
                username=token_obj.username,
                scopes=token_obj.scopes or "Not specified",
                rate_limit=token_obj.rate_limit,
                remaining=token_obj.rate_remaining,
                created_at=token_obj.created_at[:10] if token_obj.created_at else "Unknown",
                token=current_token,
            )
            self.app_state.update(
                token_info=token_info,
                current_user=user.username,
            )

            limits = github_service.check_rate_limits()

            reset_time_str = "Unknown"
            if limits.get('reset'):
                try:
                    reset_time = datetime.fromtimestamp(int(limits["reset"]))
                    reset_time_str = reset_time.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    pass

            rate_limits = RateLimits(
                limit=limits.get('limit'),
                remaining=limits.get('remaining'),
                used=(limits.get('limit', 0) - limits.get('remaining', 0)) if limits.get('limit') else 0,
                reset=limits.get('reset'),
                reset_time=reset_time_str,
            )
            self.app_state.update(rate_limits=rate_limits)

            self.load_token_data()

            QMessageBox.information(
                self, "Success",
                f"Token information refreshed for @{user.username}",
                QMessageBox.Ok,
            )

        except Exception as e:
            QMessageBox.critical(
                self, "Error",
                f"Failed to refresh token info: {str(e)}",
                QMessageBox.Ok,
            )

        finally:
            QTimer.singleShot(300, self._restore_refresh_button)

    def _restore_refresh_button(self):
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("Refresh")

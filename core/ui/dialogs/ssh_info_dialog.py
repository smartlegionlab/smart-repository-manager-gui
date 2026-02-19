# Copyright (©) 2026, Alexander Suvorov. All rights reserved.
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGroupBox, QGridLayout,
    QWidget, QScrollArea, QMessageBox,
    QComboBox, QLineEdit, QProgressBar, QTextEdit
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFont

from core.ui.dark_theme import ModernDarkTheme
from smart_repository_manager_core.services.ssh_service import SSHService
from smart_repository_manager_core.core.models.ssh_models import SSHKeyType, SSHStatus


class SSHWorker(QThread):
    progress_update = pyqtSignal(str, int)
    validation_complete = pyqtSignal(object)
    keys_displayed = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.ssh_service = SSHService()
        self._is_running = True

    def run(self):
        try:
            self.progress_update.emit("Validating SSH configuration...", 20)
            validation = self.ssh_service.validate_ssh_configuration()
            self.validation_complete.emit(validation)

            if not self._is_running:
                return

            self.progress_update.emit("Checking SSH keys...", 60)
            ssh_config = validation.ssh_config
            self.keys_displayed.emit(ssh_config.keys)

            if not self._is_running:
                return

            self.progress_update.emit("SSH configuration loaded", 100)
            self.finished.emit()

        except Exception as e:
            self.error_occurred.emit(str(e))

    def stop(self):
        self._is_running = False


class SSHInfoDialog(QDialog):
    def __init__(self, app_state, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        self.ssh_service = SSHService()
        self.worker = None

        self.setWindowTitle("SSH Configuration")
        self.setMinimumSize(700, 600)
        self.is_loading = True

        self.setup_ui()
        self.start_ssh_check()

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

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(20)
        self.content_layout.setContentsMargins(10, 10, 10, 10)

        self.create_header_section(self.content_layout)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(f"background-color: {ModernDarkTheme.BORDER_COLOR}; height: 1px;")
        self.content_layout.addWidget(separator)

        self.create_status_section(self.content_layout)

        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setStyleSheet(f"background-color: {ModernDarkTheme.BORDER_COLOR}; height: 1px;")
        self.content_layout.addWidget(separator2)

        self.create_keys_section(self.content_layout)

        separator3 = QFrame()
        separator3.setFrameShape(QFrame.Shape.HLine)
        separator3.setStyleSheet(f"background-color: {ModernDarkTheme.BORDER_COLOR}; height: 1px;")
        self.content_layout.addWidget(separator3)

        self.create_tools_section(self.content_layout)

        self.content_layout.addStretch()

        scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(scroll_area)

        self.progress_frame = QFrame()
        self.progress_frame.setFixedHeight(80)
        self.progress_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {ModernDarkTheme.CARD_BG};
                border-top: 1px solid {ModernDarkTheme.BORDER_COLOR};
            }}
        """)

        progress_layout = QHBoxLayout(self.progress_frame)
        progress_layout.setContentsMargins(15, 10, 15, 10)
        progress_layout.setSpacing(10)

        self.progress_label = QLabel("Loading SSH configuration...")
        self.progress_label.setStyleSheet(f"color: {ModernDarkTheme.TEXT_SECONDARY};")

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFixedHeight(12)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background-color: {ModernDarkTheme.BORDER_COLOR};
                border-radius: 4px;
                font-size: 9px;
                color: {ModernDarkTheme.TEXT_SECONDARY};
            }}
            QProgressBar::chunk {{
                background-color: {ModernDarkTheme.PRIMARY_COLOR};
                border-radius: 4px;
            }}
        """)

        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar, 1)

        main_layout.addWidget(self.progress_frame)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setMinimumWidth(120)
        self.refresh_btn.clicked.connect(self.refresh_ssh_info)
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
            QPushButton:disabled {{
                background-color: #5a6268;
                color: #adb5bd;
            }}
        """)
        self.refresh_btn.setEnabled(False)

        close_btn = QPushButton("Close")
        close_btn.setMinimumWidth(120)
        close_btn.clicked.connect(self.close_dialog)
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

        title_label = QLabel("SSH Configuration")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {ModernDarkTheme.PRIMARY_COLOR};")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle_label = QLabel("SSH keys and GitHub authentication")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet(f"color: {ModernDarkTheme.TEXT_SECONDARY}; font-size: 12px;")

        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)

        parent_layout.addLayout(header_layout)

    def create_status_section(self, parent_layout):
        group = QGroupBox("SSH Status")
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

        self.overall_status_label = QLabel("Checking...")
        self.ssh_dir_label = QLabel("Checking...")
        self.can_clone_label = QLabel("Checking...")
        self.can_pull_label = QLabel("Checking...")
        self.github_auth_label = QLabel("Checking...")
        self.keys_count_label = QLabel("Checking...")

        labels = [
            ("Overall Status:", self.overall_status_label),
            ("SSH Directory:", self.ssh_dir_label),
            ("Can Clone:", self.can_clone_label),
            ("Can Pull:", self.can_pull_label),
            ("GitHub Auth:", self.github_auth_label),
            ("Keys Found:", self.keys_count_label)
        ]

        for i, (label_text, widget) in enumerate(labels):
            label = QLabel(label_text)
            label.setStyleSheet(f"color: {ModernDarkTheme.TEXT_SECONDARY}; font-size: 12px;")
            layout.addWidget(label, i, 0)

            widget.setStyleSheet(f"color: {ModernDarkTheme.TEXT_PRIMARY}; font-size: 12px; font-weight: 500;")
            layout.addWidget(widget, i, 1)

        group.setLayout(layout)
        parent_layout.addWidget(group)

    def create_keys_section(self, parent_layout):
        group = QGroupBox("SSH Keys")
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
        layout.setSpacing(10)

        self.keys_scroll = QScrollArea()
        self.keys_scroll.setWidgetResizable(True)
        self.keys_scroll.setMaximumHeight(200)
        self.keys_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                background-color: #1a1a1a;
            }
        """)

        self.keys_widget = QWidget()
        self.keys_layout = QVBoxLayout(self.keys_widget)
        self.keys_layout.setSpacing(8)

        loading_label = QLabel("Loading SSH keys...")
        loading_label.setStyleSheet(f"color: {ModernDarkTheme.TEXT_SECONDARY}; font-size: 11px;")
        self.keys_layout.addWidget(loading_label)

        self.keys_scroll.setWidget(self.keys_widget)
        layout.addWidget(self.keys_scroll)

        self.show_key_btn = QPushButton("📋 Show Public Key")
        self.show_key_btn.setMinimumWidth(140)
        self.show_key_btn.clicked.connect(self.show_public_key)
        self.show_key_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: white;
                font-size: 11px;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #333333;
                border-color: #4a4a4a;
            }
            QPushButton:disabled {
                background-color: #5a6268;
                color: #adb5bd;
            }
        """)
        self.show_key_btn.setEnabled(False)
        layout.addWidget(self.show_key_btn, 0, Qt.AlignmentFlag.AlignLeft)

        group.setLayout(layout)
        parent_layout.addWidget(group)

    def create_tools_section(self, parent_layout):
        group = QGroupBox("SSH Tools")
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
        layout.setSpacing(10)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)

        gen_key_layout = QVBoxLayout()
        gen_key_layout.setSpacing(5)

        gen_key_label = QLabel("Generate New Key:")
        gen_key_label.setStyleSheet(f"color: {ModernDarkTheme.TEXT_SECONDARY}; font-size: 12px;")
        gen_key_layout.addWidget(gen_key_label)

        self.key_type_combo = QComboBox()
        self.key_type_combo.addItems(["ED25519 (Recommended)", "RSA 4096", "ECDSA", "DSA"])
        self.key_type_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {ModernDarkTheme.CARD_BG};
                border: 1px solid {ModernDarkTheme.BORDER_COLOR};
                border-radius: 4px;
                padding: 4px 8px;
                color: {ModernDarkTheme.TEXT_PRIMARY};
                font-size: 11px;
            }}
        """)
        gen_key_layout.addWidget(self.key_type_combo)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email for key comment (optional)")
        self.email_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {ModernDarkTheme.CARD_BG};
                border: 1px solid {ModernDarkTheme.BORDER_COLOR};
                border-radius: 4px;
                padding: 4px 8px;
                color: {ModernDarkTheme.TEXT_PRIMARY};
                font-size: 11px;
            }}
        """)
        gen_key_layout.addWidget(self.email_input)

        self.gen_key_btn = QPushButton("🔑 Generate Key")
        self.gen_key_btn.clicked.connect(self.generate_ssh_key)
        self.gen_key_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ModernDarkTheme.PRIMARY_COLOR};
                color: white;
                font-size: 11px;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: #1a75ff;
            }}
            QPushButton:disabled {{
                background-color: #5a6268;
                color: #adb5bd;
            }}
        """)
        gen_key_layout.addWidget(self.gen_key_btn)

        layout.addLayout(gen_key_layout, 0, 0)

        tools_layout = QVBoxLayout()
        tools_layout.setSpacing(8)

        self.fix_perms_btn = QPushButton("🔧 Fix Permissions")
        self.fix_perms_btn.clicked.connect(self.fix_permissions)
        self.fix_perms_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: white;
                font-size: 11px;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #333333;
                border-color: #4a4a4a;
            }
            QPushButton:disabled {
                background-color: #5a6268;
                color: #adb5bd;
            }
        """)

        self.add_github_btn = QPushButton("🐙 Add GitHub to known_hosts")
        self.add_github_btn.clicked.connect(self.add_github_known_hosts)
        self.add_github_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: white;
                font-size: 11px;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #333333;
                border-color: #4a4a4a;
            }
            QPushButton:disabled {
                background-color: #5a6268;
                color: #adb5bd;
            }
        """)

        self.create_config_btn = QPushButton("⚙️ Create SSH Config")
        self.create_config_btn.clicked.connect(self.create_ssh_config)
        self.create_config_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: white;
                font-size: 11px;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #333333;
                border-color: #4a4a4a;
            }
            QPushButton:disabled {
                background-color: #5a6268;
                color: #adb5bd;
            }
        """)

        self.test_conn_btn = QPushButton("🔗 Test Connection")
        self.test_conn_btn.clicked.connect(self.update_test_connection_btn)
        self.test_conn_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #28a745;
                color: white;
                font-size: 11px;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: #218838;
            }}
            QPushButton:disabled {{
                background-color: #5a6268;
                color: #adb5bd;
            }}
        """)

        tools_layout.addWidget(self.fix_perms_btn)
        tools_layout.addWidget(self.add_github_btn)
        tools_layout.addWidget(self.create_config_btn)
        tools_layout.addWidget(self.test_conn_btn)

        layout.addLayout(tools_layout, 0, 1)

        group.setLayout(layout)
        parent_layout.addWidget(group)

        self.set_tools_enabled(False)

    def set_tools_enabled(self, enabled: bool):
        self.gen_key_btn.setEnabled(enabled)
        self.fix_perms_btn.setEnabled(enabled)
        self.add_github_btn.setEnabled(enabled)
        self.create_config_btn.setEnabled(enabled)
        self.test_conn_btn.setEnabled(enabled)
        self.show_key_btn.setEnabled(enabled)

    def start_ssh_check(self):
        self.is_loading = True
        self.progress_frame.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText("Starting SSH check...")
        self.refresh_btn.setEnabled(False)
        self.set_tools_enabled(False)

        self.overall_status_label.setText("Checking...")
        self.ssh_dir_label.setText("Checking...")
        self.can_clone_label.setText("Checking...")
        self.can_pull_label.setText("Checking...")
        self.github_auth_label.setText("Checking...")
        self.keys_count_label.setText("Checking...")

        while self.keys_layout.count():
            item = self.keys_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        loading_label = QLabel("Loading SSH keys...")
        loading_label.setStyleSheet(f"color: {ModernDarkTheme.TEXT_SECONDARY}; font-size: 11px;")
        self.keys_layout.addWidget(loading_label)

        self.worker = SSHWorker()
        self.worker.progress_update.connect(self.on_progress_update)
        self.worker.validation_complete.connect(self.on_validation_complete)
        self.worker.keys_displayed.connect(self.display_ssh_keys)
        self.worker.error_occurred.connect(self.on_error_occurred)
        self.worker.finished.connect(self.on_ssh_check_finished)

        self.worker.start()

    @pyqtSlot(str, int)
    def on_progress_update(self, message: str, progress: int):
        self.progress_label.setText(message)
        self.progress_bar.setValue(progress)
        self.progress_bar.setFormat(f"{message}... {progress}%")

    @pyqtSlot(object)
    def on_validation_complete(self, validation):
        status = validation.status
        ssh_config = validation.ssh_config

        if status == SSHStatus.VALID:
            status_text = "✅ Valid"
            status_color = "#4caf50"
        elif status == SSHStatus.PARTIAL:
            status_text = "⚠️ Partial"
            status_color = "#ff9800"
        else:
            status_text = "❌ Invalid"
            status_color = "#f44336"

        self.overall_status_label.setText(status_text)
        self.overall_status_label.setStyleSheet(f"color: {status_color}; font-weight: bold;")

        self.ssh_dir_label.setText(str(ssh_config.ssh_dir))
        self.can_clone_label.setText("✅ Yes" if validation.can_clone_with_ssh else "❌ No")
        self.can_pull_label.setText("✅ Yes" if validation.can_pull_with_ssh else "❌ No")

        github_auth_text = "✅ Working" if validation.github_authentication_working else "❌ Not working"
        github_auth_color = "#4caf50" if validation.github_authentication_working else "#f44336"
        self.github_auth_label.setText(github_auth_text)
        self.github_auth_label.setStyleSheet(f"color: {github_auth_color}; font-weight: 500;")

        keys_count = len(ssh_config.keys)
        self.keys_count_label.setText(str(keys_count))

    def display_ssh_keys(self, keys):
        while self.keys_layout.count():
            item = self.keys_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not keys:
            label = QLabel("No SSH keys found")
            label.setStyleSheet(f"color: {ModernDarkTheme.TEXT_SECONDARY}; font-size: 11px;")
            self.keys_layout.addWidget(label)
            self.show_key_btn.setEnabled(False)
            return

        self.show_key_btn.setEnabled(True)

        for i, key in enumerate(keys):
            key_widget = QWidget()
            key_widget.setStyleSheet("""
                background-color: #2a2a2a;
                border-radius: 4px;
                padding: 8px;
                margin-bottom: 5px;
            """)

            key_layout = QVBoxLayout(key_widget)
            key_layout.setSpacing(4)

            type_layout = QHBoxLayout()

            type_label = QLabel(f"{key.type.value.upper()} Key")
            type_label.setStyleSheet(f"color: {ModernDarkTheme.PRIMARY_COLOR}; font-weight: bold; font-size: 11px;")
            type_layout.addWidget(type_label)

            type_layout.addStretch()

            github_status = "✅ GitHub" if key.is_github_authenticated else "❌ GitHub"
            github_label = QLabel(github_status)
            github_color = "#4caf50" if key.is_github_authenticated else "#f44336"
            github_label.setStyleSheet(f"color: {github_color}; font-size: 10px;")
            type_layout.addWidget(github_label)

            key_layout.addLayout(type_layout)

            self.keys_layout.addWidget(key_widget)

            key_widget.key_data = key

    @pyqtSlot(str)
    def on_error_occurred(self, error_message: str):
        self.progress_label.setText(f"Error: {error_message}")
        self.overall_status_label.setText("❌ Error")
        self.overall_status_label.setStyleSheet("color: #f44336; font-weight: bold;")

        self.is_loading = False
        self.refresh_btn.setEnabled(True)
        self.set_tools_enabled(False)

    @pyqtSlot()
    def on_ssh_check_finished(self):
        self.is_loading = False
        self.progress_frame.setVisible(False)
        self.refresh_btn.setEnabled(True)
        self.set_tools_enabled(True)
        self.progress_label.setText("")

    def refresh_ssh_info(self):
        if self.is_loading:
            return

        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()

        self.start_ssh_check()

    def generate_ssh_key(self):
        key_type_map = {
            "ED25519 (Recommended)": SSHKeyType.ED25519,
            "RSA 4096": SSHKeyType.RSA,
            "ECDSA": SSHKeyType.ECDSA,
            "DSA": SSHKeyType.DSA
        }

        key_type = key_type_map.get(self.key_type_combo.currentText(), SSHKeyType.ED25519)
        email = self.email_input.text() if self.email_input.text() else None

        self.set_tools_enabled(False)
        self.gen_key_btn.setText("Generating...")

        success, message, key_path = self.ssh_service.generate_ssh_key(
            key_type=key_type,
            email=email
        )

        self.set_tools_enabled(True)
        self.gen_key_btn.setText("🔑 Generate Key")

        if success:
            QMessageBox.information(self, "Success", message)
            QTimer.singleShot(500, self.refresh_ssh_info)
        else:
            QMessageBox.critical(self, "Error", message)

    def copy_to_clipboard(self, text):
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        QMessageBox.information(self, "Copied", "Public key copied to clipboard!")

    def show_public_key(self):
        for i in range(self.keys_layout.count()):
            widget = self.keys_layout.itemAt(i).widget()
            if hasattr(widget, 'key_data'):
                key = widget.key_data
                if key.public_path and key.public_path.exists():
                    try:
                        public_key_content = key.public_path.read_text().strip()

                        key_dialog = QDialog(self)
                        key_dialog.setWindowTitle(f"Public Key: {key.type.value}")
                        key_dialog.setMinimumSize(500, 200)

                        layout = QVBoxLayout(key_dialog)

                        key_text = QTextEdit()
                        key_text.setPlainText(public_key_content)
                        key_text.setReadOnly(True)
                        key_text.setStyleSheet(f"""
                            QTextEdit {{
                                background-color: {ModernDarkTheme.CARD_BG};
                                border: 1px solid {ModernDarkTheme.BORDER_COLOR};
                                border-radius: 4px;
                                color: {ModernDarkTheme.TEXT_PRIMARY};
                                font-family: 'Monospace';
                                font-size: 10px;
                            }}
                        """)
                        layout.addWidget(key_text)

                        copy_btn = QPushButton("📋 Copy to Clipboard")
                        copy_btn.clicked.connect(lambda: self.copy_to_clipboard(public_key_content))
                        copy_btn.setStyleSheet(f"""
                            QPushButton {{
                                background-color: {ModernDarkTheme.PRIMARY_COLOR};
                                color: white;
                                border: none;
                                padding: 8px;
                            }}
                        """)
                        layout.addWidget(copy_btn)

                        key_dialog.exec()
                        return

                    except Exception as e:
                        QMessageBox.warning(self, "Error", f"Could not read public key: {str(e)}")

        QMessageBox.warning(self, "Warning", "No public key found or selected")

    def fix_permissions(self):
        success, message = self.ssh_service.fix_permissions()
        if success:
            QMessageBox.information(self, "Success", message)
            QTimer.singleShot(500, self.refresh_ssh_info)
        else:
            QMessageBox.critical(self, "Error", message)

    def add_github_known_hosts(self):
        success, message = self.ssh_service.add_github_to_known_hosts()
        if success:
            QMessageBox.information(self, "Success", message)
            QTimer.singleShot(500, self.refresh_ssh_info)
        else:
            QMessageBox.critical(self, "Error", message)

    def create_ssh_config(self):
        success, message = self.ssh_service.create_ssh_config()
        if success:
            QMessageBox.information(self, "Success", message)
            QTimer.singleShot(500, self.refresh_ssh_info)
        else:
            QMessageBox.critical(self, "Error", message)

    def update_test_connection_btn(self):
        self.test_conn_btn.setEnabled(False)
        self.test_conn_btn.setText('Testing connection...')

        QTimer.singleShot(300, self.test_connection)

    def test_connection(self):
        success, message, response_time = self.ssh_service.test_connection("github.com", "git")
        if success:
            QMessageBox.information(self, "Success", f"{message}\nResponse time: {response_time:.2f}s")
        else:
            QMessageBox.critical(self, "Error", message)
        self.test_conn_btn.setEnabled(True)
        self.test_conn_btn.setText('🔗 Test Connection')

    def close_dialog(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
        self.accept()

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
        event.accept()

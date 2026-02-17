# Copyright (©) 2026, Alexander Suvorov. All rights reserved.

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGroupBox, QGridLayout,
    QWidget, QScrollArea, QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFont

from smart_repository_manager_gui.ui.dark_theme import ModernDarkTheme
from smart_repository_manager_core.services.network_service import NetworkService
import socket


class NetworkWorker(QThread):
    progress_update = pyqtSignal(str, int)
    network_check_complete = pyqtSignal(object)
    github_check_complete = pyqtSignal(bool, str)
    dns_check_complete = pyqtSignal(bool, str, list)
    ip_check_complete = pyqtSignal(str, str, str)
    servers_updated = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.network_service = NetworkService()
        self._is_running = True

    def run(self):
        try:
            self.progress_update.emit("Checking network connection...", 10)
            network_check = self.network_service.check_network()
            self.network_check_complete.emit(network_check)

            if not self._is_running:
                return

            self.progress_update.emit("Checking GitHub access...", 30)
            git_ok, git_msg = self.network_service.check_git_connectivity()
            self.github_check_complete.emit(git_ok, git_msg)

            if not self._is_running:
                return

            self.progress_update.emit("Checking DNS...", 50)
            dns_ok, dns_msg, ip_addresses = self.network_service.check_dns_resolution("github.com")
            self.dns_check_complete.emit(dns_ok, dns_msg, ip_addresses)

            if not self._is_running:
                return

            self.progress_update.emit("Updating server information...", 70)
            self.servers_updated.emit(network_check.detailed_results)

            if not self._is_running:
                return

            self.progress_update.emit("Getting IP information...", 90)
            external_ip = self.network_service.get_ip()

            try:
                hostname = socket.gethostname()
                self.ip_check_complete.emit(external_ip or "Not available", hostname)
            except:
                self.ip_check_complete.emit(external_ip or "Not available", "Not available", "Not available")

            if not self._is_running:
                return

            self.progress_update.emit("Network check complete!", 100)
            self.finished.emit()

        except Exception as e:
            self.error_occurred.emit(str(e))

    def stop(self):
        self._is_running = False


class NetworkInfoDialog(QDialog):
    def __init__(self, app_state, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        self.network_service = NetworkService()
        self.worker = None

        self.setWindowTitle("Network Information")
        self.setMinimumSize(600, 500)
        self.is_loading = True

        self.setup_ui()
        self.start_network_check()

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

        self.create_connection_section(self.content_layout)

        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setStyleSheet(f"background-color: {ModernDarkTheme.BORDER_COLOR}; height: 1px;")
        self.content_layout.addWidget(separator2)

        self.create_servers_section(self.content_layout)

        separator3 = QFrame()
        separator3.setFrameShape(QFrame.Shape.HLine)
        separator3.setStyleSheet(f"background-color: {ModernDarkTheme.BORDER_COLOR}; height: 1px;")
        self.content_layout.addWidget(separator3)

        self.create_ip_section(self.content_layout)

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

        self.progress_label = QLabel("Loading network information...")
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
        self.refresh_btn.clicked.connect(self.refresh_network_info)
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

        title_label = QLabel("Network Information")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {ModernDarkTheme.PRIMARY_COLOR};")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle_label = QLabel("Internet connection and network details")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet(f"color: {ModernDarkTheme.TEXT_SECONDARY}; font-size: 12px;")

        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)

        parent_layout.addLayout(header_layout)

    def create_connection_section(self, parent_layout):
        group = QGroupBox("Connection Status")
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

        self.online_status_label = QLabel("Checking...")
        self.check_duration_label = QLabel("0.00 seconds")
        self.git_status_label = QLabel("Checking...")
        self.dns_status_label = QLabel("Checking...")

        labels = [
            ("Internet:", self.online_status_label),
            ("Check Time:", self.check_duration_label),
            ("GitHub Access:", self.git_status_label),
            ("DNS Resolution:", self.dns_status_label)
        ]

        for i, (label_text, widget) in enumerate(labels):
            label = QLabel(label_text)
            label.setStyleSheet(f"color: {ModernDarkTheme.TEXT_SECONDARY}; font-size: 12px;")
            layout.addWidget(label, i, 0)

            widget.setStyleSheet(f"color: {ModernDarkTheme.TEXT_PRIMARY}; font-size: 12px; font-weight: 500;")
            layout.addWidget(widget, i, 1)

        group.setLayout(layout)
        parent_layout.addWidget(group)

    def create_servers_section(self, parent_layout):
        group = QGroupBox("Server Connectivity")
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
        layout.setContentsMargins(5, 15, 5, 15)

        self.servers_widget = QWidget()
        self.servers_layout = QGridLayout(self.servers_widget)
        self.servers_layout.setColumnStretch(0, 1)
        self.servers_layout.setColumnStretch(1, 1)
        self.servers_layout.setColumnStretch(2, 1)

        loading_label = QLabel("Loading server information...")
        loading_label.setStyleSheet(f"color: {ModernDarkTheme.TEXT_SECONDARY}; font-size: 11px;")
        self.servers_layout.addWidget(loading_label, 0, 0)

        layout.addWidget(self.servers_widget)
        group.setLayout(layout)
        parent_layout.addWidget(group)

    def create_ip_section(self, parent_layout):
        group = QGroupBox("IP Information")
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

        self.external_ip_label = QLabel("Checking...")
        self.hostname_label = QLabel("Checking...")

        labels = [
            ("External IP:", self.external_ip_label),
            ("Hostname:", self.hostname_label)
        ]

        for i, (label_text, widget) in enumerate(labels):
            label = QLabel(label_text)
            label.setStyleSheet(f"color: {ModernDarkTheme.TEXT_SECONDARY}; font-size: 12px;")
            layout.addWidget(label, i, 0)

            widget.setStyleSheet(f"color: {ModernDarkTheme.TEXT_PRIMARY}; font-size: 12px; font-weight: 500;")
            layout.addWidget(widget, i, 1)

        group.setLayout(layout)
        parent_layout.addWidget(group)

    def start_network_check(self):
        self.is_loading = True
        self.progress_frame.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText("Starting network check...")
        self.refresh_btn.setEnabled(False)

        self.online_status_label.setText("Checking...")
        self.check_duration_label.setText("0.00 seconds")
        self.git_status_label.setText("Checking...")
        self.dns_status_label.setText("Checking...")
        self.external_ip_label.setText("Checking...")
        self.hostname_label.setText("Checking...")

        while self.servers_layout.count():
            item = self.servers_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        loading_label = QLabel("Loading server information...")
        loading_label.setStyleSheet(f"color: {ModernDarkTheme.TEXT_SECONDARY}; font-size: 11px;")
        self.servers_layout.addWidget(loading_label, 0, 0)

        self.worker = NetworkWorker()
        self.worker.progress_update.connect(self.on_progress_update)
        self.worker.network_check_complete.connect(self.on_network_check_complete)
        self.worker.github_check_complete.connect(self.on_github_check_complete)
        self.worker.dns_check_complete.connect(self.on_dns_check_complete)
        self.worker.ip_check_complete.connect(self.on_ip_check_complete)
        self.worker.servers_updated.connect(self.update_servers_info)
        self.worker.error_occurred.connect(self.on_error_occurred)
        self.worker.finished.connect(self.on_network_check_finished)

        self.worker.start()

    @pyqtSlot(str, int)
    def on_progress_update(self, message: str, progress: int):
        self.progress_label.setText(message)
        self.progress_bar.setValue(progress)
        self.progress_bar.setFormat(f"{message}... {progress}%")

    @pyqtSlot(object)
    def on_network_check_complete(self, network_check):
        is_online = network_check.is_online
        online_text = "✅ Online" if is_online else "❌ Offline"
        online_color = "#4caf50" if is_online else "#f44336"
        self.online_status_label.setText(online_text)
        self.online_status_label.setStyleSheet(f"color: {online_color}; font-weight: bold;")

        self.check_duration_label.setText(f"{network_check.check_duration:.2f} seconds")

    @pyqtSlot(bool, str)
    def on_github_check_complete(self, git_ok: bool, git_msg: str):
        git_text = f"✅ {git_msg}" if git_ok else "❌ Unable to connect to GitHub"
        git_color = "#4caf50" if git_ok else "#f44336"
        self.git_status_label.setText(git_text)
        self.git_status_label.setStyleSheet(f"color: {git_color}; font-weight: 500;")

    @pyqtSlot(bool, str, list)
    def on_dns_check_complete(self, dns_ok: bool, dns_msg: str, ip_addresses: list):
        dns_text = f"✅ {dns_msg}" if dns_ok else f"❌ {dns_msg}"
        dns_color = "#4caf50" if dns_ok else "#f44336"
        self.dns_status_label.setText(dns_text)
        self.dns_status_label.setStyleSheet(f"color: {dns_color}; font-weight: 500;")

    @pyqtSlot(str, str, str)
    def on_ip_check_complete(self, external_ip: str, hostname: str):
        self.external_ip_label.setText(external_ip)
        self.hostname_label.setText(hostname)

    def update_servers_info(self, servers):
        while self.servers_layout.count():
            item = self.servers_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not servers:
            label = QLabel("No server data available")
            label.setStyleSheet(f"color: {ModernDarkTheme.TEXT_SECONDARY}; font-size: 11px;")
            self.servers_layout.addWidget(label, 0, 0)
            return

        headers = ["Server", "Status", "Response Time"]
        for col, header in enumerate(headers):
            label = QLabel(header)
            label.setStyleSheet(f"""
                color: {ModernDarkTheme.PRIMARY_COLOR};
                font-weight: bold;
                font-size: 11px;
                padding: 2px 0;
            """)
            self.servers_layout.addWidget(label, 0, col)

        for row, server in enumerate(servers, 1):
            name_label = QLabel(server["name"])
            name_label.setStyleSheet(f"color: {ModernDarkTheme.TEXT_PRIMARY}; font-size: 11px;")
            self.servers_layout.addWidget(name_label, row, 0)

            status_icon = "✅" if server["success"] else "❌"
            status_text = "Online" if server["success"] else "Offline"
            status_label = QLabel(f"{status_icon} {status_text}")
            status_color = "#4caf50" if server["success"] else "#f44336"
            status_label.setStyleSheet(f"color: {status_color}; font-size: 11px; font-weight: 500;")
            self.servers_layout.addWidget(status_label, row, 1)

            time_label = QLabel(f"{server['response_time']:.2f}s")
            time_label.setStyleSheet(f"color: {ModernDarkTheme.TEXT_SECONDARY}; font-size: 11px;")
            self.servers_layout.addWidget(time_label, row, 2)

    @pyqtSlot(str)
    def on_error_occurred(self, error_message: str):
        self.progress_label.setText(f"Error: {error_message}")
        self.online_status_label.setText("❌ Error")
        self.online_status_label.setStyleSheet("color: #f44336; font-weight: bold;")

        self.is_loading = False
        self.refresh_btn.setEnabled(True)

    @pyqtSlot()
    def on_network_check_finished(self):
        self.is_loading = False
        self.progress_frame.setVisible(False)
        self.refresh_btn.setEnabled(True)
        self.progress_label.setText("")

    def refresh_network_info(self):
        if self.is_loading:
            return

        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()

        self.start_network_check()

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

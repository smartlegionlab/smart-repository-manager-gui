# Copyright (©) 2026, Alexander Suvorov. All rights reserved.
import os
import shutil
import subprocess
import sys
import time
import traceback
import webbrowser
from datetime import date
from pathlib import Path
from typing import Dict, Any

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QProgressBar, QMessageBox, QDialog, QMenu, QScrollArea, QApplication
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QAction, QKeySequence
from smart_repository_manager_core.services.github_service import GitHubService
from smart_repository_manager_core.services.structure_service import StructureService
from smart_repository_manager_core.services.sync_service import SyncService

from smart_repository_manager_gui.core.state_manager import ApplicationState
from smart_repository_manager_gui.core.storage_service import StorageService
from smart_repository_manager_gui.core.sync_manager import SyncManager
from smart_repository_manager_gui.ui.dark_theme import ModernDarkTheme
from smart_repository_manager_gui.ui.folder_info_dialog import StorageManagementDialog
from smart_repository_manager_gui.ui.network_info_dialog import NetworkInfoDialog
from smart_repository_manager_gui.ui.repo_detail_dialog import RepoDetailDialog
from smart_repository_manager_gui.ui.preloader import SmartPreloader
from smart_repository_manager_gui.ui.repo_table import RepoTable
from smart_repository_manager_gui.ui.ssh_info_dialog import SSHInfoDialog
from smart_repository_manager_gui.ui.sync_dialogue import SyncDialog
from smart_repository_manager_gui.ui.token_info_dialog import TokenInfoDialog
from smart_repository_manager_gui.ui.user_info_dialog import UserInfoDialog

from smart_repository_manager_gui import __version__ as ver
from smart_repository_manager_gui.ui.repo_download_dialog import RepoDownloadDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.app_state = ApplicationState()
        self.setWindowTitle(f"Smart Repository Manager {ver}")
        self._create_menu_bar()
        self._setup_ui()
        self.center_on_screen()
        self.sync_manager = SyncManager(self.app_state)
        self._initialize_ui()
        QTimer.singleShot(100, self._show_preloader)

    def _create_menu_bar(self):
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("&File")

        switch_user_action = QAction("&Switch User...", self)
        switch_user_action.triggered.connect(self._switch_user)
        file_menu.addAction(switch_user_action)

        file_menu.addSeparator()

        create_archive_action = QAction("Create &Archive...", self)
        create_archive_action.setShortcut(QKeySequence("Ctrl+B"))
        create_archive_action.triggered.connect(self._create_user_archive)
        file_menu.addAction(create_archive_action)

        file_menu.addSeparator()

        refresh_action = QAction("&Refresh", self)
        refresh_action.setShortcut(QKeySequence("F5"))
        refresh_action.triggered.connect(self._refresh_all)
        file_menu.addAction(refresh_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.confirm_exit)
        file_menu.addAction(exit_action)

        sync_menu = menu_bar.addMenu("&Synchronization")

        sync_all_action = QAction("&Synchronize All", self)
        sync_all_action.setShortcut(QKeySequence("Ctrl+S"))
        sync_all_action.triggered.connect(self.sync_all_repositories)
        sync_menu.addAction(sync_all_action)

        update_needed_action = QAction("&Update Needed Only", self)
        update_needed_action.setShortcut(QKeySequence("Ctrl+U"))
        update_needed_action.triggered.connect(self.update_available_repositories)
        sync_menu.addAction(update_needed_action)

        clone_missing_action = QAction("&Clone Missing Only", self)
        clone_missing_action.setShortcut(QKeySequence("Ctrl+M"))
        clone_missing_action.triggered.connect(self.sync_clone_missing)
        sync_menu.addAction(clone_missing_action)

        sync_with_repair_action = QAction("Sync with &Repair", self)
        sync_with_repair_action.setShortcut(QKeySequence("Ctrl+Shift+R"))
        sync_with_repair_action.triggered.connect(self.sync_with_repair)
        sync_menu.addAction(sync_with_repair_action)

        reclone_all_action = QAction("&Re-clone All", self)
        reclone_all_action.triggered.connect(self.sync_reclone_all)
        sync_menu.addAction(reclone_all_action)

        sync_menu.addSeparator()

        sync_selected_action = QAction("Sync &Selected", self)
        sync_selected_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        sync_selected_action.triggered.connect(self._sync_selected_repositories)
        sync_menu.addAction(sync_selected_action)

        clone_selected_action = QAction("&Clone Selected", self)
        clone_selected_action.setShortcut(QKeySequence("Ctrl+Shift+C"))
        clone_selected_action.triggered.connect(self._clone_selected_repositories)
        sync_menu.addAction(clone_selected_action)

        update_selected_action = QAction("&Update Selected", self)
        update_selected_action.setShortcut(QKeySequence("Ctrl+Shift+U"))
        update_selected_action.triggered.connect(self._update_selected_repositories)
        sync_menu.addAction(update_selected_action)

        sync_menu.addSeparator()

        download_all_zip_action = QAction("Download All Repositories...", self)
        download_all_zip_action.triggered.connect(self.download_all_repositories_as_zip)
        sync_menu.addAction(download_all_zip_action)

        repo_menu = menu_bar.addMenu("&Repositories")

        open_in_browser_action = QAction("&Open in Browser", self)
        open_in_browser_action.setShortcut(QKeySequence("Ctrl+Shift+B"))
        open_in_browser_action.triggered.connect(self._open_selected_in_browser)
        repo_menu.addAction(open_in_browser_action)

        open_local_action = QAction("Open &Local Folder", self)
        open_local_action.setShortcut(QKeySequence("Ctrl+L"))
        open_local_action.triggered.connect(self._open_selected_local_folder)
        repo_menu.addAction(open_local_action)

        repo_menu.addSeparator()

        show_details_action = QAction("&Show Details", self)
        show_details_action.setShortcut(QKeySequence("Ctrl+D"))
        show_details_action.triggered.connect(self._show_selected_details)
        repo_menu.addAction(show_details_action)

        refresh_repo_action = QAction("&Refresh Repository List", self)
        refresh_repo_action.setShortcut(QKeySequence("Ctrl+R"))
        refresh_repo_action.triggered.connect(self._refresh_repository_table)
        repo_menu.addAction(refresh_repo_action)

        repo_menu.addSeparator()

        delete_local_action = QAction("&Delete Local Copy", self)
        delete_local_action.setShortcut(QKeySequence("Ctrl+Delete"))
        delete_local_action.triggered.connect(self._delete_selected_local)
        repo_menu.addAction(delete_local_action)

        tools_menu = menu_bar.addMenu("&Tools")

        user_info_action = QAction("&User Information", self)
        user_info_action.setShortcut(QKeySequence("Ctrl+I"))
        user_info_action.triggered.connect(self.show_user_info)
        tools_menu.addAction(user_info_action)

        token_info_action = QAction("&Token Information", self)
        token_info_action.setShortcut(QKeySequence("Ctrl+T"))
        token_info_action.triggered.connect(self.show_token_info)
        tools_menu.addAction(token_info_action)

        ssh_info_action = QAction("&SSH Configuration", self)
        ssh_info_action.setShortcut(QKeySequence("Ctrl+Alt+S"))
        ssh_info_action.triggered.connect(self.show_ssh_info)
        tools_menu.addAction(ssh_info_action)

        network_info_action = QAction("&Network Information", self)
        network_info_action.setShortcut(QKeySequence("Ctrl+Shift+N"))
        network_info_action.triggered.connect(self.show_network_info)
        tools_menu.addAction(network_info_action)

        storage_info_action = QAction("&Storage Management", self)
        storage_info_action.setShortcut(QKeySequence("Ctrl+Shift+M"))
        storage_info_action.triggered.connect(self.show_folder_info)
        tools_menu.addAction(storage_info_action)

        tools_menu.addSeparator()

        help_menu = menu_bar.addMenu("&Help")

        documentation_action = QAction("&Documentation", self)
        documentation_action.setShortcut(QKeySequence("F1"))
        documentation_action.triggered.connect(self._show_documentation)
        help_menu.addAction(documentation_action)

        keyboard_shortcuts_action = QAction("&Keyboard Shortcuts", self)
        keyboard_shortcuts_action.triggered.connect(self._show_keyboard_shortcuts)
        help_menu.addAction(keyboard_shortcuts_action)

        help_menu.addSeparator()

        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 10)
        self.main_layout.setSpacing(20)

        self.create_header(self.main_layout)
        self.create_info_panel(self.main_layout)

        self.create_optimized_table(self.main_layout)

        self.create_action_buttons(self.main_layout)
        self.create_progress_bar(self.main_layout)
        self.create_status_bar()

    def _initialize_ui(self):
        self.user_btn.setText("👤 ---")
        self.user_btn.setVisible(False)
        self.status_label.setText("Initializing...")

        self.update_token_info_panel()
        self.update_stats()

    def update_token_info_panel(self):
        try:
            token_info = self.app_state.get('token_info')
            rate_limits = self.app_state.get('rate_limits')

            if not token_info:
                token_lines = [
                    "Checking...",
                    "API: ?/?",
                    "Reset: ---"
                ]
            else:
                token_status = "✅ Valid" if self.app_state.get('current_token') else "❌ Invalid"

                remaining = rate_limits.get('remaining', '?') if rate_limits else '?'
                limit = rate_limits.get('limit', '?') if rate_limits else '?'
                reset_time = rate_limits.get('reset_time', '---') if rate_limits else '---'

                token_lines = [
                    token_status,
                    f"API: {remaining}/{limit}",
                    f"Reset: {reset_time}"
                ]

            for i, line in enumerate(token_lines):
                if i < len(self.token_stats_widget.line_labels):
                    self.token_stats_widget.line_labels[i].setText(line)

        except Exception as e:
            print(f"Error updating token info panel: {e}")

    def update_ssh_info_panel(self):
        try:
            ssh_status = self.app_state.get('ssh_status', 'unknown')
            ssh_keys_found = len([k for k in self.app_state.get('checkup_results', [])
                                  if 'ssh_keys_found' in (k.get('data') or {})])

            if ssh_status == 'valid':
                status_text = "✅ Valid"
            elif ssh_status == 'partial':
                status_text = "⚠️ Partial"
            elif ssh_status == 'invalid':
                status_text = "❌ Invalid"
            else:
                status_text = "⏳ Checking..."

            github_auth_working = self.app_state.get('ssh_can_clone', False) or \
                                  self.app_state.get('ssh_can_pull', False)

            github_status = "✅ OK" if github_auth_working else "❌ Failed"

            ssh_lines = [
                f"Status: {status_text}",
                f"Keys: {ssh_keys_found if ssh_keys_found > 0 else '?'}",
                f"GitHub: {github_status}"
            ]

            for i, line in enumerate(ssh_lines):
                if i < len(self.ssh_stats_widget.line_labels):
                    self.ssh_stats_widget.line_labels[i].setText(line)

        except Exception as e:
            print(f"Error updating SSH info panel: {e}")
            ssh_lines = ["Status: Error", "Keys: ?", "GitHub: ?"]
            for i, line in enumerate(ssh_lines):
                if i < len(self.ssh_stats_widget.line_labels):
                    self.ssh_stats_widget.line_labels[i].setText(line)

    def update_network_info_panel(self):
        try:
            network_status = self.app_state.get('network_status', 'unknown')
            github_access = self.app_state.get('github_access', False)
            github_message = self.app_state.get('github_access_message', '')

            if network_status == 'online':
                online_text = "✅ Online"
            elif network_status == 'offline':
                online_text = "❌ Offline"
            elif network_status == 'error':
                online_text = "❌ Error"
            else:
                online_text = "⏳ Checking..."

            if github_access:
                github_text = "✅ OK"
                if github_message:
                    github_text = f"✅ {github_message}"
            else:
                github_text = "❌ Failed"
                if github_message:
                    github_text = f"❌ {github_message}"

            external_ip = self.app_state.get('external_ip')

            network_lines = [
                f"Status: {online_text}",
                f"IP: {external_ip or "---"}",
                f"GitHub: {github_text}"
            ]

            for i, line in enumerate(network_lines):
                if i < len(self.network_stats_widget.line_labels):
                    self.network_stats_widget.line_labels[i].setText(line)

        except Exception as e:
            print(f"Error updating network info panel: {e}")
            network_lines = ["Status: Error", "IP: ---", "GitHub: ?"]
            for i, line in enumerate(network_lines):
                if i < len(self.network_stats_widget.line_labels):
                    self.network_stats_widget.line_labels[i].setText(line)

    def create_info_panel(self, parent_layout):
        self.info_widget = QWidget()
        self.info_layout = QHBoxLayout(self.info_widget)
        self.info_layout.setSpacing(15)
        self.info_layout.setContentsMargins(0, 0, 0, 0)

        self.token_stats_widget = self._create_stat_item("🔑", "Token", [
            "Checking...",
            "API: ?/?",
            "Reset: ---"
        ])

        self.repos_stats_widget = self._create_stat_item("📚", "Repositories", [
            "Total: 0",
            "Local: 0",
            "Updates: 0"
        ])

        self.user_stats_widget = self._create_stat_item("👤", "User", [
            "Name: ---",
            "Public: 0",
            "Followers: 0"
        ])

        self.network_stats_widget = self._create_stat_item("🌐", "Network", [
            "Status: Checking",
            "IP: ---",
            "GitHub: ?"
        ])

        self.ssh_stats_widget = self._create_stat_item("🔐", "SSH", [
            "Status: Checking",
            "Keys: ?",
            "GitHub: ?"
        ])

        self.info_layout.addWidget(self.token_stats_widget, 1)
        self.info_layout.addWidget(self.repos_stats_widget, 1)
        self.info_layout.addWidget(self.user_stats_widget, 1)
        self.info_layout.addWidget(self.network_stats_widget, 1)
        self.info_layout.addWidget(self.ssh_stats_widget, 1)

        parent_layout.addWidget(self.info_widget)

    def _create_stat_item(self, icon, title, lines):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(5)
        layout.setContentsMargins(15, 10, 15, 10)

        title_layout = QHBoxLayout()
        title_layout.setSpacing(8)

        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 14px;")

        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {ModernDarkTheme.PRIMARY_COLOR}; font-size: 13px; font-weight: 600;")

        title_layout.addWidget(icon_label)
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        layout.addLayout(title_layout)

        line_labels = []
        for line in lines:
            line_label = QLabel(line)
            line_label.setStyleSheet(f"color: {ModernDarkTheme.TEXT_PRIMARY}; font-size: 11px;")
            layout.addWidget(line_label)
            line_labels.append(line_label)

        widget.line_labels = line_labels
        layout.addStretch()
        return widget

    def create_optimized_table(self, parent_layout):
        self.repo_table = RepoTable()
        self.repo_table.row_double_clicked.connect(self.on_repo_double_clicked)

        self.repo_table.open_in_browser_requested.connect(self.open_repository_in_browser)
        self.repo_table.open_local_folder_requested.connect(self.open_local_repository_folder)
        self.repo_table.show_details_requested.connect(self.on_repo_double_clicked)

        self.repo_table.clone_repositories_batch.connect(self.clone_repositories_batch)
        self.repo_table.update_repositories_batch.connect(self.update_repositories_batch)
        self.repo_table.reclone_repositories_batch.connect(self.reclone_repositories_batch)
        self.repo_table.delete_repositories_batch.connect(self.delete_repositories_batch)

        self.repo_table.download_repositories_batch.connect(self.download_repositories_batch)

        parent_layout.addWidget(self.repo_table, 1)

    def clone_single_repository(self, repo):
        username = self.app_state.get('current_user')
        token = self.app_state.get('current_token')

        if not username or not token:
            QMessageBox.warning(self, "Warning", "No user selected or token not available")
            return

        reply = QMessageBox.question(
            self,
            "Clone Repository",
            f"Clone repository '{repo.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        dialog = SyncDialog(username, token, [repo], "clone_missing", self)
        dialog.start_sync()

        if dialog.exec():
            self.repo_table.update_repository_status(repo.name, True, False)
            QTimer.singleShot(1000, self._force_update_ui)

    def reclone_single_repository(self, repo):
        username = self.app_state.get('current_user')
        token = self.app_state.get('current_token')

        if not username or not token:
            QMessageBox.warning(self, "Warning", "No user selected or token not available")
            return

        if not repo.local_exists:
            QMessageBox.warning(
                self,
                "Cannot Re-clone",
                f"Repository '{repo.name}' is not cloned locally.",
                QMessageBox.StandardButton.Ok
            )
            return

        reply = QMessageBox.warning(
            self,
            "Re-clone Repository",
            f"Re-clone repository '{repo.name}'?\n\n"
            f"This will DELETE the local copy and clone it again from GitHub.\n"
            f"This action cannot be undone!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        structure_service = StructureService()
        structure = structure_service.get_user_structure(username)

        if structure and "repositories" in structure:
            repo_path = structure["repositories"] / repo.name
            if repo_path.exists():
                try:
                    shutil.rmtree(repo_path, ignore_errors=True)
                except Exception as e:
                    QMessageBox.warning(
                        self,
                        "Error",
                        f"Failed to delete local copy: {str(e)}",
                        QMessageBox.StandardButton.Ok
                    )
                    return

        dialog = SyncDialog(username, token, [repo], "clone_missing", self)
        dialog.start_sync()

        if dialog.exec():
            self.repo_table.update_repository_status(repo.name, True, False)
            QMessageBox.information(
                self,
                "Success",
                f"Repository '{repo.name}' re-cloned successfully.",
                QMessageBox.StandardButton.Ok
            )
            QTimer.singleShot(1000, self._force_update_ui)

    def create_header(self, parent_layout):
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setSpacing(10)

        title_row = QHBoxLayout()

        title_label = QLabel("Smart Repository Manager")
        title_font = QFont()
        title_font.setPointSize(29)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {ModernDarkTheme.PRIMARY_COLOR};")

        title_row.addWidget(title_label)
        title_row.addStretch()

        self.user_btn = QPushButton("👤 ---")
        self.user_btn.setFlat(True)
        self.user_btn.setStyleSheet(f"""
            QPushButton {{
                color: {ModernDarkTheme.TEXT_SECONDARY};
                font-size: 14px;
                padding: 5px 15px;
                border: none;
            }}
            QPushButton:hover {{
                color: {ModernDarkTheme.PRIMARY_COLOR};
                background-color: #2a2a2a;
                border-radius: 4px;
            }}
        """)
        self.user_btn.clicked.connect(self.show_user_info)
        self.user_btn.setVisible(False)
        title_row.addWidget(self.user_btn)

        header_layout.addLayout(title_row)

        subtitle_label = QLabel("A control center for your GitHub repository universe")
        subtitle_font = QFont()
        subtitle_font.setPointSize(14)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet(f"color: {ModernDarkTheme.TEXT_SECONDARY};")

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(f"""
            background-color: {ModernDarkTheme.BORDER_COLOR}; 
            height: 1px; 
            margin: 10px 0;
        """)

        header_layout.addWidget(subtitle_label)
        header_layout.addWidget(separator)

        parent_layout.addWidget(header_widget)

    def create_action_buttons(self, parent_layout):
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setSpacing(10)

        self.update_available_btn = QPushButton(f"🔄 Update (0)")
        self.update_available_btn.setMinimumWidth(80)
        self.update_available_btn.clicked.connect(self.update_available_repositories)
        self.update_available_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: #ff9900;
                        color: white;
                        font-weight: bold;
                    }}
                    QPushButton:hover {{
                        background-color: #e68a00;
                    }}
                """)
        self.update_available_btn.setVisible(False)

        self.sync_actions_btn = QPushButton("🔄 Sync Actions ▼")
        self.sync_actions_btn.setMinimumWidth(80)
        self.sync_actions_btn.clicked.connect(self.show_sync_actions_menu)
        self.sync_actions_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {ModernDarkTheme.PRIMARY_COLOR};
                        color: white;
                        font-weight: bold;
                    }}
                    QPushButton:hover {{
                        background-color: #1a75ff;
                    }}
                """)

        folder_info_btn = QPushButton("📁 Folders")
        folder_info_btn.setMinimumWidth(80)
        folder_info_btn.clicked.connect(self.show_folder_info)

        network_info_btn = QPushButton("🌐 Network")
        network_info_btn.setMinimumWidth(80)
        network_info_btn.clicked.connect(self.show_network_info)
        network_info_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #2a2a2a;
                color: white;
                font-weight: 500;
                border: 1px solid #3a3a3a;
            }}
            QPushButton:hover {{
                background-color: #333333;
                border-color: #4a4a4a;
            }}
        """)

        ssh_info_btn = QPushButton("🔐 SSH")
        ssh_info_btn.setMinimumWidth(80)
        ssh_info_btn.clicked.connect(self.show_ssh_info)
        ssh_info_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: white;
                font-weight: 500;
                border: 1px solid #3a3a3a;
            }
            QPushButton:hover {
                background-color: #333333;
                border-color: #4a4a4a;
            }
        """)

        token_info_btn = QPushButton("🔑 Token")
        token_info_btn.setMinimumWidth(80)
        token_info_btn.clicked.connect(self.show_token_info)

        exit_btn = QPushButton("Exit")
        exit_btn.setMinimumWidth(80)
        exit_btn.clicked.connect(self.confirm_exit)
        exit_btn.setStyleSheet("""
            QPushButton {
                background-color: #da2a2a;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ca1a1a;
            }
        """)

        button_layout.addWidget(self.update_available_btn)
        button_layout.addWidget(self.sync_actions_btn)
        button_layout.addWidget(folder_info_btn)
        button_layout.addWidget(network_info_btn)
        button_layout.addWidget(ssh_info_btn)
        button_layout.addWidget(token_info_btn)
        button_layout.addStretch()
        button_layout.addWidget(exit_btn)

        parent_layout.addWidget(button_widget)

    def show_sync_actions_menu(self):

        menu = QMenu(self)

        actions = [
            ("Synchronize All", self.sync_all_repositories, "Sync all repositories"),
            ("Clone Missing Only", self.sync_clone_missing, "Clone only missing ones"),
            ("Sync with Repair", self.sync_with_repair, "Synchronize with repairs"),
            ("Re-clone All", self.sync_reclone_all, "Re-clone all repositories"),
            ("---", None, None),
            ("Download All Repositories", self.download_all_repositories_as_zip,
             "Download all repositories as ZIP archives")
        ]

        for text, callback, tooltip in actions:
            if text == "---":
                menu.addSeparator()
            else:
                action = menu.addAction(text)
                action.setToolTip(tooltip)
                action.triggered.connect(callback)

        menu.exec(self.sync_actions_btn.mapToGlobal(self.sync_actions_btn.rect().bottomLeft()))

    def create_progress_bar(self, parent_layout):
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        parent_layout.addWidget(self.progress_bar)

    def create_status_bar(self):
        status_bar = self.statusBar()

        self.status_label = QLabel("Initializing...")
        status_bar.addWidget(self.status_label)

        self.total_repos_label = QLabel("Repositories: 0")
        self.local_repos_label = QLabel("Local: 0")
        self.updates_label = QLabel("Updates: 0")

        status_bar.addPermanentWidget(self.total_repos_label)
        status_bar.addPermanentWidget(QLabel(" | "))
        status_bar.addPermanentWidget(self.local_repos_label)
        status_bar.addPermanentWidget(QLabel(" | "))
        status_bar.addPermanentWidget(self.updates_label)

    def get_total_repos(self):
        return self.app_state.get('repositories')

    def get_total_repos_count(self):
        repos = self.get_total_repos()
        return len(repos)

    def get_local_repos(self):
        repos = self.get_total_repos()
        local_repos = [repo for repo in repos if repo.local_exists]
        return local_repos

    def get_local_repos_count(self):
        repos = self.get_total_repos()
        local_repos = [repo for repo in repos if repo.local_exists]
        return len(local_repos)

    def get_need_update_repos(self):
        repos = self.get_total_repos()
        need_update_repos = [repo for repo in repos if repo.need_update]
        return need_update_repos

    def get_need_update_repos_count(self):
        repos = self.get_total_repos()
        need_update_repos = [repo for repo in repos if repo.need_update]
        return len(need_update_repos)

    def update_info_panel(self):
        try:
            self.update_token_info_panel()
            self.update_network_info_panel()
            self.update_ssh_info_panel()

            total_repos = self.get_total_repos_count()
            local_repos = self.get_local_repos_count()
            needs_update = self.get_need_update_repos_count()

            repos_lines = [
                f"Total: {total_repos}",
                f"Local: {local_repos}",
                f"Updates: {needs_update}"
            ]

            for i, line in enumerate(repos_lines):
                if i < len(self.repos_stats_widget.line_labels):
                    self.repos_stats_widget.line_labels[i].setText(line)

            user_data = self.app_state.get('user_data', {})
            user_name = user_data.get('name', '---') if user_data else '---'
            public_repos = user_data.get('public_repos', 0) if user_data else 0
            followers = user_data.get('followers', 0) if user_data else 0

            user_lines = [
                f"Name: {user_name}",
                f"Public: {public_repos}",
                f"Followers: {followers}"
            ]

            for i, line in enumerate(user_lines):
                if i < len(self.user_stats_widget.line_labels):
                    self.user_stats_widget.line_labels[i].setText(line)

        except Exception as e:
            print(f"Error updating info panel: {e}")

    def update_stats(self):
        try:
            total = self.get_total_repos_count()
            local = self.get_local_repos_count()
            updates = self.get_need_update_repos_count()

            self.total_repos_label.setText(f"Repositories: {total}")
            self.local_repos_label.setText(f"Local: {local}")
            self.updates_label.setText(f"Updates: {updates}")

            self.update_available_button()
        except Exception as e:
            print(f"Error updating stats: {e}")

    def update_available_button(self):
        try:
            repositories = self.get_total_repos()

            needs_update_or_clone = self.get_need_update_repos_count()

            update_text = f"🔄 Update ({needs_update_or_clone})"
            self.update_available_btn.setText(update_text)
            self.update_available_btn.setVisible(needs_update_or_clone > 0)

            if needs_update_or_clone > 0:
                need_clone = len([r for r in repositories if not getattr(r, 'local_exists', False)])
                need_update = self.get_need_update_repos_count()

                tooltip_parts = []
                if need_clone > 0:
                    tooltip_parts.append(f"📥 {need_clone} need cloning")
                if need_update > 0:
                    tooltip_parts.append(f"🔄 {need_update} need updating")

                tooltip = " | ".join(tooltip_parts)
                self.update_available_btn.setToolTip(tooltip)
            else:
                local_count = len([r for r in repositories if getattr(r, 'local_exists', False)])
                if local_count > 0:
                    self.update_available_btn.setToolTip(f"✅ All {local_count} repositories are up to date")
                else:
                    self.update_available_btn.setToolTip("📁 No repositories available")

        except Exception as e:
            print(f"Error updating button: {e}")

    def _show_preloader(self):
        self.preloader = SmartPreloader(self.app_state)
        self.preloader.setup_complete.connect(self._on_checkup_complete)
        self.preloader.show()
        self.preloader.start()

    def _on_checkup_complete(self, success: bool, message: str):
        print(f"Checkup complete: success={success}, message={message}")

        if success:
            self._force_update_ui()
            self.preloader.close()
            self.show()
            self.status_label.setText("Ready")


            self.activateWindow()
            self.raise_()
        else:
            self.preloader.close()
            QMessageBox.critical(
                self,
                "Initialization Failed",
                f"System checkup failed: {message}\n\nPlease restart the application."
            )
            self.close()

    def _force_update_ui(self, wait_dialog=None):
        try:
            current_user = self.app_state.get('current_user')
            current_token = self.app_state.get('current_token')

            if current_user and current_token:
                self.sync_manager.set_user(current_user, current_token)

                local_count = self.get_local_repos_count()
                needs_update_count = self.get_need_update_repos_count()

                if local_count == 0 and needs_update_count == 0:
                    sync_stats = self.sync_manager.get_sync_stats()
                    if sync_stats:
                        self.app_state.update(
                            local_repositories_count=sync_stats.get('local', 0),
                            needs_update_count=sync_stats.get('needs_update', 0)
                        )

                self.user_btn.setText(f"👤 {current_user}")
                self.user_btn.setVisible(True)
            else:
                self.user_btn.setVisible(False)

            self.update_token_info_panel()
            self.update_info_panel()

            repositories = self.app_state.get('repositories', [])

            if repositories:
                self.repo_table.set_repositories(repositories)
            else:
                self.repo_table.clear()

            self.update_stats()

        except Exception as e:
            traceback.print_exc()
        if wait_dialog:
            wait_dialog.close()

    def on_repo_double_clicked(self, repo):
        dialog = RepoDetailDialog(repo, self, app_state=self.app_state)
        dialog.clone_requested.connect(self.clone_single_repository)
        dialog.update_requested.connect(self.update_single_repository)
        dialog.reclone_requested.connect(lambda r: self.reclone_repositories_batch([r]))
        dialog.delete_requested.connect(self.delete_local_repository)
        dialog.exec()

    def open_repository_in_browser(self, repo):
        if hasattr(repo, 'html_url') and repo.html_url:
            try:
                webbrowser.open(repo.html_url)
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Browser Error",
                    f"Failed to open browser: {str(e)}",
                    QMessageBox.StandardButton.Ok
                )

    def open_local_repository_folder(self, repo):
        username = self.app_state.get('current_user')
        if not username:
            QMessageBox.warning(self, "Error", "No user selected")
            return

        structure_service = StructureService()
        structure = structure_service.get_user_structure(username)

        if not structure or "repositories" not in structure:
            QMessageBox.warning(self, "Error", "Storage structure not found")
            return

        repo_path = structure["repositories"] / repo.name

        if not repo_path.exists():
            QMessageBox.warning(
                self,
                "Folder Not Found",
                f"Local repository folder doesn't exist:\n{repo_path}",
                QMessageBox.StandardButton.Ok
            )
            return

        try:
            if os.name == 'nt':
                os.startfile(str(repo_path))
            elif os.name == 'posix':
                subprocess.run(['xdg-open', str(repo_path)], check=False)
            else:
                subprocess.run(['open', str(repo_path)], check=False)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Cannot open folder: {str(e)}",
                QMessageBox.StandardButton.Ok
            )

    def clone_repository(self, repo):
        username = self.app_state.get('current_user')
        if not username:
            QMessageBox.warning(self, "Error", "No user selected")
            return

        reply = QMessageBox.question(
            self,
            "Clone Repository",
            f"Clone repository '{repo.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        dialog = SyncDialog(username, [repo], self)
        dialog.start_sync("clone")
        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            self.repo_table.update_repository_status(repo.name, True, False)
            QTimer.singleShot(1000, self._force_update_ui)

    def update_single_repository(self, repo):
        username = self.app_state.get('current_user')
        token = self.app_state.get('current_token')
        if not username:
            QMessageBox.warning(self, "Error", "No user selected")
            return

        if not repo.local_exists:
            QMessageBox.warning(
                self,
                "Cannot Update",
                f"Repository '{repo.name}' is not cloned locally",
                QMessageBox.StandardButton.Ok
            )
            return

        reply = QMessageBox.question(
            self,
            "Update Repository",
            f"Update repository '{repo.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        dialog = SyncDialog(username, token, [repo], "update_needed", self)
        dialog.start_sync()
        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            self.repo_table.update_repository_status(repo.name, True, False)
            QTimer.singleShot(1000, self._force_update_ui)

    def delete_local_repository(self, repo):
        username = self.app_state.get('current_user')
        if not username:
            QMessageBox.warning(self, "Error", "No user selected")
            return

        reply = QMessageBox.question(
            self,
            "Delete Local Repository",
            f"Delete local copy of '{repo.name}'?\n\nThis will only remove the local files, not the remote repository.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        structure_service = StructureService()
        structure = structure_service.get_user_structure(username)

        if not structure or "repositories" not in structure:
            QMessageBox.warning(self, "Error", "Storage structure not found")
            return

        repo_path = structure["repositories"] / repo.name

        try:
            if repo_path.exists():
                shutil.rmtree(repo_path, ignore_errors=True)

                self.repo_table.update_repository_status(repo.name, False, True)

                QMessageBox.information(
                    self,
                    "Success",
                    f"Local copy of '{repo.name}' deleted",
                    QMessageBox.StandardButton.Ok
                )

                QTimer.singleShot(1000, self._force_update_ui)
            else:
                QMessageBox.warning(
                    self,
                    "Not Found",
                    f"Local repository folder doesn't exist",
                    QMessageBox.StandardButton.Ok
                )

        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to delete: {str(e)}",
                QMessageBox.StandardButton.Ok
            )

    def clone_repositories_batch(self, repos):
        if not repos:
            return

        username = self.app_state.get('current_user')
        token = self.app_state.get('current_token')

        if not username or not token:
            QMessageBox.warning(self, "Warning", "No user selected or token not available")
            return

        reply = QMessageBox.question(
            self,
            "Clone Repositories",
            f"Clone {len(repos)} repositories?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        dialog = SyncDialog(username, token, repos, "clone_missing", self)
        dialog.start_sync()

        if dialog.exec():
            for repo in repos:
                self.repo_table.update_repository_status(repo.name, True, False)
            QTimer.singleShot(1000, self._force_update_ui)

    def update_repositories_batch(self, repos):
        if not repos:
            return

        username = self.app_state.get('current_user')
        token = self.app_state.get('current_token')

        if not username or not token:
            QMessageBox.warning(self, "Warning", "No user selected or token not available")
            return

        reply = QMessageBox.question(
            self,
            "Update Repositories",
            f"Update {len(repos)} repositories?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        dialog = SyncDialog(username, token, repos, "update_needed", self)
        dialog.start_sync()

        if dialog.exec():
            for repo in repos:
                self.repo_table.update_repository_status(repo.name, True, False)
            QTimer.singleShot(1000, self._force_update_ui)

    def reclone_repositories_batch(self, repos):
        if not repos:
            return

        username = self.app_state.get('current_user')
        token = self.app_state.get('current_token')

        if not username or not token:
            QMessageBox.warning(self, "Warning", "No user selected or token not available")
            return

        reply = QMessageBox.warning(
            self,
            "Re-clone Repositories",
            f"Re-clone {len(repos)} repositories?\n\n"
            f"This will DELETE local copies and clone them again from GitHub.\n"
            f"This action cannot be undone!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        dialog = SyncDialog(username, token, repos, "reclone_all", self)
        dialog.start_sync()

        if dialog.exec():
            for repo in repos:
                self.repo_table.update_repository_status(repo.name, True, False)

            QMessageBox.information(
                self,
                "Success",
                f"{len(repos)} repositories re-cloned successfully.",
                QMessageBox.StandardButton.Ok
            )

            QTimer.singleShot(1000, self._force_update_ui)

    def delete_repositories_batch(self, repos):
        if not repos:
            return

        username = self.app_state.get('current_user')
        if not username:
            QMessageBox.warning(self, "Error", "No user selected")
            return

        reply = QMessageBox.question(
            self,
            "Delete Local Copies",
            f"Delete local copies of {len(repos)} repositories?\n\nThis action cannot be undone!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        structure_service = StructureService()
        structure = structure_service.get_user_structure(username)

        if not structure or "repositories" not in structure:
            QMessageBox.warning(self, "Error", "Storage structure not found")
            return

        deleted_count = 0
        for repo in repos:
            repo_path = structure["repositories"] / repo.name
            if repo_path.exists():
                try:
                    shutil.rmtree(repo_path, ignore_errors=True)
                    repo.local_exists = False
                    repo.need_update = True
                    deleted_count += 1
                except Exception as e:
                    print(f"Error deleting {repo.name}: {e}")

        for repo in repos:
            if repo.local_exists is False:
                self.repo_table.update_repository_status(repo.name, False, True)

        if deleted_count > 0:
            QMessageBox.information(
                self,
                "Success",
                f"Deleted {deleted_count} local copies"
            )

        QTimer.singleShot(1000, self._force_update_ui)


    def update_available_repositories(self):
        self._start_sync_operation("update_needed")

    def _start_sync_operation(self, operation: str):
        username = self.app_state.get('current_user')
        token = self.app_state.get('current_token')
        repositories = self.app_state.get('repositories', [])

        if not username or not token:
            QMessageBox.warning(self, "Warning", "No user selected or token not available")
            return

        if not repositories:
            QMessageBox.information(self, "Information", "No repositories available to sync")
            return

        self.sync_manager.set_user(username, token)

        repos_to_sync = []
        operation_description = ""

        if operation == "sync_all":
            repos_to_sync = repositories
            operation_description = f"Synchronize All ({len(repos_to_sync)} repositories)"



        elif operation == "update_needed":
            repos_to_sync = []
            for repo in repositories:
                local_exists = getattr(repo, 'local_exists', False)
                need_update = getattr(repo, 'need_update', False)
                if not local_exists:
                    repos_to_sync.append(repo)
                elif local_exists and need_update:
                    repos_to_sync.append(repo)

            operation_description = f"Update Needed ({len(repos_to_sync)} repositories)"
            need_clone = len([r for r in repos_to_sync if not getattr(r, 'local_exists', False)])
            need_update = len([r for r in repos_to_sync if getattr(r, 'local_exists', False)])
            if need_clone > 0 and need_update > 0:
                operation_description += f" ({need_clone} to clone, {need_update} to update)"
            elif need_clone > 0:
                operation_description += f" ({need_clone} to clone)"
            elif need_update > 0:
                operation_description += f" ({need_update} to update)"

        elif operation == "clone_missing":
            repos_to_sync = [
                r for r in repositories
                if not getattr(r, 'local_exists', False)
            ]
            operation_description = f"Clone Missing ({len(repos_to_sync)} repositories)"

        elif operation == "sync_with_repair":
            repos_to_sync = repositories
            operation_description = f"Sync with Repair ({len(repos_to_sync)} repositories)"

        elif operation == "reclone_all":
            repos_to_sync = repositories
            operation_description = f"Re-clone All ({len(repos_to_sync)} repositories)"

        if not repos_to_sync:
            message = self._get_no_repos_message(operation, repositories)
            QMessageBox.information(self, "Information", message)
            return

        operation_names = {
            "sync_all": "Synchronize All",
            "update_needed": "Update Needed",
            "clone_missing": "Clone Missing",
            "sync_with_repair": "Sync with Repair",
            "reclone_all": "Re-clone All"
        }

        repo_info = self._get_repositories_info(repos_to_sync, operation)

        reply = QMessageBox.question(
            self,
            f"{operation_names.get(operation, operation)}",
            f"{operation_description}\n\n"
            f"{repo_info}\n\n"
            f"Do you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        dialog = SyncDialog(username, token, repos_to_sync, operation, self)
        dialog.start_sync()

        if dialog.exec():
            repositories = self.app_state.get('repositories', [])

            if repositories:
                self.repo_table.set_repositories(repositories)
            else:
                self.repo_table.clear()
            self.update_info_panel()
            self.update_stats()

    def _get_no_repos_message(self, operation: str, repositories: list) -> str:
        if operation == "update_needed":
            need_update_count = len([
                r for r in repositories
                if getattr(r, 'local_exists', False) and getattr(r, 'need_update', False)
            ])
            if need_update_count == 0:
                return "All local repositories are up to date!"
            else:
                return "No repositories need updating."

        elif operation == "clone_missing":
            missing_count = len([r for r in repositories if not getattr(r, 'local_exists', False)])
            if missing_count == 0:
                return "All repositories are already cloned locally!"
            else:
                return "No repositories to clone (check SSH configuration)."

        elif operation == "sync_all":
            if len(repositories) == 0:
                return "No repositories available."
            else:
                return "No repositories to sync (check SSH configuration)."

        else:
            return "No repositories available for this operation."

    def _get_repositories_info(self, repos_to_sync: list, operation: str) -> str:
        if not repos_to_sync:
            return ""

        local_count = len([r for r in repos_to_sync if getattr(r, 'local_exists', False)])
        need_update_count = len([r for r in repos_to_sync if getattr(r, 'need_update', False)])
        private_count = len([r for r in repos_to_sync if getattr(r, 'private', False)])

        info_lines = []

        if operation == "sync_all":
            info_lines.append(f"• Total repositories: {len(repos_to_sync)}")
            info_lines.append(f"• Local repositories: {local_count}")
            info_lines.append(f"• Remote repositories: {len(repos_to_sync) - local_count}")
            if need_update_count > 0:
                info_lines.append(f"• Need update: {need_update_count}")

        elif operation == "update_needed":
            info_lines.append(f"• Repositories needing update: {len(repos_to_sync)}")
            if len(repos_to_sync) <= 10:
                for repo in repos_to_sync[:10]:
                    info_lines.append(f"  - {repo.name}")
                if len(repos_to_sync) > 10:
                    info_lines.append(f"  ... and {len(repos_to_sync) - 10} more")

        elif operation == "clone_missing":
            info_lines.append(f"• Repositories to clone: {len(repos_to_sync)}")
            if len(repos_to_sync) <= 10:
                for repo in repos_to_sync[:10]:
                    info_lines.append(f"  - {repo.name}")
                if len(repos_to_sync) > 10:
                    info_lines.append(f"  ... and {len(repos_to_sync) - 10} more")

        elif operation == "reclone_all":
            info_lines.append(f"⚠️ WARNING: This will DELETE and re-clone {len(repos_to_sync)} repositories")
            info_lines.append(f"• Total repositories: {len(repos_to_sync)}")
            info_lines.append(f"• Private repositories: {private_count}")
            info_lines.append(f"• This action cannot be undone!")

        return "\n".join(info_lines)

    def show_user_info(self):
        dialog = UserInfoDialog(self.app_state, self)
        dialog.exec()

    def show_token_info(self):
        dialog = TokenInfoDialog(self.app_state, self)
        dialog.exec()

    def show_ssh_info(self):
        dialog = SSHInfoDialog(self.app_state, self)
        dialog.exec()

    def show_folder_info(self):
        username = self.app_state.get('current_user')
        if username:
            dialog = StorageManagementDialog(self.app_state, self)
            dialog.exec()
        else:
            QMessageBox.warning(self, "Warning", "No user selected")

    def show_network_info(self):
        dialog = NetworkInfoDialog(self.app_state, self)
        dialog.exec()

    def sync_all_repositories(self):
        self._start_sync_operation("sync_all")

    def sync_clone_missing(self):
        self._start_sync_operation("clone_missing")

    def sync_with_repair(self):
        reply = QMessageBox.question(
            self,
            "Sync with Repair",
            "⚠️ This operation will:\n"
            "1. Check all repositories for corruption\n"
            "2. Re-clone corrupted repositories\n"
            "3. Update all working repositories\n\n"
            "This may take longer than normal sync.\n\n"
            "Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._start_sync_operation("sync_with_repair")

    def sync_reclone_all(self):
        reply = QMessageBox.warning(
            self,
            "Warning - Re-clone All",
            "⚠️ This will delete and re-clone ALL repositories.\n\n"
            "This cannot be undone! Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._start_sync_operation("reclone_all")

    def _show_documentation(self):
        try:
            webbrowser.open("https://github.com/smartlegionlab/smart-repository-manager-gui")
        except:
            QMessageBox.information(
                self,
                "Documentation",
                "GitHub Repository: https://github.com/smartlegionlab/smart-repository-manager-gui\n\n"
                "Please visit the GitHub repository for documentation and issues."
            )

    def _show_keyboard_shortcuts(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Keyboard Shortcuts")
        dialog.setMinimumSize(600, 600)

        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        title_label = QLabel("📋 Keyboard Shortcuts")
        title_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #4d94ff;
            padding: 5px;
        """)
        main_layout.addWidget(title_label)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #444;
                border-radius: 5px;
                background-color: #1e1e1e;
            }
            QScrollBar:vertical {
                border: none;
                background: #2a2a2a;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #555;
                border-radius: 6px;
                min-height: 30px;
            }
        """)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(15, 15, 15, 15)
        content_layout.setSpacing(8)

        shortcuts = [
            ("File", [
                ("F5", "Refresh"),
                ("Ctrl+Q", "Exit")
            ]),
            ("Synchronization", [
                ("Ctrl+S", "Synchronize All"),
                ("Ctrl+U", "Update Needed Only"),
                ("Ctrl+M", "Clone Missing Only"),
                ("Ctrl+Shift+R", "Sync with Repair"),
                ("Ctrl+Shift+S", "Sync Selected"),
                ("Ctrl+Shift+C", "Clone Selected"),
                ("Ctrl+Shift+U", "Update Selected")
            ]),
            ("Repositories", [
                ("Ctrl+Shift+B", "Open in Browser"),
                ("Ctrl+L", "Open Local Folder"),
                ("Ctrl+D", "Show Details"),
                ("Ctrl+R", "Refresh List"),
                ("Ctrl+Delete", "Delete Local Copy")
            ]),
            ("Tools", [
                ("Ctrl+I", "User Information"),
                ("Ctrl+T", "Token Information"),
                ("Ctrl+Alt+S", "SSH Configuration"),
                ("Ctrl+Shift+N", "Network Information"),
                ("Ctrl+Shift+M", "Storage Management")
            ]),
            ("Help", [
                ("F1", "Documentation")
            ])
        ]

        for category, items in shortcuts:
            category_label = QLabel(f"{category}:")
            category_label.setStyleSheet("""
                color: #4d94ff;
                font-size: 14px;
                font-weight: bold;
                margin-top: 10px;
                margin-bottom: 5px;
            """)
            content_layout.addWidget(category_label)

            for shortcut, description in items:
                item_text = f"  {shortcut:<20} {description}"
                item_label = QLabel(item_text)
                item_label.setStyleSheet("""
                    color: #e0e0e0;
                    font-size: 13px;
                    font-family: 'Consolas', 'Monospace', monospace;
                    margin-left: 10px;
                """)
                content_layout.addWidget(item_label)

            content_layout.addSpacing(5)

        content_layout.addStretch()

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area, 1)

        close_btn = QPushButton("Close")
        close_btn.setMinimumWidth(100)
        close_btn.clicked.connect(dialog.accept)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ModernDarkTheme.PRIMARY_COLOR};
                color: white;
                font-weight: bold;
                padding: 8px 25px;
                border-radius: 4px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: #1a75ff;
            }}
        """)

        main_layout.addWidget(close_btn, 0, Qt.AlignmentFlag.AlignCenter)

        dialog.exec()

    def _refresh_all(self):
        self.status_label.setText("Refreshing...")
        wait_dialog = QDialog(self)
        wait_dialog.setWindowTitle("Refreshing...")
        wait_dialog.setFixedSize(300, 150)
        wait_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        wait_dialog.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)

        layout = QVBoxLayout(wait_dialog)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        wait_label = QLabel("⏳")
        wait_label.setStyleSheet("font-size: 40px;")
        wait_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        text_label = QLabel("Refreshing...\nPlease wait...")
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_label.setStyleSheet("font-size: 14px; color: #b0b0b0;")

        layout.addWidget(wait_label)
        layout.addWidget(text_label)

        wait_dialog.show()
        QTimer.singleShot(100, lambda: self._force_update_ui(wait_dialog))
        self.status_label.setText("Ready")

    def _refresh_repository_table(self):
        self.status_label.setText("Refreshing...")
        wait_dialog = QDialog(self)
        wait_dialog.setWindowTitle("Refreshing...")
        wait_dialog.setFixedSize(300, 150)
        wait_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        wait_dialog.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)

        layout = QVBoxLayout(wait_dialog)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        wait_label = QLabel("⏳")
        wait_label.setStyleSheet("font-size: 40px;")
        wait_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        text_label = QLabel("Refreshing...\nPlease wait...")
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_label.setStyleSheet("font-size: 14px; color: #b0b0b0;")

        layout.addWidget(wait_label)
        layout.addWidget(text_label)

        wait_dialog.show()
        QTimer.singleShot(100, lambda: self._refresh_repositories(wait_dialog))
        self.status_label.setText("Ready")

    def _sync_selected_repositories(self):
        selected_repos = self._get_selected_repositories()

        if not selected_repos:
            QMessageBox.warning(self, "Warning", "No repositories selected")
            return

        username = self.app_state.get('current_user')
        token = self.app_state.get('current_token')

        if not username or not token:
            QMessageBox.warning(self, "Warning", "No user selected or token not available")
            return

        reply = QMessageBox.question(
            self,
            "Sync Selected",
            f"Synchronize {len(selected_repos)} selected repositories?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        dialog = SyncDialog(username, token, selected_repos, "sync_all", self)
        dialog.start_sync()

        if dialog.exec():
            self._force_update_ui()

    def _clone_selected_repositories(self):
        selected_repos = self._get_selected_repositories()

        if not selected_repos:
            QMessageBox.warning(self, "Warning", "No repositories selected")
            return

        repos_to_clone = [r for r in selected_repos if not getattr(r, 'local_exists', False)]

        if not repos_to_clone:
            QMessageBox.information(self, "Information", "All selected repositories are already cloned locally")
            return

        username = self.app_state.get('current_user')
        token = self.app_state.get('current_token')

        if not username or not token:
            QMessageBox.warning(self, "Warning", "No user selected or token not available")
            return

        reply = QMessageBox.question(
            self,
            "Clone Selected",
            f"Clone {len(repos_to_clone)} selected repositories?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        dialog = SyncDialog(username, token, repos_to_clone, "clone_missing", self)
        dialog.start_sync()

        if dialog.exec():
            self._force_update_ui()

    def _update_selected_repositories(self):
        selected_repos = self._get_selected_repositories()

        if not selected_repos:
            QMessageBox.warning(self, "Warning", "No repositories selected")
            return

        local_repos = [r for r in selected_repos if getattr(r, 'local_exists', False)]

        if not local_repos:
            QMessageBox.information(self, "Information", "No local repositories selected")
            return

        username = self.app_state.get('current_user')
        token = self.app_state.get('current_token')

        if not username or not token:
            QMessageBox.warning(self, "Warning", "No user selected or token not available")
            return

        reply = QMessageBox.question(
            self,
            "Update Selected",
            f"Update {len(local_repos)} selected repositories?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        dialog = SyncDialog(username, token, local_repos, "update_needed", self)
        dialog.start_sync()

        if dialog.exec():
            self._force_update_ui()

    def download_all_repositories_as_zip(self):
        username = self.app_state.get('current_user')
        token = self.app_state.get('current_token')
        repositories = self.app_state.get('repositories', [])

        if not username:
            QMessageBox.warning(self, "Warning", "No user selected")
            return

        if not repositories:
            QMessageBox.information(self, "Information", "No repositories to download")
            return

        private_repos = [r for r in repositories if getattr(r, 'private', False)]

        if private_repos and not token:
            reply = QMessageBox.question(
                self,
                "Token Required",
                f"Found {len(private_repos)} private repositories that require a token.\n\n"
                f"Without a token, only public repositories will be downloaded.\n\n"
                f"Continue with public repositories only?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply != QMessageBox.StandardButton.Yes:
                return

            repositories = [r for r in repositories if not getattr(r, 'private', False)]

        if not repositories:
            QMessageBox.information(self, "Information", "No repositories to download after filtering")
            return

        dialog = RepoDownloadDialog(repositories, token, username, self)
        dialog.exec()

    def download_repositories_batch(self, repos):
        if not repos:
            return

        username = self.app_state.get('current_user')
        token = self.app_state.get('current_token')

        dialog = RepoDownloadDialog(repos, token, username, self)
        dialog.exec()

    def _open_selected_in_browser(self):
        selected_repos = self._get_selected_repositories()

        if not selected_repos:
            QMessageBox.warning(self, "Warning", "No repositories selected")
            return

        for repo in selected_repos:
            if hasattr(repo, 'html_url') and repo.html_url:
                try:
                    webbrowser.open(repo.html_url)
                except Exception as e:
                    print(f"Error: {e}")

        if len(selected_repos) == 1:
            QMessageBox.information(self, "Success", f"Opened {selected_repos[0].name} in browser")
        else:
            QMessageBox.information(self, "Success", f"Opened {len(selected_repos)} repositories in browser")

    def _open_selected_local_folder(self):
        selected_repos = self._get_selected_repositories()

        if not selected_repos:
            QMessageBox.warning(self, "Warning", "No repositories selected")
            return

        username = self.app_state.get('current_user')
        if not username:
            QMessageBox.warning(self, "Error", "No user selected")
            return

        structure_service = StructureService()
        structure = structure_service.get_user_structure(username)

        if not structure or "repositories" not in structure:
            QMessageBox.warning(self, "Error", "Storage structure not found")
            return

        opened_count = 0
        for repo in selected_repos:
            repo_path = structure["repositories"] / repo.name

            if repo_path.exists():
                try:
                    if os.name == 'nt':
                        os.startfile(str(repo_path))
                    elif os.name == 'posix':
                        subprocess.run(['xdg-open', str(repo_path)], check=False)
                    else:
                        subprocess.run(['open', str(repo_path)], check=False)
                    opened_count += 1
                except Exception as e:
                    print(f"Error: {3}")

        if opened_count > 0:
            QMessageBox.information(self, "Success", f"Opened {opened_count} local folders")
        else:
            QMessageBox.warning(self, "Warning", "No local folders found for selected repositories")

    def _show_selected_details(self):
        selected_repos = self._get_selected_repositories()

        if not selected_repos:
            QMessageBox.warning(self, "Warning", "No repository selected")
            return

        if len(selected_repos) > 1:
            QMessageBox.warning(self, "Warning", "Please select only one repository")
            return

        dialog = RepoDetailDialog(selected_repos[0], self, app_state=self.app_state)
        dialog.clone_requested.connect(self.clone_single_repository)
        dialog.update_requested.connect(self.update_single_repository)
        dialog.reclone_requested.connect(lambda r: self.reclone_repositories_batch([r]))
        dialog.delete_requested.connect(self.delete_local_repository)
        dialog.exec()

    def _refresh_repositories(self, wait_dialog):
        username = self.app_state.get('current_user')
        token = self.app_state.get('current_token')

        if not username or not token:
            QMessageBox.warning(self, "Warning", "No user selected or token not available")
            return

        try:
            github_service = GitHubService(token)
            success, repositories = github_service.fetch_user_repositories()

            if success:
                self.app_state.set('repositories', repositories)
                self.app_state.set('repositories_count', len(repositories))

                self._update_local_status()

                User = type('User', (), {})
                user_obj = User()
                user_obj.username = username

                start_time = time.time()
                sync_service = SyncService()
                update_results = sync_service.batch_check_repositories_need_update(
                    user_obj,
                    repositories
                )
                check_time = time.time() - start_time

                needs_update_count = 0
                for repo in repositories:
                    if repo.name in update_results:
                        needs_update, message = update_results[repo.name]
                        repo.need_update = needs_update

                        if needs_update:
                            needs_update_count += 1
                    else:
                        repo.need_update = False

                self.app_state.set('needs_update_count', needs_update_count)

                self.repo_table.set_repositories(repositories)
                self.update_stats()

                QMessageBox.information(
                    self,
                    "Success",
                    f"Loaded {len(repositories)} repositories\n"
                    f"{needs_update_count} require update\n"
                    f"Check took {check_time:.1f}s"
                )
            else:
                QMessageBox.warning(self, "Warning", "Failed to load repositories")

        except Exception as e:
            print(f"[ERROR] _refresh_repositories failed: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to refresh: {str(e)}")

        wait_dialog.close()

    def _delete_selected_local(self):
        selected_repos = self._get_selected_repositories()

        if not selected_repos:
            QMessageBox.warning(self, "Warning", "No repositories selected")
            return

        local_repos = [r for r in selected_repos if getattr(r, 'local_exists', False)]

        if not local_repos:
            QMessageBox.information(self, "Information", "No local repositories selected")
            return

        reply = QMessageBox.question(
            self,
            "Delete Local Copies",
            f"Delete local copies of {len(local_repos)} repositories?\n\nThis action cannot be undone!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        username = self.app_state.get('current_user')
        if not username:
            QMessageBox.warning(self, "Error", "No user selected")
            return

        structure_service = StructureService()
        structure = structure_service.get_user_structure(username)

        if not structure or "repositories" not in structure:
            QMessageBox.warning(self, "Error", "Storage structure not found")
            return

        deleted_count = 0
        for repo in local_repos:
            repo_path = structure["repositories"] / repo.name

            if repo_path.exists():
                try:
                    shutil.rmtree(repo_path, ignore_errors=True)
                    repo.local_exists = False
                    repo.need_update = True
                    deleted_count += 1
                except Exception as e:
                    print(f"Error: {e}")

        self._force_update_ui()

        if deleted_count > 0:
            QMessageBox.information(self, "Success", f"Deleted {deleted_count} local copies")
        else:
            QMessageBox.warning(self, "Warning", "Failed to delete local copies")

    def _create_user_archive(self):
        username = self.app_state.get('current_user')

        if not username:
            QMessageBox.warning(self, "Warning", "No user selected")
            return

        reply = QMessageBox.question(
            self,
            "Create Archive",
            f"Create archive of user '{username}'?\n\n"
            f"This will create a ZIP archive containing all user data.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        wait_dialog = QDialog(self)
        wait_dialog.setWindowTitle("Creating archive")
        wait_dialog.setFixedSize(300, 150)
        wait_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        wait_dialog.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)

        layout = QVBoxLayout(wait_dialog)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        wait_label = QLabel("⏳")
        wait_label.setStyleSheet("font-size: 40px;")
        wait_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        text_label = QLabel("Creating archive...\nPlease wait...")
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_label.setStyleSheet("font-size: 14px; color: #b0b0b0;")

        layout.addWidget(wait_label)
        layout.addWidget(text_label)

        wait_dialog.show()
        QTimer.singleShot(100, lambda: self._perform_archive_creation(username, wait_dialog))

    def _perform_archive_creation(self, username: str, wait_dialog=None):
        try:

            storage_service = StorageService()

            result = storage_service.create_user_archive(username)

            if wait_dialog and wait_dialog.isVisible():
                wait_dialog.close()
                wait_dialog.deleteLater()

            if result.get("success"):
                archive_path = result.get("archive_path", "Unknown")
                archive_name = result.get("archive_name", "Unknown")
                archive_size = result.get("archive_size_formatted", "Unknown")
                file_count = result.get("file_count", 0)

                details = (
                    f"✅ archive created successfully!\n\n"
                    f"📁 User: {username}\n"
                    f"📦 Archive: {archive_name}\n"
                    f"💾 Size: {archive_size}\n"
                    f"📄 Files: {file_count}\n\n"
                    f"Location:\n{archive_path}"
                )

                reply = QMessageBox.question(
                    self,
                    "archive Created",
                    details + "\n\nOpen archive folder?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.Yes:
                    archive_dir = Path(archive_path).parent
                    self._open_folder(archive_dir)
            else:
                error_msg = result.get("error", "Unknown error")
                QMessageBox.critical(self, "archive Error", f"Failed to create archive:\n{error_msg}")

        except Exception as e:
            if wait_dialog and wait_dialog.isVisible():
                wait_dialog.close()
                wait_dialog.deleteLater()

            QMessageBox.critical(
                self,
                "archive Error",
                f"Error creating archive:\n{str(e)}"
            )

    def _set_menu_actions_enabled(self, enabled: bool):
        try:
            menu_bar = self.menuBar()
            for menu in menu_bar.findChildren(QMenu):
                for action in menu.actions():
                    if action.text() != "E&xit":
                        action.setEnabled(enabled)
        except Exception as e:
            print(f"Error: {e}")

    def _open_folder(self, folder_path: Path):
        try:
            if folder_path.exists():
                import os
                import subprocess

                if os.name == 'nt':
                    os.startfile(str(folder_path))
                elif os.name == 'posix':
                    subprocess.run(['xdg-open', str(folder_path)], check=False)
                else:
                    subprocess.run(['open', str(folder_path)], check=False)
        except Exception as e:
            print(f"Cannot open folder: {e}")

    def _show_about(self):
        about_text = f"""
        <h2>Smart Repository Manager</h2>
        <p>Version: {ver}</p>
        <p>© {str(date.today().year)} Alexander Suvorov. All rights reserved.</p>

        <p>A powerful tool for managing GitHub repositories with advanced synchronization capabilities.</p>

        <p><b>Features:</b></p>
        <ul>
            <li>Multi-user GitHub account management</li>
            <li>Smart repository synchronization</li>
            <li>SSH key management</li>
            <li>Storage management and cleanup</li>
            <li>Network diagnostics</li>
            <li>Batch operations</li>
        </ul>

        <p>GitHub: <a href="https://github.com/smartlegionlab/smart-repository-manager-gui"
         style="color: #2a82da; text-decoration: none;">https://github.com/smartlegionlab/smart-repository-manager-gui</a></p>
        """

        QMessageBox.about(self, "About Smart Repository Manager", about_text)

    def _get_selected_repositories(self):
        selected_items = self.repo_table.table_widget.selectedItems()
        if not selected_items:
            return []

        selected_rows = set()
        for item in selected_items:
            selected_rows.add(item.row())

        repositories = []
        for row in selected_rows:
            if row < len(self.repo_table.displayed_repos):
                repositories.append(self.repo_table.displayed_repos[row])

        return repositories

    def _update_local_status(self):
        username = self.app_state.get('current_user')
        repositories = self.app_state.get('repositories', [])

        if not username or not repositories:
            return

        structure_service = StructureService()
        structure = structure_service.get_user_structure(username)

        if not structure or "repositories" not in structure:
            return

        repos_path = structure["repositories"]
        local_count = 0

        for repo in repositories:
            repo_path = repos_path / repo.name
            if repo_path.exists() and (repo_path / '.git').exists():
                repo.local_exists = True
                local_count += 1
            else:
                repo.local_exists = False

        self.app_state.set('local_repositories_count', local_count)
        self.app_state.set('repositories', repositories)

    def center_on_screen(self):
        screen = self.screen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def confirm_exit(self):
        self.close()

    @staticmethod
    def format_duration(seconds: float) -> str:
        from smart_repository_manager_core.utils.helpers import Helpers
        return Helpers.format_duration(seconds)

    def show_sync_summary(self, stats: Dict[str, Any], operation: str):
        from PyQt6.QtWidgets import QMessageBox

        total_time = sum(stats.get('durations', []))
        avg_time = total_time / len(stats['durations']) if stats['durations'] else 0

        summary = f"{operation.upper()} SUMMARY\n"
        summary += "=" * 40 + "\n\n"
        summary += "📊 Results:\n"

        for key, value in stats.items():
            if key != "durations" and isinstance(value, int):
                summary += f"  • {key.replace('_', ' ').title()}: {value}\n"

        summary += f"\n⏱️ Performance:\n"
        summary += f"  • Total time: {self.format_duration(total_time)}\n"
        summary += f"  • Average per repo: {self.format_duration(avg_time)}"

        QMessageBox.information(self, "Sync Summary", summary)

    def _switch_user(self):
        if hasattr(self, 'repo_table') and self.repo_table.is_loading:
            reply = QMessageBox.warning(
                self,
                "Operations in Progress",
                "Repository operations are still in progress.\n\n"
                "Switching user will cancel these operations.\n\n"
                "Continue anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply != QMessageBox.StandardButton.Yes:
                return

        reply = QMessageBox.question(
            self,
            "Switch User",
            "This will restart the application to switch to a different GitHub account.\n\n"
            "All unsaved data will be preserved in the configuration.\n\n"
            "Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        msg = QMessageBox(self)
        msg.setWindowTitle("Restarting...")
        msg.setText("Switching user. Please wait...")
        msg.setStandardButtons(QMessageBox.StandardButton.NoButton)
        msg.show()

        QApplication.processEvents()

        QTimer.singleShot(500, lambda: self._perform_restart(msg))

    def _perform_restart(self, msg_box=None):
        if msg_box:
            msg_box.close()
            msg_box.deleteLater()

        os.execv(sys.executable, [sys.executable] + sys.argv)

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self,
            "Confirm Exit",
            "Are you sure you want to exit Smart Repository Manager?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()

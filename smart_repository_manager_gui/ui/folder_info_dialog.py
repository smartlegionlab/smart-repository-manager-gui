# Copyright (©) 2026, Alexander Suvorov. All rights reserved.
from datetime import datetime

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QGridLayout,
    QWidget, QMessageBox, QProgressBar,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

import subprocess
import os
from pathlib import Path

from smart_repository_manager_gui.core.storage_service import StorageService


class StorageAnalysisThread(QThread):
    analysis_complete = pyqtSignal(dict)
    progress_update = pyqtSignal(int, str)

    def __init__(self, username: str):
        super().__init__()
        self.username = username
        self.storage_service = StorageService()
        self.is_running = True

    def run(self):
        try:
            self.progress_update.emit(0, "Starting storage analysis...")

            self.progress_update.emit(20, "Getting storage structure...")
            storage_info = self.storage_service.get_storage_info(self.username)

            if not self.is_running:
                return

            if "error" in storage_info:
                self.analysis_complete.emit({
                    "success": False,
                    "error": storage_info["error"]
                })
                return

            self.progress_update.emit(50, "Analyzing repositories...")

            repos_info = []
            if "folders" in storage_info and "repositories" in storage_info["folders"]:
                repos_path = Path(storage_info["folders"]["repositories"]["path"])
                if repos_path.exists():
                    for repo_dir in repos_path.iterdir():
                        if not self.is_running:
                            return

                        if repo_dir.is_dir():
                            repo_info = self.storage_service.get_repository_details(
                                self.username,
                                repo_dir.name
                            )
                            repos_info.append(repo_info)

            self.progress_update.emit(80, "Calculating statistics...")

            results = {
                "success": True,
                "storage_info": storage_info,
                "repositories": repos_info,
                "total_repos": len(repos_info),
                "timestamp": datetime.now().isoformat()
            }

            self.progress_update.emit(100, "Analysis complete!")
            self.analysis_complete.emit(results)

        except Exception as e:
            self.analysis_complete.emit({
                "success": False,
                "error": str(e)
            })

    def stop(self):
        self.is_running = False


class FolderPathLabel(QLabel):
    clicked = pyqtSignal(str)

    def __init__(self, text="", path=""):
        super().__init__(text)
        self.path = path
        self.setStyleSheet("""
            QLabel {
                color: #4d94ff;
                text-decoration: underline;
                padding: 2px 5px;
                border-radius: 3px;
            }
            QLabel:hover {
                background-color: #2a2a2a;
                color: #6aafff;
            }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(f"Click to open: {path}")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.path)
        super().mousePressEvent(event)


class StorageManagementDialog(QDialog):
    def __init__(self, app_state, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        self.username = app_state.get('current_user')
        self.storage_service = StorageService()
        self.analysis_thread = None

        self.setWindowTitle("Storage Management")
        self.setMinimumSize(900, 700)

        self.setup_ui()
        self.load_storage_info()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        from PyQt6.QtWidgets import QTabWidget
        self.tab_widget = QTabWidget()

        self.overview_tab = self.create_overview_tab()
        self.tab_widget.addTab(self.overview_tab, "📊 Overview")

        self.repos_tab = self.create_repositories_tab()
        self.tab_widget.addTab(self.repos_tab, "📁 Repositories")

        self.cleanup_tab = self.create_cleanup_tab()
        self.tab_widget.addTab(self.cleanup_tab, "🗑️ Cleanup")

        main_layout.addWidget(self.tab_widget)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.refresh_storage_info)

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)

        button_layout.addWidget(self.refresh_btn)
        button_layout.addWidget(self.close_btn)

        main_layout.addLayout(button_layout)

    def create_overview_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        overview_group = QGroupBox("Storage Overview")
        overview_layout = QVBoxLayout(overview_group)

        self.overview_widget = QWidget()
        self.overview_layout = QGridLayout(self.overview_widget)
        self.overview_layout.setColumnStretch(0, 1)
        self.overview_layout.setColumnStretch(1, 2)

        overview_layout.addWidget(self.overview_widget)
        layout.addWidget(overview_group)

        folders_group = QGroupBox("Folder Locations")
        folders_layout = QVBoxLayout(folders_group)

        self.folders_widget = QWidget()
        self.folders_layout = QGridLayout(self.folders_widget)
        self.folders_layout.setColumnStretch(0, 1)
        self.folders_layout.setColumnStretch(1, 2)
        self.folders_layout.setColumnStretch(2, 1)

        folders_layout.addWidget(self.folders_widget)
        layout.addWidget(folders_group)

        disk_group = QGroupBox("Disk Usage")
        disk_layout = QVBoxLayout(disk_group)

        self.disk_widget = QWidget()
        self.disk_layout = QGridLayout(self.disk_widget)
        self.disk_layout.setColumnStretch(0, 1)
        self.disk_layout.setColumnStretch(1, 2)

        disk_layout.addWidget(self.disk_widget)
        layout.addWidget(disk_group)

        layout.addStretch()
        return widget

    def create_repositories_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.repos_table = QTableWidget()
        self.repos_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.repos_table.setColumnCount(6)
        self.repos_table.setHorizontalHeaderLabels([
            "Repository", "Size", "Files", "Folders", "Git", "Last Modified"
        ])
        self.repos_table.setSortingEnabled(True)
        self.repos_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        header = self.repos_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, 6):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        button_layout = QHBoxLayout()

        self.delete_repo_btn = QPushButton("🗑️ Delete Selected")
        self.delete_repo_btn.clicked.connect(self.delete_selected_repository)
        self.delete_repo_btn.setEnabled(False)

        self.open_repo_btn = QPushButton("📂 Open Folder")
        self.open_repo_btn.clicked.connect(self.open_selected_repository)
        self.open_repo_btn.setEnabled(False)

        button_layout.addWidget(self.delete_repo_btn)
        button_layout.addWidget(self.open_repo_btn)
        button_layout.addStretch()

        layout.addWidget(self.repos_table)
        layout.addLayout(button_layout)

        self.repos_table.itemSelectionChanged.connect(self.update_repo_buttons)

        return widget

    def create_cleanup_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)

        temp_group = QGroupBox("Temporary Files Cleanup")
        temp_layout = QVBoxLayout(temp_group)

        self.temp_info_label = QLabel("Checking temporary files...")
        self.clean_temp_btn = QPushButton("🧹 Clean Temporary Files")
        self.clean_temp_btn.clicked.connect(self.cleanup_temp_files)

        temp_layout.addWidget(self.temp_info_label)
        temp_layout.addWidget(self.clean_temp_btn)
        layout.addWidget(temp_group)

        delete_group = QGroupBox("Repository Management")
        delete_layout = QVBoxLayout(delete_group)

        self.delete_all_info_label = QLabel("Warning: This will delete ALL local repositories")
        self.delete_all_btn = QPushButton("⚠️ Delete All Repositories")
        self.delete_all_btn.clicked.connect(self.delete_all_repositories)
        self.delete_all_btn.setStyleSheet("background-color: #dc3545; color: white;")

        delete_layout.addWidget(self.delete_all_info_label)
        delete_layout.addWidget(self.delete_all_btn)
        layout.addWidget(delete_group)

        self.last_cleanup_label = QLabel("")
        self.last_cleanup_label.setStyleSheet("color: #6c757d; font-size: 11px;")
        layout.addWidget(self.last_cleanup_label)

        layout.addStretch()
        return widget

    def load_storage_info(self):
        if not self.username:
            QMessageBox.warning(self, "Warning", "No user selected")
            return

        self.start_storage_analysis()

    def start_storage_analysis(self):
        if self.analysis_thread and self.analysis_thread.isRunning():
            self.analysis_thread.stop()
            self.analysis_thread.wait()

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.refresh_btn.setEnabled(False)

        self.analysis_thread = StorageAnalysisThread(self.username)
        self.analysis_thread.progress_update.connect(self.on_progress_update)
        self.analysis_thread.analysis_complete.connect(self.on_analysis_complete)
        self.analysis_thread.start()

    def on_progress_update(self, value: int, message: str):
        self.progress_bar.setValue(value)
        self.progress_bar.setFormat(f"{message}... {value}%")

    def on_analysis_complete(self, results: dict):
        self.progress_bar.setVisible(False)

        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("🔄 Refresh")

        if results.get("success"):
            self.update_overview_tab(results["storage_info"])
            self.update_repositories_tab(results["repositories"])
            self.update_cleanup_tab(results["storage_info"])
        else:
            QMessageBox.warning(
                self,
                "Analysis Error",
                f"Failed to analyze storage: {results.get('error', 'Unknown error')}"
            )

    def update_overview_tab(self, storage_info: dict):
        self.clear_layout(self.overview_layout)
        self.clear_layout(self.folders_layout)
        self.clear_layout(self.disk_layout)

        row = 0
        self.add_info_row(self.overview_layout, row, "User:", f"@{self.username}")
        row += 1

        storage_path = storage_info.get("path", "N/A")
        path_label = QLabel(storage_path)
        path_label.setStyleSheet("color: #4d94ff; text-decoration: underline; padding: 2px 5px;")
        path_label.setCursor(Qt.CursorShape.PointingHandCursor)
        path_label.setToolTip(f"Click to open: {storage_path}")
        path_label.mousePressEvent = lambda e, p=storage_path: self.open_folder(
            p) if e.button() == Qt.MouseButton.LeftButton else None

        self.overview_layout.addWidget(QLabel("Storage Path:"), row, 0)
        self.overview_layout.addWidget(path_label, row, 1)
        row += 1

        self.add_info_row(self.overview_layout, row, "Repositories:", str(storage_info.get("repo_count", 0)))
        row += 1
        self.add_info_row(self.overview_layout, row, "Total Size:",
                          f"{storage_info.get('total_size_mb', 0):.2f} MB")

        if "folders" in storage_info:
            folder_types = [
                ("repositories", "📚 Repositories"),
                ("archives", "📦 Archives"),
                ("backups", "💾 Backups"),
                ("logs", "📝 Logs"),
                ("temp", "🗑️ Temp")
            ]

            row = 0
            for folder_key, display_name in folder_types:
                if folder_key in storage_info["folders"]:
                    folder_info = storage_info["folders"][folder_key]
                    folder_path = folder_info.get("path", "")
                    size_mb = folder_info.get("size_mb", 0)
                    item_count = folder_info.get("item_count", 0)

                    name_label = QLabel(display_name)
                    name_label.setStyleSheet("font-weight: bold;")

                    if folder_path and Path(folder_path).exists():
                        path_label = FolderPathLabel(folder_path, folder_path)
                        path_label.clicked.connect(self.open_folder)
                    else:
                        path_label = QLabel("Path not available")
                        path_label.setStyleSheet("color: #6c757d;")

                    stats_label = QLabel(f"{size_mb:.1f} MB, {item_count} items")
                    stats_label.setStyleSheet("color: #6c757d; font-size: 11px;")

                    self.folders_layout.addWidget(name_label, row, 0)
                    self.folders_layout.addWidget(path_label, row, 1)
                    self.folders_layout.addWidget(stats_label, row, 2)

                    row += 1

        if "disk_usage" in storage_info and "error" not in storage_info["disk_usage"]:
            disk_info = storage_info["disk_usage"]
            row = 0

            self.add_info_row(self.disk_layout, row, "Total Space:",
                              f"{disk_info.get('total_gb', 0):.1f} GB")
            row += 1
            self.add_info_row(self.disk_layout, row, "Used Space:",
                              f"{disk_info.get('used_gb', 0):.1f} GB")
            row += 1
            self.add_info_row(self.disk_layout, row, "Free Space:",
                              f"{disk_info.get('free_gb', 0):.1f} GB")
            row += 1
            self.add_info_row(self.disk_layout, row, "Usage:",
                              f"{disk_info.get('used_percent', 0):.1f}%")

            usage_percent = disk_info.get('used_percent', 0)
            usage_bar = QProgressBar()
            usage_bar.setValue(int(usage_percent))
            usage_bar.setFormat(f"{usage_percent:.1f}%")
            usage_bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #2d2d2d;
                    border-radius: 3px;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #0e65e5;
                    border-radius: 3px;
                }
            """)
            self.disk_layout.addWidget(QLabel("Usage Bar:"), row, 0)
            self.disk_layout.addWidget(usage_bar, row, 1)

    def update_repositories_tab(self, repositories: list):
        self.repos_table.setRowCount(len(repositories))

        for i, repo_info in enumerate(repositories):
            if "error" in repo_info:
                continue

            name_item = QTableWidgetItem(repo_info.get("repo_name", "Unknown"))
            self.repos_table.setItem(i, 0, name_item)

            size_item = QTableWidgetItem(repo_info.get("size_formatted", "0 B"))
            size_item.setData(Qt.ItemDataRole.UserRole, repo_info.get("size_bytes", 0))
            self.repos_table.setItem(i, 1, size_item)

            files_item = QTableWidgetItem(str(repo_info.get("file_count", 0)))
            self.repos_table.setItem(i, 2, files_item)

            folders_item = QTableWidgetItem(str(repo_info.get("folder_count", 0)))
            self.repos_table.setItem(i, 3, folders_item)

            git_status = "✓" if repo_info.get("is_git_repo", False) else "✗"
            git_item = QTableWidgetItem(git_status)
            git_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.repos_table.setItem(i, 4, git_item)

            modified = repo_info.get("modified", "").split("T")[0] if repo_info.get("modified") else "Unknown"
            modified_item = QTableWidgetItem(modified)
            self.repos_table.setItem(i, 5, modified_item)

        self.repos_table.sortItems(1, Qt.SortOrder.DescendingOrder)

    def update_cleanup_tab(self, storage_info: dict):
        if "folders" in storage_info and "temp" in storage_info["folders"]:
            temp_info = storage_info["folders"]["temp"]
            size_mb = temp_info.get("size_mb", 0)
            item_count = temp_info.get("item_count", 0)

            if item_count > 0:
                self.temp_info_label.setText(
                    f"Found {item_count} temporary files ({size_mb:.1f} MB)"
                )
                self.clean_temp_btn.setEnabled(True)
            else:
                self.temp_info_label.setText("No temporary files found")
                self.clean_temp_btn.setEnabled(False)

        repo_count = storage_info.get("repo_count", 0)
        if repo_count > 0:
            self.delete_all_info_label.setText(
                f"⚠️ Warning: This will delete ALL {repo_count} local repositories"
            )
            self.delete_all_btn.setEnabled(True)
        else:
            self.delete_all_info_label.setText("No local repositories found")
            self.delete_all_btn.setEnabled(False)

    def refresh_storage_info(self):
        if not self.username:
            QMessageBox.warning(self, "Warning", "No user selected")
            return

        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("Refreshing...")

        self.start_storage_analysis()

    def cleanup_temp_files(self):
        if not self.username:
            return

        reply = QMessageBox.question(
            self, "Confirm Cleanup",
            "Are you sure you want to clean temporary files?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        result = self.storage_service.cleanup_temp_files(self.username)

        if result.get("success"):
            QMessageBox.information(
                self, "Success",
                f"Cleaned {result.get('deleted_count', 0)} items\n"
                f"Freed: {result.get('total_size_formatted', '0 B')}"
            )
            self.refresh_storage_info()
        else:
            QMessageBox.warning(self, "Error", result.get("error", "Unknown error"))

    def delete_all_repositories(self):
        if not self.username:
            return

        confirm_text = QMessageBox.critical(
            self, "DANGER - Delete All Repositories",
            f"⚠️ ⚠️ ⚠️\n\n"
            f"This will PERMANENTLY delete ALL local repositories for user @{self.username}.\n\n"
            f"This action cannot be undone!\n\n"
            f"Type 'DELETE-ALL' to confirm:",
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
        )

        if confirm_text != QMessageBox.StandardButton.Ok:
            return

        from PyQt6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(
            self, "Final Confirmation",
            "Type 'DELETE-ALL' to confirm deletion:"
        )

        if not ok or text != 'DELETE-ALL':
            return

        result = self.storage_service.delete_all_repositories(self.username)

        if result.get("success"):
            deleted_count = result.get("deleted_count", 0)
            QMessageBox.information(
                self, "Success",
                f"Deleted {deleted_count} repositories\n"
                f"Failed: {result.get('failed_count', 0)}"
            )
            self.refresh_storage_info()
            self.app_state.update(local_repositories_count=0)
        else:
            QMessageBox.warning(self, "Error", result.get("error", "Unknown error"))

    def delete_selected_repository(self):
        selected = self.repos_table.selectedItems()
        if not selected:
            return

        row = selected[0].row()
        repo_name = self.repos_table.item(row, 0).text()

        reply = QMessageBox.question(
            self, "Confirm Deletion",
            f"Are you sure you want to delete repository '{repo_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        result = self.storage_service.delete_repository(self.username, repo_name)

        if result.get("success"):
            QMessageBox.information(self, "Success", result.get("message", "Repository deleted"))
            self.refresh_storage_info()

            current_local = self.app_state.get('local_repositories_count', 0)
            self.app_state.update(local_repositories_count=max(0, current_local - 1))
        else:
            QMessageBox.warning(self, "Error", result.get("error", "Unknown error"))

    def open_selected_repository(self):
        selected = self.repos_table.selectedItems()
        if not selected:
            return

        row = selected[0].row()
        repo_name = self.repos_table.item(row, 0).text()

        storage_info = self.storage_service.get_storage_info(self.username)
        if "folders" in storage_info and "repositories" in storage_info["folders"]:
            repo_path = Path(storage_info["folders"]["repositories"]["path"]) / repo_name

            if repo_path.exists():
                self.open_folder(str(repo_path))

    def open_folder(self, folder_path: str):
        try:
            if not folder_path or not Path(folder_path).exists():
                QMessageBox.warning(
                    self,
                    "Folder Not Found",
                    f"Folder does not exist:\n{folder_path}"
                )
                return

            if os.name == 'nt':
                os.startfile(folder_path)
            elif os.name == 'posix':
                subprocess.run(['xdg-open', folder_path], check=False)
            else:
                subprocess.run(['open', folder_path], check=False)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Cannot open folder: {str(e)}"
            )

    def update_repo_buttons(self):
        has_selection = len(self.repos_table.selectedItems()) > 0
        self.delete_repo_btn.setEnabled(has_selection)
        self.open_repo_btn.setEnabled(has_selection)

    def add_info_row(self, layout, row, label_text, value_text):
        label = QLabel(label_text)
        label.setStyleSheet("color: #b0b0b0;")

        value = QLabel(value_text)
        value.setStyleSheet("color: #ffffff; font-weight: 500;")

        layout.addWidget(label, row, 0)
        layout.addWidget(value, row, 1)

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def closeEvent(self, event):
        if self.analysis_thread and self.analysis_thread.isRunning():
            self.analysis_thread.stop()
            self.analysis_thread.wait()
        event.accept()

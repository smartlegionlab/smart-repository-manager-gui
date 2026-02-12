# Copyright (©) 2026, Alexander Suvorov. All rights reserved.
from datetime import datetime
from typing import List, Dict, Any

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QTextEdit, QWidget, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QFont
from smart_repository_manager_core.core.models.repository import Repository

from smart_repository_manager_gui.ui.dark_theme import ModernDarkTheme
from smart_repository_manager_gui.core.sync_manager import SyncManager


class SyncWorker(QThread):

    progress_started = pyqtSignal(int)
    repo_progress = pyqtSignal(str, str, str)
    repo_completed = pyqtSignal(str, bool, str, float)
    sync_completed = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, sync_manager, repositories: List[Repository], operation: str):
        super().__init__()
        self.sync_manager = sync_manager
        self.repositories = repositories
        self.operation = operation
        self._is_running = True

    def run(self):
        try:
            total_repos = len(self.repositories)
            self.progress_started.emit(total_repos)

            stats = self._execute_sync_operation()

            if self._is_running:
                self.sync_completed.emit(stats)

        except Exception as e:
            self.error_occurred.emit(f"Sync error: {str(e)}")

    def _execute_sync_operation(self) -> Dict[str, Any]:
        stats = {
            "synced": 0,
            "failed": 0,
            "skipped": 0,
            "durations": []
        }

        total = len(self.repositories)

        for i, repo in enumerate(self.repositories, 1):
            if not self._is_running:
                break

            if not hasattr(repo, 'ssh_url') or not repo.ssh_url:
                stats["skipped"] += 1
                self.repo_progress.emit(repo.name, "skipped", "No SSH URL")
                continue

            self.repo_progress.emit(repo.name, "start", f"Processing {i}/{total}")

            if self.operation == "sync_all":
                result = self._process_repo_sync_all(repo)
            elif self.operation == "update_needed":
                result = self._process_repo_update_needed(repo)
            elif self.operation == "clone_missing":
                result = self._process_repo_clone_missing(repo)
            elif self.operation == "sync_with_repair":
                result = self._process_repo_sync_repair(repo)
            elif self.operation == "reclone_all":
                result = self._process_repo_reclone(repo)
            else:
                result = (False, "Unknown operation", 0.0)

            success, message, duration = result
            stats["durations"].append(duration)

            self.repo_completed.emit(repo.name, success, message, duration)

            if success:
                if message == 'Already up to date' or message == "Already exists":
                    stats["skipped"] += 1
                    self.repo_progress.emit(repo.name, "skipped", message)
                else:
                    stats["synced"] += 1
                    self.repo_progress.emit(repo.name, "success", message)
            else:
                stats["failed"] += 1
                self.repo_progress.emit(repo.name, "failed", message)

        return stats

    def _process_repo_sync_all(self, repo):
        if repo.local_exists:
            return self.sync_manager.sync_single_repository(repo, "pull")
        else:
            return self.sync_manager.sync_single_repository(repo, "clone")

    def _process_repo_update_needed(self, repo):

        if not repo.local_exists:
            return self.sync_manager.sync_single_repository(repo, "clone")
        elif repo.need_update:
            return self.sync_manager.sync_single_repository(repo, "pull")
        else:
            return True, "Already up to date", 0.0

    def _process_repo_clone_missing(self, repo):
        if repo.local_exists:
            return False, "Already exists", 0.0
        return self.sync_manager.sync_single_repository(repo, "clone")

    def _process_repo_sync_repair(self, repo):
        return self.sync_manager.sync_single_repository(repo, "sync")

    def _process_repo_reclone(self, repo):
        return self.sync_manager.sync_single_repository(repo, "clone")

    def stop(self):
        self._is_running = False


class SyncDialog(QDialog):
    def __init__(self, username: str, token: str, repositories=None, operation: str = "sync_all", parent=None):
        super().__init__(parent)
        self.username = username
        self.token = token
        self.repositories = repositories or []
        self.operation = operation

        self.sync_manager = SyncManager(None)
        self.sync_manager.set_user(username, token)
        self.worker = None

        self.setWindowTitle("Repository Synchronization")
        self.setMinimumSize(800, 600)

        self.setup_ui()
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setSpacing(8)

        title = QLabel("Repository Synchronization")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color: {ModernDarkTheme.PRIMARY_COLOR};")

        operation_names = {
            "sync_all": "Synchronize All Repositories",
            "update_needed": "Update Needed Repositories",
            "clone_missing": "Clone Missing Repositories",
            "sync_with_repair": "Sync with Repair",
            "reclone_all": "Re-clone All Repositories"
        }

        self.subtitle = QLabel(f"{operation_names.get(self.operation, self.operation)} for @{self.username}")
        self.subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle.setStyleSheet(f"color: {ModernDarkTheme.TEXT_SECONDARY}; font-size: 12px;")

        self.phase_label = QLabel("Ready to start...")
        self.phase_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.phase_label.setStyleSheet(f"""
            color: {ModernDarkTheme.TEXT_PRIMARY};
            font-size: 14px;
            font-weight: 500;
            padding: 8px;
            background-color: {ModernDarkTheme.CARD_BG};
            border-radius: 6px;
        """)

        progress_widget = QWidget()
        progress_layout = QVBoxLayout(progress_widget)
        progress_layout.setSpacing(6)
        progress_layout.setContentsMargins(0, 0, 0, 0)

        self.progress_label = QLabel("0%")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setStyleSheet(f"color: {ModernDarkTheme.TEXT_SECONDARY}; font-size: 11px;")

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {ModernDarkTheme.BORDER_COLOR};
                border-radius: 4px;
                background-color: {ModernDarkTheme.CARD_BG};
                height: 20px;
            }}
            QProgressBar::chunk {{
                background-color: {ModernDarkTheme.PRIMARY_COLOR};
                border-radius: 4px;
            }}
        """)

        self.stats_label = QLabel(f"0 completed, 0 failed, 0 skipped, {len(self.repositories)} total")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stats_label.setStyleSheet(f"color: {ModernDarkTheme.TEXT_SECONDARY}; font-size: 11px;")

        self.current_repo_label = QLabel("Current repository: None")
        self.current_repo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.current_repo_label.setStyleSheet(
            f"color: {ModernDarkTheme.TEXT_PRIMARY}; font-size: 12px; font-weight: 500;")

        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.stats_label)
        progress_layout.addWidget(self.current_repo_label)

        log_label = QLabel("Operation Log")
        log_label.setStyleSheet(f"""
            color: {ModernDarkTheme.TEXT_PRIMARY};
            font-weight: bold;
            font-size: 13px;
        """)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(200)
        self.log_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {ModernDarkTheme.CARD_BG};
                border: 1px solid {ModernDarkTheme.BORDER_COLOR};
                border-radius: 4px;
                color: {ModernDarkTheme.TEXT_SECONDARY};
                font-size: 11px;
                font-family: 'Consolas', 'Monaco', monospace;
                padding: 8px;
            }}
        """)

        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(0, 10, 0, 0)
        button_layout.setSpacing(10)

        self.cancel_button = QPushButton("Stop")
        self.cancel_button.setMinimumWidth(120)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                font-weight: bold;
                border: none;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:disabled {
                background-color: #5a6268;
                color: #adb5bd;
            }
        """)
        self.cancel_button.clicked.connect(self.update_stop_button)
        self.cancel_button.setEnabled(False)

        self.close_button = QPushButton("Close")
        self.close_button.setMinimumWidth(120)
        self.close_button.setEnabled(False)
        self.close_button.clicked.connect(self.accept)

        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.close_button)

        header_layout.addWidget(title)
        header_layout.addWidget(self.subtitle)
        layout.addWidget(header_widget)
        layout.addWidget(self.phase_label)
        layout.addWidget(progress_widget)
        layout.addWidget(log_label)
        layout.addWidget(self.log_text)
        layout.addWidget(button_widget)

        self.completed_count = 0
        self.failed_count = 0
        self.skipped_count = 0
        self.total_repos = len(self.repositories)

    def start_sync(self):
        if not self.repositories:
            QMessageBox.warning(self, "Warning", "No repositories to sync")
            self.close()
            return

        self.cancel_button.setEnabled(True)
        self.close_button.setEnabled(False)
        self.phase_label.setText(f"Starting {self.operation.replace('_', ' ')}...")

        self.log_text.clear()

        self.completed_count = 0
        self.failed_count = 0
        self.skipped_count = 0

        self._add_log_entry(f"🚀 Starting {self.operation} for {self.total_repos} repositories...", "#4dabf7")
        self._add_log_entry(f"👤 User: @{self.username}", "#4dabf7")
        self._add_log_entry(f"📁 Operation: {self.operation}", "#4dabf7")
        self._add_log_entry("", "")

        self.worker = SyncWorker(self.sync_manager, self.repositories, self.operation)
        self.worker.progress_started.connect(self.on_progress_started)
        self.worker.repo_progress.connect(self.on_repo_progress)
        self.worker.repo_completed.connect(self.on_repo_completed)
        self.worker.sync_completed.connect(self.on_sync_completed)
        self.worker.error_occurred.connect(self.on_error_occurred)
        self.worker.start()

    def on_progress_started(self, total_repos: int):
        self.total_repos = total_repos
        self.phase_label.setText(f"Processing {total_repos} repositories...")
        self.progress_bar.setMaximum(total_repos)
        self._update_stats_label()

    def on_repo_progress(self, repo_name: str, status: str, message: str):
        self.current_repo_label.setText(f"Current: {repo_name} - {message}")

        if status == "start":
            self._add_log_entry(f"▶ Processing: {repo_name}", "#4dabf7")
        elif status == "success":
            self._add_log_entry(f"✅ {repo_name}: {message}", "#4caf50")
        elif status == "failed":
            self._add_log_entry(f"❌ {repo_name}: {message}", "#f44336")
        elif status == "skipped":
            self._add_log_entry(f"⏭️ {repo_name}: {message}", "#ff9800")

    def on_repo_completed(self, repo_name: str, success: bool, message: str, duration: float):
        if success:
            if message == 'Already up to date':
                self.skipped_count += 1
            else:
                self.completed_count += 1
        else:
            self.failed_count += 1

        processed = self.completed_count + self.failed_count + self.skipped_count
        progress = int((processed / self.total_repos) * 100) if self.total_repos > 0 else 0
        self.progress_bar.setValue(processed)
        self.progress_label.setText(f"{progress}%")

        self._update_stats_label()

        duration_str = f"({self.format_duration(duration)})" if duration > 0 else ""
        if success:
            if message != 'Already up to date':
                self._add_log_entry(f"   ✓ {message} {duration_str}", "#4caf50")
        else:
            self._add_log_entry(f"   ✗ Error: {message} {duration_str}", "#f44336")

    def on_sync_completed(self, stats: dict):
        total_time = sum(stats.get('durations', []))

        self.progress_bar.setValue(self.total_repos)
        self.progress_label.setText("100%")

        if self.failed_count == 0:
            self.phase_label.setText(f"✅ Synchronization completed successfully in {self.format_duration(total_time)}")
            self._add_log_entry("", "")
            self._add_log_entry(f"🎉 All repositories processed successfully!", "#4caf50")
        else:
            self.phase_label.setText(f"⚠️ Synchronization completed with {self.failed_count} errors")
            self._add_log_entry("", "")
            self._add_log_entry(f"⚠️ Processing completed with {self.failed_count} errors", "#ff9800")

        self._add_log_entry(f"📊 Results:", "#4dabf7")
        self._add_log_entry(f"   • Successful: {self.completed_count}", "#4caf50")
        if self.skipped_count > 0:
            self._add_log_entry(f"   • Skipped: {self.skipped_count}", "#ff9800")
        if self.failed_count > 0:
            self._add_log_entry(f"   • Failed: {self.failed_count}", "#f44336")
        self._add_log_entry(f"   • Total time: {self.format_duration(total_time)}", "#4dabf7")

        self.cancel_button.setEnabled(False)
        self.close_button.setEnabled(True)
        self.current_repo_label.setText("Synchronization completed")

    def on_error_occurred(self, error_message: str):
        self.phase_label.setText("❌ Synchronization failed")
        self._add_log_entry(f"❌ Critical error: {error_message}", "#ff4757")
        self.cancel_button.setEnabled(False)
        self.close_button.setEnabled(True)

    def _update_stats_label(self):
        remaining = self.total_repos - (self.completed_count + self.failed_count + self.skipped_count)
        self.stats_label.setText(
            f"{self.completed_count} completed, {self.failed_count} failed, "
            f"{self.skipped_count} skipped, {remaining} remaining"
        )

    def _add_log_entry(self, message: str, color: str = None):
        timestamp = datetime.now().strftime("%H:%M:%S")
        if color:
            html = f'<span style="color: {color};">[{timestamp}] {message}</span>'
        else:
            html = f'[{timestamp}] {message}'

        self.log_text.append(html)

        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    @staticmethod
    def format_duration(seconds: float) -> str:
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"

    def update_stop_button(self):
        self.cancel_button.setEnabled(False)
        self.cancel_button.setText("Stopping...")

        QTimer.singleShot(300, self.cancel_operation)

    def cancel_operation(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()

        self.phase_label.setText("🛑 Stopping operations...")
        self._add_log_entry("Operation cancelled by user", "#ff9800")

        QTimer.singleShot(1000, self._stop_operation)

    def _stop_operation(self):
        self.phase_label.setText("⏹️ Operation cancelled")
        self.cancel_button.setText("Stop")
        self.close_button.setEnabled(True)

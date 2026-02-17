# Copyright (©) 2026, Alexander Suvorov. All rights reserved.
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QTextEdit, QWidget,
    QMessageBox, QGroupBox, QFrame, QScrollArea,
    QComboBox, QGridLayout
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFont

from smart_repository_manager_gui.ui.dark_theme import ModernDarkTheme
from smart_repository_manager_gui.core.download_service import DownloadService


class ZipDownloadWorker(QThread):
    progress_update = pyqtSignal(int, int, str)
    repo_complete = pyqtSignal(dict)
    all_complete = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, zip_service, repositories, token, username, download_all_branches):
        super().__init__()
        self.zip_service = zip_service
        self.repositories = repositories
        self.token = token
        self.username = username
        self.download_all_branches = download_all_branches
        self._is_running = True

    def run(self):
        try:
            results = []
            successful = 0
            failed = 0
            total_repos = len(self.repositories)

            for i, repo in enumerate(self.repositories, 1):
                if not self._is_running:
                    break

                repo_name = repo.name
                repo_url = repo.html_url if hasattr(repo, 'html_url') else None

                if not repo_url:
                    results.append({
                        'repo': repo_name,
                        'success': False,
                        'error': 'No URL available'
                    })
                    failed += 1
                    continue

                self.progress_update.emit(i, total_repos, repo_name)

                if self.download_all_branches:
                    result = self.zip_service.download_repository_with_all_branches(
                        repo_name=repo_name,
                        repo_url=repo_url,
                        token=self.token,
                        username=self.username
                    )
                else:
                    branch = getattr(repo, 'default_branch', 'main')
                    if branch not in ['main', 'master']:
                        branch = 'main'

                    result = self.zip_service.download_repository_zip(
                        repo_name=repo_name,
                        repo_url=repo_url,
                        branch=branch,
                        token=self.token,
                        username=self.username
                    )

                repo_result = {
                    'repo': repo_name,
                    'success': result.get('success', False),
                    'result': result,
                    'is_private': getattr(repo, 'private', False)
                }

                results.append(repo_result)
                self.repo_complete.emit(repo_result)

                if result.get('success'):
                    successful += 1
                else:
                    failed += 1

            self.all_complete.emit({
                'success': successful > 0,
                'total': total_repos,
                'successful': successful,
                'failed': failed,
                'results': results,
                'username': self.username
            })

        except Exception as e:
            self.error_occurred.emit(str(e))

    def stop(self):
        self._is_running = False


class ZipDownloadDialog(QDialog):
    def __init__(self, repositories=None, token=None, username=None, parent=None):
        super().__init__(parent)
        self.repositories = repositories or []
        self.token = token
        self.username = username
        self.zip_service = DownloadService()
        self.worker = None
        self.results_data = []

        repo_count = len(self.repositories)
        if repo_count == 1:
            self.setWindowTitle(f"Download {self.repositories[0].name} as ZIP")
        else:
            self.setWindowTitle(f"Download {repo_count} Repositories as ZIP")

        self.setMinimumSize(800, 700)
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
        """)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)

        self.create_header(content_layout)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(f"background-color: {ModernDarkTheme.BORDER_COLOR}; height: 1px;")
        content_layout.addWidget(separator)

        self.create_options(content_layout)

        self.create_stats(content_layout)

        self.create_progress(content_layout)

        self.create_results(content_layout)

        content_layout.addStretch()
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

        self.create_buttons(main_layout)

        self.update_ui_for_repos()

    def create_header(self, parent_layout):
        header_layout = QVBoxLayout()
        header_layout.setSpacing(10)

        repo_count = len(self.repositories)

        if repo_count == 1:
            repo = self.repositories[0]
            visibility = "🔒 Private" if getattr(repo, 'private', False) else "🌍 Public"
            visibility_color = "#f44336" if getattr(repo, 'private', False) else "#4caf50"

            title_label = QLabel(f"Download ZIP: {repo.name}")
            title_font = QFont()
            title_font.setPointSize(16)
            title_font.setBold(True)
            title_label.setFont(title_font)
            title_label.setStyleSheet(f"color: {ModernDarkTheme.PRIMARY_COLOR};")
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            subtitle_label = QLabel(f"{repo.full_name}  |  {visibility}")
            subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            subtitle_label.setStyleSheet(f"color: {visibility_color}; font-size: 12px; font-weight: 500;")

            header_layout.addWidget(title_label)
            header_layout.addWidget(subtitle_label)
        else:
            private_count = sum(1 for r in self.repositories if getattr(r, 'private', False))
            public_count = repo_count - private_count

            title_label = QLabel(f"📦 Batch ZIP Download")
            title_font = QFont()
            title_font.setPointSize(16)
            title_font.setBold(True)
            title_label.setFont(title_font)
            title_label.setStyleSheet(f"color: {ModernDarkTheme.PRIMARY_COLOR};")
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            subtitle_label = QLabel(
                f"Downloading {repo_count} repositories "
                f"(🌍 {public_count} public, 🔒 {private_count} private)"
            )
            subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            subtitle_label.setStyleSheet(f"color: {ModernDarkTheme.TEXT_SECONDARY}; font-size: 12px;")

            header_layout.addWidget(title_label)
            header_layout.addWidget(subtitle_label)

        parent_layout.addLayout(header_layout)

    def create_options(self, parent_layout):
        options_group = QGroupBox("Download Options")
        options_group.setStyleSheet(f"""
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

        options_layout = QGridLayout()
        options_layout.setSpacing(12)

        mode_label = QLabel("Download mode:")
        mode_label.setStyleSheet(f"color: {ModernDarkTheme.TEXT_SECONDARY}; font-size: 12px;")
        options_layout.addWidget(mode_label, 0, 0)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Main branch only", "All branches"])
        self.mode_combo.setMinimumWidth(200)
        self.mode_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {ModernDarkTheme.CARD_BG};
                border: 1px solid {ModernDarkTheme.BORDER_COLOR};
                border-radius: 4px;
                padding: 6px 12px;
                color: {ModernDarkTheme.TEXT_PRIMARY};
                font-size: 12px;
            }}
        """)
        options_layout.addWidget(self.mode_combo, 0, 1)

        location_label = QLabel("Save to:")
        location_label.setStyleSheet(f"color: {ModernDarkTheme.TEXT_SECONDARY}; font-size: 12px;")
        options_layout.addWidget(location_label, 1, 0)

        if self.username:
            downloads_dir = Path.home() / "smart_repository_manager" / self.username / "downloads"
        else:
            downloads_dir = Path.home() / "smart_repository_manager" / "downloads"

        self.location_label = QLabel(str(downloads_dir))
        self.location_label.setStyleSheet(f"""
            color: {ModernDarkTheme.TEXT_PRIMARY};
            font-size: 11px;
            background-color: {ModernDarkTheme.CARD_BG};
            padding: 6px 10px;
            border: 1px solid {ModernDarkTheme.BORDER_COLOR};
            border-radius: 4px;
        """)
        self.location_label.setWordWrap(True)
        options_layout.addWidget(self.location_label, 1, 1)

        private_repos = [r for r in self.repositories if getattr(r, 'private', False)]
        if private_repos and not self.token:
            warning_text = (f"⚠️ Found {len(private_repos)} private repositories. "
                            f"Token required for downloading them.")
            self.token_warning = QLabel(warning_text)
            self.token_warning.setStyleSheet("""
                color: #ff9800;
                font-size: 11px;
                padding: 8px;
                background-color: #332b00;
                border: 1px solid #ff9800;
                border-radius: 4px;
            """)
            options_layout.addWidget(self.token_warning, 2, 0, 1, 2)

        options_group.setLayout(options_layout)
        parent_layout.addWidget(options_group)

    def create_stats(self, parent_layout):
        self.stats_group = QGroupBox("Download Statistics")
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

        stats_layout = QGridLayout()
        stats_layout.setSpacing(10)

        self.total_label = QLabel(f"Total: {len(self.repositories)}")
        self.completed_label = QLabel("Completed: 0")
        self.successful_label = QLabel("✅ Successful: 0")
        self.failed_label = QLabel("❌ Failed: 0")
        self.current_label = QLabel("Current: -")

        labels = [
            (self.total_label, 0, 0),
            (self.completed_label, 0, 1),
            (self.successful_label, 1, 0),
            (self.failed_label, 1, 1),
            (self.current_label, 2, 0, 1, 2)
        ]

        for widget, row, col, *span in labels:
            widget.setStyleSheet(f"color: {ModernDarkTheme.TEXT_PRIMARY}; font-size: 12px;")
            if span:
                stats_layout.addWidget(widget, row, col, span[0], span[1])
            else:
                stats_layout.addWidget(widget, row, col)

        self.stats_group.setLayout(stats_layout)
        parent_layout.addWidget(self.stats_group)

    def create_progress(self, parent_layout):
        progress_group = QGroupBox("Progress")
        progress_group.setStyleSheet(f"""
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

        progress_layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
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

        progress_layout.addWidget(self.progress_bar)
        progress_group.setLayout(progress_layout)
        parent_layout.addWidget(progress_group)

    def create_results(self, parent_layout):
        results_group = QGroupBox("Download Results")
        results_group.setStyleSheet(f"""
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

        results_layout = QVBoxLayout()

        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMinimumHeight(200)
        self.results_text.setStyleSheet(f"""
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

        results_layout.addWidget(self.results_text)
        results_group.setLayout(results_layout)
        parent_layout.addWidget(results_group)

    def create_buttons(self, parent_layout):
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.start_btn = QPushButton("▶ Start Download")
        self.start_btn.setMinimumWidth(150)
        self.start_btn.clicked.connect(self.start_download)
        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ModernDarkTheme.PRIMARY_COLOR};
                color: white;
                font-weight: bold;
                border: none;
                padding: 10px 20px;
            }}
            QPushButton:hover {{
                background-color: #1a75ff;
            }}
            QPushButton:disabled {{
                background-color: #5a6268;
                color: #adb5bd;
            }}
        """)

        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setMinimumWidth(100)
        self.stop_btn.clicked.connect(self.stop_download)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                font-weight: bold;
                border: none;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:disabled {
                background-color: #5a6268;
                color: #adb5bd;
            }
        """)

        self.open_folder_btn = QPushButton("📂 Open Download Folder")
        self.open_folder_btn.setMinimumWidth(150)
        self.open_folder_btn.clicked.connect(self.open_download_folder)
        self.open_folder_btn.setEnabled(False)
        self.open_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: white;
                border: 1px solid #3a3a3a;
                padding: 10px 20px;
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

        close_btn = QPushButton("Close")
        close_btn.setMinimumWidth(100)
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #b0b0b0;
                border: 1px solid #3a3a3a;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #2a2a2a;
            }
        """)

        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.stop_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.open_folder_btn)
        button_layout.addWidget(close_btn)

        parent_layout.addLayout(button_layout)

    def update_ui_for_repos(self):
        private_repos = [r for r in self.repositories if getattr(r, 'private', False)]

        if private_repos and not self.token:
            self.start_btn.setEnabled(False)
            self.start_btn.setToolTip("Token required for private repositories")
        else:
            self.start_btn.setEnabled(True)

    def start_download(self):
        if not self.repositories:
            QMessageBox.warning(self, "Warning", "No repositories to download")
            return

        download_all_branches = (self.mode_combo.currentText() == "All branches")

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.mode_combo.setEnabled(False)
        self.open_folder_btn.setEnabled(False)

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(len(self.repositories))
        self.results_text.clear()
        self.results_data.clear()

        self.completed_label.setText("Completed: 0")
        self.successful_label.setText("✅ Successful: 0")
        self.failed_label.setText("❌ Failed: 0")
        self.current_label.setText("Current: -")

        mode_text = "ALL BRANCHES" if download_all_branches else "MAIN BRANCH ONLY"
        self._add_log_entry(f"🚀 Starting batch download of {len(self.repositories)} repositories...", "#4dabf7")
        self._add_log_entry(f"👤 User: @{self.username}" if self.username else "", "#4dabf7")
        self._add_log_entry(f"📁 Mode: {mode_text}", "#4dabf7")
        self._add_log_entry(f"📂 Target: {self.location_label.text()}", "#4dabf7")
        self._add_log_entry("", "")

        self.worker = ZipDownloadWorker(
            zip_service=self.zip_service,
            repositories=self.repositories,
            token=self.token,
            username=self.username,
            download_all_branches=download_all_branches
        )

        self.worker.progress_update.connect(self.on_progress_update)
        self.worker.repo_complete.connect(self.on_repo_complete)
        self.worker.all_complete.connect(self.on_all_complete)
        self.worker.error_occurred.connect(self.on_error_occurred)

        self.worker.start()

    @pyqtSlot(int, int, str)
    def on_progress_update(self, current: int, total: int, repo_name: str):
        self.progress_bar.setValue(current)
        self.completed_label.setText(f"Completed: {current}/{total}")
        self.current_label.setText(f"Current: {repo_name}")

    @pyqtSlot(dict)
    def on_repo_complete(self, result: dict):
        repo_name = result['repo']
        success = result['success']
        is_private = result.get('is_private', False)

        if success:
            repo_result = result['result']
            if repo_result.get('success'):
                if 'results' in repo_result:  # All branches mode
                    successful = repo_result.get('successful', 0)
                    failed = repo_result.get('failed', 0)
                    total = repo_result.get('total_branches', 0)

                    icon = "🔒" if is_private else "🌍"
                    self._add_log_entry(
                        f"✅ {icon} {repo_name}: Downloaded {successful}/{total} branches",
                        "#4caf50"
                    )

                    current_success = int(self.successful_label.text().split(': ')[1])
                    current_failed = int(self.failed_label.text().split(': ')[1])
                    self.successful_label.setText(f"✅ Successful: {current_success + successful}")
                    self.failed_label.setText(f"❌ Failed: {current_failed + failed}")
                else:
                    icon = "🔒" if is_private else "🌍"
                    size = repo_result.get('size_formatted', '0 B')
                    self._add_log_entry(
                        f"✅ {icon} {repo_name}: Downloaded ({size})",
                        "#4caf50"
                    )

                    current_success = int(self.successful_label.text().split(': ')[1])
                    self.successful_label.setText(f"✅ Successful: {current_success + 1}")
            else:
                self._add_log_entry(
                    f"❌ {repo_name}: {repo_result.get('error', 'Unknown error')}",
                    "#f44336"
                )
                current_failed = int(self.failed_label.text().split(': ')[1])
                self.failed_label.setText(f"❌ Failed: {current_failed + 1}")
        else:
            self._add_log_entry(
                f"❌ {repo_name}: {result.get('error', 'Unknown error')}",
                "#f44336"
            )
            current_failed = int(self.failed_label.text().split(': ')[1])
            self.failed_label.setText(f"❌ Failed: {current_failed + 1}")

    @pyqtSlot(dict)
    def on_all_complete(self, stats: dict):
        self.progress_bar.setValue(stats['total'])
        self.completed_label.setText(f"Completed: {stats['total']}/{stats['total']}")
        self.current_label.setText("Current: -")

        self.stop_btn.setEnabled(False)
        self.start_btn.setEnabled(True)
        self.mode_combo.setEnabled(True)
        self.open_folder_btn.setEnabled(True)

        self._add_log_entry("", "")
        self._add_log_entry("=" * 50, "#4dabf7")
        self._add_log_entry(f"📊 BATCH DOWNLOAD COMPLETE", "#4dabf7")
        self._add_log_entry(f"   • Total: {stats['total']}", "#4dabf7")
        self._add_log_entry(f"   • ✅ Successful: {stats['successful']}", "#4caf50")
        if stats['failed'] > 0:
            self._add_log_entry(f"   • ❌ Failed: {stats['failed']}", "#f44336")
        self._add_log_entry(f"   • 📁 Location: {self.location_label.text()}", "#4dabf7")
        self._add_log_entry("=" * 50, "#4dabf7")

        if stats['total'] > 1:
            QMessageBox.information(
                self,
                "Download Complete",
                f"Downloaded {stats['successful']} of {stats['total']} repositories\n"
                f"Failed: {stats['failed']}\n\n"
                f"Files saved to:\n{self.location_label.text()}"
            )

    @pyqtSlot(str)
    def on_error_occurred(self, error_message: str):
        self._add_log_entry(f"❌ Critical error: {error_message}", "#f44336")
        self.stop_btn.setEnabled(False)
        self.start_btn.setEnabled(True)
        self.mode_combo.setEnabled(True)
        self.open_folder_btn.setEnabled(True)

    def stop_download(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()

        self._add_log_entry("⏹️ Download stopped by user", "#ff9800")
        self.stop_btn.setEnabled(False)
        self.start_btn.setEnabled(True)
        self.mode_combo.setEnabled(True)

    def open_download_folder(self):
        if self.username:
            folder_path = Path.home() / "smart_repository_manager" / self.username / "downloads"
        else:
            folder_path = Path.home() / "smart_repository_manager" / "downloads"

        if folder_path.exists():
            import os
            import subprocess

            try:
                if os.name == 'nt':
                    os.startfile(str(folder_path))
                elif os.name == 'posix':
                    subprocess.run(['xdg-open', str(folder_path)], check=False)
                else:
                    subprocess.run(['open', str(folder_path)], check=False)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Cannot open folder: {str(e)}")

    def _add_log_entry(self, message: str, color: str = None):
        if not message:
            return

        timestamp = datetime.now().strftime("%H:%M:%S")

        if color:
            html = f'<span style="color: {color};">[{timestamp}] {message}</span>'
        else:
            html = f'[{timestamp}] {message}'

        self.results_text.append(html)

        scrollbar = self.results_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Download in Progress",
                "Download is still in progress. Stop and exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.worker.stop()
                self.worker.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

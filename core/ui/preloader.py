# Copyright (©) 2026, Alexander Suvorov. All rights reserved.
import time
from datetime import datetime

import requests
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QFrame, QPushButton, QTextEdit, QHBoxLayout
from PyQt6.QtGui import QFont
import sys
from pathlib import Path

from core.ui.dark_theme import ModernDarkTheme
from smart_repository_manager_core.services.config_service import ConfigService
from smart_repository_manager_core.services.github_service import GitHubService
from smart_repository_manager_core.services.ssh_service import SSHService
from smart_repository_manager_core.services.network_service import NetworkService
from smart_repository_manager_core.services.structure_service import StructureService
from smart_repository_manager_core.services.sync_service import SyncService
from smart_repository_manager_core.core.models.ssh_models import SSHStatus
from core import  __version__ as ver


class SmartPreloader(QWidget):
    setup_complete = pyqtSignal(bool, str)

    def __init__(self, app_state):
        super().__init__()
        self.app_state = app_state
        self.config_service = ConfigService(self.app_state.config_path)
        self.ssh_service = SSHService()
        self.network_service = NetworkService()
        self.structure_service = StructureService(Path.home() / "smart_repository_manager")
        self.sync_service = SyncService()

        self.current_step = 0
        self.checkup_steps = [
            ("Checking directory structure...", self.check_structure),
            ("Checking internet connection...", self.check_internet),
            ("Checking SSH configuration...", self.check_ssh),
            ("Managing GitHub users...", self.manage_users),
            ("Getting GitHub user data...", self.get_user_data),
            ("Loading repositories...", self.get_repositories),
            ("Checking local copies...", self.check_local_repos),
            ("Checking for updates...", self.check_updates)
        ]

        self.setFixedSize(600, 500)
        self.setWindowTitle("Smart Repository Manager - Initialization")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 10)
        layout.setSpacing(15)

        title = QLabel("Smart Repository Manager")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color: {ModernDarkTheme.PRIMARY_COLOR}; margin-bottom: 10px;")

        subtitle = QLabel("System Initialization")
        subtitle_font = QFont()
        subtitle_font.setPointSize(12)
        subtitle.setFont(subtitle_font)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f"color: {ModernDarkTheme.TEXT_SECONDARY}; margin-bottom: 20px;")

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(f"background-color: {ModernDarkTheme.BORDER_COLOR}; height: 1px; margin: 10px 0;")

        self.step_label = QLabel("Preparing to start...")
        self.step_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.step_label.setStyleSheet(f"""
            color: {ModernDarkTheme.TEXT_PRIMARY};
            font-size: 14px;
            font-weight: 500;
            padding: 10px;
            background-color: {ModernDarkTheme.CARD_BG};
            border-radius: 6px;
            border: 1px solid {ModernDarkTheme.BORDER_COLOR};
        """)

        progress_widget = QWidget()
        progress_layout = QVBoxLayout(progress_widget)
        progress_layout.setSpacing(5)
        progress_layout.setContentsMargins(0, 10, 0, 10)

        self.progress_label = QLabel("0%")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setStyleSheet(f"color: {ModernDarkTheme.TEXT_SECONDARY}; font-size: 12px;")

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {ModernDarkTheme.BORDER_COLOR};
                border-radius: 4px;
                background-color: {ModernDarkTheme.CARD_BG};
                height: 16px;
            }}
            QProgressBar::chunk {{
                background-color: {ModernDarkTheme.PRIMARY_COLOR};
                border-radius: 4px;
            }}
        """)

        self.step_counter = QLabel(f"Step 0/{len(self.checkup_steps)}")
        self.step_counter.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.step_counter.setStyleSheet(f"color: {ModernDarkTheme.TEXT_SECONDARY}; font-size: 11px;")

        log_label = QLabel("Initialization Log")
        log_label.setStyleSheet(f"""
            color: {ModernDarkTheme.TEXT_PRIMARY};
            font-weight: bold;
            font-size: 13px;
            margin-top: 10px;
        """)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {ModernDarkTheme.CARD_BG};
                border: 1px solid {ModernDarkTheme.BORDER_COLOR};
                border-radius: 4px;
                color: {ModernDarkTheme.TEXT_SECONDARY};
                font-size: 10px;
                font-family: 'Consolas', 'Monaco', monospace;
                padding: 8px;
            }}
        """)

        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(0, 10, 0, 0)
        button_layout.setSpacing(10)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setMinimumWidth(100)
        self.cancel_button.clicked.connect(self.cancel_checkup)

        self.retry_button = QPushButton("Retry")
        self.retry_button.setMinimumWidth(100)
        self.retry_button.clicked.connect(self.restart_checkup)
        self.retry_button.hide()

        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.retry_button)

        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.step_counter)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(separator)
        layout.addWidget(self.step_label)
        layout.addWidget(progress_widget)
        layout.addWidget(log_label)
        layout.addWidget(self.log_text)
        layout.addWidget(button_widget)

    def start(self):
        self.current_step = 0
        self.progress_bar.setValue(0)
        self.log_text.clear()
        self.app_state.clear_results()

        self.cancel_button.setEnabled(True)
        self.cancel_button.setText("Cancel")

        self._add_log_entry("🚀 Starting system checkup...", "#4dabf7")
        QTimer.singleShot(500, self._run_next_step)

    def _run_next_step(self):
        if self.current_step >= len(self.checkup_steps):
            self._finish_checkup(True, "Checkup completed successfully")
            return

        step_name, step_func = self.checkup_steps[self.current_step]

        progress = int((self.current_step) / len(self.checkup_steps) * 100)
        self.progress_bar.setValue(progress)
        self.progress_label.setText(f"{progress}%")
        self.step_counter.setText(f"Step {self.current_step + 1}/{len(self.checkup_steps)}")
        self.step_label.setText(step_name)

        self._add_log_entry(f"▶ {step_name}")

        if step_func == self.manage_users:
            QTimer.singleShot(1000, lambda: self._open_user_selection())
        else:
            QTimer.singleShot(1000, lambda: self._execute_step(step_func))

    def _execute_step(self, step_func):
        try:
            success = step_func()
            if success:
                self.current_step += 1
                QTimer.singleShot(500, self._run_next_step)
            else:
                self._finish_checkup(False, f"Step {self.current_step + 1} failed")
        except Exception as e:
            self._add_log_entry(f"❌ Error: {str(e)}", "#ff4757")
            self._finish_checkup(False, f"Exception: {str(e)}")

    def _open_user_selection(self):
        from core.ui.dialogs.token_selection_dialog import TokenSelectionDialog

        dialog = TokenSelectionDialog()
        if dialog.exec():
            selected_user = dialog.get_selected_user()
            if selected_user:
                config = self.config_service.load_config()
                if selected_user in config.users:
                    self.config_service.set_active_user(selected_user)
                    self.app_state.set_multiple(
                        current_user=selected_user,
                        current_token=config.users[selected_user]
                    )
                    self._add_log_entry(f"✅ User selected: {selected_user}", "#4caf50")
                    self.current_step += 1
                    QTimer.singleShot(500, self._run_next_step)
                else:
                    self._add_log_entry(f"❌ User not found in config", "#ff4757")
                    self._finish_checkup(False, "User selection failed")
            else:
                self._add_log_entry("❌ No user selected", "#ff4757")
                self._finish_checkup(False, "User selection cancelled")
        else:
            self._add_log_entry("❌ User selection cancelled", "#ff9800")
            self._finish_checkup(False, "User selection cancelled")

    def check_structure(self) -> bool:
        try:

            config = self.config_service.load_config()

            config.set_version(ver)

            config.update_last_launch()

            self.config_service.save_config()
            self.config_service.load_config()

            base_dir = Path.home() / "smart_repository_manager"
            base_dir_exists = base_dir.exists()

            if not base_dir_exists:
                self._add_log_entry("⚠️ Base directory will be created when needed", "#ff9800")

            test_user = "_test_check"
            test_structure = self.structure_service.create_user_structure(test_user)

            if test_structure:
                self._add_log_entry(f"✅ Directory structure works", "#4caf50")

                test_user_dir = base_dir / test_user
                if test_user_dir.exists():
                    import shutil
                    shutil.rmtree(test_user_dir)

                self.app_state.log_result(True, "Directory structure check passed", {
                    "base_dir": str(base_dir),
                    "config_loaded": True
                })
                return True
            else:
                self._add_log_entry("❌ Failed to create structure", "#ff4757")
                return False

        except Exception as e:
            self._add_log_entry(f"❌ Structure error: {str(e)}", "#ff4757")
            return False

    def check_internet(self) -> bool:
        try:
            is_online = self.network_service.is_online()

            if not is_online:
                self._add_log_entry("❌ Internet unavailable", "#ff4757")
                self.app_state.update(network_status='offline', github_access=False)
                return False

            network_check = self.network_service.check_network()
            successful_checks = sum(1 for r in network_check.detailed_results if r["success"])

            self._add_log_entry(f"✅ Internet available ({successful_checks}/4 servers)", "#4caf50")

            git_ok, git_msg = self.network_service.check_git_connectivity()
            if git_ok:
                self._add_log_entry(f"✅ Git server access: {git_msg}", "#4caf50")
                self.app_state.update(github_access=True, github_access_message=git_msg)
            else:
                self._add_log_entry(f"⚠️ Git access issue: {git_msg}", "#ff9800")
                self.app_state.update(github_access=False, github_access_message=git_msg)

            dns_ok, dns_msg, ip_addresses = self.network_service.check_dns_resolution("github.com")
            if dns_ok and ip_addresses:
                self._add_log_entry(f"✅ DNS working: {dns_msg}", "#4caf50")
                self.app_state.update(dns_working=True, github_ips=ip_addresses)

            external_ip = self.network_service.get_ip()

            self.app_state.update(
                network_status='online',
                external_ip=external_ip,
                network_servers_available=successful_checks,
                network_total_servers=4
            )

            self.app_state.log_result(
                network_check.is_online,
                f"Internet check: {successful_checks}/4 servers",
                {
                    "online": network_check.is_online,
                    "external_ip": external_ip,
                    "github_access": git_ok,
                    "dns_working": dns_ok
                }
            )

            return network_check.is_online

        except Exception as e:
            self._add_log_entry(f"❌ Network error: {str(e)}", "#ff4757")
            self.app_state.update(network_status='error', github_access=False)
            return False

    def check_ssh(self) -> bool:
        try:
            validation = self.ssh_service.validate_ssh_configuration()

            data = {
                "status": validation.status.value,
                "ssh_keys_found": len(validation.ssh_config.keys),
                "github_auth_working": validation.github_authentication_working,
                "can_clone": validation.can_clone_with_ssh,
                "can_pull": validation.can_pull_with_ssh
            }

            self.app_state.set_multiple(
                ssh_status=validation.status.value,
                ssh_can_clone=validation.can_clone_with_ssh,
                ssh_can_pull=validation.can_pull_with_ssh
            )

            if validation.ssh_config.keys:
                key_info = []
                for key in validation.ssh_config.keys:
                    status = "✅" if key.is_github_authenticated else "⚠️"
                    key_info.append(f"{status} {key.type.value}")
                self._add_log_entry(f"Found {len(key_info)} SSH keys", "#4dabf7")

            status_color = "#4caf50" if validation.status == SSHStatus.VALID else "#ff9800"
            self._add_log_entry(f"SSH Status: {validation.status.value}", status_color)

            if validation.ssh_config.keys:
                test_success, test_msg, test_time = self.ssh_service.test_connection("github.com", "git")
                if test_success:
                    self._add_log_entry(f"✅ SSH connection to GitHub: {test_msg}", "#4caf50")
                else:
                    self._add_log_entry(f"⚠️ SSH test failed: {test_msg}", "#ff9800")

            self.app_state.log_result(
                validation.status in [SSHStatus.VALID, SSHStatus.PARTIAL],
                f"SSH configuration check",
                data
            )

            return validation.status in [SSHStatus.VALID, SSHStatus.PARTIAL]

        except Exception as e:
            self._add_log_entry(f"❌ SSH error: {str(e)}", "#ff4757")
            return False

    def manage_users(self) -> bool:
        return True

    def get_user_data(self) -> bool:
        token = self.app_state.get('current_token')
        if not token:
            self._add_log_entry("❌ No token available", "#ff4757")
            return False

        try:
            github_service = GitHubService(token)
            valid, user = github_service.validate_token()

            if not valid or not user:
                self._add_log_entry("❌ Invalid token", "#ff4757")
                return False

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

            self.app_state.update(
                current_user=user.username,
                user_data=user_data
            )

            if hasattr(user, 'avatar_url') and user.avatar_url:
                self.download_avatar(user.username, user.avatar_url)

            self._add_log_entry(f"✅ User: {user.username} ({user.name or 'No name'})", "#4caf50")

            token_info = github_service.get_token_info()

            token_data = {
                'username': token_info.username,
                'scopes': token_info.scopes or "Not specified",
                'rate_limit': token_info.rate_limit,
                'rate_remaining': token_info.rate_remaining,
                'created_at': token_info.created_at[:10] if token_info.created_at else "Unknown"
            }
            self.app_state.update(token_info=token_data)

            limits = github_service.check_rate_limits()

            reset_time_str = "Unknown"
            if limits.get('reset'):
                try:
                    reset_time = datetime.fromtimestamp(int(limits["reset"]))
                    reset_time_str = reset_time.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    pass

            rate_limits = {
                'limit': limits.get('limit'),
                'remaining': limits.get('remaining'),
                'used': limits.get('limit', 0) - limits.get('remaining', 0) if limits.get('limit') else 0,
                'reset': limits.get('reset'),
                'reset_time': reset_time_str
            }
            self.app_state.update(rate_limits=rate_limits)

            self._add_log_entry(f"API Limits: {limits.get('remaining', '?')}"
                                f"/{limits.get('limit', '?')}", "#4dabf7")

            self.app_state.log_result(
                True,
                f"GitHub user data loaded",
                {
                    "username": user.username,
                    "public_repos": user.public_repos,
                    "token_scopes": token_info.scopes
                }
            )

            return True

        except Exception as e:
            self._add_log_entry(f"❌ User data error: {str(e)}", "#ff4757")
            return False

    def download_avatar(self, username, avatar_url):
        try:

            user_dir = Path.home() / "smart_repository_manager" / username
            user_dir.mkdir(parents=True, exist_ok=True)

            avatar_path = user_dir / "avatar.png"

            response = requests.get(avatar_url, timeout=10)
            if response.status_code == 200:
                with open(avatar_path, 'wb') as f:
                    f.write(response.content)

        except Exception as e:
            print(f"Error downloading avatar: {e}")

    def get_repositories(self) -> bool:
        token = self.app_state.get('current_token')
        user = self.app_state.get('current_user')

        if not token or not user:
            self._add_log_entry("❌ User not set", "#ff4757")
            return False

        try:
            github_service = GitHubService(token)
            success, repositories = github_service.fetch_user_repositories()

            if not success:
                self._add_log_entry("❌ Failed to load repositories", "#ff4757")
                return False

            self.app_state.set('repositories', repositories)

            total = len(repositories)
            private_count = sum(1 for r in repositories if r.private)
            public_count = total - private_count
            forks_count = sum(1 for r in repositories if r.fork)
            archived_count = sum(1 for r in repositories if r.archived)

            self.app_state.update(
                repositories_count=total,
                total_private=private_count,
                total_public=public_count,
                total_forks=forks_count,
                total_archived=archived_count
            )

            self._add_log_entry(f"✅ Loaded {total} repositories", "#4caf50")
            self._add_log_entry(f"  • Private: {private_count}, Public: {public_count}", "#4dabf7")

            self.app_state.log_result(
                True,
                f"Repositories loaded",
                {
                    "total": total,
                    "private": private_count,
                    "public": public_count,
                    "forks": forks_count
                }
            )

            return True

        except Exception as e:
            self._add_log_entry(f"❌ Repositories error: {str(e)}", "#ff4757")
            return False

    def check_local_repos(self) -> bool:
        user = self.app_state.get('current_user')
        repositories = self.app_state.get('repositories', [])

        if not user or not repositories:
            self._add_log_entry("❌ No data available", "#ff4757")
            return False

        try:
            user_structure = self.structure_service.create_user_structure(user)

            if not user_structure:
                self._add_log_entry("❌ Failed to create directory structure", "#ff4757")
                return False

            repos_path = user_structure["repositories"]
            local_count = 0

            for repo in repositories:
                repo_path = repos_path / repo.name
                if repo_path.exists() and (repo_path / '.git').exists():
                    repo.local_exists = True
                    local_count += 1
                else:
                    repo.local_exists = False

            self.app_state.update(
                local_repositories_count=local_count,
                storage_path=str(user_structure["user"])
            )

            self._add_log_entry(f"✅ Local copies: {local_count}/{len(repositories)}", "#4caf50")

            self.app_state.log_result(
                True,
                f"Local repository check",
                {
                    "total": len(repositories),
                    "local": local_count,
                    "missing": len(repositories) - local_count
                }
            )

            return True

        except Exception as e:
            self._add_log_entry(f"❌ Local check error: {str(e)}", "#ff4757")
            return False

    def check_updates(self) -> bool:
        user = self.app_state.get('current_user')
        repositories = self.app_state.get('repositories', [])

        if not user or not repositories:
            self._add_log_entry("❌ No data to check updates", "#ff4757")
            return False

        try:
            user_structure = self.structure_service.get_user_structure(user)

            if not user_structure or "repositories" not in user_structure:
                self._add_log_entry("❌ User structure not found", "#ff4757")
                return False

            repos_path = user_structure["repositories"]

            User = type('User', (), {})
            user_obj = User()
            user_obj.username = user

            batch_start = time.time()

            all_update_status = self.sync_service.batch_check_repositories_need_update(
                user_obj,
                repositories
            )

            batch_time = time.time() - batch_start

            needs_update_count = 0

            for repo in repositories:
                if not repo.ssh_url:
                    continue

                repo_path = repos_path / repo.name

                if not repo_path.exists() or not (repo_path / '.git').exists():
                    repo.need_update = True
                    needs_update_count += 1
                    continue

                needs_update, message = all_update_status.get(
                    repo.name,
                    (True, "Not checked in batch")
                )

                repo.need_update = needs_update

                if needs_update:
                    needs_update_count += 1

            self.app_state.set('needs_update_count', needs_update_count)
            self._add_log_entry(f"✅ Updates needed: {needs_update_count}/{len(repositories)}", "#4caf50")

            self.app_state.log_result(
                True,
                f"Update check completed in {batch_time:.2f}s",
                {
                    "needs_update": needs_update_count,
                    "total": len(repositories),
                    "check_time_seconds": batch_time
                }
            )

            return True

        except Exception as e:
            print(f"[ERROR] Update check failed: {e}")
            import traceback
            traceback.print_exc()
            self._add_log_entry(f"❌ Update check error: {str(e)}", "#ff4757")
            return False

    def _add_log_entry(self, message: str, color: str = None):
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")

        if color:
            html = f'<span style="color: {color};">[{timestamp}] {message}</span>'
        else:
            html = f'[{timestamp}] {message}'

        self.log_text.append(html)

        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _finish_checkup(self, success: bool, message: str):
        if success:
            self.progress_bar.setValue(100)
            self.progress_label.setText("100%")
            self.step_label.setText("✅ Initialization complete")
            self._add_log_entry(f"\n🎉 {message}", "#4caf50")

            self.cancel_button.setText("Continue")
            self.cancel_button.clicked.disconnect()

            self.cancel_button.clicked.connect(self._on_continue_clicked)

            self.retry_button.hide()
        else:
            self.step_label.setText("❌ Initialization failed")
            self._add_log_entry(f"\n❌ {message}", "#ff4757")
            self.retry_button.show()
            self.cancel_button.setText("Exit")

        self.app_state.update(is_checking=False)

    def _on_continue_clicked(self):
        self.cancel_button.setEnabled(False)
        self.cancel_button.setText("Preparing...")

        self.step_label.setText("Starting main application...")
        self._add_log_entry("Loading main window...", "#4dabf7")

        QTimer.singleShot(500, self._emit_success_signal)

    def _emit_success_signal(self):
        self.setup_complete.emit(True, "Checkup completed successfully")

    def cancel_checkup(self):
        sys.exit(1)

    def restart_checkup(self):
        self.retry_button.hide()
        self.cancel_button.setEnabled(True)
        self.cancel_button.setText("Cancel")
        self.cancel_button.clicked.disconnect()
        self.cancel_button.clicked.connect(self.cancel_checkup)
        self.start()


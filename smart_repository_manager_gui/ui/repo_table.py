# Copyright (©) 2026, Alexander Suvorov. All rights reserved.
from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView,
    QProgressBar, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QComboBox, QLineEdit, QMenu
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QBrush, QColor

from smart_repository_manager_gui.ui.dark_theme import ModernDarkTheme


class OptimizedRepoTable(QWidget):
    row_double_clicked = pyqtSignal(object)
    load_more_requested = pyqtSignal()
    filter_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.repositories = []
        self.filtered_repositories = []
        self.displayed_repos = []
        self.current_batch = 0
        self.batch_size = 20
        self.is_loading = False

        self.current_filter = "all"
        self.search_text = ""

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        control_widget = QWidget()
        control_layout = QHBoxLayout(control_widget)
        control_layout.setContentsMargins(5, 5, 5, 5)
        control_layout.setSpacing(10)

        search_label = QLabel("Search:")
        search_label.setStyleSheet(f"color: {ModernDarkTheme.TEXT_SECONDARY}; font-size: 11px;")

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name, description...")
        self.search_input.setMinimumWidth(200)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {ModernDarkTheme.CARD_BG};
                border: 1px solid {ModernDarkTheme.BORDER_COLOR};
                border-radius: 4px;
                padding: 4px 8px;
                color: {ModernDarkTheme.TEXT_PRIMARY};
                font-size: 11px;
            }}
            QLineEdit:focus {{
                border: 1px solid {ModernDarkTheme.PRIMARY_COLOR};
            }}
        """)
        self.search_input.textChanged.connect(self.on_search_changed)

        filter_label = QLabel("Filter:")
        filter_label.setStyleSheet(f"color: {ModernDarkTheme.TEXT_SECONDARY}; font-size: 11px;")

        self.filter_combo = QComboBox()
        self.filter_combo.addItems([
            "All Repositories",
            "Local Only",
            "Remote Only",
            "Needs Update",
            "Private",
            "Public",
            "Forks",
            "Archived"
        ])
        self.filter_combo.setCurrentIndex(0)
        self.filter_combo.setMinimumWidth(120)
        self.filter_combo.currentTextChanged.connect(self.on_filter_changed)
        self.filter_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {ModernDarkTheme.CARD_BG};
                border: 1px solid {ModernDarkTheme.BORDER_COLOR};
                border-radius: 4px;
                padding: 4px 8px;
                color: {ModernDarkTheme.TEXT_PRIMARY};
                font-size: 11px;
                min-width: 120px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 1px solid {ModernDarkTheme.BORDER_COLOR};
                padding-left: 5px;
            }}
        """)

        control_layout.addWidget(search_label)
        control_layout.addWidget(self.search_input)
        control_layout.addWidget(filter_label)
        control_layout.addWidget(self.filter_combo)

        layout.addWidget(control_widget)

        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(6)
        self.table_widget.setHorizontalHeaderLabels([
            "#",
            "Name",
            "Last Update",
            "Actual",
            "Local",
            "Private"
        ])

        self.table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.table_widget.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.table_widget.setShowGrid(False)
        self.table_widget.setSortingEnabled(False)

        self.table_widget.setStyleSheet(f"""
            QTableWidget {{
                background-color: {ModernDarkTheme.ROW_EVEN};
                alternate-background-color: {ModernDarkTheme.ROW_ODD};
                font-size: 13px;
                border: none;
                outline: none;
            }}
            QHeaderView::section {{
                background-color: #252525;
                padding: 8px 4px;
                border: 1px solid {ModernDarkTheme.BORDER_COLOR};
                font-weight: bold;
                font-size: 12px;
            }}
            QTableWidget::item {{
                padding: 6px 4px;
                border-bottom: 1px solid {ModernDarkTheme.BORDER_COLOR};
            }}
            QTableWidget::item:selected {{
                background-color: {ModernDarkTheme.ROW_SELECTED};
                color: white;
            }}
        """)

        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        self.table_widget.doubleClicked.connect(self._on_row_double_clicked)

        self.table_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_widget.customContextMenuRequested.connect(self.show_context_menu)

        self.status_widget = QWidget()
        status_layout = QHBoxLayout(self.status_widget)
        status_layout.setContentsMargins(10, 5, 10, 5)

        self.loading_label = QLabel("")
        self.loading_label.setStyleSheet(f"color: {ModernDarkTheme.TEXT_SECONDARY}; font-size: 11px;")

        self.load_more_btn = QPushButton("Load more...")
        self.load_more_btn.setMinimumWidth(100)
        self.load_more_btn.clicked.connect(self.load_next_batch)
        self.load_more_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ModernDarkTheme.PRIMARY_COLOR};
                color: white;
                font-size: 11px;
                padding: 4px 8px;
                border: none;
                border-radius: 3px;
            }}
            QPushButton:hover {{
                background-color: #1a75ff;
            }}
        """)
        self.load_more_btn.setVisible(False)

        status_layout.addWidget(self.loading_label)
        status_layout.addStretch()
        status_layout.addWidget(self.load_more_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumHeight(4)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background-color: {ModernDarkTheme.BORDER_COLOR};
            }}
            QProgressBar::chunk {{
                background-color: {ModernDarkTheme.PRIMARY_COLOR};
            }}
        """)

        layout.addWidget(self.table_widget, 1)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_widget)

        self.scroll_timer = QTimer()
        self.scroll_timer.setSingleShot(True)
        self.scroll_timer.timeout.connect(self._check_scroll_position)

        scrollbar = self.table_widget.verticalScrollBar()
        scrollbar.valueChanged.connect(self._on_scroll)

    def set_repositories(self, repositories: list):
        self.repositories = repositories
        self.apply_filters()

    def apply_filters(self):
        if not self.repositories:
            self.filtered_repositories = []
        else:
            if self.search_text:
                search_lower = self.search_text.lower()
                filtered = []
                for repo in self.repositories:
                    if search_lower in repo.name.lower():
                        filtered.append(repo)
                        continue
                    if hasattr(repo, 'description') and repo.description and search_lower in repo.description.lower():
                        filtered.append(repo)
                        continue
                    if hasattr(repo, 'language') and repo.language and search_lower in repo.language.lower():
                        filtered.append(repo)
                        continue
            else:
                filtered = self.repositories.copy()

            filter_map = {
                "All Repositories": "all",
                "Local Only": "local",
                "Remote Only": "remote",
                "Needs Update": "needs_update",
                "Private": "private",
                "Public": "public",
                "Forks": "forks",
                "Archived": "archived"
            }

            filter_type = filter_map.get(self.filter_combo.currentText(), "all")
            self.current_filter = filter_type

            if filter_type == "all":
                self.filtered_repositories = filtered
            elif filter_type == "local":
                self.filtered_repositories = [r for r in filtered if getattr(r, 'local_exists', False)]
            elif filter_type == "remote":
                self.filtered_repositories = [r for r in filtered if not getattr(r, 'local_exists', False)]
            elif filter_type == "needs_update":
                self.filtered_repositories = [r for r in filtered if getattr(r, 'need_update', False)]
            elif filter_type == "private":
                self.filtered_repositories = [r for r in filtered if getattr(r, 'private', False)]
            elif filter_type == "public":
                self.filtered_repositories = [r for r in filtered if not getattr(r, 'private', False)]
            elif filter_type == "forks":
                self.filtered_repositories = [r for r in filtered if getattr(r, 'fork', False)]
            elif filter_type == "archived":
                self.filtered_repositories = [r for r in filtered if getattr(r, 'archived', False)]

        self.current_batch = 0
        self.displayed_repos = []
        self.table_widget.setRowCount(0)

        if self.filtered_repositories:
            self.update_status_label()
            self.load_next_batch()
        else:
            self.loading_label.setText(f"No repositories found")
            self.load_more_btn.setVisible(False)

        self.filter_changed.emit(self.current_filter)

    def on_search_changed(self, text: str):
        self.search_text = text.strip()
        self.apply_filters()

    def on_filter_changed(self, filter_text: str):
        self.apply_filters()

    def refresh_table(self):
        self.apply_filters()

    def load_next_batch(self):
        if self.is_loading or not self.filtered_repositories:
            return

        self.is_loading = True
        self.progress_bar.setVisible(True)
        self.load_more_btn.setEnabled(False)

        start_idx = self.current_batch * self.batch_size
        end_idx = start_idx + self.batch_size

        if start_idx >= len(self.filtered_repositories):
            self.is_loading = False
            self.progress_bar.setVisible(False)
            return

        batch_repos = self.filtered_repositories[start_idx:end_idx]

        self.displayed_repos.extend(batch_repos)

        QTimer.singleShot(10, lambda: self._update_table_batch(batch_repos, start_idx))

    def _update_table_batch(self, batch_repos, start_idx):
        try:
            current_rows = self.table_widget.rowCount()
            self.table_widget.setRowCount(current_rows + len(batch_repos))

            for i, repo in enumerate(batch_repos):
                row = current_rows + i

                num_item = QTableWidgetItem(str(start_idx + i + 1))
                num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                num_item.setForeground(QBrush(QColor("#6c757d")))
                self.table_widget.setItem(row, 0, num_item)

                name_item = QTableWidgetItem(repo.name[:50] if repo.name else "Unknown")
                self.table_widget.setItem(row, 1, name_item)

                last_update = getattr(repo, 'last_update', None) or getattr(repo, 'updated_at', None) or "Unknown"
                if isinstance(last_update, str) and len(last_update) > 10:
                    last_update = last_update[:10]
                update_item = QTableWidgetItem(str(last_update))
                update_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table_widget.setItem(row, 2, update_item)

                needs_update = getattr(repo, 'need_update', False)
                status_text = "⚠️" if needs_update else "✅"
                status_item = QTableWidgetItem(status_text)
                status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                if needs_update:
                    status_item.setForeground(QBrush(QColor("#ff9900")))
                    status_item.setToolTip("Update available" if repo.local_exists else "Not cloned locally")
                else:
                    status_item.setToolTip("Up to date")

                self.table_widget.setItem(row, 3, status_item)

                local_exists = getattr(repo, 'local_exists', False)
                local_text = "📁" if local_exists else "🌐"
                local_item = QTableWidgetItem(local_text)
                local_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                if not local_exists:
                    local_item.setForeground(QBrush(QColor("#f44336")))
                    local_item.setToolTip("Not cloned locally")
                else:
                    local_item.setToolTip("Local copy exists")

                self.table_widget.setItem(row, 4, local_item)

                is_private = getattr(repo, 'private', False)
                private_text = "🔒" if is_private else "🌍"
                private_item = QTableWidgetItem(private_text)
                private_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                private_item.setToolTip("Private repository" if is_private else "Public repository")
                self.table_widget.setItem(row, 5, private_item)

        except Exception as e:
            print(f"Error updating table batch: {e}")

        finally:
            self.current_batch += 1
            self.is_loading = False
            self.progress_bar.setVisible(False)
            self.load_more_btn.setEnabled(True)

            self.update_status_label()

            displayed_count = len(self.displayed_repos)
            total_count = len(self.filtered_repositories)

            if displayed_count >= total_count:
                self.load_more_btn.setVisible(False)
            else:
                self.load_more_btn.setText(f"Load more ({min(self.batch_size, total_count - displayed_count)})")
                self.load_more_btn.setVisible(True)

    def update_status_label(self):
        if not self.filtered_repositories:
            self.loading_label.setText("No repositories")
            return

        displayed_count = len(self.displayed_repos)
        total_count = len(self.filtered_repositories)

        local_count = sum(1 for r in self.filtered_repositories if getattr(r, 'local_exists', False))
        needs_update_count = sum(1 for r in self.filtered_repositories if getattr(r, 'need_update', False))

        filter_display = {
            "all": "All",
            "local": "Local",
            "remote": "Remote",
            "needs_update": "Needs Update",
            "private": "Private",
            "public": "Public",
            "forks": "Forks",
            "archived": "Archived"
        }.get(self.current_filter, "All")

        if displayed_count >= total_count:
            self.loading_label.setText(
                f"Showing all {displayed_count} {filter_display.lower()} repositories "
                f"({local_count} local, {needs_update_count} need update)"
            )
        else:
            self.loading_label.setText(
                f"Showing {displayed_count} of {total_count} {filter_display.lower()} repositories "
                f"({local_count} local, {needs_update_count} need update)"
            )

    def _on_scroll(self, value):
        self.scroll_timer.start(200)

    def _check_scroll_position(self):
        scrollbar = self.table_widget.verticalScrollBar()

        if (scrollbar.value() >= scrollbar.maximum() * 0.8 and
                not self.is_loading and
                len(self.displayed_repos) < len(self.filtered_repositories)):
            self.load_next_batch()

    def _on_row_double_clicked(self, index):
        row = index.row()
        if 0 <= row < len(self.displayed_repos):
            repo = self.displayed_repos[row]
            self.row_double_clicked.emit(repo)

    def show_context_menu(self, position):
        row = self.table_widget.rowAt(position.y())
        if row < 0 or row >= len(self.displayed_repos):
            return

        repo = self.displayed_repos[row]
        menu = QMenu()

        open_action = QAction("📂 Open in Browser", self)
        open_action.triggered.connect(lambda: self.open_in_browser(repo))
        menu.addAction(open_action)

        menu.exec(self.table_widget.viewport().mapToGlobal(position))

    def open_in_browser(self, repo):
        if hasattr(repo, 'html_url') and repo.html_url:
            import webbrowser
            webbrowser.open(repo.html_url)

    def clear(self):
        self.repositories = []
        self.filtered_repositories = []
        self.displayed_repos = []
        self.current_batch = 0
        self.table_widget.setRowCount(0)
        self.search_input.clear()
        self.filter_combo.setCurrentIndex(0)
        self.loading_label.setText("")
        self.load_more_btn.setVisible(False)

    def update_repository_status(self, repo_name: str, local_exists: bool, needs_update: bool):
        for repo_list in [self.repositories, self.filtered_repositories, self.displayed_repos]:
            for repo in repo_list:
                if repo.name == repo_name:
                    repo.local_exists = local_exists
                    repo.need_update = needs_update
                    break

        for row in range(self.table_widget.rowCount()):
            item = self.table_widget.item(row, 1)
            if item and item.text().startswith(repo_name[:50]):
                status_text = "⚠️" if needs_update else "✅"
                status_item = QTableWidgetItem(status_text)
                status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if needs_update:
                    status_item.setForeground(QBrush(QColor("#ff9900")))
                self.table_widget.setItem(row, 3, status_item)

                local_text = "📁" if local_exists else "🌐"
                local_item = QTableWidgetItem(local_text)
                local_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if not local_exists:
                    local_item.setForeground(QBrush(QColor("#f44336")))
                self.table_widget.setItem(row, 4, local_item)
                break

        self.apply_filters()

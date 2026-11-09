# Copyright (©) 2026, Alexander Suvorov. All rights reserved.
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from PyQt5.QtCore import QObject, pyqtSignal

from core.models.state import (
    AppState,
    CheckupResult,
)


class ApplicationState(QObject):
    state_changed = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self._data = AppState()
        self._results_log: List[CheckupResult] = []
        self.config_path = Path.home() / "smart_repository_manager" / "config.json"

    def _emit(self):
        self._data.last_update = datetime.now().isoformat()
        self._data.checkup_results = list(self._results_log)
        self.state_changed.emit(self._data)

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self._data, key):
                setattr(self._data, key, value)
        self._emit()
        return self

    def get(self, key: str, default: Any = None) -> Any:
        if hasattr(self._data, key):
            return getattr(self._data, key)
        return default

    def set(self, key: str, value: Any):
        if hasattr(self._data, key):
            setattr(self._data, key, value)
            self._emit()
        return self

    def set_multiple(self, **kwargs):
        return self.update(**kwargs)

    def log_result(self, success: bool, message: str, data: Dict[str, Any] = None):
        self._results_log.append(CheckupResult(
            timestamp=datetime.now().isoformat(),
            success=success,
            message=message,
            data=data or {},
        ))
        self._emit()
        return success

    def clear_results(self):
        self._results_log.clear()
        self._emit()

    def get_state_summary(self) -> Dict[str, Any]:
        successful = sum(1 for r in self._results_log if r.success)
        total = len(self._results_log)
        d = self._data
        return {
            'user': d.current_user,
            'repositories': {
                'total': d.repositories_count,
                'local': d.local_repositories_count,
                'needs_update': d.needs_update_count,
            },
            'ssh_status': d.ssh_status,
            'storage_mb': d.storage_size_mb,
            'checkup_success_rate': (successful / total * 100) if total > 0 else 0,
            'last_update': d.last_update,
        }

    @property
    def state(self) -> AppState:
        return self._data

    @property
    def data(self) -> AppState:
        return self._data

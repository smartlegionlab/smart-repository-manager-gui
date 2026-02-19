# Copyright (©) 2026, Alexander Suvorov. All rights reserved.
from PyQt6.QtCore import QObject, pyqtSignal
from typing import Dict, Any
from pathlib import Path
from datetime import datetime


class ApplicationState(QObject):
    state_changed = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self._state = {
            'current_user': None,
            'current_token': None,
            'repositories': [],
            'user_data': None,
            'ssh_status': 'unknown',
            'ssh_can_clone': False,
            'ssh_can_pull': False,
            'storage_path': None,
            'storage_size_mb': 0,
            'network_status': 'unknown',
            'checkup_results': [],
            'is_checking': False,
            'checkup_step': 0,
            'checkup_total_steps': 8,
            'checkup_message': '',
            'errors': [],
            'warnings': [],
            'repositories_count': 0,
            'local_repositories_count': 0,
            'needs_update_count': 0,
            'total_private': 0,
            'total_public': 0,
            'total_archived': 0,
            'total_forks': 0,
            'last_update': None,
            'external_ip': "127.0.0.1"
        }
        self._results_log = []
        self.config_path = Path.home() / "smart_repository_manager" / "config.json"

    def update(self, **kwargs):
        self._state.update(kwargs)
        self._state['last_update'] = datetime.now().isoformat()
        self.state_changed.emit(self._state)
        return self

    def get(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)

    def set(self, key: str, value: Any):
        self._state[key] = value
        self._state['last_update'] = datetime.now().isoformat()
        self.state_changed.emit(self._state)
        return self

    def set_multiple(self, **kwargs):
        self._state.update(kwargs)
        self._state['last_update'] = datetime.now().isoformat()
        self.state_changed.emit(self._state)
        return self

    def log_result(self, success: bool, message: str, data: Dict[str, Any] = None):
        result = {
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "message": message,
            "data": data or {}
        }
        self._results_log.append(result)
        self._state['checkup_results'] = self._results_log.copy()
        return success

    def clear_results(self):
        self._results_log.clear()
        self._state['checkup_results'] = []

    def get_state_summary(self) -> Dict[str, Any]:
        successful = sum(1 for r in self._results_log if r["success"])
        total = len(self._results_log)

        return {
            'user': self._state.get('current_user'),
            'repositories': {
                'total': self._state.get('repositories_count', 0),
                'local': self._state.get('local_repositories_count', 0),
                'needs_update': self._state.get('needs_update_count', 0)
            },
            'ssh_status': self._state.get('ssh_status'),
            'storage_mb': self._state.get('storage_size_mb', 0),
            'checkup_success_rate': (successful / total * 100) if total > 0 else 0,
            'last_update': self._state.get('last_update')
        }

    @property
    def state(self) -> Dict[str, Any]:
        return self._state.copy()

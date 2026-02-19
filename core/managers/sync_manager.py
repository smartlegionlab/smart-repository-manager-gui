# Copyright (©) 2026, Alexander Suvorov. All rights reserved.
import shutil
import subprocess
from typing import Dict, Any, List, Tuple, Optional

from smart_repository_manager_core.services.structure_service import StructureService
from smart_repository_manager_core.services.sync_service import SyncService
from smart_repository_manager_core.core.models.repository import Repository


class SyncManager:
    def __init__(self, app_state):
        self.app_state = app_state
        self.structure_service = StructureService()
        self.sync_service = SyncService()
        self.current_username: Optional[str] = None
        self.current_token: Optional[str] = None

    def set_user(self, username: str, token: str):
        self.current_username = username
        self.current_token = token

    def get_sync_stats(self) -> Dict[str, Any]:
        if not self.current_username:
            return {}

        repos = self.app_state.get('repositories', [])

        user_structure = self.structure_service.get_user_structure(self.current_username)
        local_count = 0
        needs_update_count = 0

        if user_structure and "repositories" in user_structure:
            repos_path = user_structure["repositories"]

            for repo in repos:
                repo_path = repos_path / repo.name

                if repo_path.exists() and (repo_path / '.git').exists():
                    repo.local_exists = True
                    local_count += 1
                    repo.need_update = False
                else:
                    repo.local_exists = False
                    repo.need_update = True

        return {
            'total': len(repos),
            'local': local_count,
            'needs_update': needs_update_count,
            'missing': len(repos) - local_count
        }

    def _create_user_object(self):
        if not self.current_username:
            return None
        return type('User', (), {'username': self.current_username})()

    def sync_single_repository(self, repo: Repository, operation: str = "sync") -> Tuple[bool, str, float]:
        if not self.current_username:
            return False, "User not set", 0.0

        user_obj = self._create_user_object()
        if not user_obj:
            return False, "User object creation failed", 0.0

        try:

            if operation == "clone" or not repo.local_exists:
                success, message, duration = self.sync_service.sync_single_repository(
                    user_obj,
                    repo,
                    "clone"
                )
            elif operation == "pull":
                success, message, duration = self.sync_service.sync_single_repository(
                    user_obj,
                    repo,
                    "pull"
                )
            else:
                success, message, duration = self.sync_service.sync_single_repository(
                    user_obj,
                    repo,
                    "sync"
                )

            if success:
                user_structure = self.structure_service.get_user_structure(self.current_username)
                if user_structure and "repositories" in user_structure:
                    repos_path = user_structure["repositories"]
                    repo_path = repos_path / repo.name

                    if repo_path.exists() and (repo_path / '.git').exists():
                        repo.local_exists = True

            return success, message, duration

        except Exception as e:
            return False, f"Error: {str(e)}", 0.0

    def sync_all_repositories(self, repos: List[Repository]) -> Dict[str, Any]:
        stats = {
            "synced": 0,
            "failed": 0,
            "skipped": 0,
            "durations": []
        }

        for i, repo in enumerate(repos, 1):
            if not hasattr(repo, 'ssh_url') or not repo.ssh_url:
                stats["skipped"] += 1
                continue

            if repo.local_exists:
                success, message, duration = self.sync_single_repository(repo, "pull")
            else:
                success, message, duration = self.sync_single_repository(repo, "clone")

            stats["durations"].append(duration)

            if success:
                if message == 'Already up to date':
                    stats["skipped"] += 1
                else:
                    stats["synced"] += 1
            else:
                stats["failed"] += 1

        return stats

    def update_needed_repositories(self, repos: List[Repository]) -> Dict[str, Any]:
        stats = {
            "updated": 0,
            "failed": 0,
            "durations": []
        }

        for i, repo in enumerate(repos, 1):
            if not hasattr(repo, 'local_exists') or not repo.local_exists:
                continue

            if not hasattr(repo, 'need_update') or not repo.need_update:
                continue

            success, message, duration = self.sync_single_repository(repo, "pull")
            stats["durations"].append(duration)

            if success:
                stats["updated"] += 1
            else:
                stats["failed"] += 1

        return stats

    def clone_missing_repositories(self, repos: List[Repository]) -> Dict[str, Any]:
        stats = {
            "cloned": 0,
            "failed": 0,
            "durations": []
        }

        for i, repo in enumerate(repos, 1):
            if not hasattr(repo, 'ssh_url') or not repo.ssh_url:
                continue

            if hasattr(repo, 'local_exists') and repo.local_exists:
                continue

            success, message, duration = self.sync_single_repository(repo, "clone")
            stats["durations"].append(duration)

            if success:
                stats["cloned"] += 1
            else:
                stats["failed"] += 1

        return stats

    def sync_with_repair(self, repos: List[Repository]) -> Dict[str, Any]:
        stats = {
            "synced": 0,
            "failed": 0,
            "skipped": 0,
            "durations": []
        }

        user_obj = self._create_user_object()
        if not user_obj:
            return stats

        for i, repo in enumerate(repos, 1):
            if not hasattr(repo, 'ssh_url') or not repo.ssh_url:
                stats["skipped"] += 1
                continue

            if hasattr(repo, 'local_exists') and repo.local_exists:
                user_structure = self.structure_service.get_user_structure(self.current_username)
                if user_structure and "repositories" in user_structure:
                    repos_path = user_structure["repositories"]
                    repo_path = repos_path / repo.name

                    if repo_path.exists():
                        if not (repo_path / '.git').exists():
                            try:
                                shutil.rmtree(repo_path, ignore_errors=True)
                                repo.local_exists = False
                            except:
                                pass
                        else:
                            try:
                                result = subprocess.run(
                                    ['git', '-C', str(repo_path), 'rev-parse', '--git-dir'],
                                    capture_output=True,
                                    text=True,
                                    timeout=5
                                )
                                if result.returncode != 0:
                                    shutil.rmtree(repo_path, ignore_errors=True)
                                    repo.local_exists = False
                            except:
                                shutil.rmtree(repo_path, ignore_errors=True)
                                repo.local_exists = False

            success, message, duration = self.sync_single_repository(repo, "sync")
            stats["durations"].append(duration)

            if success:
                if "repaired" in message.lower() or "re-cloned" in message.lower():
                    stats["synced"] += 1
                elif message == 'Already up to date':
                    stats["skipped"] += 1
                else:
                    stats["synced"] += 1
            else:
                stats["failed"] += 1

        return stats

    def reclone_all_repositories(self, repos: List[Repository]) -> Dict[str, Any]:
        stats = {
            "cloned": 0,
            "failed": 0,
            "durations": []
        }

        for i, repo in enumerate(repos, 1):
            if not hasattr(repo, 'ssh_url') or not repo.ssh_url:
                continue

            user_structure = self.structure_service.get_user_structure(self.current_username)
            if user_structure and "repositories" in user_structure:
                repos_path = user_structure["repositories"]
                repo_path = repos_path / repo.name

                if repo_path.exists():
                    try:
                        shutil.rmtree(repo_path, ignore_errors=True)
                    except:
                        pass

            success, message, duration = self.sync_single_repository(repo, "clone")
            stats["durations"].append(duration)

            if success:
                stats["cloned"] += 1
            else:
                stats["failed"] += 1

        return stats

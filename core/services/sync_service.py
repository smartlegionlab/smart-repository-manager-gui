# Copyright (©) 2026, Alexander Suvorov. All rights reserved.
import time
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Callable, Any, Tuple
from datetime import datetime

import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

from smart_repository_manager_core.core.git_status import GitStatusChecker
from smart_repository_manager_core.core.models.repository import Repository
from smart_repository_manager_core.core.models.user import User
from smart_repository_manager_core.services.structure_service import StructureService
from smart_repository_manager_core.utils.helpers import Helpers

from core.services.git_service import GitService


class SyncResult:

    def __init__(self):
        self.successful: int = 0
        self.failed: int = 0
        self.skipped: int = 0
        self.repaired: int = 0
        self.total: int = 0
        self.duration: float = 0.0
        self.start_time: Optional[str] = None
        self.end_time: Optional[str] = None
        self.failed_repos: Dict[str, str] = {}
        self.repaired_repos: Dict[str, str] = {}
        self.skipped_repos: Dict[str, str] = {}
        self.health_stats: Dict[str, int] = {
            "healthy": 0,
            "partially_broken": 0,
            "broken": 0,
            "not_exists": 0
        }

    def __str__(self) -> str:
        return (f"SyncResult(success={self.successful}, failed={self.failed}, "
                f"repaired={self.repaired}, duration={Helpers.format_duration(self.duration)})")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "successful": self.successful,
            "failed": self.failed,
            "skipped": self.skipped,
            "repaired": self.repaired,
            "total": self.total,
            "duration": self.duration,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "failed_repos": self.failed_repos,
            "repaired_repos": self.repaired_repos,
            "skipped_repos": self.skipped_repos,
            "health_stats": self.health_stats
        }


class SyncService:

    def __init__(self, token: Optional[str] = None, timeout: int = 30, max_retries: int = 3):
        self.token = token
        self.timeout = timeout
        self.max_retries = max_retries
        self.git_service = GitService(token=token, timeout=timeout)
        self.structure_service = StructureService()
        self._callbacks: Dict[str, List[Callable]] = {}

    def register_callback(self, event: str, callback: Callable) -> None:
        if event not in self._callbacks:
            self._callbacks[event] = []
        self._callbacks[event].append(callback)

    def _emit(self, event: str, *args, **kwargs) -> None:
        if event in self._callbacks:
            for callback in self._callbacks[event]:
                try:
                    callback(*args, **kwargs)
                except Exception as e:
                    print(e)
                    pass

    def sync_user_repositories(
            self,
            user: User,
            repositories: List[Repository],
            operation: str = "sync",
            auto_repair: bool = True,
            health_check: bool = True
    ) -> SyncResult:
        result = SyncResult()
        result.total = len(repositories)
        result.start_time = datetime.now().isoformat()

        self._emit("sync_started", user, result.total, operation)

        structure = self.structure_service.create_user_structure(user.username)
        if not structure:
            result.failed = result.total
            result.end_time = datetime.now().isoformat()
            self._emit("sync_finished", result)
            return result

        repos_path = structure["repositories"]
        start_time = time.time()

        health_results = {}
        if health_check:
            self._emit("health_check_started")
            for repo in repositories:
                health_status = self._check_repository_health(repo, repos_path)
                health_results[repo.name] = health_status
                result.health_stats[health_status["status"]] += 1
                self._emit("health_checked", repo.name, health_status["status"])
            self._emit("health_check_completed", result.health_stats)

        for i, repo in enumerate(repositories):
            clone_url = repo.clone_url or repo.html_url.replace("github.com", "github.com").rstrip('/') + '.git'

            if not clone_url:
                result.failed += 1
                result.failed_repos[repo.name] = "No clone URL"
                self._emit("repo_failed", repo, "No clone URL")
                continue

            self._emit("repo_started", repo, i, result.total)

            repo_path = repos_path / repo.name
            health_status = health_results.get(repo.name) if health_check else None

            operation_type = self._determine_smart_operation(
                repo, repo_path, operation, health_status
            )

            if operation_type == "skip":
                result.skipped += 1
                result.skipped_repos[repo.name] = "Already up to date"
                self._emit("repo_skipped", repo, "Already up to date")
                continue

            success, message, attempts = self._execute_with_retries(
                operation_type, clone_url, repo_path, repo.name, auto_repair
            )

            if success:
                if "repaired" in message.lower() or "re-cloned" in message.lower():
                    result.repaired += 1
                    result.repaired_repos[repo.name] = f"{message} (attempts: {attempts})"
                    self._emit("repo_repaired", repo, message, attempts)
                else:
                    result.successful += 1
                    self._emit("repo_completed", repo, success, message, attempts)
                repo.need_update = False
                repo.local_exists = True
            else:
                result.failed += 1
                result.failed_repos[repo.name] = f"{message} (attempts: {attempts})"
                self._emit("repo_failed", repo, message, attempts)

        result.duration = time.time() - start_time
        result.end_time = datetime.now().isoformat()

        self._emit("sync_finished", result)
        return result

    def _check_repository_health(self, repo: Repository, repos_path: Path) -> Dict[str, Any]:
        repo_path = repos_path / repo.name

        health_result = {
            "name": repo.name,
            "exists": repo_path.exists(),
            "is_git_repo": False,
            "health_checks": [],
            "status": "unknown",
            "needs_repair": False,
            "recommendations": []
        }

        if not repo_path.exists():
            health_result["status"] = "not_exists"
            health_result["needs_repair"] = True
            health_result["recommendations"].append("Repository does not exist - needs cloning")
            return health_result

        if not (repo_path / '.git').exists():
            health_result["status"] = "broken"
            health_result["needs_repair"] = True
            health_result["recommendations"].append("Not a git repository - needs re-cloning")
            return health_result

        health_result["is_git_repo"] = True

        checks = [
            ("git_dir", ["git", "-C", str(repo_path), "rev-parse", "--git-dir"]),
            ("git_log", ["git", "-C", str(repo_path), "log", "--oneline", "-1"]),
            ("git_remote", ["git", "-C", str(repo_path), "remote", "-v"]),
            ("git_status", ["git", "-C", str(repo_path), "status", "--porcelain"]),
        ]

        passed_checks = 0
        for check_name, command in checks:
            try:
                result = subprocess.run(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=5
                )

                check_result = {
                    "name": check_name,
                    "success": result.returncode == 0,
                    "output": result.stdout[:100] if result.returncode == 0 else result.stderr[:100]
                }
                health_result["health_checks"].append(check_result)

                if result.returncode == 0:
                    passed_checks += 1
                else:
                    if check_name == "git_dir":
                        health_result["recommendations"].append("Git directory corrupted")
                    elif check_name == "git_log":
                        health_result["recommendations"].append("Cannot read git history")
                    elif check_name == "git_remote":
                        health_result["recommendations"].append("Remote configuration missing")

            except Exception as e:
                health_result["health_checks"].append({
                    "name": check_name,
                    "success": False,
                    "output": str(e)
                })
                health_result["recommendations"].append(f"{check_name} check failed")

        if passed_checks == len(checks):
            health_result["status"] = "healthy"
        elif passed_checks >= len(checks) * 0.7:
            health_result["status"] = "partially_broken"
            health_result["needs_repair"] = True
            health_result["recommendations"].append("Partially broken - may need repair")
        else:
            health_result["status"] = "broken"
            health_result["needs_repair"] = True
            health_result["recommendations"].append("Broken - needs re-cloning")

        return health_result

    def _determine_smart_operation(
            self,
            repo: Repository,
            repo_path: Path,
            requested_operation: str,
            health_status: Optional[Dict[str, Any]] = None
    ) -> str:
        if requested_operation == "clone":
            return "clone"
        elif requested_operation == "update":
            return "pull"

        if health_status is None:
            health_status = self._check_repository_health(repo, repo_path.parent)

        if health_status["status"] in ["broken", "not_exists"]:
            return "clone"

        if health_status["status"] == "partially_broken":
            return "repair"

        if not repo_path.exists() or not (repo_path / '.git').exists():
            return "clone"

        if repo.pushed_at:
            needs_update = GitStatusChecker.needs_update(repo_path, repo.pushed_at)
            if needs_update:
                return "pull"

        return "skip"

    def _execute_with_retries(
            self,
            operation_type: str,
            clone_url: str,
            repo_path: Path,
            repo_name: str,
            auto_repair: bool
    ) -> Tuple[bool, str, int]:
        last_error = ""

        for attempt in range(1, self.max_retries + 1):
            self._emit("operation_attempt", repo_name, operation_type, attempt)

            try:
                if operation_type == "clone":
                    success, message = self._execute_clone(clone_url, repo_path)
                elif operation_type == "pull":
                    success, message = self._execute_pull(repo_path)
                elif operation_type == "repair":
                    success, message = self._execute_repair(clone_url, repo_path, repo_name)
                else:
                    return False, f"Unknown operation: {operation_type}", attempt

                if success:
                    return True, message, attempt

                last_error = message

                if auto_repair and operation_type != "repair":
                    self._emit("auto_repair_triggered", repo_name)
                    repair_success, repair_message = self._execute_repair(clone_url, repo_path, repo_name)
                    if repair_success:
                        return True, f"Auto-repaired: {repair_message}", attempt + 1
                    last_error = repair_message

                if attempt < self.max_retries:
                    wait_time = min(2 ** attempt, 10)
                    time.sleep(wait_time)

            except Exception as e:
                last_error = f"Exception: {str(e)}"
                if attempt < self.max_retries:
                    time.sleep(2)

        return False, f"Failed after {self.max_retries} attempts: {last_error}", self.max_retries

    def _execute_clone(self, clone_url: str, repo_path: Path) -> Tuple[bool, str]:
        result = self.git_service.clone_repository(clone_url, repo_path, self.token)

        if result.success:
            if self._verify_repository_health(repo_path):
                return True, "Cloned successfully"
            else:
                self._cleanup_repository(repo_path)
                return False, "Clone succeeded but repository is unhealthy"

        return False, result.error or "Clone failed"

    def _execute_pull(self, repo_path: Path) -> Tuple[bool, str]:
        if not self._verify_repository_health(repo_path):
            return False, "Repository is unhealthy, cannot pull"

        result = self.git_service.pull_repository(repo_path, self.token)

        if result.success:
            if self._verify_repository_health(repo_path):
                if "Already up to date" in (result.message or ""):
                    return True, "Already up to date"
                return True, "Updated successfully"
            else:
                return False, "Pull succeeded but repository became unhealthy"

        return False, result.error or "Pull failed"

    def _execute_repair(self, clone_url: str, repo_path: Path, repo_name: str) -> Tuple[bool, str]:
        self._emit("repair_started", repo_name)

        fix_success, fix_message = self._try_fix_repository(repo_path)
        if fix_success:
            self._emit("repair_fixed", repo_name, fix_message)
            return True, f"Fixed: {fix_message}"

        self._emit("repair_recloning", repo_name)

        self._cleanup_repository(repo_path)

        result = self.git_service.clone_repository(clone_url, repo_path, self.token)

        if result.success:
            if self._verify_repository_health(repo_path):
                self._emit("repair_success", repo_name, "Re-cloned successfully")
                return True, "Re-cloned successfully"
            else:
                self._cleanup_repository(repo_path)
                self._emit("repair_failed", repo_name, "Re-cloned but unhealthy")
                return False, "Re-cloned but repository is still unhealthy"

        self._emit("repair_failed", repo_name, result.error)
        return False, f"Re-clone failed: {result.error}"

    def _try_fix_repository(self, repo_path: Path) -> Tuple[bool, str]:
        if not repo_path.exists():
            return False, "Repository does not exist"

        if not (repo_path / '.git').exists():
            return False, "Not a git repository"

        try:
            git_dir = repo_path / '.git'
            if not git_dir.exists():
                result = subprocess.run(
                    ['git', '-C', str(repo_path), 'init'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=10
                )
                if result.returncode != 0:
                    return False, "Failed to reinitialize git"

            subprocess.run(
                ['git', '-C', str(repo_path), 'fetch', '--all'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10
            )

            subprocess.run(
                ['git', '-C', str(repo_path), 'reset', '--hard', 'origin/HEAD'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10
            )

            if self._verify_repository_health(repo_path):
                return True, "Fixed with fetch and reset"
            else:
                return False, "Fix attempted but repository still unhealthy"

        except Exception as e:
            return False, f"Fix error: {str(e)}"

    def _verify_repository_health(self, repo_path: Path) -> bool:
        try:
            result1 = subprocess.run(
                ['git', '-C', str(repo_path), 'rev-parse', '--git-dir'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )

            result2 = subprocess.run(
                ['git', '-C', str(repo_path), 'log', '--oneline', '-1'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )

            return result1.returncode == 0 and result2.returncode == 0
        except Exception as e:
            print(e)
            return False

    def _cleanup_repository(self, repo_path: Path) -> bool:
        try:
            if repo_path.exists():
                shutil.rmtree(repo_path, ignore_errors=True)
            return True
        except Exception as e:
            print(e)
            return False

    def sync_single_repository(
            self,
            user: User,
            repo: Repository,
            operation: str = "sync",
            auto_repair: bool = True
    ) -> Tuple[bool, str, float]:
        clone_url = repo.clone_url or repo.html_url.replace("github.com", "github.com").rstrip('/') + '.git'

        if not clone_url:
            return False, "No clone URL", 0.0

        structure = self.structure_service.create_user_structure(user.username)
        if not structure:
            return False, "Failed to create directory structure", 0.0

        repos_path = structure["repositories"]
        repo_path = repos_path / repo.name

        operation_type = self._determine_smart_operation(repo, repo_path, operation)

        if operation_type == "skip":
            return True, "Already up to date", 0.0

        start_time = time.time()
        success, message, attempts = self._execute_with_retries(
            operation_type,
            clone_url,
            repo_path,
            repo.name,
            auto_repair
        )

        if success:
            repo.need_update = False
            repo.local_exists = True

        duration = time.time() - start_time

        return success, message, duration

    def check_repository_needs_update(
            self,
            user: User,
            repo: Repository
    ) -> Tuple[bool, str]:
        results = self._batch_check_needs_update_internal(user, [repo])
        return results.get(repo.name, (True, "Error checking"))

    def batch_check_repositories_need_update(
            self,
            user: User,
            repositories: List[Repository]
    ) -> Dict[str, Tuple[bool, str]]:
        return self._batch_check_needs_update_internal(user, repositories)

    def _batch_check_needs_update_internal(
            self,
            user: User,
            repositories: List[Repository]
    ) -> Dict[str, Tuple[bool, str]]:
        if not repositories:
            return {}

        structure = self.structure_service.get_user_structure(user.username)
        if "repositories" not in structure:
            return {repo.name: (True, "Directory structure not found") for repo in repositories}

        repos_path = structure["repositories"]
        results = {}

        repos_to_check = []
        for repo in repositories:
            repo_path = repos_path / repo.name

            clone_url = repo.clone_url or repo.html_url.replace("github.com", "github.com").rstrip('/') + '.git'
            if not clone_url:
                results[repo.name] = (False, "No clone URL")
                continue

            if not repo_path.exists() or not (repo_path / '.git').exists():
                results[repo.name] = (True, "Repository not found locally")
                continue

            if not repo.pushed_at:
                results[repo.name] = (False, "Unknown remote status")
                continue

            repos_to_check.append((repo, repo_path))

        if not repos_to_check:
            return results

        with ThreadPoolExecutor(max_workers=min(10, len(repos_to_check))) as executor:
            future_to_repo = {}

            for repo, repo_path in repos_to_check:
                future = executor.submit(
                    GitStatusChecker.needs_update,
                    repo_path,
                    repo.pushed_at
                )
                future_to_repo[future] = repo.name

            for future in concurrent.futures.as_completed(future_to_repo):
                repo_name = future_to_repo[future]
                try:
                    needs_update = future.result(timeout=30)

                    if needs_update:
                        results[repo_name] = (True, "Update needed")
                    else:
                        results[repo_name] = (False, "Up to date")

                except Exception as e:
                    results[repo_name] = (True, f"Check failed: {str(e)}")

        return results

    def get_repository_health(
            self,
            user: User,
            repo: Repository
    ) -> Dict[str, Any]:
        structure = self.structure_service.get_user_structure(user.username)
        if not structure or "repositories" not in structure:
            return {"error": "Directory structure not found"}

        return self._check_repository_health(repo, structure["repositories"])

    def batch_health_check(
            self,
            user: User,
            repositories: List[Repository]
    ) -> Dict[str, Any]:
        results = {}
        stats = {
            "total": len(repositories),
            "healthy": 0,
            "partially_broken": 0,
            "broken": 0,
            "not_exists": 0,
            "needs_repair": 0
        }

        structure = self.structure_service.get_user_structure(user.username)
        if not structure or "repositories" not in structure:
            return {"error": "Directory structure not found"}

        repos_path = structure["repositories"]

        for repo in repositories:
            health = self._check_repository_health(repo, repos_path)
            results[repo.name] = health
            stats[health["status"]] += 1

            if health["needs_repair"]:
                stats["needs_repair"] += 1

        results["_summary"] = stats
        return results

# Copyright (©) 2026, Alexander Suvorov. All rights reserved.
import os
import shutil
import subprocess
import signal
import time
import random
from pathlib import Path
from typing import Optional, Tuple

from smart_repository_manager_core.core.git_commands import GitCommandResult


class GitOperation:

    def __init__(self, timeout: int = 30, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self.process = None
        self.BASE_DELAY = 2
        self.MAX_DELAY = 60

    def _terminate_process(self) -> None:
        if self.process:
            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                self.process.wait(timeout=5)
            except Exception as e:
                print(e)
                try:
                    os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                except Exception as e:
                    print(e)
                    pass

    def _verify_repository_health(self, repo_path: Path) -> bool:
        try:
            result1 = subprocess.run(
                ['git', '-C', str(repo_path), 'rev-parse', '--git-dir'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )

            result2 = subprocess.run(
                ['git', '-C', str(repo_path), 'log', '--oneline', '-1'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )

            return result1.returncode == 0 and result2.returncode == 0
        except Exception as e:
            print(e)
            return False

    def _get_auth_url(self, clone_url: str, token: str) -> str:
        if not token:
            return clone_url
        return clone_url.replace('https://', f'https://oauth2:{token}@')

    def _execute_with_retry(self, func, *args, **kwargs) -> Tuple[bool, str]:
        last_error = ""

        for attempt in range(self.max_retries):
            try:
                result = func(*args, **kwargs)
                if result.success:
                    return True, result.message if hasattr(result, 'message') else "Success"
                last_error = result.error if hasattr(result, 'error') else "Unknown error"
            except Exception as e:
                last_error = str(e)

            if attempt < self.max_retries - 1:
                delay = min(self.BASE_DELAY * (2 ** attempt) + random.random(), self.MAX_DELAY)
                time.sleep(delay)

        return False, f"Failed after {self.max_retries} attempts: {last_error}"

    def cancel(self) -> None:
        if self.process:
            self._terminate_process()


class GitCloneOperation(GitOperation):

    def execute(self, clone_url: str, target_path: Path, token: Optional[str] = None) -> GitCommandResult:
        result = GitCommandResult()

        try:
            if target_path.exists():
                shutil.rmtree(target_path)

            target_path.parent.mkdir(parents=True, exist_ok=True)

            auth_url = self._get_auth_url(clone_url, token) if token else clone_url

            cmd = ['git', 'clone', auth_url, str(target_path)]

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                start_new_session=True
            )

            try:
                stdout, stderr = self.process.communicate(timeout=self.timeout)
                result.return_code = self.process.returncode
                result.output = stdout
                result.error = stderr
                result.success = self.process.returncode == 0

                if result.success:
                    self._fetch_all_branches(target_path)
                    result.success = self._verify_repository_health(target_path)

                    if not result.success:
                        shutil.rmtree(target_path, ignore_errors=True)
                    else:
                        result.message = "Repository cloned successfully"

            except subprocess.TimeoutExpired:
                self._terminate_process()
                result.timed_out = True
                result.error = f"Clone timeout after {self.timeout} seconds"
                result.success = False
                if target_path.exists():
                    shutil.rmtree(target_path, ignore_errors=True)

        except Exception as e:
            result.error = f"Clone error: {str(e)}"
            result.success = False
            if target_path.exists():
                shutil.rmtree(target_path, ignore_errors=True)

        finally:
            self.process = None

        return result

    def _fetch_all_branches(self, repo_path: Path) -> None:
        try:
            git_dir = repo_path / '.git'

            subprocess.run(
                ['git', '--git-dir', str(git_dir), 'fetch', '--all', '--tags'],
                check=False,
                timeout=60,
                capture_output=True
            )

            try:
                subprocess.run(
                    ['git', '--git-dir', str(git_dir), 'config',
                     '--add', 'remote.origin.fetch',
                     '+refs/pull/*/head:refs/heads/pull/*'],
                    check=False,
                    timeout=10,
                    capture_output=True
                )
                subprocess.run(
                    ['git', '--git-dir', str(git_dir), 'fetch', 'origin'],
                    check=False,
                    timeout=60,
                    capture_output=True
                )
            except:
                pass

        except Exception as e:
            print(f"Warning: Failed to fetch all branches: {e}")


class GitPullOperation(GitOperation):

    def execute(self, repo_path: Path, token: Optional[str] = None) -> GitCommandResult:
        result = GitCommandResult()

        try:
            if not repo_path.exists():
                result.error = "Repository path does not exist"
                return result

            if not (repo_path / '.git').exists():
                result.error = "Not a git repository"
                return result

            if token:
                self._update_remote_url_with_token(repo_path, token)

            fetch_result = self._fetch_repository(repo_path)
            if not fetch_result.success:
                return fetch_result

            branch_result = subprocess.run(
                ['git', '-C', str(repo_path), 'rev-parse', '--abbrev-ref', 'HEAD'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )

            branch = "main"
            if branch_result.returncode == 0:
                branch = branch_result.stdout.strip()

            cmd = ['git', '-C', str(repo_path), 'pull', 'origin', branch]

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                start_new_session=True
            )

            try:
                stdout, stderr = self.process.communicate(timeout=self.timeout)
                result.return_code = self.process.returncode
                result.output = stdout
                result.error = stderr
                result.success = self.process.returncode == 0

                if result.success:
                    result.success = self._verify_repository_health(repo_path)
                    if result.success:
                        if "Already up to date" in stdout:
                            result.message = "Already up to date"
                        else:
                            result.message = "Repository updated successfully"

            except subprocess.TimeoutExpired:
                self._terminate_process()
                result.timed_out = True
                result.error = f"Pull timeout after {self.timeout} seconds"
                result.success = False

        except Exception as e:
            result.error = f"Pull error: {str(e)}"
            result.success = False

        finally:
            self.process = None

        return result

    def _fetch_repository(self, repo_path: Path) -> GitCommandResult:
        result = GitCommandResult()

        try:
            cmd = ['git', '-C', str(repo_path), 'fetch', '--all', '--prune', '--tags']

            fetch_process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=self.timeout
            )

            result.return_code = fetch_process.returncode
            result.output = fetch_process.stdout
            result.error = fetch_process.stderr
            result.success = fetch_process.returncode == 0

            if not result.success:
                result.error = f"Fetch failed: {fetch_process.stderr}"

        except Exception as e:
            result.success = False
            result.error = f"Fetch error: {str(e)}"

        return result

    def _update_remote_url_with_token(self, repo_path: Path, token: str) -> bool:
        try:
            result = subprocess.run(
                ['git', '-C', str(repo_path), 'remote', 'get-url', 'origin'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                return False

            current_url = result.stdout.strip()

            if current_url.startswith('https://') and 'oauth2:' not in current_url:
                auth_url = current_url.replace('https://', f'https://oauth2:{token}@')

                subprocess.run(
                    ['git', '-C', str(repo_path), 'remote', 'set-url', 'origin', auth_url],
                    check=False,
                    timeout=5
                )
                return True

        except Exception as e:
            print(f"Warning: Failed to update remote URL: {e}")

        return False


class GitStatusOperation(GitOperation):

    def check_needs_update(self, repo_path: Path, remote_ref: str = "origin/main") -> Tuple[bool, str]:
        try:
            if not repo_path.exists() or not (repo_path / '.git').exists():
                return True, "Repository not found locally"

            fetch_result = subprocess.run(
                ['git', '-C', str(repo_path), 'fetch', 'origin'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10
            )

            local_result = subprocess.run(
                ['git', '-C', str(repo_path), 'rev-parse', 'HEAD'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )

            if local_result.returncode != 0:
                return True, "Failed to get local commit"

            local_hash = local_result.stdout.strip()

            remote_result = subprocess.run(
                ['git', '-C', str(repo_path), 'rev-parse', remote_ref],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )

            if remote_result.returncode != 0:
                return True, "Failed to get remote commit"

            remote_hash = remote_result.stdout.strip()

            if local_hash != remote_hash:
                return True, "Updates available"
            else:
                return False, "Up to date"

        except Exception as e:
            return True, f"Check failed: {str(e)}"

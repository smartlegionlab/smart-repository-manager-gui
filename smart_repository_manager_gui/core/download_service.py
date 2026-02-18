# Copyright (©) 2026, Alexander Suvorov. All rights reserved.
import zipfile
import subprocess
import multiprocessing
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from urllib.parse import urlparse

from smart_repository_manager_core.utils.helpers import Helpers


class DownloadService:

    def __init__(self):
        self.download_cache = {}
        self.repository = None
        try:
            self.cpu_count = multiprocessing.cpu_count()
            self.max_workers = max(1, self.cpu_count - 1)
        except:
            self.max_workers = 4

        print(f"🎯 DownloadService initialized with {self.max_workers} parallel workers (CPU cores: {self.cpu_count})")

    def _download_with_curl(self, url: str, file_path: Path, timeout: int = 30, verbose: bool = False) -> bool:
        try:
            if file_path.exists():
                file_path.unlink()

            file_path.parent.mkdir(parents=True, exist_ok=True)

            cmd = [
                'curl',
                '-L',
                '-o', str(file_path),
                '--connect-timeout', '30',
                '--max-time', str(timeout),
                '--retry', '3',
                '--retry-delay', '5',
            ]

            if not verbose:
                cmd.append('--silent')

            cmd.append(url)

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout + 10
            )

            if result.returncode == 0:
                if file_path.exists() and file_path.stat().st_size > 100:
                    with open(file_path, 'rb') as f:
                        header = f.read(4)
                        if header == b'PK\x03\x04':
                            return True
                        else:
                            if verbose:
                                print(f"⚠️ File is not a valid ZIP: {file_path.name}")
                            file_path.unlink()
                            return False
                else:
                    if verbose:
                        print(f"⚠️ Downloaded file is empty or missing")
                    return False
            else:
                if verbose:
                    print(f"⚠️ Download failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            if verbose:
                print(f"⏰ Download timeout")
            return False
        except Exception as e:
            if verbose:
                print(f"❌ Error downloading: {e}")
            if file_path.exists():
                file_path.unlink()
            return False

    def download_repository_zip(self,
                                repo_name: str,
                                repo_url: str,
                                branch: str = "main",
                                token: Optional[str] = None,
                                username: Optional[str] = None,
                                target_dir: Optional[Path] = None,
                                verbose: bool = False) -> Dict[str, Any]:
        try:
            parsed_url = urlparse(repo_url)
            path_parts = parsed_url.path.strip('/').split('/')

            if len(path_parts) < 2:
                return {
                    "success": False,
                    "error": f"Invalid repository URL: {repo_url}"
                }

            owner = path_parts[0]
            repo = path_parts[1]

            is_private = False
            if hasattr(self, 'repository') and self.repository and hasattr(self.repository, 'private'):
                is_private = self.repository.private

            if is_private and not token:
                return {
                    "success": False,
                    "error": "Token required for private repository"
                }

            full_repo_name = f"{owner}/{repo}"

            if token:
                url = f"https://{token}@github.com/{full_repo_name}/archive/refs/heads/{branch}.zip"
            else:
                url = f"https://github.com/{full_repo_name}/archive/refs/heads/{branch}.zip"

            if username:
                base_dir = Path.home() / "smart_repository_manager" / username / "downloads" / repo_name
            else:
                base_dir = Path.home() / "smart_repository_manager" / "downloads" / repo_name

            if target_dir:
                base_dir = Path(target_dir) / repo_name

            base_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            visibility = "private" if is_private else "public"
            filename = f"{branch}_{visibility}_{timestamp}.zip"
            filepath = base_dir / filename

            if verbose:
                print(f"🎯 URL: {url}")
                print(f"📁 Saving to: {filepath}")

            success = self._download_with_curl(url, filepath, verbose=verbose)

            if not success:
                if branch == "main":
                    if verbose:
                        print(f"⚠️ Trying master branch for: {repo_name}")

                    if token:
                        url = f"https://{token}@github.com/{full_repo_name}/archive/refs/heads/master.zip"
                    else:
                        url = f"https://github.com/{full_repo_name}/archive/refs/heads/master.zip"

                    success = self._download_with_curl(url, filepath, verbose=verbose)

                    if success:
                        branch = "master"

            if not success:
                return {
                    "success": False,
                    "error": f"Failed to download repository"
                }

            file_size = filepath.stat().st_size

            return {
                "success": True,
                "message": f"Repository downloaded successfully",
                "filepath": str(filepath),
                "filename": filename,
                "size_bytes": file_size,
                "size_formatted": Helpers.format_size(file_size),
                "branch": branch,
                "repository": repo_name,
                "owner": owner,
                "timestamp": timestamp,
                "is_private": is_private,
                "download_dir": str(base_dir)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Download failed: {str(e)}"
            }

    def _download_single_branch_task(self,
                                     branch_name: str,
                                     repo_name: str,
                                     repo_url: str,
                                     token: Optional[str],
                                     username: Optional[str],
                                     base_dir: Path,
                                     owner: str,
                                     repo: str,
                                     verbose: bool = False) -> Tuple[str, Dict[str, Any]]:
        try:
            full_repo_name = f"{owner}/{repo}"

            if token:
                url = f"https://{token}@github.com/{full_repo_name}/archive/refs/heads/{branch_name}.zip"
            else:
                url = f"https://github.com/{full_repo_name}/archive/refs/heads/{branch_name}.zip"

            branch_dir = base_dir / "branches"
            branch_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{branch_name}_{timestamp}.zip"
            filepath = branch_dir / filename

            success = self._download_with_curl(url, filepath, verbose=verbose)

            if not success:
                return branch_name, {
                    "success": False,
                    "error": f"Failed to download branch {branch_name}"
                }

            file_size = filepath.stat().st_size

            return branch_name, {
                "success": True,
                "filepath": str(filepath),
                "filename": filename,
                "size_bytes": file_size,
                "size_formatted": Helpers.format_size(file_size),
                "branch": branch_name
            }

        except Exception as e:
            return branch_name, {
                "success": False,
                "error": str(e)
            }

    def download_repository_with_all_branches(self,
                                              repo_name: str,
                                              repo_url: str,
                                              token: Optional[str] = None,
                                              username: Optional[str] = None,
                                              target_dir: Optional[Path] = None,
                                              max_workers: Optional[int] = None,
                                              verbose: bool = False) -> Dict[str, Any]:
        try:
            parsed_url = urlparse(repo_url)
            path_parts = parsed_url.path.strip('/').split('/')

            if len(path_parts) < 2:
                return {
                    "success": False,
                    "error": f"Invalid repository URL: {repo_url}"
                }

            owner = path_parts[0]
            repo = path_parts[1]

            is_private = False
            if hasattr(self, 'repository') and self.repository and hasattr(self.repository, 'private'):
                is_private = self.repository.private

            if is_private and not token:
                return {
                    "success": False,
                    "error": "Token required for private repository"
                }

            import requests

            branches_url = f"https://api.github.com/repos/{owner}/{repo}/branches"
            headers = {}
            if token:
                headers['Authorization'] = f'token {token}'

            response = requests.get(branches_url, headers=headers, timeout=10)

            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Failed to get branches: HTTP {response.status_code}"
                }

            branches_data = response.json()
            branches = [branch['name'] for branch in branches_data]

            if not branches:
                return {
                    "success": False,
                    "error": "No branches found"
                }

            if username:
                base_dir = Path.home() / "smart_repository_manager" / username / "downloads" / repo_name
            else:
                base_dir = Path.home() / "smart_repository_manager" / "downloads" / repo_name

            if target_dir:
                base_dir = Path(target_dir) / repo_name

            base_dir.mkdir(parents=True, exist_ok=True)

            workers = max_workers if max_workers else self.max_workers
            workers = min(workers, len(branches))

            if verbose:
                print(f"🚀 Starting parallel download of {len(branches)} branches using {workers} workers")

            results = []
            successful = 0
            failed = 0
            lock = threading.Lock()

            with ThreadPoolExecutor(max_workers=workers) as executor:
                future_to_branch = {}
                for branch_name in branches:
                    future = executor.submit(
                        self._download_single_branch_task,
                        branch_name,
                        repo_name,
                        repo_url,
                        token,
                        username,
                        base_dir,
                        owner,
                        repo,
                        verbose
                    )
                    future_to_branch[future] = branch_name

                for future in as_completed(future_to_branch):
                    branch_name, result = future.result()

                    with lock:
                        results.append({
                            'branch': branch_name,
                            'result': result
                        })

                        if result.get('success'):
                            successful += 1
                            if verbose:
                                print(f"✅ Downloaded branch: {branch_name}")
                        else:
                            failed += 1
                            if verbose:
                                print(f"❌ Failed branch: {branch_name} - {result.get('error', 'Unknown error')}")

            results.sort(key=lambda x: x['branch'])

            total_size = sum(
                r['result'].get('size_bytes', 0)
                for r in results
                if r['result'].get('success')
            )

            return {
                "success": successful > 0,
                "message": f"Downloaded {successful}/{len(branches)} branches using {workers} workers",
                "total_branches": len(branches),
                "successful": successful,
                "failed": failed,
                "results": results,
                "download_dir": str(base_dir),
                "is_private": is_private,
                "total_size_bytes": total_size,
                "total_size_formatted": Helpers.format_size(total_size),
                "workers_used": workers,
                "cpu_cores": self.cpu_count
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to download branches: {str(e)}"
            }

    def get_user_downloads_dir(self, username: str) -> Path:
        return Path.home() / "smart_repository_manager" / username / "downloads"

    def extract_zip_archive(self, zip_path: Path, extract_dir: Optional[Path] = None) -> Dict[str, Any]:
        try:
            if not zip_path.exists():
                return {
                    "success": False,
                    "error": f"ZIP file not found: {zip_path}"
                }

            if extract_dir:
                extract_path = extract_dir
            else:
                extract_path = zip_path.parent / zip_path.stem

            extract_path.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)

            extracted_count = 0
            total_size = 0

            for item in extract_path.rglob('*'):
                extracted_count += 1
                if item.is_file():
                    total_size += item.stat().st_size

            return {
                "success": True,
                "message": f"Extracted {extracted_count} items",
                "extract_path": str(extract_path),
                "extracted_count": extracted_count,
                "total_size_bytes": total_size,
                "total_size_formatted": Helpers.format_size(total_size)
            }

        except zipfile.BadZipFile:
            return {
                "success": False,
                "error": "Invalid or corrupted ZIP file"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Extraction failed: {str(e)}"
            }

    def list_downloaded_archives(self, username: Optional[str] = None) -> Dict[str, Any]:
        try:
            if username:
                downloads_dir = self.get_user_downloads_dir(username)
            else:
                downloads_dir = Path.home() / "smart_repository_manager" / "downloads"

            if not downloads_dir.exists():
                return {
                    "success": True,
                    "message": "No downloads directory",
                    "archives": [],
                    "total_size_bytes": 0,
                    "total_size_formatted": "0 B",
                    "count": 0
                }

            archives = []
            total_size = 0

            for zip_file in downloads_dir.rglob("*.zip"):
                if zip_file.is_file():
                    stat = zip_file.stat()
                    total_size += stat.st_size

                    rel_path = zip_file.relative_to(downloads_dir)

                    name_parts = zip_file.stem.split('_')

                    visibility = "private" if "private" in zip_file.stem else "public"

                    archives.append({
                        "filename": zip_file.name,
                        "path": str(zip_file),
                        "relative_path": str(rel_path),
                        "repository": rel_path.parts[0] if len(rel_path.parts) > 1 else "Unknown",
                        "size_bytes": stat.st_size,
                        "size_formatted": Helpers.format_size(stat.st_size),
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "branch": name_parts[0] if len(name_parts) > 0 else "Unknown",
                        "visibility": visibility,
                        "timestamp": name_parts[2] if len(name_parts) > 2 else "Unknown"
                    })

            archives.sort(key=lambda x: x['modified'], reverse=True)

            return {
                "success": True,
                "message": f"Found {len(archives)} archives",
                "archives": archives,
                "total_size_bytes": total_size,
                "total_size_formatted": Helpers.format_size(total_size),
                "count": len(archives),
                "directory": str(downloads_dir)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to list archives: {str(e)}"
            }

    def delete_archive(self, archive_path: Path) -> Dict[str, Any]:
        try:
            if not archive_path.exists():
                return {
                    "success": False,
                    "error": f"Archive not found: {archive_path}"
                }

            file_size = archive_path.stat().st_size
            archive_path.unlink()

            parent_dir = archive_path.parent
            if parent_dir.exists() and not any(parent_dir.iterdir()):
                parent_dir.rmdir()

            return {
                "success": True,
                "message": f"Deleted {archive_path.name}",
                "filename": archive_path.name,
                "size_bytes": file_size,
                "size_formatted": Helpers.format_size(file_size)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to delete archive: {str(e)}"
            }

    def cleanup_old_archives(self, username: str, days: int = 30) -> Dict[str, Any]:
        try:
            downloads_dir = self.get_user_downloads_dir(username)

            if not downloads_dir.exists():
                return {
                    "success": True,
                    "message": "No downloads directory",
                    "deleted_count": 0,
                    "freed_bytes": 0,
                    "freed_formatted": "0 B"
                }

            cutoff_time = datetime.now().timestamp() - (days * 24 * 3600)
            deleted_count = 0
            freed_bytes = 0
            deleted_files = []

            for zip_file in downloads_dir.rglob("*.zip"):
                if zip_file.stat().st_mtime < cutoff_time:
                    file_size = zip_file.stat().st_size
                    deleted_files.append(str(zip_file))
                    zip_file.unlink()
                    deleted_count += 1
                    freed_bytes += file_size

            for dir_path in sorted(downloads_dir.rglob("*"), key=lambda x: len(str(x)), reverse=True):
                if dir_path.is_dir() and not any(dir_path.iterdir()):
                    dir_path.rmdir()

            return {
                "success": True,
                "message": f"Cleaned {deleted_count} old archives",
                "deleted_count": deleted_count,
                "freed_bytes": freed_bytes,
                "freed_formatted": Helpers.format_size(freed_bytes),
                "deleted_files": deleted_files
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Cleanup failed: {str(e)}"
            }

    def get_repository_size_info(self, repo_name: str, repo_url: str,
                                 token: Optional[str] = None) -> Dict[str, Any]:
        try:
            parsed_url = urlparse(repo_url)
            path_parts = parsed_url.path.strip('/').split('/')

            if len(path_parts) < 2:
                return {
                    "success": False,
                    "error": f"Invalid repository URL: {repo_url}"
                }

            owner = path_parts[0]
            repo = path_parts[1]

            import requests

            api_url = f"https://api.github.com/repos/{owner}/{repo}"

            headers = {}
            if token:
                headers['Authorization'] = f'token {token}'

            response = requests.get(api_url, headers=headers, timeout=10)

            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Failed to get repo info: HTTP {response.status_code}"
                }

            data = response.json()

            branches_url = f"https://api.github.com/repos/{owner}/{repo}/branches"
            branches_response = requests.get(branches_url, headers=headers, timeout=10)
            branches_count = len(branches_response.json()) if branches_response.status_code == 200 else 1

            return {
                "success": True,
                "repository": repo_name,
                "owner": owner,
                "size_kb": data.get('size', 0),
                "size_mb": data.get('size', 0) / 1024,
                "size_formatted": Helpers.format_size(data.get('size', 0) * 1024),
                "private": data.get('private', False),
                "default_branch": data.get('default_branch', 'main'),
                "branches_count": branches_count,
                "html_url": data.get('html_url', '')
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get size info: {str(e)}"
            }

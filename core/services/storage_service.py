# Copyright (©) 2026, Alexander Suvorov. All rights reserved.
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from smart_repository_manager_core.services.archive_creator import ArchiveCreator
from smart_repository_manager_core.services.structure_service import StructureService
from smart_repository_manager_core.utils.helpers import Helpers


class StorageService:
    def __init__(self):
        self.structure_service = StructureService()
        self._cache = {}

    def get_storage_info(self, username: str) -> Dict[str, Any]:
        cache_key = f"storage_info_{username}_{datetime.now().strftime('%H')}"

        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            if not username:
                return {"error": "No user selected", "exists": False}

            structure = self.structure_service.get_user_structure(username)
            if not structure or "repositories" not in structure:
                return {"error": "Storage structure not found", "exists": False}

            repos_path = structure["repositories"]

            info = {
                "username": username,
                "path": str(repos_path),
                "exists": repos_path.exists(),
                "repo_count": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0,
                "folders": {},
                "last_updated": datetime.now().isoformat()
            }

            if repos_path.exists():
                try:
                    for folder_type, folder_path in structure.items():
                        if isinstance(folder_path, Path) and folder_path.exists():
                            size_bytes = self._get_folder_size(folder_path)
                            item_count = self._count_items(folder_path)

                            info["folders"][folder_type] = {
                                "path": str(folder_path),
                                "exists": True,
                                "size_bytes": size_bytes,
                                "size_mb": size_bytes / (1024 * 1024),
                                "item_count": item_count
                            }

                    repo_count = 0
                    total_repo_size = 0

                    if repos_path.exists():
                        for item in repos_path.iterdir():
                            if item.is_dir():
                                repo_count += 1
                                repo_size = self._get_folder_size(item)
                                total_repo_size += repo_size

                    info["repo_count"] = repo_count
                    info["total_size_bytes"] = total_repo_size
                    info["total_size_mb"] = total_repo_size / (1024 * 1024)

                    try:
                        disk_usage = shutil.disk_usage(repos_path)
                        info["disk_usage"] = {
                            "total_gb": disk_usage.total / (1024 ** 3),
                            "used_gb": disk_usage.used / (1024 ** 3),
                            "free_gb": disk_usage.free / (1024 ** 3),
                            "used_percent": (disk_usage.used / disk_usage.total) * 100
                        }
                    except Exception as e:
                        info["disk_usage"] = {"error": str(e)}

                except Exception as e:
                    info["error"] = str(e)

            self._cache[cache_key] = info
            return info

        except Exception as e:
            return {"error": f"Error getting storage info: {str(e)}", "exists": False}

    def delete_repository(self, username: str, repo_name: str) -> Dict[str, Any]:
        try:
            if not username or not repo_name:
                return {"success": False, "error": "Username or repository name not provided"}

            structure = self.structure_service.get_user_structure(username)
            if "repositories" not in structure:
                return {"success": False, "error": "Storage structure not found"}

            repos_path = structure["repositories"]
            repo_path = repos_path / repo_name

            if not repo_path.exists():
                return {"success": False, "error": f"Repository '{repo_name}' not found"}

            if (repo_path / '.git').exists() or any((repo_path / item).is_dir() for item in repo_path.iterdir()):
                shutil.rmtree(repo_path, ignore_errors=True)

                self._clear_cache(username)

                return {
                    "success": True,
                    "message": f"Repository '{repo_name}' deleted successfully",
                    "repo_name": repo_name,
                    "path": str(repo_path)
                }
            else:
                return {"success": False, "error": f"'{repo_name}' doesn't appear to be a repository"}

        except Exception as e:
            return {"success": False, "error": f"Error deleting repository: {str(e)}"}

    def delete_all_repositories(self, username: str) -> Dict[str, Any]:
        try:
            if not username:
                return {"success": False, "error": "Username not provided"}

            structure = self.structure_service.get_user_structure(username)
            if "repositories" not in structure:
                return {"success": False, "error": "Storage structure not found"}

            repos_path = structure["repositories"]

            if not repos_path.exists():
                return {"success": False, "error": "No repositories directory found"}

            deleted_count = 0
            failed_count = 0
            deleted_repos = []

            for item in repos_path.iterdir():
                if item.is_dir():
                    repo_name = item.name
                    try:
                        shutil.rmtree(item, ignore_errors=True)
                        deleted_count += 1
                        deleted_repos.append(repo_name)
                    except Exception as e:
                        print(f"Error deleting {repo_name}: {e}")
                        failed_count += 1

            self._clear_cache(username)

            return {
                "success": True,
                "message": f"Deleted {deleted_count} repositories, failed: {failed_count}",
                "deleted_count": deleted_count,
                "failed_count": failed_count,
                "deleted_repos": deleted_repos
            }

        except Exception as e:
            return {"success": False, "error": f"Error deleting repositories: {str(e)}"}

    def cleanup_archives(self, username: str) -> Dict[str, Any]:
        try:
            if not username:
                return {"success": False, "error": "Username not provided"}

            structure = self.structure_service.get_user_structure(username)
            if "archives" not in structure:
                return {"success": False, "error": "Archives directory not found in structure"}

            archives_path = structure["archives"]

            if not archives_path.exists():
                return {"success": False, "error": "Archives directory doesn't exist"}

            deleted_count = 0
            total_size = 0
            deleted_files = []

            for item in archives_path.iterdir():
                try:
                    if item.is_file():
                        file_size = item.stat().st_size
                        item.unlink()
                        deleted_count += 1
                        total_size += file_size
                        deleted_files.append(item.name)
                    elif item.is_dir():
                        dir_size = self._get_folder_size(item)
                        shutil.rmtree(item, ignore_errors=True)
                        deleted_count += 1
                        total_size += dir_size
                        deleted_files.append(item.name)
                except Exception as e:
                    print(f"Error deleting {item}: {e}")
                    continue

            self._clear_cache(username)

            return {
                "success": True,
                "message": f"Cleaned {deleted_count} archive items ({Helpers.format_size(total_size)})",
                "deleted_count": deleted_count,
                "total_size_bytes": total_size,
                "total_size_formatted": Helpers.format_size(total_size),
                "deleted_files": deleted_files
            }

        except Exception as e:
            return {"success": False, "error": f"Error cleaning archives: {str(e)}"}

    def cleanup_logs(self, username: str) -> Dict[str, Any]:
        try:
            if not username:
                return {"success": False, "error": "Username not provided"}

            structure = self.structure_service.get_user_structure(username)
            if "logs" not in structure:
                return {"success": False, "error": "Logs directory not found in structure"}

            logs_path = structure["logs"]

            if not logs_path.exists():
                return {"success": False, "error": "Logs directory doesn't exist"}

            deleted_count = 0
            total_size = 0
            deleted_files = []

            for item in logs_path.iterdir():
                try:
                    if item.is_file():
                        file_size = item.stat().st_size
                        item.unlink()
                        deleted_count += 1
                        total_size += file_size
                        deleted_files.append(item.name)
                    elif item.is_dir():
                        dir_size = self._get_folder_size(item)
                        shutil.rmtree(item, ignore_errors=True)
                        deleted_count += 1
                        total_size += dir_size
                        deleted_files.append(item.name)
                except Exception as e:
                    print(f"Error deleting {item}: {e}")
                    continue

            self._clear_cache(username)

            return {
                "success": True,
                "message": f"Cleaned {deleted_count} log items ({Helpers.format_size(total_size)})",
                "deleted_count": deleted_count,
                "total_size_bytes": total_size,
                "total_size_formatted": Helpers.format_size(total_size),
                "deleted_files": deleted_files
            }

        except Exception as e:
            return {"success": False, "error": f"Error cleaning logs: {str(e)}"}

    def cleanup_downloads(self, username: str) -> Dict[str, Any]:
        try:
            if not username:
                return {"success": False, "error": "Username not provided"}

            structure = self.structure_service.get_user_structure(username)
            if "downloads" not in structure:
                return {"success": False, "error": "Downloads directory not found in structure"}

            downloads_path = structure["downloads"]

            if not downloads_path.exists():
                return {"success": False, "error": "Downloads directory doesn't exist"}

            deleted_count = 0
            total_size = 0
            deleted_files = []

            for item in downloads_path.iterdir():
                try:
                    if item.is_file():
                        file_size = item.stat().st_size
                        item.unlink()
                        deleted_count += 1
                        total_size += file_size
                        deleted_files.append(item.name)
                    elif item.is_dir():
                        dir_size = self._get_folder_size(item)
                        shutil.rmtree(item, ignore_errors=True)
                        deleted_count += 1
                        total_size += dir_size
                        deleted_files.append(item.name)
                except Exception as e:
                    print(f"Error deleting {item}: {e}")
                    continue

            self._clear_cache(username)

            return {
                "success": True,
                "message": f"Cleaned {deleted_count} download items ({Helpers.format_size(total_size)})",
                "deleted_count": deleted_count,
                "total_size_bytes": total_size,
                "total_size_formatted": Helpers.format_size(total_size),
                "deleted_files": deleted_files
            }

        except Exception as e:
            return {"success": False, "error": f"Error cleaning downloads: {str(e)}"}

    def cleanup_backups(self, username: str) -> Dict[str, Any]:
        try:
            if not username:
                return {"success": False, "error": "Username not provided"}

            structure = self.structure_service.get_user_structure(username)
            if "backups" not in structure:
                return {"success": False, "error": "Backups directory not found in structure"}

            backups_path = structure["backups"]

            if not backups_path.exists():
                return {"success": False, "error": "Backups directory doesn't exist"}

            deleted_count = 0
            total_size = 0
            deleted_files = []

            for item in backups_path.iterdir():
                try:
                    if item.is_file():
                        file_size = item.stat().st_size
                        item.unlink()
                        deleted_count += 1
                        total_size += file_size
                        deleted_files.append(item.name)
                    elif item.is_dir():
                        dir_size = self._get_folder_size(item)
                        shutil.rmtree(item, ignore_errors=True)
                        deleted_count += 1
                        total_size += dir_size
                        deleted_files.append(item.name)
                except Exception as e:
                    print(f"Error deleting {item}: {e}")
                    continue

            self._clear_cache(username)

            return {
                "success": True,
                "message": f"Cleaned {deleted_count} backup items ({Helpers.format_size(total_size)})",
                "deleted_count": deleted_count,
                "total_size_bytes": total_size,
                "total_size_formatted": Helpers.format_size(total_size),
                "deleted_files": deleted_files
            }

        except Exception as e:
            return {"success": False, "error": f"Error cleaning backups: {str(e)}"}

    def cleanup_temp(self, username: str) -> Dict[str, Any]:
        try:
            if not username:
                return {"success": False, "error": "Username not provided"}

            structure = self.structure_service.get_user_structure(username)
            if "temp" not in structure:
                return {"success": False, "error": "Temp directory not found in structure"}

            temp_path = structure["temp"]

            if not temp_path.exists():
                return {"success": False, "error": "Temp directory doesn't exist"}

            deleted_count = 0
            total_size = 0
            deleted_files = []

            for item in temp_path.iterdir():
                try:
                    if item.is_file():
                        file_size = item.stat().st_size
                        item.unlink()
                        deleted_count += 1
                        total_size += file_size
                        deleted_files.append(item.name)
                    elif item.is_dir():
                        dir_size = self._get_folder_size(item)
                        shutil.rmtree(item, ignore_errors=True)
                        deleted_count += 1
                        total_size += dir_size
                        deleted_files.append(item.name)
                except Exception as e:
                    print(f"Error deleting {item}: {e}")
                    continue

            self._clear_cache(username)

            return {
                "success": True,
                "message": f"Cleaned {deleted_count} temp items ({Helpers.format_size(total_size)})",
                "deleted_count": deleted_count,
                "total_size_bytes": total_size,
                "total_size_formatted": Helpers.format_size(total_size),
                "deleted_files": deleted_files
            }

        except Exception as e:
            return {"success": False, "error": f"Error cleaning temp: {str(e)}"}

    def get_repository_details(self, username: str, repo_name: str) -> Dict[str, Any]:
        try:
            if not username or not repo_name:
                return {"error": "Username or repository name not provided"}

            structure = self.structure_service.get_user_structure(username)
            if "repositories" not in structure:
                return {"error": "Storage structure not found"}

            repos_path = structure["repositories"]
            repo_path = repos_path / repo_name

            if not repo_path.exists():
                return {"error": f"Repository '{repo_name}' not found locally"}

            info = {
                "repo_name": repo_name,
                "path": str(repo_path),
                "exists": True,
                "is_git_repo": (repo_path / '.git').exists(),
                "size_bytes": self._get_folder_size(repo_path),
                "created": self._get_creation_time(repo_path),
                "modified": self._get_modification_time(repo_path),
                "folder_count": 0,
                "file_count": 0,
                "git_info": {}
            }

            for root, dirs, files in Path(repo_path).walk():
                info["folder_count"] += len(dirs)
                info["file_count"] += len(files)

            if info["is_git_repo"]:
                try:
                    result = subprocess.run(
                        ['git', '-C', str(repo_path), 'branch', '--show-current'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        info["git_info"]["branch"] = result.stdout.strip()

                    result = subprocess.run(
                        ['git', '-C', str(repo_path), 'log', '-1', '--format=%H|%s|%an|%ad'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        parts = result.stdout.strip().split('|')
                        if len(parts) >= 4:
                            info["git_info"]["last_commit"] = {
                                "hash": parts[0][:8],
                                "message": parts[1],
                                "author": parts[2],
                                "date": parts[3]
                            }
                except Exception as e:
                    info["git_info"]["error"] = str(e)

            info["size_formatted"] = Helpers.format_size(info["size_bytes"])

            return info

        except Exception as e:
            return {"error": f"Error getting repository details: {str(e)}"}

    def _get_folder_size(self, path: Path) -> int:
        total_size = 0
        try:
            for file_path in path.rglob('*'):
                if file_path.is_file():
                    try:
                        total_size += file_path.stat().st_size
                    except (OSError, PermissionError):
                        continue
        except (OSError, PermissionError):
            pass
        return total_size

    def _count_items(self, path: Path) -> int:
        count = 0
        try:
            for _ in path.rglob('*'):
                count += 1
        except (OSError, PermissionError):
            pass
        return count

    def _get_creation_time(self, path: Path) -> Optional[str]:
        try:
            stat = path.stat()
            return datetime.fromtimestamp(stat.st_ctime).isoformat()
        except (OSError, PermissionError):
            return None

    def _get_modification_time(self, path: Path) -> Optional[str]:
        try:
            stat = path.stat()
            return datetime.fromtimestamp(stat.st_mtime).isoformat()
        except (OSError, PermissionError):
            return None

    def _clear_cache(self, username: str):
        keys_to_remove = [k for k in self._cache.keys() if k.startswith(f"storage_info_{username}")]
        for key in keys_to_remove:
            del self._cache[key]

    def create_user_archive(self, username: str) -> Dict[str, Any]:
        try:

            if not username:
                return {"success": False, "error": "Username not provided"}

            structure = self.structure_service.get_user_structure(username)
            if not structure:
                return {"success": False, "error": "User structure not found"}

            user_dir = structure["user"]
            if not user_dir.exists():
                return {"success": False, "error": "User directory does not exist"}

            backups_dir = user_dir.parent / username / "archives"
            backups_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_name = f"{username}_repositories_{timestamp}.zip"
            archive_path = backups_dir / archive_name

            repos_path = structure["repositories"]

            created_archive_path = ArchiveCreator.create_archive(
                folder_path=str(repos_path),
                archive_format='zip',
                archive_name=archive_name
            )

            created_archive = Path(created_archive_path)

            if created_archive.exists():
                created_archive.rename(archive_path)
                archive_size = archive_path.stat().st_size
            else:
                return {"success": False, "error": "Archive was not created"}

            return {
                "success": True,
                "message": "Backup created successfully",
                "archive_path": str(archive_path),
                "archive_name": archive_name,
                "archive_size_bytes": archive_size,
                "archive_size_formatted": Helpers.format_size(archive_size),
                "username": username,
                "timestamp": timestamp
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Error creating backup: {str(e)}",
                "username": username
            }

# Copyright (©) 2026, Alexander Suvorov. All rights reserved.
import os
import zipfile
import requests
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from urllib.parse import urlparse

from smart_repository_manager_core.utils.helpers import Helpers


class DownloadService:

    def __init__(self):
        self.download_cache = {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Smart-Repository-Manager/1.0',
            'Accept': 'application/vnd.github.v3+json'
        })
        self.repository = None

    def download_repository_zip(self,
                                repo_name: str,
                                repo_url: str,
                                branch: str = "main",
                                token: Optional[str] = None,
                                username: Optional[str] = None,
                                target_dir: Optional[Path] = None) -> Dict[str, Any]:
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

            archive_url = f"https://api.github.com/repos/{owner}/{repo}/zipball/{branch}"

            if username:
                base_dir = Path.home() / "smart_repository_manager" / username / "downloads" / repo_name
            else:
                base_dir = Path.home() / "smart_repository_manager" / "downloads" / repo_name

            base_dir.mkdir(parents=True, exist_ok=True)

            if target_dir:
                base_dir = Path(target_dir)
                base_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            visibility = "private" if is_private else "public"
            filename = f"{branch}_{visibility}_{timestamp}.zip"
            filepath = base_dir / filename

            headers = {}
            if token:
                headers['Authorization'] = f'token {token}'
                self.session.headers.update(headers)

            response = self.session.get(archive_url, stream=True, timeout=30, allow_redirects=True)

            if response.status_code == 401:
                return {
                    "success": False,
                    "error": "Invalid or expired token. Please check your GitHub token."
                }
            elif response.status_code == 403:
                if 'rate limit' in response.text.lower():
                    return {
                        "success": False,
                        "error": "Rate limit exceeded. Please wait before trying again."
                    }
                else:
                    return {
                        "success": False,
                        "error": "Insufficient permissions. Token may need 'repo' scope for private repos."
                    }
            elif response.status_code == 404:
                if branch == "main":
                    return self.download_repository_zip(repo_name, repo_url, "master", token, username, target_dir)
                else:
                    return {
                        "success": False,
                        "error": f"Branch '{branch}' not found. Make sure the branch exists and you have access."
                    }
            elif response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Failed to download: HTTP {response.status_code} - {response.reason}"
                }

            content_type = response.headers.get('content-type', '')
            if 'application/zip' not in content_type and 'application/octet-stream' not in content_type:
                content_sample = response.content[:200].decode('utf-8', errors='ignore')
                if '404' in content_sample or 'Not Found' in content_sample:
                    return {
                        "success": False,
                        "error": f"Branch '{branch}' not found or repository is empty"
                    }

            downloaded = 0

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

            if not filepath.exists():
                return {
                    "success": False,
                    "error": "Download failed: File not created"
                }

            file_size = filepath.stat().st_size

            if file_size == 0:
                filepath.unlink()
                return {
                    "success": False,
                    "error": "Download failed: Empty file"
                }

            is_valid_zip = False

            try:
                with zipfile.ZipFile(filepath, 'r') as zip_ref:
                    bad_file = zip_ref.testzip()
                    is_valid_zip = bad_file is None
            except zipfile.BadZipFile:
                is_valid_zip = False
            except Exception:
                is_valid_zip = False

            if not is_valid_zip:
                filepath.unlink()
                return {
                    "success": False,
                    "error": "Downloaded file is not a valid ZIP archive"
                }

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

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Download timeout. Please check your internet connection."
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": "Connection error. Please check your internet connection."
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Download failed: {str(e)}"
            }

    def download_repository_with_all_branches(self,
                                              repo_name: str,
                                              repo_url: str,
                                              token: Optional[str] = None,
                                              username: Optional[str] = None,
                                              target_dir: Optional[Path] = None) -> Dict[str, Any]:
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

            branches_url = f"https://api.github.com/repos/{owner}/{repo}/branches"

            headers = {}
            if token:
                headers['Authorization'] = f'token {token}'

            response = self.session.get(branches_url, headers=headers, timeout=10)

            if response.status_code == 401:
                return {
                    "success": False,
                    "error": "Invalid token for accessing branches"
                }
            elif response.status_code == 403:
                if 'rate limit' in response.text.lower():
                    return {
                        "success": False,
                        "error": "Rate limit exceeded. Please wait before trying again."
                    }
                else:
                    return {
                        "success": False,
                        "error": "Insufficient permissions to access branches"
                    }
            elif response.status_code == 404:
                return {
                    "success": False,
                    "error": "Repository not found or you don't have access"
                }
            elif response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Failed to get branches: HTTP {response.status_code}"
                }

            branches_data = response.json()

            if not branches_data:
                return {
                    "success": False,
                    "error": "No branches found"
                }

            branches = [branch['name'] for branch in branches_data]

            if username:
                base_dir = Path.home() / "smart_repository_manager" / username / "downloads" / repo_name
            else:
                base_dir = Path.home() / "smart_repository_manager" / "downloads" / repo_name

            base_dir.mkdir(parents=True, exist_ok=True)

            if target_dir:
                base_dir = Path(target_dir)
                base_dir.mkdir(parents=True, exist_ok=True)

            results = []
            successful = 0
            failed = 0

            for i, branch_name in enumerate(branches):
                result = self.download_repository_zip(
                    repo_name=repo_name,
                    repo_url=repo_url,
                    branch=branch_name,
                    token=token,
                    username=username,
                    target_dir=base_dir
                )

                results.append({
                    'branch': branch_name,
                    'result': result
                })

                if result.get('success'):
                    successful += 1
                else:
                    failed += 1

            return {
                "success": successful > 0,
                "message": f"Downloaded {successful} branches, failed: {failed}",
                "total_branches": len(branches),
                "successful": successful,
                "failed": failed,
                "results": results,
                "download_dir": str(base_dir),
                "is_private": is_private
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
                    total_size += stat.st_yize

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

            api_url = f"https://api.github.com/repos/{owner}/{repo}"

            headers = {}
            if token:
                headers['Authorization'] = f'token {token}'

            response = self.session.get(api_url, headers=headers, timeout=10)

            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Failed to get repo info: HTTP {response.status_code}"
                }

            data = response.json()

            branches_url = f"https://api.github.com/repos/{owner}/{repo}/branches"
            branches_response = self.session.get(branches_url, headers=headers, timeout=10)
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

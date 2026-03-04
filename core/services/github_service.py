# Copyright (©) 2026, Alexander Suvorov. All rights reserved.
import requests
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from smart_repository_manager_core.core.models.repository import Repository
from smart_repository_manager_core.core.models.token import GitHubToken
from smart_repository_manager_core.core.models.user import User
from smart_repository_manager_core.utils.helpers import Helpers
from smart_repository_manager_core.utils.validators import Validators


class GitHubService:
    BASE_URL = "https://api.github.com"

    def __init__(self, token: str):
        if not Validators.validate_token(token):
            raise ValueError("Invalid GitHub token")

        self.token = token
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def validate_token(self) -> Tuple[bool, Optional[User]]:
        try:
            response = requests.get(
                f"{self.BASE_URL}/user",
                headers=self.headers,
                timeout=10
            )

            if response.status_code == 200:
                user_data = response.json()
                username = user_data.get("login")

                if not username or not Validators.validate_username(username):
                    return False, None

                user = User(username=username, token=self.token)
                user.update_from_api(user_data)
                user.scopes = response.headers.get('X-OAuth-Scopes', '').split(', ')

                return True, user

            return False, None

        except Exception as e:
            print(e)
            return False, None

    def fetch_user_repositories(self) -> Tuple[bool, List[Repository]]:
        all_repos = []
        page = 1
        per_page = 100

        try:
            while True:
                url = f"{self.BASE_URL}/user/repos"
                params = {
                    "page": page,
                    "per_page": per_page,
                    "sort": "updated",
                    "affiliation": "owner,collaborator,organization_member",
                    "visibility": "all"
                }

                response = requests.get(
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=30
                )

                if response.status_code != 200:
                    break

                repos = response.json()
                if not repos:
                    break

                all_repos.extend(repos)

                link_header = response.headers.get('Link', '')
                if 'rel="next"' not in link_header:
                    break

                page += 1
                if page > 10:
                    break

            unique_repos = Helpers.deduplicate_list(all_repos, 'id')
            repositories = []

            for repo_data in unique_repos:
                try:
                    repo = Repository.from_dict(repo_data)

                    if not repo.clone_url and repo_data.get('clone_url'):
                        repo.clone_url = repo_data.get('clone_url')

                    repositories.append(repo)
                except Exception as e:
                    print(e)
                    continue

            return True, repositories

        except Exception as e:
            print(e)
            return False, []

    def get_token_info(self) -> GitHubToken:
        try:
            response = requests.get(
                f"{self.BASE_URL}/user",
                headers=self.headers,
                timeout=10
            )

            user_data = response.json()
            username = user_data.get("login", "")

            token = GitHubToken(
                token=self.token,
                username=username,
                created_at=datetime.now().isoformat(),
                scopes=response.headers.get('X-OAuth-Scopes')
            )

            token.update_rate_limits(response.headers)
            return token

        except Exception as e:
            print(e)
            return GitHubToken(
                token=self.token,
                username="",
                created_at=datetime.now().isoformat()
            )

    def check_rate_limits(self) -> Dict[str, int]:
        try:
            response = requests.get(
                f"{self.BASE_URL}/rate_limit",
                headers=self.headers,
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                resources = data.get("resources", {})
                core = resources.get("core", {})

                return {
                    "limit": core.get("limit", 60),
                    "remaining": core.get("remaining", 60),
                    "reset": core.get("reset", 0)
                }

            return {"limit": 60, "remaining": 60, "reset": 0}

        except Exception as e:
            print(e)
            return {"limit": 60, "remaining": 60, "reset": 0}

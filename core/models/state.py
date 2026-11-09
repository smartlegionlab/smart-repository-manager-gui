# Copyright (©) 2026, Alexander Suvorov. All rights reserved.
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any


@dataclass
class UserData:
    username: str = ""
    name: Optional[str] = None
    bio: Optional[str] = None
    public_repos: int = 0
    followers: int = 0
    following: int = 0
    created_date: Optional[str] = None
    html_url: Optional[str] = None
    location: Optional[str] = None
    company: Optional[str] = None
    avatar_url: Optional[str] = None


@dataclass
class TokenInfo:
    username: Optional[str] = None
    scopes: Optional[str] = None
    rate_limit: Optional[int] = None
    remaining: Optional[int] = None
    created_at: Optional[str] = None
    token: Optional[str] = None


@dataclass
class RateLimits:
    limit: Optional[int] = None
    remaining: Optional[int] = None
    used: int = 0
    reset: Optional[int] = None
    reset_time: Optional[str] = None


@dataclass
class CheckupResult:
    timestamp: str
    success: bool
    message: str
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AppState:
    current_user: Optional[str] = None
    current_token: Optional[str] = None
    repositories: list = field(default_factory=list)
    user_data: Optional[UserData] = None
    token_info: Optional[TokenInfo] = None
    rate_limits: Optional[RateLimits] = None

    ssh_status: str = "unknown"
    ssh_can_clone: bool = False
    ssh_can_pull: bool = False

    storage_path: Optional[str] = None
    storage_size_mb: float = 0.0

    network_status: str = "unknown"
    external_ip: str = "127.0.0.1"
    github_access: bool = False
    github_access_message: str = ""

    is_checking: bool = False
    checkup_step: int = 0
    checkup_total_steps: int = 8
    checkup_message: str = ""

    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    repositories_count: int = 0
    local_repositories_count: int = 0
    needs_update_count: int = 0
    total_private: int = 0
    total_public: int = 0
    total_archived: int = 0
    total_forks: int = 0

    last_update: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

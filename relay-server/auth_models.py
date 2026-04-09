#!/usr/bin/env python3
"""
用户认证和授权系统 - 数据模型

包含所有数据模型和枚举类型。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional

# ============================================================================
# 枚举类型
# ============================================================================


class AuthType(Enum):
    """认证类型"""

    TOKEN = "token"
    JWT = "jwt"
    OAUTH2 = "oauth2"


class UserRole(Enum):
    """用户角色"""

    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"


class Permission(Enum):
    """权限"""

    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    MANAGE_USERS = "manage_users"
    MANAGE_SESSIONS = "manage_sessions"


# ============================================================================
# 数据模型
# ============================================================================


@dataclass
class User:
    """用户模型"""

    user_id: str
    username: str
    email: Optional[str] = None
    password_hash: Optional[str] = None
    role: UserRole = UserRole.USER
    permissions: List[str] = field(default_factory=list)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    oauth_provider: Optional[str] = None
    oauth_id: Optional[str] = None
    totp_secret: Optional[str] = None
    totp_enabled: bool = False
    totp_backup_codes: Optional[List[str]] = None

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "role": self.role.value,
            "permissions": self.permissions,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "totp_enabled": self.totp_enabled,
        }


@dataclass
class TokenInfo:
    """令牌信息"""

    token: str
    token_type: str
    user_id: str
    username: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    scopes: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.scopes:
            self.scopes = ["read", "write"]

    def is_expired(self) -> bool:
        """检查令牌是否过期"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    def has_scope(self, scope: str) -> bool:
        """检查令牌是否具有指定权限"""
        return scope in self.scopes


@dataclass
class OAuth2Token:
    """OAuth2 令牌"""

    token_id: str
    user_id: str
    provider: str
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)

#!/usr/bin/env python3
"""
智桥认证系统

支持 Token 认证和简单的 JWT 认证
"""

import hashlib
import hmac
import secrets
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from logger import get_logger

# Import UserDatabase for token persistence
from user_auth import UserDatabase

from config import settings

# Import AuthType from auth_models to avoid duplication


@dataclass
class TokenInfo:
    """令牌信息"""

    token: str
    user_id: str
    username: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    scopes: List[str] = None

    def __post_init__(self):
        if self.scopes is None:
            self.scopes = ["read", "write"]

    def is_expired(self) -> bool:
        """检查令牌是否过期"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    def has_scope(self, scope: str) -> bool:
        """检查令牌是否具有指定权限"""
        return scope in self.scopes


class TokenAuth:
    """简单的 Token 认证"""

    def __init__(self, secret_key: Optional[str] = None):
        """
        初始化 Token 认证

        Args:
            secret_key: 用于签名 token 的密钥
        """
        self.logger = get_logger(__name__)
        self.secret_key = secret_key or settings.security.secret_key

        if not self.secret_key:
            # 如果没有提供密钥，生成一个随机密钥
            self.secret_key = secrets.token_hex(32)
            self.logger.warning(
                "No secret key provided, using auto-generated key. "
                "Set ZHINENG_BRIDGE_SECURITY_SECRET_KEY environment variable for production."
            )

        # 使用数据库存储令牌
        self.db = UserDatabase()
        self._tokens_lock = threading.Lock()

    def generate_token(
        self,
        user_id: str,
        username: str,
        expires_in_hours: int = 24,
        scopes: List[str] = None,
    ) -> str:
        """
        生成新的令牌

        Args:
            user_id: 用户 ID
            username: 用户名
            expires_in_hours: 过期时间（小时）
            scopes: 权限列表

        Returns:
            生成的令牌
        """
        if scopes is None:
            scopes = ["read", "write"]

        # 使用 HMAC-SHA256 生成令牌
        timestamp = str(int(time.time()))
        # 添加随机 nonce 使令牌不可预测
        nonce = secrets.token_hex(16)
        data = f"{user_id}:{username}:{timestamp}:{nonce}".encode()

        signature = hmac.new(self.secret_key.encode(), data, hashlib.sha256).hexdigest()

        token = f"{user_id}:{timestamp}:{nonce}:{signature}"

        # 存储令牌信息到数据库
        created_at = datetime.now()
        expires_at = created_at + timedelta(hours=expires_in_hours)
        session_id = str(secrets.token_hex(16))

        # 存储到数据库
        self.db.store_token(
            session_id=session_id,
            user_id=user_id,
            token=token,
            expires_at=expires_at,
        )

        self.logger.info(
            "Token generated and stored",
            user_id=user_id,
            username=username,
            expires_at=expires_at.isoformat(),
        )

        return token

    def validate_token(self, token: str) -> Optional[TokenInfo]:
        """
        验证令牌

        Args:
            token: 要验证的令牌

        Returns:
            TokenInfo 如果令牌有效，否则返回 None
        """
        if not token:
            self.logger.warning("Token validation failed: empty token")
            return None

        # 从数据库获取令牌信息
        token_data = self.db.get_token(token)

        if not token_data:
            self.logger.warning("Token validation failed: token not found in database")
            return None

        # 检查令牌是否过期
        if datetime.now() > token_data["expires_at"]:
            self.logger.warning(
                "Token validation failed: token expired",
                user_id=token_data["user_id"],
            )
            # 移除过期令牌
            self.db.revoke_token(token)
            return None

        # 验证签名
        try:
            # 新格式: user_id:timestamp:nonce:signature
            parts = token.split(":")
            if len(parts) != 4:
                self.logger.warning("Token validation failed: invalid token format")
                return None

            user_id, timestamp, nonce, signature = parts
            # 需要从数据库获取用户名，但 sessions 表没有存储 username
            # 我们需要从 users 表获取
            user = self.db.get_user(user_id=user_id)
            if not user:
                self.logger.warning("Token validation failed: user not found", user_id=user_id)
                return None

            data = f"{user_id}:{user.username}:{timestamp}:{nonce}".encode()

            expected_signature = hmac.new(
                self.secret_key.encode(), data, hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(signature, expected_signature):
                self.logger.warning(
                    "Token validation failed: invalid signature",
                    user_id=user_id,
                )
                return None

            self.logger.debug(
                "Token validated successfully",
                user_id=user_id,
                username=user.username,
            )

            # 构造 TokenInfo 对象
            return TokenInfo(
                token=token,
                user_id=user_id,
                username=user.username,
                created_at=token_data["created_at"],
                expires_at=token_data["expires_at"],
                scopes=["read", "write"],  # 默认权限
            )

        except (ValueError, AttributeError) as e:
            self.logger.error("Token validation failed: malformed token", error=str(e))
            return None

    def revoke_token(self, token: str) -> bool:
        """
        撤销令牌

        Args:
            token: 要撤销的令牌

        Returns:
            是否成功撤销
        """
        token_data = self.db.get_token(token)
        if token_data:
            deleted = self.db.revoke_token(token)
            if deleted:
                self.logger.info("Token revoked", user_id=token_data["user_id"])
            return deleted
        return False

    def revoke_all_user_tokens(self, user_id: str) -> int:
        """
        撤销用户的所有令牌

        Args:
            user_id: 用户 ID

        Returns:
            撤销的令牌数量
        """
        count = self.db.revoke_all_user_tokens(user_id)
        return count

    def get_active_tokens(self, user_id: Optional[str] = None) -> List[TokenInfo]:
        """
        获取活跃的令牌

        Args:
            user_id: 用户 ID（可选，如果提供则只返回该用户的令牌）

        Returns:
            令牌信息列表
        """
        if user_id:
            # 获取特定用户的令牌
            token_list = self.db.get_user_tokens(user_id)
            result = []
            for token_data in token_list:
                user = self.db.get_user(user_id=user_id)
                if user:
                    result.append(
                        TokenInfo(
                            token=token_data["token"],
                            user_id=user_id,
                            username=user.username,
                            created_at=token_data["created_at"],
                            expires_at=token_data["expires_at"],
                            scopes=["read", "write"],
                        )
                    )
            return result
        else:
            # 获取所有活跃令牌（需要查询数据库）
            self.logger.warning("Getting all active tokens is not supported with database storage")
            return []

    def cleanup_expired_tokens(self) -> int:
        """清理过期的令牌

        Returns:
            清理的令牌数量
        """
        count = self.db.cleanup_expired_tokens()
        return count


class WebSocketAuth:
    """WebSocket 认证"""

    def __init__(self, token_auth: TokenAuth):
        """
        初始化 WebSocket 认证

        Args:
            token_auth: Token 认证实例
        """
        self.logger = get_logger(__name__)
        self.token_auth = token_auth
        self.authenticated_connections: Dict[str, TokenInfo] = {}
        self._connections_lock = threading.Lock()

    def authenticate_connection(self, connection_id: str, token: str) -> Tuple[bool, str]:
        """
        认证 WebSocket 连接

        Args:
            connection_id: 连接 ID
            token: 认证令牌

        Returns:
            (是否成功, 错误消息)
        """
        # 如果认证未启用，直接通过
        if not settings.security.enable_auth:
            self.logger.debug("Authentication disabled, connection allowed")
            return True, ""

        # 验证令牌
        token_info = self.token_auth.validate_token(token)

        if not token_info:
            self.logger.warning(
                "WebSocket authentication failed",
                connection_id=connection_id,
            )
            return False, "Authentication failed: invalid or expired token"

        # 存储认证信息
        with self._connections_lock:
            self.authenticated_connections[connection_id] = token_info

        self.logger.info(
            "WebSocket connection authenticated",
            connection_id=connection_id,
            user_id=token_info.user_id,
            username=token_info.username,
        )

        return True, ""

    def disconnect(self, connection_id: str):
        """
        处理连接断开

        Args:
            connection_id: 连接 ID
        """
        with self._connections_lock:
            if connection_id in self.authenticated_connections:
                del self.authenticated_connections[connection_id]
                self.logger.debug(
                    "Connection removed from authenticated connections",
                    connection_id=connection_id,
                )

    def is_authenticated(self, connection_id: str) -> bool:
        """
        检查连接是否已认证

        Args:
            connection_id: 连接 ID

        Returns:
            是否已认证
        """
        # 如果认证未启用，所有连接都视为已认证
        if not settings.security.enable_auth:
            return True

        with self._connections_lock:
            return connection_id in self.authenticated_connections

    def get_user_info(self, connection_id: str) -> Optional[TokenInfo]:
        """
        获取连接的用户信息

        Args:
            connection_id: 连接 ID

        Returns:
            TokenInfo 如果已认证，否则返回 None
        """
        with self._connections_lock:
            return self.authenticated_connections.get(connection_id)

    def has_scope(self, connection_id: str, scope: str) -> bool:
        """
        检查连接是否具有指定权限

        Args:
            connection_id: 连接 ID
            scope: 权限名称

        Returns:
            是否具有权限
        """
        token_info = self.get_user_info(connection_id)
        if not token_info:
            return False

        return token_info.has_scope(scope)


# ============================================================================
# 全局认证实例（向后兼容）
# ============================================================================

# 向后兼容的全局实例
token_auth = TokenAuth()
ws_auth = WebSocketAuth(token_auth)


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    "TokenInfo",
    "TokenAuth",
    "WebSocketAuth",
    "token_auth",
    "ws_auth",
]

#!/usr/bin/env python3
"""
认证管理器模块

提供用户注册、登录、token验证等功能。
"""

import hashlib
import sqlite3
import threading
from typing import Optional, Dict, Tuple
from datetime import datetime, timedelta

from cachetools import TTLCache

from logger import get_logger
from auth_models import User, TokenInfo, UserRole
from auth_jwt import JWTAuth
from auth_db import UserDatabase
from auth_totp import TOTPManager

# ============================================================================
# 缓存配置
# ============================================================================

# Token验证缓存 (TTL: 1分钟, 最大5000条)
TOKEN_CACHE_TTL = 60
TOKEN_CACHE_MAXSIZE = 5000


class AuthenticationManager:
    """认证管理器"""

    # Token验证缓存 (TTL: 1分钟, 最大5000条)
    _token_cache: TTLCache = TTLCache(maxsize=TOKEN_CACHE_MAXSIZE, ttl=TOKEN_CACHE_TTL)
    _token_cache_lock = threading.Lock()

    @classmethod
    def invalidate_token_cache(cls, token: str = None):
        """
        使token缓存失效

        Args:
            token: JWT token（可选）
        """
        with cls._token_cache_lock:
            if token:
                key = hashlib.sha256(token.encode()).hexdigest()
                if key in cls._token_cache:
                    del cls._token_cache[key]

    def __init__(self, db_path: str = None):
        """
        初始化认证管理器

        Args:
            db_path: 数据库路径
        """
        self.logger = get_logger(__name__)
        self.db = UserDatabase(db_path)
        self.jwt_auth = JWTAuth()
        self.totp_manager = TOTPManager(self.db)
        self._sessions: Dict[str, TokenInfo] = {}
        self._sessions_lock = threading.Lock()

    def register_user(
        self,
        username: str,
        password: str,
        email: str = None,
    ) -> User:
        """
        注册新用户

        Args:
            username: 用户名
            password: 密码
            email: 邮箱

        Returns:
            创建的用户

        Raises:
            ValueError: 如果用户名或邮箱已存在
        """
        return self.db.create_user(
            username=username,
            password=password,
            email=email,
            role=UserRole.USER,
            permissions=["read", "write"],
        )

    def login_user(
        self,
        username: str,
        password: str,
    ) -> Tuple[str, TokenInfo]:
        """
        用户登录

        Args:
            username: 用户名
            password: 密码

        Returns:
            (token, token_info)

        Raises:
            AuthenticationError: 如果认证失败
        """
        user = self.db.verify_user(username, password)
        if not user:
            from exceptions import AuthenticationError
            raise AuthenticationError("Invalid username or password")

        # 生成 JWT token
        token = self.jwt_auth.generate_token(
            user_id=user.user_id,
            username=user.username,
            scopes=user.permissions,
        )

        token_info = TokenInfo(
            token=token,
            token_type="JWT",
            user_id=user.user_id,
            username=user.username,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=24),
            scopes=user.permissions,
        )

        # 存储会话
        with self._sessions_lock:
            self._sessions[token] = token_info

        self.logger.info("User logged in", user_id=user.user_id, username=username)
        return token, token_info

    def login_user_oauth(
        self,
        provider: str,
        oauth_id: str,
        email: str = None,
        username: str = None,
    ) -> Tuple[str, TokenInfo]:
        """
        OAuth2 用户登录

        Args:
            provider: OAuth2 提供商（github, google）
            oauth_id: OAuth2 用户 ID
            email: 用户邮箱（可选）
            username: 用户名（可选）

        Returns:
            (token, token_info)

        Raises:
            AuthenticationError: 如果认证失败
        """
        # 查找现有用户
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM users WHERE oauth_provider = ? AND oauth_id = ?",
                (provider, oauth_id)
            )
            row = cursor.fetchone()
        finally:
            if conn:
                conn.close()

        if row:
            # 用户已存在
            user = self.db._row_to_user(row)
        else:
            # 创建新用户
            if not username:
                username = f"{provider}_{oauth_id[:8]}"
            if not email:
                email = f"{username}@oauth.local"

            user = self.db.create_user(
                username=username,
                password=None,
                email=email,
                role=UserRole.USER,
                permissions=["read", "write"],
            )

            # 更新 OAuth 信息
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE users SET oauth_provider = ?, oauth_id = ? WHERE user_id = ?",
                    (provider, oauth_id, user.user_id)
                )
                conn.commit()

            user.oauth_provider = provider
            user.oauth_id = oauth_id

        # 生成 JWT token
        token = self.jwt_auth.generate_token(
            user_id=user.user_id,
            username=user.username,
            scopes=user.permissions,
        )

        token_info = TokenInfo(
            token=token,
            token_type="JWT",
            user_id=user.user_id,
            username=user.username,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=24),
            scopes=user.permissions,
        )

        # 存储会话
        with self._sessions_lock:
            self._sessions[token] = token_info

        self.logger.info(
            "User logged in via OAuth2",
            user_id=user.user_id,
            username=username,
            provider=provider,
        )
        return token, token_info

    def logout_user(self, token: str) -> bool:
        """
        用户登出（登出后使token缓存失效）

        Args:
            token: JWT token

        Returns:
            是否成功
        """
        with self._sessions_lock:
            if token in self._sessions:
                del self._sessions[token]
                self.logger.info("User logged out", token=token[:20] + "...")

                # 使token缓存失效
                self.invalidate_token_cache(token)
                return True
            return False

    def validate_token(self, token: str) -> Optional[TokenInfo]:
        """
        验证 token（带缓存，TTL 1分钟）

        Args:
            token: JWT token

        Returns:
            TokenInfo 如果有效，否则返回 None
        """
        # 使用token的hash作为缓存键（避免碰撞风险）
        cache_key = hashlib.sha256(token.encode()).hexdigest()

        # 尝试从缓存获取
        with self._token_cache_lock:
            if cache_key in self._token_cache:
                cached_result = self._token_cache[cache_key]
                if cached_result is None or cached_result.is_expired():
                    # 缓存的无效token或已过期
                    del self._token_cache[cache_key]
                else:
                    self.logger.debug("Token cache hit", cache_key=cache_key)
                    return cached_result

        # 验证 JWT 签名和过期
        payload = self.jwt_auth.validate_token(token)
        if not payload:
            # 缓存无效结果
            with self._token_cache_lock:
                self._token_cache[cache_key] = None
            return None

        # 检查会话是否存在
        with self._sessions_lock:
            if token in self._sessions:
                token_info = self._sessions[token]
            else:
                token_info = None

        # 内存中未找到会话时，尝试从数据库加载（处理服务器重启后的情况）
        if not token_info:
            user_id = payload.get("sub")
            username = payload.get("username", "")
            scopes = payload.get("scopes", ["read", "write"])
            exp = payload.get("exp")

            if user_id and exp:
                token_info = TokenInfo(
                    token=token,
                    token_type="JWT",
                    user_id=user_id,
                    username=username,
                    created_at=datetime.now(),
                    expires_at=datetime.fromtimestamp(exp),
                    scopes=scopes,
                )
                with self._sessions_lock:
                    self._sessions[token] = token_info

        if not token_info:
            self.logger.warning("Token not found in active sessions")
            return None

        # 检查是否过期
        if token_info.is_expired():
            with self._sessions_lock:
                self._sessions.pop(token, None)
            self.logger.warning("Token expired")
            return None

        # 写入缓存
        with self._token_cache_lock:
            self._token_cache[cache_key] = token_info

        return token_info

    def get_user_from_token(self, token: str) -> Optional[User]:
        """
        从 token 获取用户

        Args:
            token: JWT token

        Returns:
            用户对象或 None
        """
        payload = self.jwt_auth.validate_token(token)
        if not payload:
            return None

        return self.db.get_user(user_id=payload.get("sub"))

    def cleanup_expired_sessions(self) -> int:
        """
        清理过期的会话

        Returns:
            清理的会话数量
        """
        cleaned_count = 0

        with self._sessions_lock:
            # 找出所有过期的会话
            expired_tokens = [
                token for token, token_info in self._sessions.items()
                if token_info.is_expired()
            ]

            # 删除过期会话
            for token in expired_tokens:
                del self._sessions[token]
                cleaned_count += 1

        if cleaned_count > 0:
            self.logger.info("Expired sessions cleaned up", count=cleaned_count)

        return cleaned_count

    # ========================================================================
    # 密码重置
    # ========================================================================

    def request_password_reset(self, email: str) -> Optional[str]:
        """请求密码重置，返回重置令牌（由调用方发送邮件）"""
        target = self.db.get_user_by_email(email)
        if not target:
            self.logger.warning("Password reset requested for unknown email")
            return None
        token = self.db.create_password_reset_token(target.user_id, expires_in_hours=1)
        self.logger.info("Password reset token created", user_id=target.user_id)
        return token

    def confirm_password_reset(self, token: str, new_password: str) -> bool:
        """确认密码重置"""
        if len(new_password) < 8:
            raise ValueError("Password must be at least 8 characters")
        return self.db.reset_password(token, new_password)

    def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        """修改密码"""
        if len(new_password) < 8:
            raise ValueError("Password must be at least 8 characters")
        return self.db.change_password(user_id, current_password, new_password)

    # ========================================================================
    # 双因素认证 (TOTP)
    # ========================================================================

    def setup_2fa(self, user_id: str) -> dict:
        """初始化 2FA，返回 secret 和 QR 码信息"""
        return self.totp_manager.setup_2fa(user_id)

    def enable_2fa(self, user_id: str, code: str) -> bool:
        """验证并启用 2FA"""
        return self.totp_manager.verify_and_enable_2fa(user_id, code)

    def verify_2fa(self, user_id: str, code: str) -> bool:
        """验证 2FA 码"""
        return self.totp_manager.verify_2fa(user_id, code)

    def disable_2fa(self, user_id: str, code: str) -> bool:
        """禁用 2FA"""
        return self.totp_manager.disable_2fa(user_id, code)

    def regenerate_backup_codes(self, user_id: str, code: str) -> Optional[list]:
        """重新生成恢复码"""
        return self.totp_manager.regenerate_backup_codes(user_id, code)

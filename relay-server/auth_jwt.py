#!/usr/bin/env python3
"""
JWT 认证模块

提供 JWT 令牌的生成和验证功能，包括重放攻击防护。
"""

import base64
import hashlib
import hmac
import json
import secrets
import threading
import time
import uuid
from typing import Dict, List, Optional

from cachetools import TTLCache
from logger import get_logger

from config import settings

# ============================================================================
# 缓存配置
# ============================================================================

# Token 验证缓存 (TTL: 1分钟, 最大5000条)
TOKEN_CACHE_TTL = 60
TOKEN_CACHE_MAXSIZE = 5000


class JWTAuth:
    """JWT 认证"""

    # JWT 发行者标识
    ISSUER = "zhineng-bridge"

    # 时间容差（秒），用于防止时钟偏移问题
    TIME_LEEWAY = 30

    def __init__(self, secret_key: Optional[str] = None):
        """
        初始化 JWT 认证

        Args:
            secret_key: 用于签名的密钥
        """
        self.logger = get_logger(__name__)
        self.secret_key = secret_key or settings.security.secret_key

        if not self.secret_key:
            self.secret_key = secrets.token_hex(32)
            self.logger.warning(
                "No secret key provided, using auto-generated key. "
                "Set ZHINENG_BRIDGE_SECURITY_SECRET_KEY environment variable for production."
            )

        # 重放攻击防护: 已撤销的 token 记录
        # 格式: {jti: revoke_timestamp}
        self._revoked_tokens: Dict[str, float] = {}
        self._revoked_tokens_lock = threading.Lock()

        # Token 验证缓存 (TTL: 1分钟, 最大5000条)
        self._token_cache: TTLCache = TTLCache(maxsize=TOKEN_CACHE_MAXSIZE, ttl=TOKEN_CACHE_TTL)
        self._token_cache_lock = threading.Lock()

    def invalidate_token_cache(self, token: str = None):
        """
        使 token 缓存失效

        Args:
            token: JWT token
        """
        with self._token_cache_lock:
            if token and token in self._token_cache:
                del self._token_cache[token]

    def generate_token(
        self,
        user_id: str,
        username: str,
        expires_in_hours: int = 24,
        scopes: List[str] = None,
    ) -> str:
        """
        生成 JWT 令牌

        安全增强:
        - iss (issuer): 标识令牌发行者
        - nbf (not before): 令牌在此之前无效
        - jti (JWT ID): 唯一标识符，用于重放攻击防护

        Args:
            user_id: 用户 ID
            username: 用户名
            expires_in_hours: 过期时间（小时）
            scopes: 权限列表

        Returns:
            JWT 令牌
        """
        if scopes is None:
            scopes = ["read", "write"]

        header = {
            "alg": "HS256",
            "typ": "JWT",
        }

        now = int(time.time())
        # 生成唯一的 JWT ID 用于重放攻击防护
        jti = str(uuid.uuid4())

        payload = {
            "sub": user_id,  # Subject: 用户 ID
            "username": username,
            "iss": self.ISSUER,  # Issuer: 发行者
            "iat": now,  # Issued At: 签发时间
            "nbf": now,  # Not Before: 生效时间
            "exp": now + (expires_in_hours * 3600),  # Expiration: 过期时间
            "jti": jti,  # JWT ID: 唯一标识符
            "scopes": scopes,
        }

        # 编码 header
        header_b64 = self._base64url_encode(json.dumps(header))

        # 编码 payload
        payload_b64 = self._base64url_encode(json.dumps(payload))

        # 生成签名
        message = f"{header_b64}.{payload_b64}"
        signature = self._sign(message)

        token = f"{message}.{signature}"
        self.logger.debug(
            "JWT token generated", user_id=user_id, jti=jti, expires_in=expires_in_hours
        )
        return token

    def validate_token(self, token: str) -> Optional[dict]:
        """
        验证 JWT 令牌（带缓存，TTL 1分钟）

        安全验证包括:
        1. 签名验证
        2. 格式验证 (3部分)
        3. iss (issuer) 验证
        4. iat (issued at) 时间验证
        5. nbf (not before) 时间验证
        6. exp (expiration) 过期验证
        7. jti (JWT ID) 重放攻击检测

        注意：重放攻击防护（JTI 检查）每次都会执行，
        只有在 JTI 检查通过后才使用缓存的验证结果。

        Args:
            token: JWT 令牌

        Returns:
            payload 如果有效，否则返回 None
        """
        # 快速检查格式
        parts = token.split(".")
        if len(parts) != 3:
            self.logger.warning("JWT validation failed: invalid format")
            return None

        # 检查缓存
        with self._token_cache_lock:
            cached = self._token_cache.get(token)
            if cached is not None:
                # 缓存命中后仍需检查撤销
                jti = cached.get("jti")
                if jti:
                    with self._revoked_tokens_lock:
                        if jti in self._revoked_tokens:
                            del self._token_cache[token]
                            return None
                return cached

        header_b64, payload_b64, signature = parts

        # 1. 验证签名
        message = f"{header_b64}.{payload_b64}"
        expected_signature = self._sign(message)

        if not hmac.compare_digest(signature, expected_signature):
            self.logger.warning("JWT validation failed: invalid signature")
            return None

        # 解码 payload
        try:
            payload_str = self._base64url_decode(payload_b64)
            payload = json.loads(payload_str)
        except (ValueError, json.JSONDecodeError) as e:
            self.logger.error("JWT validation failed: invalid payload", error=str(e))
            return None

        now = int(time.time())

        # 2. 验证发行者 (iss) - 向后兼容，旧 token 可能没有
        issuer = payload.get("iss")
        if issuer and issuer != self.ISSUER:
            self.logger.warning(
                "JWT validation failed: invalid issuer",
                expected_issuer=self.ISSUER,
                actual_issuer=issuer,
            )
            return None

        # 3. 验证签发时间 (iat) - 防止时间戳伪造
        iat = payload.get("iat")
        if iat:
            if iat > now + self.TIME_LEEWAY:
                self.logger.warning(
                    "JWT validation failed: token issued in the future", iat=iat, now=now
                )
                return None

        # 4. 验证生效时间 (nbf) - 向后兼容，旧 token 可能没有
        nbf = payload.get("nbf")
        if nbf:
            if nbf > now + self.TIME_LEEWAY:
                self.logger.warning("JWT validation failed: token not yet valid", nbf=nbf, now=now)
                return None

        # 5. 验证过期时间 (exp)
        exp = payload.get("exp", 0)
        if exp < now - self.TIME_LEEWAY:
            self.logger.warning("JWT validation failed: token expired", exp=exp, now=now)
            return None

        # 6. 重放攻击防护 - 检查 JTI 是否已被撤销
        jti = payload.get("jti")
        if jti:
            with self._revoked_tokens_lock:
                if jti in self._revoked_tokens:
                    revoked_at = self._revoked_tokens[jti]
                    self.logger.warning(
                        "JWT validation failed: revoked token used", jti=jti, revoked_at=revoked_at
                    )
                    return None

            # 清理过期的撤销记录（超过 24 小时的记录）
            self._cleanup_expired_jti(int(time.time()))

        self.logger.debug("JWT validated successfully", user_id=payload.get("sub"), jti=jti)

        # 写入缓存
        with self._token_cache_lock:
            self._token_cache[token] = payload

        return payload

    def _cleanup_expired_jti(self, now: float) -> None:
        """
        清理过期的 JTI 记录

        Args:
            now: 当前时间戳
        """
        # 清理超过 24 小时的记录
        expiry_threshold = now - (24 * 3600)
        expired_jtis = [
            jti for jti, timestamp in self._revoked_tokens.items() if timestamp < expiry_threshold
        ]
        for jti in expired_jtis:
            del self._revoked_tokens[jti]

    def revoke_token_jti(self, jti: str) -> bool:
        """
        撤销特定的 JWT (通过 JTI)

        Args:
            jti: JWT ID

        Returns:
            是否成功撤销
        """
        with self._revoked_tokens_lock:
            self._revoked_tokens[jti] = time.time()
            self.logger.info("Token JTI revoked", jti=jti)
            return True

    def _base64url_encode(self, data: str) -> str:
        """Base64 URL 安全编码"""
        return base64.urlsafe_b64encode(data.encode()).decode().rstrip("=")

    def _base64url_decode(self, data: str) -> str:
        """Base64 URL 安全解码"""
        padding = "=" * (-len(data) % 4)
        return base64.urlsafe_b64decode(data + padding).decode()

    def _sign(self, message: str) -> str:
        """生成 HMAC-SHA256 签名"""
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()
        return signature

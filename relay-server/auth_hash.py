#!/usr/bin/env python3
"""
密码哈希器

使用 PBKDF2-HMAC-SHA256 进行安全的密码哈希。
"""

import hashlib
import hmac
import secrets

try:
    from config import settings

    PBKDF2_ITERATIONS = getattr(settings.security, "pbkdf2_iterations", 210000)
except Exception:
    PBKDF2_ITERATIONS = 210000


class PasswordHasher:
    """密码哈希器"""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        哈希密码

        Args:
            password: 明文密码

        Returns:
            哈希后的密码
        """
        salt = secrets.token_hex(16)
        hash_value = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            salt.encode(),
            PBKDF2_ITERATIONS,
        ).hex()
        return f"{salt}${hash_value}"

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        验证密码

        Args:
            password: 明文密码
            password_hash: 存储的哈希

        Returns:
            是否匹配
        """
        try:
            salt, hash_value = password_hash.split("$")
            computed_hash = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode(),
                salt.encode(),
                PBKDF2_ITERATIONS,
            ).hex()
            return hmac.compare_digest(hash_value, computed_hash)
        except (ValueError, AttributeError):
            return False

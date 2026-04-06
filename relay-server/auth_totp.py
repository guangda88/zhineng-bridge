#!/usr/bin/env python3
"""
TOTP 双因素认证模块

基于 RFC 6238 的 TOTP (Time-based One-Time Password) 实现。
兼容 Google Authenticator、Authy 等验证器应用。
"""

import hashlib
import hmac
import secrets
import struct
import time
import base64
from typing import Optional, Tuple
from io import BytesIO

try:
    import qrcode
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False

from logger import get_logger


class TOTPAuth:
    """TOTP 双因素认证"""

    DIGITS = 6
    PERIOD = 30
    ALGORITHM = "SHA1"

    def __init__(self, issuer: str = "zhineng-bridge"):
        self.issuer = issuer
        self.logger = get_logger(__name__)

    @staticmethod
    def generate_secret() -> str:
        """生成 Base32 编码的随机密钥（20 bytes = 32 chars base32）"""
        return base64.b32encode(secrets.token_bytes(20)).decode("ascii")

    @staticmethod
    def generate_backup_codes(count: int = 10) -> list[str]:
        """生成一次性恢复码"""
        return [secrets.token_hex(4).upper() for _ in range(count)]

    def generate_totp(
        self,
        secret: str,
        timestamp: Optional[int] = None,
        digits: int = DIGITS,
        period: int = PERIOD,
    ) -> str:
        """根据密钥和时间生成 TOTP 码"""
        if timestamp is None:
            timestamp = int(time.time())

        counter = timestamp // period
        key = base64.b32decode(secret, casefold=True)
        msg = struct.pack(">Q", counter)
        mac = hmac.new(key, msg, hashlib.sha1).digest()
        offset = mac[-1] & 0x0F
        code = struct.unpack(">I", mac[offset:offset + 4])[0] & 0x7FFFFFFF
        return str(code % (10 ** digits)).zfill(digits)

    def verify_totp(
        self,
        secret: str,
        code: str,
        window: int = 1,
    ) -> bool:
        """
        验证 TOTP 码，允许前后 window 个时间步长的偏移。

        Args:
            secret: Base32 编码的密钥
            code: 用户输入的 TOTP 码
            window: 允许的时间窗口偏移（默认 ±1 个周期）

        Returns:
            是否验证通过
        """
        now = int(time.time())
        for offset in range(-window, window + 1):
            expected = self.generate_totp(secret, timestamp=now + offset * self.PERIOD)
            if hmac.compare_digest(code, expected):
                return True
        return False

    def get_provisioning_uri(
        self,
        secret: str,
        username: str,
        issuer: Optional[str] = None,
    ) -> str:
        """生成 otpauth:// URI，供验证器应用扫描"""
        import urllib.parse
        issuer = issuer or self.issuer
        label = urllib.parse.quote(f"{issuer}:{username}")
        params = urllib.parse.urlencode({
            "secret": secret,
            "issuer": issuer,
            "algorithm": self.ALGORITHM,
            "digits": self.DIGITS,
            "period": self.PERIOD,
        })
        return f"otpauth://totp/{label}?{params}"

    def get_qr_code_data_uri(
        self,
        secret: str,
        username: str,
        issuer: Optional[str] = None,
    ) -> Optional[str]:
        """生成 QR code 的 data URI（用于嵌入 HTML）"""
        if not HAS_QRCODE:
            self.logger.warning("qrcode library not installed, cannot generate QR code")
            return None

        uri = self.get_provisioning_uri(secret, username, issuer)
        img = qrcode.make(uri)
        buf = BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        return f"data:image/png;base64,{b64}"


class TOTPManager:
    """TOTP 管理器 — 管理 2FA 的完整生命周期"""

    def __init__(self, db):
        """
        Args:
            db: UserDatabase 实例
        """
        self.db = db
        self.totp = TOTPAuth()
        self.logger = get_logger(__name__)
        self._used_codes: dict[str, float] = {}
        self._used_codes_lock = __import__("threading").Lock()

    def setup_2fa(self, user_id: str) -> dict:
        """
        为用户初始化 2FA，返回密钥和恢复码（尚未启用）。

        前端流程:
        1. 调用此接口获取 secret + backup_codes + provisioning_uri
        2. 用户用验证器扫描 QR 码
        3. 用户输入 TOTP 码调用 verify_and_enable_2fa 完成激活
        """
        secret = TOTPAuth.generate_secret()
        backup_codes = TOTPAuth.generate_backup_codes()

        self.db.update_user(user_id, totp_secret=secret, totp_backup_codes=backup_codes)

        user = self.db.get_user(user_id=user_id)
        if not user:
            raise ValueError("User not found")

        provisioning_uri = self.totp.get_provisioning_uri(secret, user.username)
        qr_data_uri = self.totp.get_qr_code_data_uri(secret, user.username)

        return {
            "secret": secret,
            "backup_codes": backup_codes,
            "provisioning_uri": provisioning_uri,
            "qr_code_data_uri": qr_data_uri,
        }

    def verify_and_enable_2fa(self, user_id: str, code: str) -> bool:
        """验证 TOTP 码并正式启用 2FA"""
        user = self.db.get_user(user_id=user_id)
        if not user or not user.totp_secret:
            return False

        if self.totp.verify_totp(user.totp_secret, code):
            self.db.update_user(user_id, totp_enabled=True)
            self.logger.info("2FA enabled", user_id=user_id)
            return True
        return False

    def verify_2fa(self, user_id: str, code: str) -> bool:
        """验证 2FA 码（登录时调用）"""
        user = self.db.get_user(user_id=user_id)
        if not user or not user.totp_enabled:
            return False

        # 检查是否已使用过（防重放）
        code_key = f"{user_id}:{code}"
        with self._used_codes_lock:
            if code_key in self._used_codes:
                return False

        # 验证 TOTP
        if self.totp.verify_totp(user.totp_secret, code):
            with self._used_codes_lock:
                self._used_codes[code_key] = time.time()
            self._cleanup_used_codes()
            return True

        # 尝试恢复码
        if user.totp_backup_codes and code.upper() in user.totp_backup_codes:
            self.db._consume_backup_code(user_id, code.upper())
            self.logger.info("2FA backup code used", user_id=user_id)
            return True

        return False

    def disable_2fa(self, user_id: str, code: str) -> bool:
        """禁用 2FA（需验证当前码或恢复码）"""
        if not self.verify_2fa(user_id, code):
            return False
        self.db.update_user(
            user_id,
            totp_enabled=False,
            totp_secret=None,
            totp_backup_codes=None,
        )
        self.logger.info("2FA disabled", user_id=user_id)
        return True

    def regenerate_backup_codes(self, user_id: str, code: str) -> Optional[list[str]]:
        """重新生成恢复码（需验证当前 TOTP）"""
        if not self.verify_2fa(user_id, code):
            return None
        new_codes = TOTPAuth.generate_backup_codes()
        self.db.update_user(user_id, totp_backup_codes=new_codes)
        return new_codes

    def is_2fa_enabled(self, user_id: str) -> bool:
        user = self.db.get_user(user_id=user_id)
        return bool(user and user.totp_enabled)

    def _cleanup_used_codes(self):
        now = time.time()
        with self._used_codes_lock:
            expired = [k for k, t in self._used_codes.items() if now - t > 120]
            for k in expired:
                del self._used_codes[k]


__all__ = ["TOTPAuth", "TOTPManager"]

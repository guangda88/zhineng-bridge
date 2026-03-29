#!/usr/bin/env python3
"""
zhineng-bridge CSRF Protection

Provides Cross-Site Request Forgery protection for WebSocket connections.
"""

import secrets
import time
import hashlib
import hmac
from typing import Optional, Dict, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from logger import get_logger
from config import settings


# CSRF Token configuration
CSRF_TOKEN_LENGTH = 32  # bytes
CSRF_TOKEN_TTL = 3600  # 1 hour in seconds
CSRF_NONCE_LENGTH = 16  # bytes


@dataclass
class CSRFToken:
    """CSRF Token data structure"""

    token: str
    nonce: str
    created_at: float
    user_id: Optional[str] = None
    session_id: Optional[str] = None

    def is_expired(self, ttl: int = CSRF_TOKEN_TTL) -> bool:
        """Check if token is expired

        Args:
            ttl: Time-to-live in seconds

        Returns:
            True if token is expired
        """
        return (time.time() - self.created_at) > ttl

    def to_dict(self) -> dict:
        """Convert to dictionary

        Returns:
            Token information dict
        """
        return {
            "token": self.token,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "created_at": datetime.fromtimestamp(self.created_at).isoformat(),
            "expires_at": datetime.fromtimestamp(self.created_at + CSRF_TOKEN_TTL).isoformat(),
        }


class CSRFProtection:
    """CSRF Protection Manager

    Generates and validates CSRF tokens for WebSocket connections.
    Uses HMAC-SHA256 for token signing and verification.
    """

    def __init__(self, secret_key: Optional[str] = None):
        """Initialize CSRF protection

        Args:
            secret_key: Secret key for HMAC signing (defaults to settings)
        """
        self.logger = get_logger(__name__)
        self.secret_key = secret_key or settings.security.secret_key

        if not self.secret_key:
            self.secret_key = secrets.token_hex(32)
            self.logger.warning(
                "No CSRF secret key provided, using auto-generated key. "
                "Set ZHINENG_BRIDGE_SECURITY_SECRET_KEY for production."
            )

        # Store active tokens (in production, use Redis or similar)
        self._tokens: Dict[str, CSRFToken] = {}
        self._user_tokens: Dict[str, str] = {}  # user_id -> token mapping

        self.logger.info(
            "CSRF protection initialized",
            token_ttl=CSRF_TOKEN_TTL,
            token_length=CSRF_TOKEN_LENGTH
        )

    def generate_token(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> str:
        """Generate a new CSRF token

        Args:
            user_id: Optional user ID for token binding
            session_id: Optional session ID for token binding

        Returns:
            CSRF token string
        """
        # Generate nonce for uniqueness
        nonce = secrets.token_hex(CSRF_NONCE_LENGTH)

        # Create token data
        timestamp = time.time()
        token_data = f"{nonce}:{timestamp}:{user_id or ''}:{session_id or ''}"

        # Sign with HMAC
        signature = hmac.new(
            self.secret_key.encode(),
            token_data.encode(),
            hashlib.sha256
        ).hexdigest()

        # Combine nonce and signature
        csrf_token = f"{nonce}:{signature}"

        # Store token
        csrf_obj = CSRFToken(
            token=csrf_token,
            nonce=nonce,
            created_at=timestamp,
            user_id=user_id,
            session_id=session_id,
        )

        self._tokens[nonce] = csrf_obj

        # Link to user if provided
        if user_id:
            self._user_tokens[user_id] = csrf_token

        self.logger.debug(
            "CSRF token generated",
            user_id=user_id,
            session_id=session_id,
            nonce=nonce[:8] + "..."  # Log partial nonce for debugging
        )

        return csrf_token

    def _check_token_format(self, token: str) -> Tuple[Optional[Tuple[str, str]], Optional[str]]:
        """检查token格式"""
        parts = token.split(":")
        if len(parts) != 2:
            self.logger.warning("CSRF validation failed: invalid format")
            return None, "Invalid CSRF token format"
        return (parts[0], parts[1]), None

    def _check_token_expiration(self, csrf_obj: 'CSRFToken', nonce: str, token: str) -> Tuple[bool, Optional[str]]:
        """检查token是否过期"""
        if csrf_obj.is_expired():
            self.logger.warning("CSRF validation failed: token expired")
            # Clean up expired token
            del self._tokens[nonce]
            if csrf_obj.user_id and self._user_tokens.get(csrf_obj.user_id) == token:
                del self._user_tokens[csrf_obj.user_id]
            return False, "CSRF token has expired"
        return True, None

    def _verify_token_binding(self, csrf_obj: 'CSRFToken', user_id: Optional[str], session_id: Optional[str]) -> Tuple[bool, Optional[str]]:
        """验证token绑定"""
        if user_id and csrf_obj.user_id and csrf_obj.user_id != user_id:
            self.logger.warning(
                "CSRF validation failed: user mismatch",
                expected_user=csrf_obj.user_id,
                provided_user=user_id
            )
            return False, "CSRF token user mismatch"

        if session_id and csrf_obj.session_id and csrf_obj.session_id != session_id:
            self.logger.warning(
                "CSRF validation failed: session mismatch",
                expected_session=csrf_obj.session_id,
                provided_session=session_id
            )
            return False, "CSRF token session mismatch"

        return True, None

    def _verify_token_signature(self, nonce: str, csrf_obj: 'CSRFToken', signature: str) -> Tuple[bool, Optional[str]]:
        """验证token签名"""
        token_data = f"{nonce}:{csrf_obj.created_at}:{csrf_obj.user_id or ''}:{csrf_obj.session_id or ''}"
        expected_signature = hmac.new(
            self.secret_key.encode(),
            token_data.encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_signature):
            self.logger.warning("CSRF validation failed: invalid signature")
            return False, "Invalid CSRF token signature"

        return True, None

    def validate_token(
        self,
        token: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """Validate a CSRF token

        Args:
            token: CSRF token to validate
            user_id: Optional user ID for verification
            session_id: Optional session ID for verification

        Returns:
            (is_valid, error_message) tuple
        """
        if not token:
            self.logger.warning("CSRF validation failed: empty token")
            return False, "CSRF token is required"

        try:
            # Check token format
            format_result = self._check_token_format(token)
            if format_result[1]:
                return False, format_result[1]

            nonce, signature = format_result[0]

            # Check if nonce exists
            if nonce not in self._tokens:
                self.logger.warning("CSRF validation failed: nonce not found")
                return False, "Invalid CSRF token"

            csrf_obj = self._tokens[nonce]

            # Check expiration
            expiration_result = self._check_token_expiration(csrf_obj, nonce, token)
            if expiration_result[1]:
                return False, expiration_result[1]

            # Verify binding
            binding_result = self._verify_token_binding(csrf_obj, user_id, session_id)
            if binding_result[1]:
                return False, binding_result[1]

            # Verify signature
            signature_result = self._verify_token_signature(nonce, csrf_obj, signature)
            if signature_result[1]:
                return False, signature_result[1]

            self.logger.debug(
                "CSRF token validated",
                user_id=user_id,
                nonce=nonce[:8] + "..."
            )

            return True, None

        except Exception as e:
            self.logger.error("CSRF validation error", error=str(e))
            return False, "CSRF validation error"

    def revoke_token(self, token: str) -> bool:
        """Revoke a CSRF token

        Args:
            token: CSRF token to revoke

        Returns:
            True if token was revoked
        """
        try:
            parts = token.split(":")
            if len(parts) != 2:
                return False

            nonce, _ = parts

            if nonce in self._tokens:
                csrf_obj = self._tokens[nonce]

                # Remove from user mapping
                if csrf_obj.user_id and self._user_tokens.get(csrf_obj.user_id) == token:
                    del self._user_tokens[csrf_obj.user_id]

                # Remove token
                del self._tokens[nonce]

                self.logger.debug("CSRF token revoked", nonce=nonce[:8] + "...")
                return True

            return False

        except Exception as e:
            self.logger.error("CSRF revocation error", error=str(e))
            return False

    def revoke_user_tokens(self, user_id: str) -> int:
        """Revoke all tokens for a user

        Args:
            user_id: User ID

        Returns:
            Number of tokens revoked
        """
        count = 0

        # Find and remove all tokens for this user
        tokens_to_remove = [
            nonce for nonce, csrf_obj in self._tokens.items()
            if csrf_obj.user_id == user_id
        ]

        for nonce in tokens_to_remove:
            del self._tokens[nonce]
            count += 1

        # Remove user mapping
        if user_id in self._user_tokens:
            del self._user_tokens[user_id]

        if count > 0:
            self.logger.info("CSRF tokens revoked for user", user_id=user_id, count=count)

        return count

    def get_user_token(self, user_id: str) -> Optional[str]:
        """Get the current active token for a user

        Args:
            user_id: User ID

        Returns:
            CSRF token or None
        """
        return self._user_tokens.get(user_id)

    def cleanup_expired_tokens(self) -> int:
        """Clean up expired tokens

        Returns:
            Number of tokens cleaned up
        """
        count = 0
        now = time.time()
        expired_nonces = []

        for nonce, csrf_obj in self._tokens.items():
            if (now - csrf_obj.created_at) > CSRF_TOKEN_TTL:
                expired_nonces.append(nonce)

        for nonce in expired_nonces:
            csrf_obj = self._tokens[nonce]
            if csrf_obj.user_id and self._user_tokens.get(csrf_obj.user_id) == csrf_obj.token:
                del self._user_tokens[csrf_obj.user_id]
            del self._tokens[nonce]
            count += 1

        if count > 0:
            self.logger.debug("Expired CSRF tokens cleaned up", count=count)

        return count

    def get_stats(self) -> dict:
        """Get CSRF protection statistics

        Returns:
            Statistics dictionary
        """
        return {
            "active_tokens": len(self._tokens),
            "active_users": len(self._user_tokens),
            "token_ttl": CSRF_TOKEN_TTL,
        }


# Global CSRF protection instance
csrf_protection = CSRFProtection()


def get_csrf_token(user_id: Optional[str] = None, session_id: Optional[str] = None) -> str:
    """Generate a new CSRF token (convenience function)

    Args:
        user_id: Optional user ID for token binding
        session_id: Optional session ID for token binding

    Returns:
        CSRF token string
    """
    return csrf_protection.generate_token(user_id, session_id)


def validate_csrf_token(
    token: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
) -> Tuple[bool, Optional[str]]:
    """Validate a CSRF token (convenience function)

    Args:
        token: CSRF token to validate
        user_id: Optional user ID for verification
        session_id: Optional session ID for verification

    Returns:
        (is_valid, error_message) tuple
    """
    return csrf_protection.validate_token(token, user_id, session_id)


def revoke_csrf_token(token: str) -> bool:
    """Revoke a CSRF token (convenience function)

    Args:
        token: CSRF token to revoke

    Returns:
        True if token was revoked
    """
    return csrf_protection.revoke_token(token)


__all__ = [
    "CSRFToken",
    "CSRFProtection",
    "csrf_protection",
    "get_csrf_token",
    "validate_csrf_token",
    "revoke_csrf_token",
]

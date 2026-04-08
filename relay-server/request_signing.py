#!/usr/bin/env python3
"""
zhineng-bridge Request Signing

Provides HMAC-based request signing for sensitive operations.
This adds an additional layer of security beyond CSRF protection.
"""

import hashlib
import hmac
import time
from typing import Optional, Dict, Tuple
from dataclasses import dataclass

from logger import get_logger
from config import settings


# Signature configuration
SIGNATURE_VERSION = "v1"
SIGNATURE_TTL = 300  # 5 minutes in seconds
SIGNATURE_ALGORITHM = "sha256"
TIMESTAMP_TOLERANCE = 60  # seconds - allow for clock skew


@dataclass
class SignatureInfo:
    """Request signature information"""

    version: str
    timestamp: float
    signature: str
    algorithm: str
    data: str

    def is_expired(self, ttl: int = SIGNATURE_TTL) -> bool:
        """Check if signature is expired

        Args:
            ttl: Time-to-live in seconds

        Returns:
            True if signature is expired
        """
        return (time.time() - self.timestamp) > ttl


class RequestSigner:
    """Request Signing Manager

    Generates and verifies HMAC-SHA256 request signatures
    for sensitive operations.
    """

    def __init__(self, secret_key: Optional[str] = None):
        """Initialize request signer

        Args:
            secret_key: Secret key for HMAC signing (defaults to settings)
        """
        self.logger = get_logger(__name__)
        self.secret_key = secret_key or settings.security.secret_key

        if not self.secret_key:
            self.logger.error(
                "No request signing key configured. "
                "Set ZHINENG_BRIDGE_SECURITY_SECRET_KEY environment variable."
            )
            raise ValueError(
                "Request signing requires a secret key. "
                "Set ZHINENG_BRIDGE_SECURITY_SECRET_KEY environment variable."
            )

        self.logger.info(
            "Request signing initialized",
            algorithm=SIGNATURE_ALGORITHM,
            version=SIGNATURE_VERSION,
            ttl=SIGNATURE_TTL
        )

    def sign_request(
        self,
        data: Dict,
        user_id: Optional[str] = None,
    ) -> str:
        """Generate signature for request data

        Args:
            data: Request data to sign (will be serialized)
            user_id: Optional user ID for additional binding

        Returns:
            Signature string in format: version:timestamp:signature
        """
        # Generate timestamp
        timestamp = time.time()

        # Sort keys for consistent serialization
        sorted_keys = sorted(data.keys())
        data_str = "&".join([f"{k}={data[k]}" for k in sorted_keys])

        # Add user_id if provided
        if user_id:
            data_str += f"&user_id={user_id}"

        # Create message to sign
        message = f"{SIGNATURE_VERSION}:{timestamp}:{data_str}"

        # Generate signature
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            getattr(hashlib, SIGNATURE_ALGORITHM)
        ).hexdigest()

        # Combine into final signature string
        sig_string = f"{SIGNATURE_VERSION}:{timestamp}:{signature}"

        self.logger.debug(
            "Request signed",
            version=SIGNATURE_VERSION,
            data_keys=sorted_keys,
            user_id=user_id
        )

        return sig_string

    def verify_request(
        self,
        data: Dict,
        signature: str,
        user_id: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """Verify request signature

        Args:
            data: Request data to verify
            signature: Signature string to verify
            user_id: Optional user ID for verification

        Returns:
            (is_valid, error_message) tuple
        """
        if not signature:
            return False, "Request signature is required"

        try:
            # Parse signature
            parts = signature.split(":")
            if len(parts) != 3:
                return False, "Invalid signature format"

            version, timestamp_str, provided_signature = parts

            # Verify version
            if version != SIGNATURE_VERSION:
                return False, f"Unsupported signature version: {version}"

            # Parse timestamp
            try:
                timestamp = float(timestamp_str)
            except ValueError:
                return False, "Invalid timestamp in signature"

            # Check timestamp is not too old
            if time.time() - timestamp > SIGNATURE_TTL:
                return False, f"Signature expired (max age: {SIGNATURE_TTL}s)"

            # Check timestamp is not too far in future (clock skew)
            if timestamp - time.time() > TIMESTAMP_TOLERANCE:
                return False, f"Signature timestamp too far in future (max skew: {TIMESTAMP_TOLERANCE}s)"

            # Recreate the message that was signed
            sorted_keys = sorted(data.keys())
            data_str = "&".join([f"{k}={data[k]}" for k in sorted_keys])

            if user_id:
                data_str += f"&user_id={user_id}"

            message = f"{version}:{timestamp}:{data_str}"

            # Calculate expected signature
            expected_signature = hmac.new(
                self.secret_key.encode(),
                message.encode(),
                getattr(hashlib, SIGNATURE_ALGORITHM)
            ).hexdigest()

            # Compare signatures using constant-time comparison
            if not hmac.compare_digest(provided_signature, expected_signature):
                self.logger.warning("Signature verification failed: signature mismatch")
                return False, "Invalid signature"

            self.logger.debug("Request signature verified")
            return True, None

        except Exception as e:
            self.logger.error("Signature verification error", error=str(e))
            return False, f"Signature verification error: {str(e)}"

    def get_signature_headers(
        self,
        data: Dict,
        user_id: Optional[str] = None,
    ) -> Dict[str, str]:
        """Get headers for signed request

        Args:
            data: Request data to sign
            user_id: Optional user ID for binding

        Returns:
            Dictionary with signature headers
        """
        signature = self.sign_request(data, user_id)

        return {
            "X-Signature-Version": SIGNATURE_VERSION,
            "X-Signature": signature,
            "X-Signature-Algorithm": SIGNATURE_ALGORITHM,
        }

    def verify_from_headers(
        self,
        data: Dict,
        headers: Dict[str, str],
        user_id: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """Verify request from headers

        Args:
            data: Request data to verify
            headers: Request headers containing signature
            user_id: Optional user ID for verification

        Returns:
            (is_valid, error_message) tuple
        """
        signature = headers.get("X-Signature") or headers.get("signature")

        if not signature:
            return False, "Signature header not found"

        return self.verify_request(data, signature, user_id)


# Global request signer instance (lazy initialization)
_request_signer: Optional["RequestSigner"] = None


def _get_signer() -> "RequestSigner":
    """Get or create the global request signer instance"""
    global _request_signer
    if _request_signer is None:
        _request_signer = RequestSigner()
    return _request_signer


def sign_request(data: Dict, user_id: Optional[str] = None) -> str:
    """Generate request signature (convenience function)

    Args:
        data: Request data to sign
        user_id: Optional user ID for binding

    Returns:
        Signature string
    """
    return _get_signer().sign_request(data, user_id)


def verify_request(
    data: Dict,
    signature: str,
    user_id: Optional[str] = None,
) -> Tuple[bool, Optional[str]]:
    """Verify request signature (convenience function)

    Args:
        data: Request data to verify
        signature: Signature string
        user_id: Optional user ID for verification

    Returns:
        (is_valid, error_message) tuple
    """
    return _get_signer().verify_request(data, signature, user_id)


__all__ = [
    "SignatureInfo",
    "RequestSigner",
    "sign_request",
    "verify_request",
]

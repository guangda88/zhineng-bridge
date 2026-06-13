"""
E2E加密模块测试
"""

import pytest

from gateway.crypto import (
    ENCRYPTED_HEADER,
    KEY_ID_HEADER,
    NONCE_HEADER,
    generate_key,
    is_encrypted_request,
    is_sensitive_backend,
    strip_encryption_headers,
)


class TestCrypto:
    def test_generate_key_returns_base64(self):
        key = generate_key()
        import base64

        decoded = base64.b64decode(key)
        assert len(decoded) == 32

    def test_generate_key_unique(self):
        assert generate_key() != generate_key()

    def test_is_encrypted_request_true(self):
        headers = {ENCRYPTED_HEADER: "true"}
        assert is_encrypted_request(headers) is True

    def test_is_encrypted_request_false(self):
        headers = {ENCRYPTED_HEADER: "false"}
        assert is_encrypted_request(headers) is False

    def test_is_encrypted_request_missing(self):
        assert is_encrypted_request({}) is False

    def test_is_encrypted_request_case_insensitive(self):
        headers = {ENCRYPTED_HEADER: "True"}
        assert is_encrypted_request(headers) is True

    def test_is_sensitive_backend_health(self):
        assert is_sensitive_backend("linghealth") is True

    def test_is_sensitive_backend_law(self):
        assert is_sensitive_backend("linglaw") is True

    def test_is_sensitive_backend_others(self):
        for b in (
            "lingvision",
            "lingvoice",
            "lingtouch",
            "sizhen",
            "lingwear",
            "lingtong_plus",
            "lingzhi",
        ):
            assert is_sensitive_backend(b) is False

    def test_strip_encryption_headers_removes_all(self):
        headers = {
            ENCRYPTED_HEADER.lower(): "true",
            NONCE_HEADER.lower(): "abc123",
            KEY_ID_HEADER.lower(): "key-1",
            "content-type": "application/json",
            "x-api-key": "test123",
        }
        stripped = strip_encryption_headers(headers)
        assert ENCRYPTED_HEADER.lower() not in stripped
        assert NONCE_HEADER.lower() not in stripped
        assert KEY_ID_HEADER.lower() not in stripped
        assert "content-type" in stripped
        assert "x-api-key" in stripped

    def test_strip_encryption_headers_passthrough(self):
        headers = {"content-type": "application/json"}
        stripped = strip_encryption_headers(headers)
        assert stripped == headers

    def test_encrypt_decrypt_roundtrip(self):
        from gateway.crypto import decrypt, encrypt

        key = generate_key()
        plaintext = b'{"patient_id": "123", "diagnosis": "hypertension"}'
        ciphertext_b64, nonce_b64 = encrypt(plaintext, key)
        decrypted = decrypt(ciphertext_b64, nonce_b64, key)
        assert decrypted == plaintext

    def test_encrypt_produces_different_ciphertext(self):
        from gateway.crypto import encrypt

        key = generate_key()
        plaintext = b"same data"
        ct1, _ = encrypt(plaintext, key)
        ct2, _ = encrypt(plaintext, key)
        assert ct1 != ct2

    def test_decrypt_wrong_key_fails(self):
        from gateway.crypto import decrypt, encrypt

        key1 = generate_key()
        key2 = generate_key()
        plaintext = b"secret data"
        ct, nonce = encrypt(plaintext, key1)
        with pytest.raises(Exception):
            decrypt(ct, nonce, key2)

    def test_decrypt_tampered_ciphertext_fails(self):
        import base64

        from gateway.crypto import decrypt, encrypt

        key = generate_key()
        plaintext = b"secret data"
        ct, nonce = encrypt(plaintext, key)
        tampered = base64.b64encode(b"\x00" * 32).decode()
        with pytest.raises(Exception):
            decrypt(tampered, nonce, key)

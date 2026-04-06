#!/usr/bin/env python3
"""
密码重置和双因素认证单元测试
"""

import pytest
import sys
import os
import tempfile
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../relay-server'))

from auth_db import UserDatabase
from auth_hash import PasswordHasher
from auth_totp import TOTPAuth, TOTPManager
from auth_manager import AuthenticationManager
from auth_models import UserRole


class TestPasswordReset:
    """密码重置流程测试"""

    @pytest.fixture
    def db(self, tmp_path):
        db_path = str(tmp_path / "test_reset.db")
        return UserDatabase(db_path)

    @pytest.fixture
    def user_data(self, db):
        user = db.create_user(
            username="resetuser",
            password="OldPass123",
            email="reset@test.com",
            role=UserRole.USER,
            permissions=["read", "write"],
        )
        return user

    def test_create_and_verify_reset_token(self, db, user_data):
        token = db.create_password_reset_token(user_data.user_id, expires_in_hours=1)
        assert token is not None
        assert len(token) > 10

        user_id = db.verify_password_reset_token(token)
        assert user_id == user_data.user_id

    def test_expired_reset_token(self, db, user_data):
        token = db.create_password_reset_token(user_data.user_id, expires_in_hours=0)
        import time
        time.sleep(1)
        user_id = db.verify_password_reset_token(token)
        assert user_id is None

    def test_consume_reset_token(self, db, user_data):
        token = db.create_password_reset_token(user_data.user_id, expires_in_hours=1)
        assert db.consume_password_reset_token(token) is True
        assert db.consume_password_reset_token(token) is False

    def test_reset_password_full_flow(self, db, user_data):
        token = db.create_password_reset_token(user_data.user_id, expires_in_hours=1)
        result = db.reset_password(token, "NewPass456")
        assert result is True

        user = db.verify_user("resetuser", "NewPass456")
        assert user is not None
        assert user.user_id == user_data.user_id

    def test_reset_password_invalid_token(self, db, user_data):
        result = db.reset_password("invalid_token", "NewPass456")
        assert result is False

    def test_change_password(self, db, user_data):
        result = db.change_password(user_data.user_id, "OldPass123", "NewPass789")
        assert result is True

        user = db.verify_user("resetuser", "NewPass789")
        assert user is not None

    def test_change_password_wrong_current(self, db, user_data):
        result = db.change_password(user_data.user_id, "WrongPass", "NewPass789")
        assert result is False

    def test_verify_user_by_id(self, db, user_data):
        user = db.verify_user_by_id(user_data.user_id, "OldPass123")
        assert user is not None
        assert user.user_id == user_data.user_id

        user = db.verify_user_by_id(user_data.user_id, "WrongPass")
        assert user is None

    def test_cleanup_expired_reset_tokens(self, db, user_data):
        db.create_password_reset_token(user_data.user_id, expires_in_hours=1)
        db.create_password_reset_token(user_data.user_id, expires_in_hours=0)
        import time
        time.sleep(1)
        count = db.cleanup_expired_reset_tokens()
        assert count >= 1

    def test_manager_request_password_reset(self, user_data):
        mgr = AuthenticationManager.__new__(AuthenticationManager)
        mgr.db = user_data.__class__.__bases__[0].__dict__.get('_user_cache', None)
        from auth_manager import AuthenticationManager as AM
        tmp = tempfile.mktemp(suffix=".db")
        am = AM(db_path=tmp)
        user = am.db.create_user(
            username="mgrreset",
            password="OldPass123",
            email="mgr@test.com",
            role=UserRole.USER,
            permissions=["read", "write"],
        )
        token = am.request_password_reset("mgr@test.com")
        assert token is not None

        token2 = am.request_password_reset("nonexistent@test.com")
        assert token2 is None

    def test_manager_confirm_password_reset(self):
        tmp = tempfile.mktemp(suffix=".db")
        am = AuthenticationManager(db_path=tmp)
        user = am.db.create_user(
            username="confirmreset",
            password="OldPass123",
            email="confirm@test.com",
            role=UserRole.USER,
            permissions=["read", "write"],
        )
        token = am.request_password_reset("confirm@test.com")
        result = am.confirm_password_reset(token, "NewPass456")
        assert result is True

        user = am.db.verify_user("confirmreset", "NewPass456")
        assert user is not None


class TestTOTP:
    """TOTP 双因素认证测试"""

    def test_generate_secret(self):
        secret = TOTPAuth.generate_secret()
        assert len(secret) == 32
        import base64
        decoded = base64.b32decode(secret, casefold=True)
        assert len(decoded) == 20

    def test_generate_backup_codes(self):
        codes = TOTPAuth.generate_backup_codes(10)
        assert len(codes) == 10
        assert len(set(codes)) == 10
        for code in codes:
            assert len(code) == 8
            assert code == code.upper()

    def test_totp_generate_and_verify(self):
        totp = TOTPAuth()
        secret = TOTPAuth.generate_secret()
        code = totp.generate_totp(secret)
        assert len(code) == 6
        assert code.isdigit()
        assert totp.verify_totp(secret, code)

    def test_totp_reject_wrong_code(self):
        totp = TOTPAuth()
        secret = TOTPAuth.generate_secret()
        assert not totp.verify_totp(secret, "000000")

    def test_totp_provisioning_uri(self):
        totp = TOTPAuth()
        secret = TOTPAuth.generate_secret()
        uri = totp.get_provisioning_uri(secret, "testuser")
        assert uri.startswith("otpauth://totp/")
        assert "secret=" in uri
        assert "testuser" in uri

    def test_totp_window_tolerance(self):
        totp = TOTPAuth()
        secret = TOTPAuth.generate_secret()
        import time
        code = totp.generate_totp(secret, timestamp=int(time.time()) - 30)
        assert totp.verify_totp(secret, code, window=1)


class TestTOTPManager:
    """TOTP 管理器集成测试"""

    @pytest.fixture
    def manager_and_user(self):
        tmp = tempfile.mktemp(suffix=".db")
        am = AuthenticationManager(db_path=tmp)
        user = am.db.create_user(
            username="tfauser",
            password="Pass1234",
            email="tfa@test.com",
            role=UserRole.USER,
            permissions=["read", "write"],
        )
        return am, user

    def test_setup_2fa(self, manager_and_user):
        am, user = manager_and_user
        result = am.setup_2fa(user.user_id)
        assert "secret" in result
        assert "backup_codes" in result
        assert len(result["backup_codes"]) == 10
        assert "provisioning_uri" in result

    def test_enable_2fa(self, manager_and_user):
        am, user = manager_and_user
        result = am.setup_2fa(user.user_id)
        secret = result["secret"]
        code = am.totp_manager.totp.generate_totp(secret)
        assert am.enable_2fa(user.user_id, code) is True

    def test_enable_2fa_wrong_code(self, manager_and_user):
        am, user = manager_and_user
        am.setup_2fa(user.user_id)
        assert am.enable_2fa(user.user_id, "000000") is False

    def test_verify_2fa(self, manager_and_user):
        am, user = manager_and_user
        result = am.setup_2fa(user.user_id)
        secret = result["secret"]
        code = am.totp_manager.totp.generate_totp(secret)
        am.enable_2fa(user.user_id, code)

        code2 = am.totp_manager.totp.generate_totp(secret)
        assert am.verify_2fa(user.user_id, code2) is True

    def test_2fa_backup_code(self, manager_and_user):
        am, user = manager_and_user
        result = am.setup_2fa(user.user_id)
        secret = result["secret"]
        code = am.totp_manager.totp.generate_totp(secret)
        am.enable_2fa(user.user_id, code)

        backup_code = result["backup_codes"][0]
        assert am.verify_2fa(user.user_id, backup_code) is True

    def test_disable_2fa(self, manager_and_user):
        am, user = manager_and_user
        result = am.setup_2fa(user.user_id)
        secret = result["secret"]
        code = am.totp_manager.totp.generate_totp(secret)
        am.enable_2fa(user.user_id, code)

        code2 = am.totp_manager.totp.generate_totp(secret)
        assert am.disable_2fa(user.user_id, code2) is True

    def test_regenerate_backup_codes(self, manager_and_user):
        am, user = manager_and_user
        result = am.setup_2fa(user.user_id)
        secret = result["secret"]
        code = am.totp_manager.totp.generate_totp(secret)
        am.enable_2fa(user.user_id, code)

        code2 = am.totp_manager.totp.generate_totp(secret)
        new_codes = am.regenerate_backup_codes(user.user_id, code2)
        assert new_codes is not None
        assert len(new_codes) == 10

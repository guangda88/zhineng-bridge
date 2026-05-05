#!/usr/bin/env python3
"""
SessionProtocol 单元测试

覆盖: ABC协议、ContextBudget、SessionSnapshot、FamilySessionManager、ZhiBridgeAdapter
"""

import json
import os
import sys
import tempfile
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from session_protocol.protocol import (
    CompressionStrategy,
    ContextBudget,
    SessionProtocol,
    SessionSnapshot,
    SessionStatus,
)
from session_protocol.manager import FamilySessionManager
from session_protocol.auth import AuthorizationManager, AuthorizationError
from session_protocol.zhi_bridge_adapter import ZhiBridgeAdapter


class TestContextBudget:
    def test_defaults(self):
        b = ContextBudget()
        assert b.max_tokens == 32000
        assert b.max_turns == 40
        assert b.compression_threshold == 0.8
        assert b.strategy == CompressionStrategy.TRUNCATE

    def test_usage_ratio(self):
        b = ContextBudget(current_tokens=16000, max_tokens=32000)
        assert abs(b.usage_ratio - 0.5) < 0.01

    def test_should_compress(self):
        b = ContextBudget(current_tokens=26000, max_tokens=32000, compression_threshold=0.8)
        assert b.should_compress is True

    def test_should_not_compress(self):
        b = ContextBudget(current_tokens=10000, max_tokens=32000, compression_threshold=0.8)
        assert b.should_compress is False

    def test_to_dict(self):
        b = ContextBudget()
        d = b.to_dict()
        assert "max_tokens" in d
        assert "usage_ratio" in d
        assert "should_compress" in d
        assert d["strategy"] == "truncate"


class TestSessionSnapshot:
    def test_create(self):
        s = SessionSnapshot(member_id="ZhiBridge", session_id="test-123")
        assert s.member_id == "ZhiBridge"
        assert s.session_id == "test-123"
        assert s.status == SessionStatus.ACTIVE

    def test_to_json_roundtrip(self):
        s = SessionSnapshot(
            member_id="ZhiBridge",
            session_id="test-123",
            budget=ContextBudget(current_tokens=500),
            context_data={"key": "value"},
        )
        json_str = s.to_json()
        restored = SessionSnapshot.from_json(json_str)
        assert restored.member_id == "ZhiBridge"
        assert restored.session_id == "test-123"
        assert restored.budget.current_tokens == 500
        assert restored.context_data["key"] == "value"

    def test_from_dict(self):
        data = {
            "snapshot_id": "snap-1",
            "member_id": "lingke",
            "session_id": "sess-1",
            "status": "compressed",
            "budget": {"max_tokens": 16000, "strategy": "summarize"},
        }
        s = SessionSnapshot.from_dict(data)
        assert s.snapshot_id == "snap-1"
        assert s.status == SessionStatus.COMPRESSED
        assert s.budget.max_tokens == 16000
        assert s.budget.strategy == CompressionStrategy.SUMMARIZE


class TestFamilySessionManager:
    @pytest.fixture
    def mgr(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_sessions.db")
            m = FamilySessionManager(db_path=db_path)
            yield m

    def test_init_creates_db(self, mgr):
        assert os.path.exists(mgr.db_path)

    def test_members_registered(self, mgr):
        members = mgr.list_members()
        ids = [m["member_id"] for m in members]
        assert "ZhiBridge" in ids
        assert "lingflow" in ids
        assert "lingclaude" in ids

    def test_create_session(self, mgr):
        sid = mgr.create_session("ZhiBridge", tool_name="crush")
        session = mgr.get_session(sid)
        assert session is not None
        assert session["member_id"] == "ZhiBridge"
        assert session["tool_name"] == "crush"

    def test_list_sessions(self, mgr):
        mgr.create_session("ZhiBridge")
        mgr.create_session("lingclaude")
        all_sessions = mgr.list_sessions()
        assert len(all_sessions) == 2
        zb_sessions = mgr.list_sessions(member_id="ZhiBridge")
        assert len(zb_sessions) == 1

    def test_update_session_status(self, mgr):
        sid = mgr.create_session("ZhiBridge")
        mgr.update_session_status(sid, "active")
        session = mgr.get_session(sid)
        assert session["status"] == "active"

    def test_delete_session(self, mgr):
        sid = mgr.create_session("ZhiBridge")
        mgr.delete_session(sid)
        assert mgr.get_session(sid) is None

    def test_save_and_get_snapshot(self, mgr):
        sid = mgr.create_session("ZhiBridge")
        snapshot = SessionSnapshot(
            member_id="ZhiBridge",
            session_id=sid,
            budget=ContextBudget(current_tokens=1000),
            context_data={"hello": "world"},
        )
        mgr.save_snapshot(snapshot)
        loaded = mgr.get_snapshot(snapshot.snapshot_id)
        assert loaded is not None
        assert loaded.member_id == "ZhiBridge"
        assert loaded.budget.current_tokens == 1000
        assert loaded.context_data["hello"] == "world"

    def test_list_snapshots(self, mgr):
        sid = mgr.create_session("ZhiBridge")
        for i in range(3):
            mgr.save_snapshot(SessionSnapshot(
                member_id="ZhiBridge",
                session_id=sid,
                context_data={"i": i},
            ))
        snaps = mgr.list_snapshots(member_id="ZhiBridge")
        assert len(snaps) == 3

    def test_family_overview(self, mgr):
        mgr.create_session("ZhiBridge")
        overview = mgr.get_family_overview()
        assert overview["members"] >= 12
        assert overview["sessions"] >= 1

    def test_member_health(self, mgr):
        health = mgr.get_member_health("ZhiBridge")
        assert health["member_id"] == "ZhiBridge"
        assert health["protocol_registered"] is False

    def test_update_heartbeat(self, mgr):
        mgr.update_heartbeat("ZhiBridge")
        m = mgr.get_member("ZhiBridge")
        assert m["last_heartbeat"] is not None


class TestZhiBridgeAdapter:
    @pytest.fixture
    def adapter(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield ZhiBridgeAdapter(data_dir=tmpdir)

    def test_save_context(self, adapter):
        snapshot = adapter.save_context()
        assert snapshot.member_id == "ZhiBridge"
        assert snapshot.snapshot_id

    def test_restore_context(self, adapter):
        adapter.add_context_entry("test", {"msg": "hello"}, tokens=50)
        snapshot = adapter.save_context()
        sid = snapshot.session_id

        adapter2 = ZhiBridgeAdapter(data_dir=adapter.data_dir)
        result = adapter2.restore_context(sid)
        assert result is True

    def test_get_budget(self, adapter):
        budget = adapter.get_budget()
        assert isinstance(budget, ContextBudget)
        assert budget.max_tokens == 32000

    def test_compress_truncate(self, adapter):
        for i in range(50):
            adapter.add_context_entry("msg", {"i": i}, tokens=100)
        snapshot = adapter.compress_context(CompressionStrategy.TRUNCATE)
        assert snapshot.member_id == "ZhiBridge"

    def test_compress_summarize(self, adapter):
        adapter.add_context_entry("msg", {"text": "x" * 1000}, tokens=5000)
        snapshot = adapter.compress_context(CompressionStrategy.SUMMARIZE)
        assert snapshot.member_id == "ZhiBridge"

    def test_compress_structured(self, adapter):
        for i in range(50):
            adapter.add_context_entry("msg", {"i": i}, tokens=100)
        snapshot = adapter.compress_context(CompressionStrategy.STRUCTURED)
        assert snapshot.member_id == "ZhiBridge"

    def test_validate_integrity(self, adapter):
        snapshot = adapter.save_context()
        assert adapter.validate_integrity(snapshot) is True

    def test_validate_integrity_bad_member(self, adapter):
        snapshot = SessionSnapshot(member_id="fake", session_id="test")
        assert adapter.validate_integrity(snapshot) is False

    def test_export_import_roundtrip(self, adapter):
        adapter.add_context_entry("test", {"data": 42}, tokens=10)
        json_str = adapter.export_snapshot()
        data = json.loads(json_str)
        assert data["member_id"] == "ZhiBridge"

        adapter2 = ZhiBridgeAdapter(data_dir=adapter.data_dir)
        imported = adapter2.import_snapshot(json_str)
        assert imported.member_id == "ZhiBridge"

    def test_health_check(self, adapter):
        health = adapter.health_check()
        assert health["member_id"] == "ZhiBridge"
        assert health["status"] == "healthy"

    def test_add_context_entry(self, adapter):
        adapter.add_context_entry("ws_connect", {"client": "test"}, tokens=50)
        budget = adapter.get_budget()
        assert budget.current_turns == 1
        assert budget.current_tokens == 50


class TestIntegration:
    def test_full_workflow(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            data_dir = os.path.join(tmpdir, "data")
            mgr = FamilySessionManager(db_path=db_path)
            adapter = ZhiBridgeAdapter(data_dir=data_dir)
            mgr.register_protocol("ZhiBridge", adapter)

            adapter.add_context_entry("ws_connect", {"client": "crush"}, tokens=200)
            adapter.add_context_entry("message", {"text": "hello"}, tokens=100)

            snapshot = mgr.delegate_save("ZhiBridge")
            assert snapshot is not None
            assert snapshot.member_id == "ZhiBridge"

            health = mgr.get_member_health("ZhiBridge")
            assert health["protocol_registered"] is True
            assert health["snapshots"] >= 1

            overview = mgr.get_family_overview()
            assert overview["members"] >= 12

            compressed = mgr.delegate_compress("ZhiBridge", CompressionStrategy.STRUCTURED)
            assert compressed is not None

            adapter2 = ZhiBridgeAdapter(data_dir=data_dir)
            restored = adapter2.restore_context(snapshot.session_id)
            assert restored is True


class TestAuthorizationManager:
    @pytest.fixture
    def auth(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_auth.db")
            yield AuthorizationManager(db_path)

    def test_self_access_always_allowed(self, auth):
        assert auth.check_permission("ZhiBridge", "ZhiBridge", "write") is True
        assert auth.check_permission("ZhiBridge", "ZhiBridge", "delete") is True
        assert auth.check_permission("ZhiBridge", "ZhiBridge", "read") is True

    def test_cross_member_denied_by_default(self, auth):
        assert auth.check_permission("ZhiBridge", "lingflow", "write") is False
        assert auth.check_permission("ZhiBridge", "lingclaude", "delete") is False
        assert auth.check_permission("ZhiBridge", "lingresearch", "delegate_save") is False

    def test_grant_permission(self, auth):
        auth.grant_permission("ZhiBridge", "lingflow", "write", granted_by="human")
        assert auth.check_permission("ZhiBridge", "lingflow", "write") is True
        assert auth.check_permission("ZhiBridge", "lingflow", "delete") is False

    def test_require_permission_self_ok(self, auth):
        auth.require_permission("ZhiBridge", "ZhiBridge", "write")

    def test_require_permission_raises(self, auth):
        with pytest.raises(AuthorizationError):
            auth.require_permission("ZhiBridge", "lingflow", "write")

    def test_require_permission_after_grant(self, auth):
        auth.grant_permission("ZhiBridge", "lingflow", "write", granted_by="human")
        auth.require_permission("ZhiBridge", "lingflow", "write")

    def test_revoke_permission(self, auth):
        auth.grant_permission("ZhiBridge", "lingflow", "write", granted_by="human")
        assert auth.revoke_permission("ZhiBridge", "lingflow", "write") is True
        assert auth.check_permission("ZhiBridge", "lingflow", "write") is False
        assert auth.revoke_permission("ZhiBridge", "lingflow", "write") is False

    def test_list_permissions(self, auth):
        auth.grant_permission("ZhiBridge", "lingflow", "write", granted_by="human")
        auth.grant_permission("ZhiBridge", "lingclaude", "read", granted_by="human")
        perms = auth.list_permissions(caller_id="ZhiBridge")
        assert len(perms) == 2
        all_perms = auth.list_permissions()
        assert len(all_perms) == 2

    def test_invalid_operation(self, auth):
        with pytest.raises(ValueError):
            auth.grant_permission("ZhiBridge", "lingflow", "invalid_op", granted_by="human")

    def test_audit_log(self, auth):
        auth.require_permission("ZhiBridge", "ZhiBridge", "write")
        auth.grant_permission("ZhiBridge", "lingflow", "write", granted_by="human")
        auth.require_permission("ZhiBridge", "lingflow", "write")
        with pytest.raises(AuthorizationError):
            auth.require_permission("ZhiBridge", "lingclaude", "write")

        logs = auth.get_audit_log()
        assert len(logs) >= 4
        denied = [l for l in logs if l["result"] == "denied"]
        assert len(denied) >= 1

    def test_audit_log_filter(self, auth):
        auth.require_permission("ZhiBridge", "ZhiBridge", "write")
        auth.require_permission("lingflow", "lingflow", "read")
        zb_logs = auth.get_audit_log(caller_id="ZhiBridge")
        assert all(l["caller_id"] == "ZhiBridge" for l in zb_logs)


class TestFamilySessionManagerAuth:
    @pytest.fixture
    def mgr(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_auth_mgr.db")
            m = FamilySessionManager(db_path=db_path, caller_id="ZhiBridge")
            yield m

    def test_create_session_self_allowed(self, mgr):
        sid = mgr.create_session("ZhiBridge", tool_name="crush")
        assert sid is not None

    def test_create_session_cross_member_denied(self, mgr):
        with pytest.raises(AuthorizationError):
            mgr.create_session("lingflow", tool_name="web")

    def test_create_session_cross_member_after_grant(self, mgr):
        mgr.auth.grant_permission("ZhiBridge", "lingflow", "write", granted_by="human")
        sid = mgr.create_session("lingflow", tool_name="web")
        assert sid is not None

    def test_delete_session_self_allowed(self, mgr):
        sid = mgr.create_session("ZhiBridge")
        mgr.delete_session(sid)
        assert mgr.get_session(sid) is None

    def test_delete_session_cross_member_denied(self, mgr):
        mgr.auth.grant_permission("ZhiBridge", "lingflow", "write", granted_by="human")
        sid = mgr.create_session("lingflow")
        mgr.auth.revoke_permission("ZhiBridge", "lingflow", "write")
        mgr.auth.revoke_permission("ZhiBridge", "lingflow", "delete")
        with pytest.raises(AuthorizationError):
            mgr.delete_session(sid)

    def test_list_sessions_self_allowed(self, mgr):
        mgr.create_session("ZhiBridge")
        sessions = mgr.list_sessions(member_id="ZhiBridge")
        assert len(sessions) == 1

    def test_list_sessions_cross_member_denied(self, mgr):
        with pytest.raises(AuthorizationError):
            mgr.list_sessions(member_id="lingflow")

    def test_list_sessions_all_system(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            mgr = FamilySessionManager(db_path=db_path, caller_id="system")
            mgr.create_session("ZhiBridge")
            mgr.create_session("lingflow")
            sessions = mgr.list_sessions()
            assert len(sessions) == 2

    def test_list_snapshots_cross_member_denied(self, mgr):
        with pytest.raises(AuthorizationError):
            mgr.list_snapshots(member_id="lingclaude")

    def test_list_snapshots_self_allowed(self, mgr):
        sid = mgr.create_session("ZhiBridge")
        mgr.save_snapshot(SessionSnapshot(
            member_id="ZhiBridge", session_id=sid,
        ))
        snaps = mgr.list_snapshots(member_id="ZhiBridge")
        assert len(snaps) == 1

    def test_delegate_save_cross_member_denied(self, mgr):
        with pytest.raises(AuthorizationError):
            mgr.delegate_save("lingflow")

    def test_delegate_restore_cross_member_denied(self, mgr):
        with pytest.raises(AuthorizationError):
            mgr.delegate_restore("lingflow", "fake-session")

    def test_delegate_compress_cross_member_denied(self, mgr):
        with pytest.raises(AuthorizationError):
            mgr.delegate_compress("lingflow")

    def test_delegate_save_self_allowed(self, mgr):
        adapter = ZhiBridgeAdapter(data_dir=os.path.join(
            os.path.dirname(mgr.db_path), "data"
        ))
        mgr.register_protocol("ZhiBridge", adapter)
        adapter.add_context_entry("test", {"msg": "hello"}, tokens=50)
        snapshot = mgr.delegate_save("ZhiBridge")
        assert snapshot is not None
        assert snapshot.member_id == "ZhiBridge"

    def test_delegate_cross_member_with_grant(self, mgr):
        mgr.auth.grant_permission("ZhiBridge", "lingflow", "delegate_save", granted_by="human")
        mock_protocol = MagicMock()
        snapshot = SessionSnapshot(member_id="lingflow", session_id="test-session")
        mock_protocol.save_context.return_value = snapshot
        mgr.register_protocol("lingflow", mock_protocol)
        result = mgr.delegate_save("lingflow")
        assert result is not None
        assert result.member_id == "lingflow"

    def test_system_caller_has_no_special_access(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            mgr = FamilySessionManager(db_path=db_path, caller_id="ZhiBridge")
            mgr.auth.grant_permission("ZhiBridge", "lingflow", "write", granted_by="human")
            mgr.create_session("lingflow")
            with pytest.raises(AuthorizationError):
                mgr.delete_session(
                    mgr.list_sessions(member_id="lingflow")[0]["session_id"]
                )

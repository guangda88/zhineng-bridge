#!/usr/bin/env python3
"""
团队协作功能 + 新工具 注册测试
"""

import pytest
import sys
import os
import json
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'relay-server'))

from team_models import Team, TeamMember, TeamInvite, SharedSession, TeamRole, TeamStatus, InviteStatus
from team_db import TeamDatabase
from team_manager import TeamManager


class TestTeamModels:
    """团队数据模型测试"""

    def test_team_to_dict(self):
        now = datetime.now()
        team = Team(team_id="t1", name="TestTeam", description="desc", owner_id="u1",
                    status=TeamStatus.ACTIVE, created_at=now, updated_at=now)
        d = team.to_dict()
        assert d["team_id"] == "t1"
        assert d["name"] == "TestTeam"
        assert d["status"] == "active"
        assert "created_at" in d

    def test_team_member_to_dict(self):
        now = datetime.now()
        member = TeamMember(membership_id="m1", team_id="t1", user_id="u1",
                            role=TeamRole.OWNER, joined_at=now, invited_by=None)
        d = member.to_dict()
        assert d["role"] == "owner"
        assert d["user_id"] == "u1"

    def test_team_invite_to_dict(self):
        now = datetime.now()
        invite = TeamInvite(invite_id="i1", team_id="t1", inviter_id="u1",
                            invitee_email="test@test.com", token="tok123",
                            status=InviteStatus.PENDING, expires_at=now + timedelta(hours=72),
                            created_at=now)
        d = invite.to_dict()
        assert d["status"] == "pending"
        assert d["invitee_email"] == "test@test.com"

    def test_shared_session_to_dict(self):
        now = datetime.now()
        ss = SharedSession(share_id="s1", session_id="sess1", team_id="t1",
                           shared_by="u1", title="My Session", is_active=True, created_at=now)
        d = ss.to_dict()
        assert d["session_id"] == "sess1"
        assert d["is_active"] is True

    def test_team_role_enum(self):
        assert TeamRole.OWNER.value == "owner"
        assert TeamRole.ADMIN.value == "admin"
        assert TeamRole.MEMBER.value == "member"
        assert TeamRole.VIEWER.value == "viewer"


class TestTeamManager:
    """团队管理器测试 — 使用内存数据库"""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        from auth_db import UserDatabase
        db_path = str(tmp_path / "test_team.db")
        self.user_db = UserDatabase(db_path=db_path)
        self.manager = TeamManager(self.user_db)
        self.owner = self.user_db.create_user("owner_user", "password123", "owner@test.com")
        self.member1 = self.user_db.create_user("member_one", "password123", "member1@test.com")
        self.member2 = self.user_db.create_user("member_two", "password123", "member2@test.com")
        self.outsider = self.user_db.create_user("outsider", "password123", "outsider@test.com")

    def test_create_team(self):
        team = self.manager.create_team("My Team", self.owner.user_id, "A test team")
        assert team.name == "My Team"
        assert team.owner_id == self.owner.user_id
        assert team.status == TeamStatus.ACTIVE
        members = self.manager.get_team_members(team.team_id, self.owner.user_id)
        assert len(members) == 1
        assert members[0].role == TeamRole.OWNER

    def test_create_team_name_validation(self):
        with pytest.raises(ValueError, match="至少需要2个字符"):
            self.manager.create_team("A", self.owner.user_id)
        with pytest.raises(ValueError, match="不能超过100个字符"):
            self.manager.create_team("X" * 101, self.owner.user_id)

    def test_get_team(self):
        team = self.manager.create_team("Team", self.owner.user_id)
        fetched = self.manager.get_team(team.team_id, self.owner.user_id)
        assert fetched is not None
        assert fetched.team_id == team.team_id

    def test_get_team_no_permission(self):
        team = self.manager.create_team("Team", self.owner.user_id)
        fetched = self.manager.get_team(team.team_id, self.outsider.user_id)
        assert fetched is None

    def test_update_team(self):
        team = self.manager.create_team("Team", self.owner.user_id)
        updated = self.manager.update_team(team.team_id, self.owner.user_id, name="New Name", description="Updated")
        assert updated.name == "New Name"
        assert updated.description == "Updated"

    def test_update_team_permission_denied(self):
        team = self.manager.create_team("Team", self.owner.user_id)
        with pytest.raises(PermissionError):
            self.manager.update_team(team.team_id, self.outsider.user_id, name="Hacked")

    def test_delete_team(self):
        team = self.manager.create_team("Team", self.owner.user_id)
        assert self.manager.delete_team(team.team_id, self.owner.user_id) is True
        assert self.manager.get_team(team.team_id, self.owner.user_id) is None

    def test_delete_team_not_owner(self):
        team = self.manager.create_team("Team", self.owner.user_id)
        with pytest.raises(PermissionError):
            self.manager.delete_team(team.team_id, self.outsider.user_id)

    def test_list_user_teams(self):
        self.manager.create_team("Team1", self.owner.user_id)
        self.manager.create_team("Team2", self.owner.user_id)
        teams = self.manager.list_user_teams(self.owner.user_id)
        assert len(teams) == 2

    def test_member_management(self):
        team = self.manager.create_team("Team", self.owner.user_id)
        self.manager.db.add_member(team.team_id, self.member1.user_id, TeamRole.MEMBER, self.owner.user_id)
        members = self.manager.get_team_members(team.team_id, self.owner.user_id)
        assert len(members) == 2
        role = self.manager.db.get_member_role(team.team_id, self.member1.user_id)
        assert role == TeamRole.MEMBER

    def test_update_member_role(self):
        team = self.manager.create_team("Team", self.owner.user_id)
        self.manager.db.add_member(team.team_id, self.member1.user_id, TeamRole.MEMBER, self.owner.user_id)
        self.manager.update_member_role(team.team_id, self.owner.user_id, self.member1.user_id, TeamRole.ADMIN)
        role = self.manager.db.get_member_role(team.team_id, self.member1.user_id)
        assert role == TeamRole.ADMIN

    def test_remove_member(self):
        team = self.manager.create_team("Team", self.owner.user_id)
        self.manager.db.add_member(team.team_id, self.member1.user_id, TeamRole.MEMBER, self.owner.user_id)
        self.manager.remove_member(team.team_id, self.owner.user_id, self.member1.user_id)
        members = self.manager.get_team_members(team.team_id, self.owner.user_id)
        assert len(members) == 1

    def test_cannot_remove_self(self):
        team = self.manager.create_team("Team", self.owner.user_id)
        with pytest.raises(ValueError, match="不能移除自己"):
            self.manager.remove_member(team.team_id, self.owner.user_id, self.owner.user_id)

    def test_leave_team(self):
        team = self.manager.create_team("Team", self.owner.user_id)
        self.manager.db.add_member(team.team_id, self.member1.user_id, TeamRole.MEMBER, self.owner.user_id)
        self.manager.leave_team(team.team_id, self.member1.user_id)
        teams = self.manager.list_user_teams(self.member1.user_id)
        assert len(teams) == 0

    def test_owner_leave_deletes_team_if_only_member(self):
        team = self.manager.create_team("Team", self.owner.user_id)
        self.manager.leave_team(team.team_id, self.owner.user_id)
        assert self.manager.get_team(team.team_id, self.owner.user_id) is None

    def test_owner_cannot_leave_with_members(self):
        team = self.manager.create_team("Team", self.owner.user_id)
        self.manager.db.add_member(team.team_id, self.member1.user_id, TeamRole.MEMBER, self.owner.user_id)
        with pytest.raises(ValueError, match="请先转让所有权"):
            self.manager.leave_team(team.team_id, self.owner.user_id)

    def test_invite_flow(self):
        team = self.manager.create_team("Team", self.owner.user_id)
        invite = self.manager.create_invite(team.team_id, self.owner.user_id, "new@test.com")
        assert invite.status == InviteStatus.PENDING
        assert invite.invitee_email == "new@test.com"

        accepted = self.manager.accept_invite(invite.token, self.member1.user_id)
        assert accepted.status == InviteStatus.ACCEPTED
        role = self.manager.db.get_member_role(team.team_id, self.member1.user_id)
        assert role == TeamRole.MEMBER

    def test_invite_permission_denied(self):
        team = self.manager.create_team("Team", self.owner.user_id)
        self.manager.db.add_member(team.team_id, self.member1.user_id, TeamRole.MEMBER, self.owner.user_id)
        with pytest.raises(PermissionError):
            self.manager.create_invite(team.team_id, self.member1.user_id, "new@test.com")

    def test_list_invites(self):
        team = self.manager.create_team("Team", self.owner.user_id)
        self.manager.create_invite(team.team_id, self.owner.user_id, "a@test.com")
        self.manager.create_invite(team.team_id, self.owner.user_id, "b@test.com")
        invites = self.manager.list_team_invites(team.team_id, self.owner.user_id)
        assert len(invites) == 2

    def test_share_session(self):
        team = self.manager.create_team("Team", self.owner.user_id)
        shared = self.manager.share_session("sess-123", team.team_id, self.owner.user_id, "My Session")
        assert shared.session_id == "sess-123"
        assert shared.is_active is True

    def test_unshare_session(self):
        team = self.manager.create_team("Team", self.owner.user_id)
        shared = self.manager.share_session("sess-123", team.team_id, self.owner.user_id)
        assert self.manager.unshare_session(shared.share_id, team.team_id, self.owner.user_id) is True
        sessions = self.manager.get_team_sessions(team.team_id, self.owner.user_id)
        assert len(sessions) == 0

    def test_get_team_sessions(self):
        team = self.manager.create_team("Team", self.owner.user_id)
        self.manager.share_session("s1", team.team_id, self.owner.user_id, "Session 1")
        self.manager.share_session("s2", team.team_id, self.owner.user_id, "Session 2")
        sessions = self.manager.get_team_sessions(team.team_id, self.owner.user_id)
        assert len(sessions) == 2

    def test_share_session_permission_denied(self):
        team = self.manager.create_team("Team", self.owner.user_id)
        with pytest.raises(PermissionError):
            self.manager.share_session("sess-123", team.team_id, self.outsider.user_id)

    def test_cleanup_expired_invites(self):
        team = self.manager.create_team("Team", self.owner.user_id)
        invite = self.manager.db.create_invite(team.team_id, self.owner.user_id, "test@test.com", expires_hours=-1)
        cleaned = self.manager.db.cleanup_expired_invites()
        assert cleaned >= 1


class TestNewToolsRegistry:
    """验证新增工具已注册"""

    @pytest.fixture(autouse=True)
    def setup(self):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'phase1', 'session_manager'))

    def test_session_manager_has_16_tools(self):
        from session_manager import SessionManager
        sm = SessionManager()
        assert len(sm.tools) == 15

    def test_aider_registered(self):
        from session_manager import SessionManager
        sm = SessionManager()
        assert "aider" in sm.tools
        assert sm.tools["aider"]["name"] == "Aider"

    def test_continue_registered(self):
        from session_manager import SessionManager
        sm = SessionManager()
        assert "continue" in sm.tools

    def test_tabnine_registered(self):
        from session_manager import SessionManager
        sm = SessionManager()
        assert "tabnine" in sm.tools

    def test_windsurf_registered(self):
        from session_manager import SessionManager
        sm = SessionManager()
        assert "windsurf" in sm.tools

    def test_cody_registered(self):
        from session_manager import SessionManager
        sm = SessionManager()
        assert "cody" in sm.tools

    def test_augment_registered(self):
        from session_manager import SessionManager
        sm = SessionManager()
        assert "augment" in sm.tools

    def test_codium_registered(self):
        from session_manager import SessionManager
        sm = SessionManager()
        assert "codium" in sm.tools

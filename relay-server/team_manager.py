#!/usr/bin/env python3
"""
团队协作 - 管理器

提供团队协作的业务逻辑层，包含权限检查。
"""

from typing import Optional, List

from logger import get_logger
from auth_db import UserDatabase
from team_models import TeamRole, TeamStatus, InviteStatus, Team, TeamMember, TeamInvite, SharedSession
from team_db import TeamDatabase


class TeamManager:
    """团队管理器"""

    def __init__(self, user_db: UserDatabase):
        self.logger = get_logger(__name__)
        self.db = TeamDatabase(user_db)

    def _check_permission(self, team_id: str, user_id: str, min_role: TeamRole = TeamRole.MEMBER) -> bool:
        role = self.db.get_member_role(team_id, user_id)
        if role is None:
            return False
        hierarchy = {TeamRole.VIEWER: 0, TeamRole.MEMBER: 1, TeamRole.ADMIN: 2, TeamRole.OWNER: 3}
        return hierarchy.get(role, 0) >= hierarchy.get(min_role, 0)

    # ========================================================================
    # Team CRUD
    # ========================================================================

    def create_team(self, name: str, owner_id: str, description: str = None) -> Team:
        if not name or len(name.strip()) < 2:
            raise ValueError("团队名称至少需要2个字符")
        if len(name) > 100:
            raise ValueError("团队名称不能超过100个字符")
        return self.db.create_team(name.strip(), owner_id, description)

    def get_team(self, team_id: str, user_id: str) -> Optional[Team]:
        if not self._check_permission(team_id, user_id, TeamRole.VIEWER):
            return None
        return self.db.get_team(team_id)

    def update_team(self, team_id: str, user_id: str, **kwargs) -> Optional[Team]:
        if not self._check_permission(team_id, user_id, TeamRole.ADMIN):
            raise PermissionError("需要管理员权限才能修改团队")
        return self.db.update_team(team_id, **kwargs)

    def delete_team(self, team_id: str, user_id: str) -> bool:
        role = self.db.get_member_role(team_id, user_id)
        if role != TeamRole.OWNER:
            raise PermissionError("只有团队所有者才能删除团队")
        return self.db.delete_team(team_id)

    def list_user_teams(self, user_id: str) -> List[Team]:
        return self.db.list_user_teams(user_id)

    # ========================================================================
    # Members
    # ========================================================================

    def get_team_members(self, team_id: str, user_id: str) -> List[TeamMember]:
        if not self._check_permission(team_id, user_id, TeamRole.VIEWER):
            raise PermissionError("无权查看团队成员")
        return self.db.get_team_members(team_id)

    def update_member_role(self, team_id: str, user_id: str, target_user_id: str,
                           new_role: TeamRole) -> bool:
        if not self._check_permission(team_id, user_id, TeamRole.OWNER):
            raise PermissionError("只有团队所有者才能修改成员角色")
        if new_role == TeamRole.OWNER:
            raise ValueError("不能直接将成员设为所有者，请使用转让功能")
        return self.db.update_member_role(team_id, target_user_id, new_role)

    def remove_member(self, team_id: str, user_id: str, target_user_id: str) -> bool:
        if user_id == target_user_id:
            raise ValueError("不能移除自己，请使用退出团队功能")
        if not self._check_permission(team_id, user_id, TeamRole.ADMIN):
            raise PermissionError("需要管理员权限才能移除成员")
        target_role = self.db.get_member_role(team_id, target_user_id)
        if target_role == TeamRole.OWNER:
            raise PermissionError("不能移除团队所有者")
        return self.db.remove_member(team_id, target_user_id)

    def leave_team(self, team_id: str, user_id: str) -> bool:
        role = self.db.get_member_role(team_id, user_id)
        if role is None:
            raise ValueError("你不是该团队成员")
        if role == TeamRole.OWNER:
            members = self.db.get_team_members(team_id)
            if len(members) > 1:
                raise ValueError("团队还有其他成员，请先转让所有权或移除其他成员")
            return self.db.delete_team(team_id)
        return self.db.remove_member(team_id, user_id)

    # ========================================================================
    # Invites
    # ========================================================================

    def create_invite(self, team_id: str, inviter_id: str, invitee_email: str,
                      expires_hours: int = 72) -> TeamInvite:
        if not self._check_permission(team_id, inviter_id, TeamRole.ADMIN):
            raise PermissionError("需要管理员权限才能邀请成员")
        return self.db.create_invite(team_id, inviter_id, invitee_email, expires_hours)

    def accept_invite(self, token: str, user_id: str) -> TeamInvite:
        invite = self.db.accept_invite(token, user_id)
        if invite is None:
            raise ValueError("邀请无效、已过期或已被使用")
        return invite

    def list_team_invites(self, team_id: str, user_id: str) -> List[TeamInvite]:
        if not self._check_permission(team_id, user_id, TeamRole.ADMIN):
            raise PermissionError("需要管理员权限才能查看邀请")
        return self.db.list_team_invites(team_id)

    # ========================================================================
    # Shared Sessions
    # ========================================================================

    def share_session(self, session_id: str, team_id: str, shared_by: str,
                      title: str = None) -> SharedSession:
        if not self._check_permission(team_id, shared_by, TeamRole.MEMBER):
            raise PermissionError("需要成员权限才能共享会话")
        return self.db.share_session(session_id, team_id, shared_by, title)

    def unshare_session(self, share_id: str, team_id: str, user_id: str) -> bool:
        if not self._check_permission(team_id, user_id, TeamRole.MEMBER):
            raise PermissionError("需要成员权限才能取消共享")
        return self.db.unshare_session(share_id)

    def get_team_sessions(self, team_id: str, user_id: str) -> List[SharedSession]:
        if not self._check_permission(team_id, user_id, TeamRole.VIEWER):
            raise PermissionError("无权查看团队会话")
        return self.db.get_team_sessions(team_id)

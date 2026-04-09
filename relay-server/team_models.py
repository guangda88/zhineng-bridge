#!/usr/bin/env python3
"""
团队协作 - 数据模型

包含团队、团队成员、共享会话相关的数据模型。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class TeamRole(Enum):
    """团队角色"""

    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class TeamStatus(Enum):
    """团队状态"""

    ACTIVE = "active"
    ARCHIVED = "archived"


class InviteStatus(Enum):
    """邀请状态"""

    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"


@dataclass
class Team:
    """团队模型"""

    team_id: str
    name: str
    description: Optional[str] = None
    owner_id: str = ""
    status: TeamStatus = TeamStatus.ACTIVE
    settings: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "team_id": self.team_id,
            "name": self.name,
            "description": self.description,
            "owner_id": self.owner_id,
            "status": self.status.value,
            "settings": self.settings,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class TeamMember:
    """团队成员模型"""

    membership_id: str
    team_id: str
    user_id: str
    role: TeamRole = TeamRole.MEMBER
    joined_at: datetime = field(default_factory=datetime.now)
    invited_by: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "membership_id": self.membership_id,
            "team_id": self.team_id,
            "user_id": self.user_id,
            "role": self.role.value,
            "joined_at": self.joined_at.isoformat(),
            "invited_by": self.invited_by,
        }


@dataclass
class TeamInvite:
    """团队邀请模型"""

    invite_id: str
    team_id: str
    inviter_id: str
    invitee_email: str
    token: str
    status: InviteStatus = InviteStatus.PENDING
    expires_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    accepted_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "invite_id": self.invite_id,
            "team_id": self.team_id,
            "inviter_id": self.inviter_id,
            "invitee_email": self.invitee_email,
            "status": self.status.value,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class SharedSession:
    """共享会话模型"""

    share_id: str
    session_id: str
    team_id: str
    shared_by: str
    title: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "share_id": self.share_id,
            "session_id": self.session_id,
            "team_id": self.team_id,
            "shared_by": self.shared_by,
            "title": self.title,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
        }

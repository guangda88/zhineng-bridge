#!/usr/bin/env python3
"""
团队协作 - 数据库操作

提供团队、成员、邀请、共享会话的数据库操作。
"""

import uuid
import json
from typing import Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass

from logger import get_logger
from auth_db import UserDatabase
from team_models import Team, TeamMember, TeamInvite, SharedSession, TeamRole, TeamStatus, InviteStatus


class TeamDatabase:
    """团队数据库操作"""

    def __init__(self, user_db: UserDatabase):
        self.logger = get_logger(__name__)
        self._pool = user_db._pool
        self._init_tables()

    def _init_tables(self):
        with self._pool.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS teams (
                    team_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    owner_id TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    settings TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (owner_id) REFERENCES users (user_id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS team_members (
                    membership_id TEXT PRIMARY KEY,
                    team_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'member',
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    invited_by TEXT,
                    UNIQUE(team_id, user_id),
                    FOREIGN KEY (team_id) REFERENCES teams (team_id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS team_invites (
                    invite_id TEXT PRIMARY KEY,
                    team_id TEXT NOT NULL,
                    inviter_id TEXT NOT NULL,
                    invitee_email TEXT NOT NULL,
                    token TEXT UNIQUE NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    accepted_at TIMESTAMP,
                    FOREIGN KEY (team_id) REFERENCES teams (team_id) ON DELETE CASCADE,
                    FOREIGN KEY (inviter_id) REFERENCES users (user_id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS shared_sessions (
                    share_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    team_id TEXT NOT NULL,
                    shared_by TEXT NOT NULL,
                    title TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (team_id) REFERENCES teams (team_id) ON DELETE CASCADE,
                    FOREIGN KEY (shared_by) REFERENCES users (user_id)
                )
            """)

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_team_members_team ON team_members(team_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_team_members_user ON team_members(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_team_invites_team ON team_invites(team_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_team_invites_token ON team_invites(token)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_shared_sessions_team ON shared_sessions(team_id)")

            conn.commit()
            self.logger.info("Team database tables initialized")

    # ========================================================================
    # Team CRUD
    # ========================================================================

    def create_team(self, name: str, owner_id: str, description: str = None) -> Team:
        team_id = str(uuid.uuid4())
        now = datetime.now()

        with self._pool.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO teams (team_id, name, description, owner_id, status, settings, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'active', '{}', ?, ?)
            """, (team_id, name, description, owner_id, now.isoformat(), now.isoformat()))

            membership_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO team_members (membership_id, team_id, user_id, role, joined_at, invited_by)
                VALUES (?, ?, ?, 'owner', ?, NULL)
            """, (membership_id, team_id, owner_id, now.isoformat()))

            conn.commit()

        self.logger.info("Team created", team_id=team_id, name=name, owner_id=owner_id)
        return Team(
            team_id=team_id, name=name, description=description,
            owner_id=owner_id, status=TeamStatus.ACTIVE,
            created_at=now, updated_at=now,
        )

    def get_team(self, team_id: str) -> Optional[Team]:
        with self._pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM teams WHERE team_id = ?", (team_id,))
            row = cursor.fetchone()
            if not row:
                return None

        return Team(
            team_id=row["team_id"],
            name=row["name"],
            description=row["description"],
            owner_id=row["owner_id"],
            status=TeamStatus(row["status"]),
            settings=json.loads(row["settings"]) if row["settings"] else {},
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def update_team(self, team_id: str, **kwargs) -> Optional[Team]:
        allowed = {"name", "description", "status", "settings"}
        fields = []
        values = []
        for k, v in kwargs.items():
            if k in allowed:
                if k == "settings":
                    v = json.dumps(v)
                if isinstance(v, TeamStatus):
                    v = v.value
                fields.append(f"{k} = ?")
                values.append(v)

        if not fields:
            return self.get_team(team_id)

        fields.append("updated_at = ?")
        values.append(datetime.now().isoformat())
        values.append(team_id)

        with self._pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE teams SET {', '.join(fields)} WHERE team_id = ?", values)
            conn.commit()

        return self.get_team(team_id)

    def delete_team(self, team_id: str) -> bool:
        with self._pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM teams WHERE team_id = ?", (team_id,))
            conn.commit()
            return cursor.rowcount > 0

    def list_user_teams(self, user_id: str) -> List[Team]:
        with self._pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT t.* FROM teams t
                JOIN team_members tm ON t.team_id = tm.team_id
                WHERE tm.user_id = ? AND t.status = 'active'
                ORDER BY t.updated_at DESC
            """, (user_id,))
            rows = cursor.fetchall()

        teams = []
        for row in rows:
            teams.append(Team(
                team_id=row["team_id"],
                name=row["name"],
                description=row["description"],
                owner_id=row["owner_id"],
                status=TeamStatus(row["status"]),
                settings=json.loads(row["settings"]) if row["settings"] else {},
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            ))
        return teams

    # ========================================================================
    # Members
    # ========================================================================

    def add_member(self, team_id: str, user_id: str, role: TeamRole = TeamRole.MEMBER, invited_by: str = None) -> TeamMember:
        membership_id = str(uuid.uuid4())
        now = datetime.now()

        with self._pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO team_members (membership_id, team_id, user_id, role, joined_at, invited_by)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (membership_id, team_id, user_id, role.value, now.isoformat(), invited_by))
            conn.commit()

        return TeamMember(
            membership_id=membership_id, team_id=team_id,
            user_id=user_id, role=role, joined_at=now, invited_by=invited_by,
        )

    def remove_member(self, team_id: str, user_id: str) -> bool:
        with self._pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM team_members WHERE team_id = ? AND user_id = ?", (team_id, user_id))
            conn.commit()
            return cursor.rowcount > 0

    def update_member_role(self, team_id: str, user_id: str, role: TeamRole) -> bool:
        with self._pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE team_members SET role = ? WHERE team_id = ? AND user_id = ?",
                           (role.value, team_id, user_id))
            conn.commit()
            return cursor.rowcount > 0

    def get_team_members(self, team_id: str) -> List[TeamMember]:
        with self._pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM team_members WHERE team_id = ? ORDER BY joined_at", (team_id,))
            rows = cursor.fetchall()

        return [
            TeamMember(
                membership_id=row["membership_id"],
                team_id=row["team_id"],
                user_id=row["user_id"],
                role=TeamRole(row["role"]),
                joined_at=datetime.fromisoformat(row["joined_at"]),
                invited_by=row["invited_by"],
            )
            for row in rows
        ]

    def get_member_role(self, team_id: str, user_id: str) -> Optional[TeamRole]:
        with self._pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT role FROM team_members WHERE team_id = ? AND user_id = ?",
                           (team_id, user_id))
            row = cursor.fetchone()
            if not row:
                return None
            return TeamRole(row["role"])

    # ========================================================================
    # Invites
    # ========================================================================

    def create_invite(self, team_id: str, inviter_id: str, invitee_email: str,
                      expires_hours: int = 72) -> TeamInvite:
        import secrets
        invite_id = str(uuid.uuid4())
        token = secrets.token_urlsafe(32)
        now = datetime.now()
        expires_at = now + timedelta(hours=expires_hours)

        with self._pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO team_invites (invite_id, team_id, inviter_id, invitee_email, token, status, expires_at, created_at)
                VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)
            """, (invite_id, team_id, inviter_id, invitee_email, token, expires_at.isoformat(), now.isoformat()))
            conn.commit()

        return TeamInvite(
            invite_id=invite_id, team_id=team_id, inviter_id=inviter_id,
            invitee_email=invitee_email, token=token, status=InviteStatus.PENDING,
            expires_at=expires_at, created_at=now,
        )

    def get_invite_by_token(self, token: str) -> Optional[TeamInvite]:
        with self._pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM team_invites WHERE token = ?", (token,))
            row = cursor.fetchone()
            if not row:
                return None

        return TeamInvite(
            invite_id=row["invite_id"],
            team_id=row["team_id"],
            inviter_id=row["inviter_id"],
            invitee_email=row["invitee_email"],
            token=row["token"],
            status=InviteStatus(row["status"]),
            expires_at=datetime.fromisoformat(row["expires_at"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            accepted_at=datetime.fromisoformat(row["accepted_at"]) if row["accepted_at"] else None,
        )

    def accept_invite(self, token: str, user_id: str) -> Optional[TeamInvite]:
        invite = self.get_invite_by_token(token)
        if not invite:
            return None
        if invite.status != InviteStatus.PENDING:
            return None
        if invite.expires_at and datetime.now() > invite.expires_at:
            with self._pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE team_invites SET status = 'expired' WHERE token = ?", (token,))
                conn.commit()
            return None

        now = datetime.now()
        with self._pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE team_invites SET status = 'accepted', accepted_at = ? WHERE token = ?",
                           (now.isoformat(), token))
            membership_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT OR IGNORE INTO team_members (membership_id, team_id, user_id, role, joined_at, invited_by)
                VALUES (?, ?, ?, 'member', ?, ?)
            """, (membership_id, invite.team_id, user_id, now.isoformat(), invite.inviter_id))
            conn.commit()

        invite.status = InviteStatus.ACCEPTED
        invite.accepted_at = now
        return invite

    def list_team_invites(self, team_id: str) -> List[TeamInvite]:
        with self._pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM team_invites WHERE team_id = ? ORDER BY created_at DESC", (team_id,))
            rows = cursor.fetchall()

        return [
            TeamInvite(
                invite_id=row["invite_id"],
                team_id=row["team_id"],
                inviter_id=row["inviter_id"],
                invitee_email=row["invitee_email"],
                token=row["token"],
                status=InviteStatus(row["status"]),
                expires_at=datetime.fromisoformat(row["expires_at"]),
                created_at=datetime.fromisoformat(row["created_at"]),
                accepted_at=datetime.fromisoformat(row["accepted_at"]) if row["accepted_at"] else None,
            )
            for row in rows
        ]

    def cleanup_expired_invites(self) -> int:
        with self._pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE team_invites SET status = 'expired'
                WHERE status = 'pending' AND expires_at < ?
            """, (datetime.now().isoformat(),))
            conn.commit()
            return cursor.rowcount

    # ========================================================================
    # Shared Sessions
    # ========================================================================

    def share_session(self, session_id: str, team_id: str, shared_by: str, title: str = None) -> SharedSession:
        share_id = str(uuid.uuid4())
        now = datetime.now()

        with self._pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO shared_sessions (share_id, session_id, team_id, shared_by, title, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, TRUE, ?)
            """, (share_id, session_id, team_id, shared_by, title, now.isoformat()))
            conn.commit()

        return SharedSession(
            share_id=share_id, session_id=session_id, team_id=team_id,
            shared_by=shared_by, title=title, is_active=True, created_at=now,
        )

    def unshare_session(self, share_id: str) -> bool:
        with self._pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE shared_sessions SET is_active = FALSE WHERE share_id = ?", (share_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_team_sessions(self, team_id: str, active_only: bool = True) -> List[SharedSession]:
        query = "SELECT * FROM shared_sessions WHERE team_id = ?"
        params: list = [team_id]
        if active_only:
            query += " AND is_active = TRUE"
        query += " ORDER BY created_at DESC"

        with self._pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

        return [
            SharedSession(
                share_id=row["share_id"],
                session_id=row["session_id"],
                team_id=row["team_id"],
                shared_by=row["shared_by"],
                title=row["title"],
                is_active=bool(row["is_active"]),
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]

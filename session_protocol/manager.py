"""
FamilySessionManager — 灵族全族会话管理器

SQLite后端，管理全族12成员的会话元数据。
各成员的上下文数据仍保存在本地，此管理器只负责：
  - 注册/发现成员
  - 会话元数据持久化
  - 快照索引与查询
  - 跨成员快照共享
"""

import json
import logging
import os
import sqlite3
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from .protocol import (
    CompressionStrategy,
    ContextBudget,
    SessionProtocol,
    SessionSnapshot,
    SessionStatus,
)

logger = logging.getLogger("zhineng-bridge.session_protocol")

DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS members (
    member_id   TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    description TEXT DEFAULT '',
    run_mode    TEXT DEFAULT 'cli',
    status      TEXT DEFAULT 'active',
    registered_at TEXT NOT NULL,
    last_heartbeat TEXT
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id  TEXT PRIMARY KEY,
    member_id   TEXT NOT NULL,
    status      TEXT DEFAULT 'created',
    tool_name   TEXT DEFAULT '',
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL,
    metadata    TEXT DEFAULT '{}',
    FOREIGN KEY (member_id) REFERENCES members(member_id)
);

CREATE TABLE IF NOT EXISTS snapshots (
    snapshot_id TEXT PRIMARY KEY,
    session_id  TEXT NOT NULL,
    member_id   TEXT NOT NULL,
    status      TEXT DEFAULT 'active',
    budget_json TEXT DEFAULT '{}',
    context_json TEXT DEFAULT '{}',
    metadata_json TEXT DEFAULT '{}',
    created_at  TEXT NOT NULL,
    parent_snapshot_id TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id),
    FOREIGN KEY (member_id) REFERENCES members(member_id)
);

CREATE INDEX IF NOT EXISTS idx_sessions_member ON sessions(member_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_session ON snapshots(session_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_member ON snapshots(member_id);
"""

MEMBER_REGISTRY = {
    "ZhiBridge":      {"name": "智桥",   "run_mode": "daemon"},
    "lingflow":       {"name": "灵通",   "run_mode": "web"},
    "lingclaude":     {"name": "灵克",   "run_mode": "cli"},
    "lingresearch":   {"name": "灵研",   "run_mode": "cli"},
    "lingzhi":        {"name": "灵知",   "run_mode": "daemon"},
    "lingtongask":    {"name": "灵通问道", "run_mode": "daemon"},
    "lingflow_plus":  {"name": "灵通+",  "run_mode": "daemon"},
    "lingxi":         {"name": "灵犀",   "run_mode": "daemon"},
    "lingmessage":    {"name": "灵信",   "run_mode": "daemon"},
    "lingweb":        {"name": "灵网",   "run_mode": "web"},
    "lingminopt":     {"name": "灵极优", "run_mode": "cli"},
    "lingyang":       {"name": "灵扬",   "run_mode": "cli"},
}


class FamilySessionManager:
    """全族会话管理器 — SQLite持久化，管理12成员会话元数据"""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_dir = os.path.join(os.path.expanduser("~"), ".zhineng-bridge")
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, "family_sessions.db")

        self.db_path = db_path
        self._local_protocols: Dict[str, SessionProtocol] = {}
        self._init_db()
        self._register_known_members()
        logger.info(f"[FamilySessionManager] 初始化完成: {db_path}")

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.executescript(DB_SCHEMA)
        conn.commit()
        conn.close()

    def _register_known_members(self):
        conn = sqlite3.connect(self.db_path)
        for mid, info in MEMBER_REGISTRY.items():
            existing = conn.execute(
                "SELECT member_id FROM members WHERE member_id = ?", (mid,)
            ).fetchone()
            if not existing:
                conn.execute(
                    "INSERT INTO members (member_id, name, description, run_mode, status, registered_at) "
                    "VALUES (?, ?, '', ?, 'active', ?)",
                    (mid, info["name"], info["run_mode"], datetime.now().isoformat()),
                )
        conn.commit()
        conn.close()

    def register_protocol(self, member_id: str, protocol: SessionProtocol):
        self._local_protocols[member_id] = protocol
        logger.info(f"[FamilySessionManager] 注册协议: {member_id}")

    # ---- 成员管理 ----

    def list_members(self) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(
            "SELECT member_id, name, run_mode, status, registered_at, last_heartbeat "
            "FROM members"
        ).fetchall()
        conn.close()
        return [
            {
                "member_id": r[0], "name": r[1], "run_mode": r[2],
                "status": r[3], "registered_at": r[4], "last_heartbeat": r[5],
            }
            for r in rows
        ]

    def get_member(self, member_id: str) -> Optional[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT member_id, name, run_mode, status, registered_at, last_heartbeat "
            "FROM members WHERE member_id = ?", (member_id,)
        ).fetchone()
        conn.close()
        if not row:
            return None
        return {
            "member_id": row[0], "name": row[1], "run_mode": row[2],
            "status": row[3], "registered_at": row[4], "last_heartbeat": row[5],
        }

    def update_heartbeat(self, member_id: str):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "UPDATE members SET last_heartbeat = ? WHERE member_id = ?",
            (datetime.now().isoformat(), member_id),
        )
        conn.commit()
        conn.close()

    # ---- 会话管理 ----

    def create_session(self, member_id: str, tool_name: str = "",
                       session_id: Optional[str] = None) -> str:
        sid = session_id or str(uuid.uuid4())
        now = datetime.now().isoformat()
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO sessions (session_id, member_id, status, tool_name, created_at, updated_at, metadata) "
            "VALUES (?, ?, 'created', ?, ?, ?, '{}')",
            (sid, member_id, tool_name, now, now),
        )
        conn.commit()
        conn.close()
        logger.info(f"[FamilySessionManager] 创建会话: {sid[:8]} ({member_id})")
        return sid

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT session_id, member_id, status, tool_name, created_at, updated_at, metadata "
            "FROM sessions WHERE session_id = ?", (session_id,)
        ).fetchone()
        conn.close()
        if not row:
            return None
        return {
            "session_id": row[0], "member_id": row[1], "status": row[2],
            "tool_name": row[3], "created_at": row[4], "updated_at": row[5],
            "metadata": json.loads(row[6]) if row[6] else {},
        }

    def list_sessions(self, member_id: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        if member_id:
            rows = conn.execute(
                "SELECT session_id, member_id, status, tool_name, created_at, updated_at "
                "FROM sessions WHERE member_id = ? ORDER BY updated_at DESC",
                (member_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT session_id, member_id, status, tool_name, created_at, updated_at "
                "FROM sessions ORDER BY updated_at DESC"
            ).fetchall()
        conn.close()
        return [
            {
                "session_id": r[0], "member_id": r[1], "status": r[2],
                "tool_name": r[3], "created_at": r[4], "updated_at": r[5],
            }
            for r in rows
        ]

    def update_session_status(self, session_id: str, status: str):
        now = datetime.now().isoformat()
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "UPDATE sessions SET status = ?, updated_at = ? WHERE session_id = ?",
            (status, now, session_id),
        )
        conn.commit()
        conn.close()

    def delete_session(self, session_id: str):
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM snapshots WHERE session_id = ?", (session_id,))
        conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        conn.commit()
        conn.close()

    # ---- 快照管理 ----

    def save_snapshot(self, snapshot: SessionSnapshot) -> str:
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO snapshots "
            "(snapshot_id, session_id, member_id, status, budget_json, context_json, "
            " metadata_json, created_at, parent_snapshot_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                snapshot.snapshot_id,
                snapshot.session_id,
                snapshot.member_id,
                snapshot.status.value,
                json.dumps(snapshot.budget.to_dict(), ensure_ascii=False),
                json.dumps(snapshot.context_data, ensure_ascii=False),
                json.dumps(snapshot.metadata, ensure_ascii=False),
                snapshot.created_at,
                snapshot.parent_snapshot_id,
            ),
        )
        conn.commit()
        conn.close()
        logger.info(f"[FamilySessionManager] 快照保存: {snapshot.snapshot_id[:8]} ({snapshot.member_id})")
        return snapshot.snapshot_id

    def get_snapshot(self, snapshot_id: str) -> Optional[SessionSnapshot]:
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT snapshot_id, session_id, member_id, status, budget_json, context_json, "
            "metadata_json, created_at, parent_snapshot_id "
            "FROM snapshots WHERE snapshot_id = ?", (snapshot_id,)
        ).fetchone()
        conn.close()
        if not row:
            return None
        return self._row_to_snapshot(row)

    def list_snapshots(self, member_id: Optional[str] = None,
                       session_id: Optional[str] = None,
                       limit: int = 50) -> List[SessionSnapshot]:
        conn = sqlite3.connect(self.db_path)
        query = (
            "SELECT snapshot_id, session_id, member_id, status, budget_json, context_json, "
            "metadata_json, created_at, parent_snapshot_id FROM snapshots WHERE 1=1"
        )
        params: list = []
        if member_id:
            query += " AND member_id = ?"
            params.append(member_id)
        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(query, params).fetchall()
        conn.close()
        return [self._row_to_snapshot(r) for r in rows]

    def get_latest_snapshot(self, member_id: str, session_id: Optional[str] = None) -> Optional[SessionSnapshot]:
        snaps = self.list_snapshots(member_id=member_id, session_id=session_id, limit=1)
        return snaps[0] if snaps else None

    def _row_to_snapshot(self, row) -> SessionSnapshot:
        budget_data = json.loads(row[4]) if row[4] else {}
        budget = ContextBudget(
            max_tokens=budget_data.get("max_tokens", 32000),
            max_turns=budget_data.get("max_turns", 40),
            current_tokens=budget_data.get("current_tokens", 0),
            current_turns=budget_data.get("current_turns", 0),
            compression_threshold=budget_data.get("compression_threshold", 0.8),
            strategy=CompressionStrategy(budget_data.get("strategy", "truncate")),
        )
        return SessionSnapshot(
            snapshot_id=row[0],
            session_id=row[1],
            member_id=row[2],
            status=SessionStatus(row[3]),
            budget=budget,
            context_data=json.loads(row[5]) if row[5] else {},
            metadata=json.loads(row[6]) if row[6] else {},
            created_at=row[7],
            parent_snapshot_id=row[8],
        )

    # ---- 跨成员操作 ----

    def delegate_save(self, member_id: str, session_id: Optional[str] = None) -> Optional[SessionSnapshot]:
        protocol = self._local_protocols.get(member_id)
        if not protocol:
            logger.warning(f"[FamilySessionManager] 无本地协议: {member_id}")
            return None
        snapshot = protocol.save_context(session_id)
        self.save_snapshot(snapshot)
        self.update_heartbeat(member_id)
        return snapshot

    def delegate_restore(self, member_id: str, session_id: str) -> bool:
        protocol = self._local_protocols.get(member_id)
        if not protocol:
            return False
        result = protocol.restore_context(session_id)
        self.update_heartbeat(member_id)
        return result

    def delegate_compress(self, member_id: str,
                          strategy: Optional[CompressionStrategy] = None) -> Optional[SessionSnapshot]:
        protocol = self._local_protocols.get(member_id)
        if not protocol:
            return None
        snapshot = protocol.compress_context(strategy)
        self.save_snapshot(snapshot)
        return snapshot

    # ---- 全局查询 ----

    def get_family_overview(self) -> Dict[str, Any]:
        conn = sqlite3.connect(self.db_path)
        member_count = conn.execute("SELECT COUNT(*) FROM members").fetchone()[0]
        session_count = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        snapshot_count = conn.execute("SELECT COUNT(*) FROM snapshots").fetchone()[0]
        active_sessions = conn.execute(
            "SELECT COUNT(*) FROM sessions WHERE status IN ('created', 'active')"
        ).fetchone()[0]
        conn.close()
        return {
            "members": member_count,
            "sessions": session_count,
            "active_sessions": active_sessions,
            "snapshots": snapshot_count,
        }

    def get_member_health(self, member_id: str) -> Dict[str, Any]:
        conn = sqlite3.connect(self.db_path)
        session_count = conn.execute(
            "SELECT COUNT(*) FROM sessions WHERE member_id = ?", (member_id,)
        ).fetchone()[0]
        snapshot_count = conn.execute(
            "SELECT COUNT(*) FROM snapshots WHERE member_id = ?", (member_id,)
        ).fetchone()[0]
        last_hb = conn.execute(
            "SELECT last_heartbeat FROM members WHERE member_id = ?", (member_id,)
        ).fetchone()
        conn.close()
        return {
            "member_id": member_id,
            "sessions": session_count,
            "snapshots": snapshot_count,
            "last_heartbeat": last_hb[0] if last_hb else None,
            "protocol_registered": member_id in self._local_protocols,
        }

"""
ZhiBridgeAdapter — 智桥的SessionProtocol实现

智桥(ZhiBridge)作为跨平台通信桥梁，运行模式为daemon。
上下文来源：WebSocket连接状态、LingBus消息队列、relay-server会话。
"""

import json
import os
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


class ZhiBridgeAdapter(SessionProtocol):
    """智桥的会话管理协议实现"""

    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is None:
            data_dir = os.path.join(os.path.expanduser("~"), ".zhineng-bridge", "zhibridge")
        os.makedirs(data_dir, exist_ok=True)
        self.data_dir = data_dir
        self.member_id = "ZhiBridge"
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._budget = ContextBudget(
            max_tokens=32000,
            max_turns=40,
            compression_threshold=0.8,
            strategy=CompressionStrategy.STRUCTURED,
        )
        self._current_session_id: Optional[str] = None
        self._context_log: List[Dict[str, Any]] = []

    def _context_file(self, session_id: str) -> str:
        return os.path.join(self.data_dir, f"{session_id}.json")

    def _ensure_session(self, session_id: Optional[str] = None) -> str:
        if session_id is None:
            session_id = self._current_session_id or str(uuid.uuid4())
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "session_id": session_id,
                "member_id": self.member_id,
                "status": "created",
                "created_at": datetime.now().isoformat(),
                "turns": 0,
                "tokens": 0,
            }
            self._current_session_id = session_id
        return session_id

    def save_context(self, session_id: Optional[str] = None) -> SessionSnapshot:
        sid = self._ensure_session(session_id)
        session = self._sessions[sid]
        session["status"] = "active"
        session["updated_at"] = datetime.now().isoformat()

        budget = ContextBudget(
            max_tokens=self._budget.max_tokens,
            max_turns=self._budget.max_turns,
            current_tokens=session.get("tokens", 0),
            current_turns=session.get("turns", 0),
            compression_threshold=self._budget.compression_threshold,
            strategy=self._budget.strategy,
        )

        context_data = {
            "session": session,
            "context_log": self._context_log[-100:],
            "websocket_connections": self._count_ws_connections(),
        }

        snapshot = SessionSnapshot(
            member_id=self.member_id,
            session_id=sid,
            status=SessionStatus.ACTIVE,
            budget=budget,
            context_data=context_data,
            metadata={"source": "ZhiBridgeAdapter"},
        )

        filepath = self._context_file(sid)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(snapshot.to_json())

        return snapshot

    def restore_context(self, session_id: str) -> bool:
        filepath = self._context_file(session_id)
        if not os.path.exists(filepath):
            return False
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            snapshot = SessionSnapshot.from_dict(data)
            self._sessions[session_id] = snapshot.context_data.get("session", {})
            self._context_log = snapshot.context_data.get("context_log", [])
            self._current_session_id = session_id
            self._budget = snapshot.budget
            return True
        except Exception:
            return False

    def get_budget(self) -> ContextBudget:
        sid = self._current_session_id
        if sid and sid in self._sessions:
            session = self._sessions[sid]
            self._budget.current_tokens = session.get("tokens", 0)
            self._budget.current_turns = session.get("turns", 0)
        return self._budget

    def compress_context(self, strategy: Optional[CompressionStrategy] = None) -> SessionSnapshot:
        strat = strategy or self._budget.strategy
        sid = self._ensure_session(self._current_session_id)

        if strat == CompressionStrategy.TRUNCATE:
            self._context_log = self._context_log[-20:]
            if sid in self._sessions:
                self._sessions[sid]["tokens"] = int(self._budget.max_tokens * 0.5)
        elif strat == CompressionStrategy.SUMMARIZE:
            self._context_log = [{"summary": True, "compressed_from": len(self._context_log), "at": datetime.now().isoformat()}]
            if sid in self._sessions:
                self._sessions[sid]["tokens"] = int(self._budget.max_tokens * 0.3)
        elif strat == CompressionStrategy.STRUCTURED:
            structured = []
            for entry in self._context_log:
                structured.append({"type": entry.get("type", "unknown"), "ts": entry.get("ts", "")})
            self._context_log = structured[-30:]
            if sid in self._sessions:
                self._sessions[sid]["tokens"] = int(self._budget.max_tokens * 0.4)

        snapshot = self.save_snapshot()
        return snapshot

    def save_snapshot(self) -> SessionSnapshot:
        return self.save_context(self._current_session_id)

    def validate_integrity(self, snapshot: SessionSnapshot) -> bool:
        if not snapshot.snapshot_id:
            return False
        if not snapshot.member_id:
            return False
        if not snapshot.session_id:
            return False
        if snapshot.member_id != self.member_id:
            return False
        budget = snapshot.budget
        if budget.current_tokens > budget.max_tokens * 2:
            return False
        return True

    def export_snapshot(self, session_id: Optional[str] = None) -> str:
        snapshot = self.save_context(session_id)
        return snapshot.to_json()

    def import_snapshot(self, json_data: str) -> SessionSnapshot:
        snapshot = SessionSnapshot.from_json(json_data)
        self._sessions[snapshot.session_id] = snapshot.context_data.get("session", {})
        self._context_log = snapshot.context_data.get("context_log", [])
        self._current_session_id = snapshot.session_id
        self._budget = snapshot.budget

        filepath = self._context_file(snapshot.session_id)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(snapshot.to_json())
        return snapshot

    def health_check(self) -> Dict[str, Any]:
        budget = self.get_budget()
        active_sessions = sum(1 for s in self._sessions.values() if s.get("status") == "active")
        return {
            "member_id": self.member_id,
            "status": "healthy",
            "active_sessions": active_sessions,
            "total_sessions": len(self._sessions),
            "context_log_size": len(self._context_log),
            "budget": budget.to_dict(),
            "data_dir": self.data_dir,
            "timestamp": datetime.now().isoformat(),
        }

    def add_context_entry(self, entry_type: str, data: Dict[str, Any], tokens: int = 0):
        self._ensure_session()
        entry = {
            "type": entry_type,
            "data": data,
            "ts": datetime.now().isoformat(),
            "tokens": tokens,
        }
        self._context_log.append(entry)
        if self._current_session_id and self._current_session_id in self._sessions:
            self._sessions[self._current_session_id]["turns"] = self._sessions[self._current_session_id].get("turns", 0) + 1
            self._sessions[self._current_session_id]["tokens"] = self._sessions[self._current_session_id].get("tokens", 0) + tokens

    def _count_ws_connections(self) -> int:
        return 0

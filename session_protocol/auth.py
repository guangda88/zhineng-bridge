"""
AuthorizationManager — Layer 1 跨成员操作授权

默认拒绝 + 显式允许模式:
  - 自身访问：成员始终可操作自己的数据
  - 跨成员操作：需要明确的权限授予记录
  - 审计日志：所有跨成员操作均被记录
"""

import json
import logging
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger("zhineng-bridge.session_protocol.auth")

AUTH_SCHEMA = """
CREATE TABLE IF NOT EXISTS permissions (
    caller_id   TEXT NOT NULL,
    target_id   TEXT NOT NULL,
    operation   TEXT NOT NULL,
    granted_by  TEXT NOT NULL,
    granted_at  TEXT NOT NULL,
    PRIMARY KEY (caller_id, target_id, operation)
);

CREATE TABLE IF NOT EXISTS audit_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT NOT NULL,
    caller_id   TEXT NOT NULL,
    target_id   TEXT NOT NULL,
    operation   TEXT NOT NULL,
    result      TEXT NOT NULL,
    details     TEXT DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_audit_caller ON audit_log(caller_id);
CREATE INDEX IF NOT EXISTS idx_audit_target ON audit_log(target_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);
"""


class AuthorizationError(Exception):
    """跨成员操作未授权时抛出"""
    pass


class AuthorizationManager:
    """跨成员操作授权管理器 — 默认拒绝，显式允许"""

    VALID_OPERATIONS = {"read", "write", "delete", "delegate_save",
                        "delegate_restore", "delegate_compress"}

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_tables()

    def _init_tables(self):
        conn = sqlite3.connect(self.db_path)
        conn.executescript(AUTH_SCHEMA)
        conn.commit()
        conn.close()

    SYSTEM_CALLER = "system"

    def check_permission(self, caller_id: str, target_id: str,
                         operation: str) -> bool:
        if caller_id == self.SYSTEM_CALLER:
            logger.warning(
                f"[Auth] system caller bypasses auth check: "
                f"target={target_id} op={operation}"
            )
            return True
        if caller_id == target_id:
            return True
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT 1 FROM permissions "
            "WHERE caller_id = ? AND target_id = ? AND operation = ?",
            (caller_id, target_id, operation),
        ).fetchone()
        conn.close()
        return row is not None

    def require_permission(self, caller_id: str, target_id: str,
                           operation: str) -> None:
        if caller_id == target_id:
            self.log_audit(caller_id, target_id, operation, "allowed",
                           {"reason": "self_access"})
            return
        if self.check_permission(caller_id, target_id, operation):
            self.log_audit(caller_id, target_id, operation, "allowed",
                           {"reason": "permission_granted"})
            return
        self.log_audit(caller_id, target_id, operation, "denied",
                       {"reason": "no_permission"})
        raise AuthorizationError(
            f"{caller_id} 没有对 {target_id} 的 {operation} 权限"
        )

    def grant_permission(self, caller_id: str, target_id: str,
                         operation: str, granted_by: str) -> None:
        if operation not in self.VALID_OPERATIONS:
            raise ValueError(f"无效操作类型: {operation}")
        now = datetime.now().isoformat()
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT OR REPLACE INTO permissions "
            "(caller_id, target_id, operation, granted_by, granted_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (caller_id, target_id, operation, granted_by, now),
        )
        conn.commit()
        conn.close()
        self.log_audit(granted_by, target_id, operation, "granted",
                       {"caller_id": caller_id})
        logger.info(
            f"[Auth] 权限授予: {caller_id} -> {target_id} ({operation}) "
            f"by {granted_by}"
        )

    def revoke_permission(self, caller_id: str, target_id: str,
                          operation: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "DELETE FROM permissions "
            "WHERE caller_id = ? AND target_id = ? AND operation = ?",
            (caller_id, target_id, operation),
        )
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        if deleted:
            self.log_audit(caller_id, target_id, operation, "revoked", {})
            logger.info(
                f"[Auth] 权限撤销: {caller_id} -> {target_id} ({operation})"
            )
        return deleted

    def list_permissions(self, caller_id: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        if caller_id:
            rows = conn.execute(
                "SELECT caller_id, target_id, operation, granted_by, granted_at "
                "FROM permissions WHERE caller_id = ?",
                (caller_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT caller_id, target_id, operation, granted_by, granted_at "
                "FROM permissions"
            ).fetchall()
        conn.close()
        return [
            {
                "caller_id": r[0], "target_id": r[1], "operation": r[2],
                "granted_by": r[3], "granted_at": r[4],
            }
            for r in rows
        ]

    def log_audit(self, caller_id: str, target_id: str, operation: str,
                  result: str, details: Optional[Dict[str, Any]] = None) -> None:
        now = datetime.now().isoformat()
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO audit_log (timestamp, caller_id, target_id, operation, result, details) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (now, caller_id, target_id, operation, result,
             json.dumps(details or {}, ensure_ascii=False)),
        )
        conn.commit()
        conn.close()

    def get_audit_log(self, caller_id: Optional[str] = None,
                      target_id: Optional[str] = None,
                      limit: int = 100) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        query = (
            "SELECT id, timestamp, caller_id, target_id, operation, result, details "
            "FROM audit_log WHERE 1=1"
        )
        params: list = []
        if caller_id:
            query += " AND caller_id = ?"
            params.append(caller_id)
        if target_id:
            query += " AND target_id = ?"
            params.append(target_id)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(query, params).fetchall()
        conn.close()
        return [
            {
                "id": r[0], "timestamp": r[1], "caller_id": r[2],
                "target_id": r[3], "operation": r[4], "result": r[5],
                "details": json.loads(r[6]) if r[6] else {},
            }
            for r in rows
        ]

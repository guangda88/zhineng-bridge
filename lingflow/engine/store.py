"""
FlowStore — SQLite 状态持久化

将工作流运行记录持久化到 SQLite 数据库。
"""

import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

from lingflow.engine.flow import Flow, FlowEdge, FlowNode, FlowStatus, NodeStatus


class FlowStore:
    def __init__(self, db_path: str = "lingflow.db"):
        self._db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self):
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS flow_runs (
                flow_id TEXT PRIMARY KEY,
                name TEXT NOT NULL DEFAULT '',
                description TEXT NOT NULL DEFAULT '',
                version TEXT NOT NULL DEFAULT '1.0.0',
                category TEXT NOT NULL DEFAULT 'general',
                tags TEXT NOT NULL DEFAULT '[]',
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                started_at TEXT,
                finished_at TEXT,
                metadata TEXT NOT NULL DEFAULT '{}',
                results TEXT NOT NULL DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS flow_nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                flow_id TEXT NOT NULL,
                node_id TEXT NOT NULL,
                handler_path TEXT,
                config TEXT NOT NULL DEFAULT '{}',
                status TEXT NOT NULL DEFAULT 'pending',
                error TEXT,
                started_at TEXT,
                finished_at TEXT,
                outputs TEXT NOT NULL DEFAULT '{}',
                FOREIGN KEY (flow_id) REFERENCES flow_runs(flow_id),
                UNIQUE(flow_id, node_id)
            );

            CREATE TABLE IF NOT EXISTS flow_edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                flow_id TEXT NOT NULL,
                from_node TEXT NOT NULL,
                to_node TEXT NOT NULL,
                condition TEXT,
                FOREIGN KEY (flow_id) REFERENCES flow_runs(flow_id)
            );

            CREATE INDEX IF NOT EXISTS idx_flow_runs_status ON flow_runs(status);
            CREATE INDEX IF NOT EXISTS idx_flow_runs_name ON flow_runs(name);
            CREATE INDEX IF NOT EXISTS idx_flow_nodes_flow ON flow_nodes(flow_id);
        """)
        conn.commit()
        conn.close()

    def save_run(self, flow: Flow) -> None:
        conn = self._get_conn()
        try:
            conn.execute(
                """INSERT OR REPLACE INTO flow_runs
                   (flow_id, name, description, version, category, tags,
                    status, created_at, started_at, finished_at, metadata, results)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    flow.flow_id,
                    flow.name,
                    flow.description,
                    flow.version,
                    flow.category,
                    json.dumps(flow.tags, ensure_ascii=False),
                    flow.status.value,
                    flow.created_at.isoformat() if flow.created_at else datetime.now().isoformat(),
                    flow.started_at.isoformat() if flow.started_at else None,
                    flow.finished_at.isoformat() if flow.finished_at else None,
                    json.dumps(flow.metadata, ensure_ascii=False),
                    json.dumps(flow.results, ensure_ascii=False),
                ),
            )

            conn.execute("DELETE FROM flow_nodes WHERE flow_id = ?", (flow.flow_id,))
            for nid, node in flow.nodes.items():
                conn.execute(
                    """INSERT INTO flow_nodes
                       (flow_id, node_id, handler_path, config, status, error,
                        started_at, finished_at, outputs)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        flow.flow_id,
                        nid,
                        node.handler_path,
                        json.dumps(node.config, ensure_ascii=False),
                        node.status.value,
                        node.error,
                        node.started_at.isoformat() if node.started_at else None,
                        node.finished_at.isoformat() if node.finished_at else None,
                        json.dumps(node.outputs, ensure_ascii=False),
                    ),
                )

            conn.execute("DELETE FROM flow_edges WHERE flow_id = ?", (flow.flow_id,))
            for edge in flow.edges:
                conn.execute(
                    """INSERT INTO flow_edges (flow_id, from_node, to_node, condition)
                       VALUES (?, ?, ?, ?)""",
                    (flow.flow_id, edge.from_node, edge.to_node, edge.condition),
                )

            conn.commit()
        finally:
            conn.close()

    def load_run(self, flow_id: str) -> Optional[Flow]:
        conn = self._get_conn()
        try:
            row = conn.execute("SELECT * FROM flow_runs WHERE flow_id = ?", (flow_id,)).fetchone()
            if not row:
                return None

            flow = Flow(
                flow_id=row["flow_id"],
                name=row["name"],
                description=row["description"],
                version=row["version"],
                category=row["category"],
                tags=json.loads(row["tags"]),
                status=FlowStatus(row["status"]),
                created_at=datetime.fromisoformat(row["created_at"]),
                started_at=datetime.fromisoformat(row["started_at"]) if row["started_at"] else None,
                finished_at=(
                    datetime.fromisoformat(row["finished_at"]) if row["finished_at"] else None
                ),
                metadata=json.loads(row["metadata"]),
                results=json.loads(row["results"]),
            )

            for nrow in conn.execute(
                "SELECT * FROM flow_nodes WHERE flow_id = ?", (flow_id,)
            ).fetchall():
                node = FlowNode(
                    node_id=nrow["node_id"],
                    handler_path=nrow["handler_path"],
                    config=json.loads(nrow["config"]),
                    status=NodeStatus(nrow["status"]),
                    error=nrow["error"],
                    started_at=(
                        datetime.fromisoformat(nrow["started_at"]) if nrow["started_at"] else None
                    ),
                    finished_at=(
                        datetime.fromisoformat(nrow["finished_at"]) if nrow["finished_at"] else None
                    ),
                    outputs=json.loads(nrow["outputs"]),
                )
                flow.nodes[node.node_id] = node

            for erow in conn.execute(
                "SELECT * FROM flow_edges WHERE flow_id = ?", (flow_id,)
            ).fetchall():
                flow.edges.append(
                    FlowEdge(
                        from_node=erow["from_node"],
                        to_node=erow["to_node"],
                        condition=erow["condition"],
                    )
                )

            return flow
        finally:
            conn.close()

    def list_runs(
        self,
        status: Optional[FlowStatus] = None,
        name: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        try:
            query = "SELECT flow_id, name, status, category, created_at, started_at, finished_at FROM flow_runs WHERE 1=1"
            params: List[Any] = []

            if status:
                query += " AND status = ?"
                params.append(status.value)
            if name:
                query += " AND name = ?"
                params.append(name)
            if category:
                query += " AND category = ?"
                params.append(category)

            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def delete_run(self, flow_id: str) -> bool:
        conn = self._get_conn()
        try:
            cursor = conn.execute("DELETE FROM flow_runs WHERE flow_id = ?", (flow_id,))
            conn.execute("DELETE FROM flow_nodes WHERE flow_id = ?", (flow_id,))
            conn.execute("DELETE FROM flow_edges WHERE flow_id = ?", (flow_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def cleanup(self, max_age_days: int = 30) -> int:
        conn = self._get_conn()
        try:
            cutoff = datetime.now().isoformat()
            cursor = conn.execute(
                """DELETE FROM flow_runs
                   WHERE finished_at IS NOT NULL
                     AND finished_at < datetime(?, '-' || ? || ' days')""",
                (cutoff, max_age_days),
            )
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()

    def count_runs(self, status: Optional[FlowStatus] = None) -> int:
        conn = self._get_conn()
        try:
            if status:
                row = conn.execute(
                    "SELECT COUNT(*) as cnt FROM flow_runs WHERE status = ?",
                    (status.value,),
                ).fetchone()
            else:
                row = conn.execute("SELECT COUNT(*) as cnt FROM flow_runs").fetchone()
            return row["cnt"] if row else 0
        finally:
            conn.close()

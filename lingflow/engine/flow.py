"""
Flow 数据模型

定义工作流 (Flow)、节点 (FlowNode)、边 (FlowEdge) 的核心数据结构。
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class FlowStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NodeStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class FlowEdge:
    from_node: str
    to_node: str
    condition: Optional[str] = None

    def to_dict(self) -> dict:
        d = {"from": self.from_node, "to": self.to_node}
        if self.condition:
            d["condition"] = self.condition
        return d


@dataclass
class FlowNode:
    node_id: str
    handler: Optional[Callable] = None
    handler_path: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    status: NodeStatus = NodeStatus.PENDING
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "handler_path": self.handler_path,
            "config": self.config,
            "status": self.status.value,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FlowNode":
        return cls(
            node_id=data["node_id"],
            handler_path=data.get("handler_path"),
            config=data.get("config", {}),
            status=NodeStatus(data.get("status", "pending")),
            error=data.get("error"),
        )


@dataclass
class Flow:
    flow_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    nodes: Dict[str, FlowNode] = field(default_factory=dict)
    edges: List[FlowEdge] = field(default_factory=list)
    status: FlowStatus = FlowStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)

    def add_node(self, node: FlowNode) -> "Flow":
        self.nodes[node.node_id] = node
        return self

    def add_edge(self, from_node: str, to_node: str, condition: Optional[str] = None) -> "Flow":
        self.edges.append(FlowEdge(from_node=from_node, to_node=to_node, condition=condition))
        return self

    def get_entry_nodes(self) -> List[str]:
        targets = {e.to_node for e in self.edges}
        return [nid for nid in self.nodes if nid not in targets]

    def get_successors(self, node_id: str) -> List[str]:
        return [e.to_node for e in self.edges if e.from_node == node_id]

    def get_predecessors(self, node_id: str) -> List[str]:
        return [e.from_node for e in self.edges if e.to_node == node_id]

    def validate(self) -> List[str]:
        errors = []
        node_ids = set(self.nodes.keys())

        if not self.nodes:
            errors.append("Flow has no nodes")
            return errors

        for edge in self.edges:
            if edge.from_node not in node_ids:
                errors.append(f"Edge references unknown source node: {edge.from_node}")
            if edge.to_node not in node_ids:
                errors.append(f"Edge references unknown target node: {edge.to_node}")

        visited = set()
        stack = list(self.get_entry_nodes())
        while stack:
            nid = stack.pop()
            if nid in visited:
                errors.append(f"Cycle detected involving node: {nid}")
                continue
            visited.add(nid)
            stack.extend(self.get_successors(nid))

        if not self.get_entry_nodes():
            errors.append("Flow has no entry node (all nodes have predecessors)")

        return errors

    def to_dict(self) -> dict:
        return {
            "flow_id": self.flow_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "category": self.category,
            "tags": self.tags,
            "nodes": {nid: n.to_dict() for nid, n in self.nodes.items()},
            "edges": [e.to_dict() for e in self.edges],
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "results": self.results,
        }

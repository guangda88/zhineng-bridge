"""
Flow Registry — 工作流注册中心

注册、查询、管理工作流模板。
"""

import json
import os
from typing import Dict, List, Optional

from lingflow.engine.flow import Flow


class FlowRegistry:
    def __init__(self, flows_dir: Optional[str] = None):
        self._templates: Dict[str, Flow] = {}
        self._flows_dir = flows_dir

    def register(self, flow: Flow) -> str:
        key = flow.name or flow.flow_id
        if key in self._templates:
            raise ValueError(f"Flow '{key}' already registered")
        errors = flow.validate()
        if errors:
            raise ValueError(f"Invalid flow: {'; '.join(errors)}")
        self._templates[key] = flow
        return key

    def get(self, name: str) -> Optional[Flow]:
        return self._templates.get(name)

    def list_flows(self, category: Optional[str] = None, tag: Optional[str] = None) -> List[Flow]:
        flows = list(self._templates.values())
        if category:
            flows = [f for f in flows if f.category == category]
        if tag:
            flows = [f for f in flows if tag in f.tags]
        return flows

    def unregister(self, name: str) -> bool:
        if name in self._templates:
            del self._templates[name]
            return True
        return False

    def load_from_dir(self, flows_dir: Optional[str] = None) -> int:
        directory = flows_dir or self._flows_dir
        if not directory or not os.path.isdir(directory):
            return 0
        loaded = 0
        for fname in os.listdir(directory):
            if not fname.endswith((".json", ".yaml", ".yml")):
                continue
            fpath = os.path.join(directory, fname)
            try:
                flow = self._load_flow_file(fpath)
                if flow:
                    self.register(flow)
                    loaded += 1
            except Exception:
                continue
        return loaded

    def _load_flow_file(self, path: str) -> Optional[Flow]:
        if path.endswith(".json"):
            return self._load_json(path)
        return None

    def _load_json(self, path: str) -> Optional[Flow]:
        from lingflow.engine.flow import FlowNode, NodeStatus

        with open(path) as f:
            data = json.load(f)

        flow = Flow(
            name=data.get("name", ""),
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            category=data.get("category", "general"),
            tags=data.get("tags", []),
        )
        for nid, ndata in data.get("nodes", {}).items():
            node = FlowNode(
                node_id=nid,
                handler_path=ndata.get("handler_path"),
                config=ndata.get("config", {}),
                status=NodeStatus.PENDING,
            )
            flow.add_node(node)
        for edata in data.get("edges", []):
            flow.add_edge(
                from_node=edata["from"],
                to_node=edata["to"],
                condition=edata.get("condition"),
            )
        return flow

    def count(self) -> int:
        return len(self._templates)

    def categories(self) -> List[str]:
        return sorted({f.category for f in self._templates.values()})

"""
SessionProtocol ABC — 灵族全族会话管理统一协议

8个抽象方法覆盖所有12成员的不同运行模式：
  CLI (Crush, Claude Code)、Web (LingWeb)、Daemon (LingMessage, Ling-term-mcp)

设计原则:
  - 灰度渐进：各成员可选择性实现，不强制全覆盖
  - 兼容现有：session_state.py / context_hygiene.py 的超集
  - 本地自治：各成员保留本地上下文，协议层只管元数据
"""

import json
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class SessionStatus(Enum):
    CREATED = "created"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    COMPRESSED = "compressed"
    ARCHIVED = "archived"
    ERROR = "error"


class CompressionStrategy(Enum):
    NONE = "none"
    TRUNCATE = "truncate"
    SUMMARIZE = "summarize"
    STRUCTURED = "structured"


@dataclass
class ContextBudget:
    """上下文预算 — 控制各成员的上下文使用量"""
    max_tokens: int = 32000
    max_turns: int = 40
    current_tokens: int = 0
    current_turns: int = 0
    compression_threshold: float = 0.8
    strategy: CompressionStrategy = CompressionStrategy.TRUNCATE

    @property
    def usage_ratio(self) -> float:
        if self.max_tokens == 0:
            return 0.0
        return self.current_tokens / self.max_tokens

    @property
    def should_compress(self) -> bool:
        return self.usage_ratio >= self.compression_threshold

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_tokens": self.max_tokens,
            "max_turns": self.max_turns,
            "current_tokens": self.current_tokens,
            "current_turns": self.current_turns,
            "usage_ratio": self.usage_ratio,
            "should_compress": self.should_compress,
            "strategy": self.strategy.value,
        }


@dataclass
class SessionSnapshot:
    """会话快照 — 可序列化的会话状态"""
    snapshot_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    member_id: str = ""
    session_id: str = ""
    status: SessionStatus = SessionStatus.ACTIVE
    budget: ContextBudget = field(default_factory=ContextBudget)
    context_data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    parent_snapshot_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "snapshot_id": self.snapshot_id,
            "member_id": self.member_id,
            "session_id": self.session_id,
            "status": self.status.value,
            "budget": self.budget.to_dict(),
            "context_data": self.context_data,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "parent_snapshot_id": self.parent_snapshot_id,
        }
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionSnapshot":
        if "budget" in data and isinstance(data["budget"], dict):
            strategy = data["budget"].get("strategy", "truncate")
            data["budget"] = ContextBudget(
                max_tokens=data["budget"].get("max_tokens", 32000),
                max_turns=data["budget"].get("max_turns", 40),
                current_tokens=data["budget"].get("current_tokens", 0),
                current_turns=data["budget"].get("current_turns", 0),
                compression_threshold=data["budget"].get("compression_threshold", 0.8),
                strategy=CompressionStrategy(strategy),
            )
        if "status" in data and isinstance(data["status"], str):
            data["status"] = SessionStatus(data["status"])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    @classmethod
    def from_json(cls, json_str: str) -> "SessionSnapshot":
        return cls.from_dict(json.loads(json_str))


class SessionProtocol(ABC):
    """
    会话管理统一协议 — 所有灵族成员必须实现的接口

    8个抽象方法:
      1. save_context()       — 保存当前会话上下文
      2. restore_context()    — 恢复指定会话
      3. get_budget()         — 获取上下文预算
      4. compress_context()   — 压缩上下文
      5. validate_integrity() — 完整性校验
      6. export_snapshot()    — 导出快照
      7. import_snapshot()    — 导入快照
      8. health_check()       — 健康检查
    """

    @abstractmethod
    def save_context(self, session_id: Optional[str] = None) -> SessionSnapshot:
        """保存当前会话上下文，返回快照"""

    @abstractmethod
    def restore_context(self, session_id: str) -> bool:
        """恢复指定会话，成功返回True"""

    @abstractmethod
    def get_budget(self) -> ContextBudget:
        """获取当前上下文预算"""

    @abstractmethod
    def compress_context(self, strategy: Optional[CompressionStrategy] = None) -> SessionSnapshot:
        """压缩上下文，返回压缩后的快照"""

    @abstractmethod
    def validate_integrity(self, snapshot: SessionSnapshot) -> bool:
        """校验快照完整性"""

    @abstractmethod
    def export_snapshot(self, session_id: Optional[str] = None) -> str:
        """导出快照为JSON字符串"""

    @abstractmethod
    def import_snapshot(self, json_data: str) -> SessionSnapshot:
        """从JSON字符串导入快照"""

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """返回健康状态"""

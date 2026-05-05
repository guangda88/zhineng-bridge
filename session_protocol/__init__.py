"""
SessionProtocol — 灵族全族会话管理协议

统一12成员的会话上下文管理，支持自觉+结构双轨制。

架构:
  SessionProtocol (ABC)          — 统一协议接口
  ├── ZhiBridgeAdapter           — 智桥实现
  ├── FamilySessionManager       — 全族会话管理器（SQLite后端）
  └── SessionSnapshot            — 上下文快照数据模型

使用:
  from session_protocol import SessionProtocol, FamilySessionManager
"""

from session_protocol.protocol import SessionProtocol, SessionSnapshot, ContextBudget
from session_protocol.manager import FamilySessionManager
from session_protocol.auth import AuthorizationManager, AuthorizationError
from session_protocol.zhi_bridge_adapter import ZhiBridgeAdapter

__all__ = [
    "SessionProtocol",
    "SessionSnapshot",
    "ContextBudget",
    "FamilySessionManager",
    "AuthorizationManager",
    "AuthorizationError",
    "ZhiBridgeAdapter",
]
__version__ = "0.1.0"

#!/usr/bin/env python3
"""
智桥数据模型和验证

使用 Pydantic 进行数据验证和序列化
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
import uuid
import warnings


# ============================================================================
# WebSocket 消息模型
# ============================================================================

class BaseMessage(BaseModel):
    """基础消息模型"""
    type: str = Field(..., description="消息类型")

    class Config:
        extra = "allow"  # Allow extra fields for backward compatibility


class PingMessage(BaseMessage):
    """Ping 心跳消息"""
    type: Literal["ping"] = "ping"


class PongMessage(BaseMessage):
    """Pong 心跳响应"""
    type: Literal["pong"] = "pong"
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class AuthenticateMessage(BaseMessage):
    """认证消息"""
    type: Literal["authenticate"] = "authenticate"
    token: str = Field(..., min_length=1, description="认证令牌")
    csrf_token: Optional[str] = Field(None, description="CSRF令牌（如果启用CSRF保护）")


class ListSessionsMessage(BaseMessage):
    """列出会话请求"""
    type: Literal["list_sessions"] = "list_sessions"


class StartSessionMessage(BaseMessage):
    """启动会话请求"""
    type: Literal["start_session"] = "start_session"
    tool_name: str = Field(..., min_length=1, max_length=50, description="工具名称")
    args: List[str] = Field(default_factory=list, description="命令参数")
    csrf_token: Optional[str] = Field(None, description="CSRF令牌（敏感操作需要）")
    signature: Optional[str] = Field(None, description="请求签名（高敏感操作需要）")

    @field_validator('tool_name')
    @classmethod
    def validate_tool_name(cls, v: str) -> str:
        """验证工具名称"""
        valid_tools = [
            'crush', 'claude', 'iflow', 'cursor',
            'trae', 'droid', 'openclaw', 'copilot'
        ]
        if v.lower() not in [t.lower() for t in valid_tools]:
            raise ValueError(f"Invalid tool_name: {v}. Valid tools: {', '.join(valid_tools)}")
        return v.lower()


class StopSessionMessage(BaseMessage):
    """停止会话请求"""
    type: Literal["stop_session"] = "stop_session"
    session_id: str = Field(..., pattern=r'^[a-f0-9-]{36}$', description="会话ID (UUID)")
    csrf_token: Optional[str] = Field(None, description="CSRF令牌（敏感操作需要）")


class DeleteSessionMessage(BaseMessage):
    """删除会话请求"""
    type: Literal["delete_session"] = "delete_session"
    session_id: str = Field(..., pattern=r'^[a-f0-9-]{36}$', description="会话ID (UUID)")
    csrf_token: Optional[str] = Field(None, description="CSRF令牌（敏感操作需要）")
    signature: Optional[str] = Field(None, description="请求签名（高敏感操作需要）")


class SendInputMessage(BaseMessage):
    """发送输入到会话请求"""
    type: Literal["send_input"] = "send_input"
    session_id: str = Field(..., pattern=r'^[a-f0-9-]{36}$', description="会话ID (UUID)")
    input: str = Field(..., description="要发送的输入")
    csrf_token: Optional[str] = Field(None, description="CSRF令牌（敏感操作需要）")
    signature: Optional[str] = Field(None, description="请求签名（高敏感操作需要）")


# ============================================================================
# WebSocket 响应模型
# ============================================================================

class SessionsListResponse(BaseModel):
    """会话列表响应"""
    type: Literal["sessions_list"] = "sessions_list"
    sessions: List[Dict[str, Any]] = Field(default_factory=list)
    count: int = Field(default=0, ge=0)


class SessionStartedResponse(BaseModel):
    """会话启动响应"""
    type: Literal["session_started"] = "session_started"
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tool_name: str
    status: Literal["created", "running", "stopped"] = "running"


class SessionStoppedResponse(BaseModel):
    """会话停止响应"""
    type: Literal["session_stopped"] = "session_stopped"
    session_id: str
    status: Literal["stopped"] = "stopped"


class SessionDeletedResponse(BaseModel):
    """会话删除响应"""
    type: Literal["session_deleted"] = "session_deleted"
    session_id: str


class OutputResponse(BaseModel):
    """输出响应"""
    type: Literal["output"] = "output"
    session_id: str
    output: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class ErrorResponse(BaseModel):
    """错误响应"""
    type: Literal["error"] = "error"
    message: str = Field(..., min_length=1, max_length=500)
    code: Optional[int] = Field(None, ge=100, le=599, description="错误代码")


class AuthSuccessResponse(BaseModel):
    """认证成功响应"""
    type: Literal["auth_success"] = "auth_success"
    message: str = "Authentication successful"
    user_id: str
    username: str
    csrf_token: Optional[str] = Field(None, description="CSRF令牌（用于后续请求）")


# ============================================================================
# 会话模型
# ============================================================================

class Session(BaseModel):
    """会话模型"""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tool_name: str
    status: Literal["created", "running", "stopped", "error"] = "created"
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    args: List[str] = Field(default_factory=list)
    pid: Optional[int] = Field(None, gt=0, description="进程ID")
    exit_code: Optional[int] = Field(None, ge=0)


class SessionInfo(BaseModel):
    """会话信息（精简版）"""
    session_id: str
    tool_name: str
    status: str
    created_at: str


# ============================================================================
# 工具模型
# ============================================================================

class ToolInfo(BaseModel):
    """工具信息"""
    name: str
    description: str
    executable: Optional[str] = None
    icon: str = "🔧"
    color: str = "#667eea"

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        warnings.warn(
            "ToolInfo is deprecated: the relay server uses a different message protocol.",
            DeprecationWarning,
            stacklevel=2,
        )


class ToolRegistry(BaseModel):
    """工具注册表"""
    tools: Dict[str, ToolInfo]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        warnings.warn(
            "ToolRegistry is deprecated: the relay server uses a different message protocol.",
            DeprecationWarning,
            stacklevel=2,
        )

    def get_tool(self, tool_name: str) -> Optional[ToolInfo]:
        """获取工具信息"""
        return self.tools.get(tool_name.lower())

    def list_tools(self) -> List[ToolInfo]:
        """列出所有工具"""
        return list(self.tools.values())


# ============================================================================
# 服务器配置模型
# ============================================================================

class ServerConfig(BaseModel):
    """服务器配置"""
    host: str = Field(default="0.0.0.0", description="监听主机")
    port: int = Field(default=8765, ge=1, le=65535, description="监听端口")
    max_connections: int = Field(default=100, ge=1, le=1000, description="最大连接数")
    ping_interval: int = Field(default=10, ge=1, le=60, description="心跳间隔(秒)")
    session_timeout: int = Field(default=3600, ge=60, le=86400, description="会话超时(秒)")
    enable_cors: bool = Field(default=False, description="启用CORS")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"


# ============================================================================
# 验证辅助函数
# ============================================================================

def validate_message(message: str) -> BaseMessage:
    """
    验证并解析 WebSocket 消息

    Args:
        message: JSON 字符串消息

    Returns:
        验证后的消息对象

    Raises:
        ValidationError: 如果消息格式无效
    """
    import json
    data = json.loads(message)
    message_type = data.get("type", "")

    message_types = {
        "ping": PingMessage,
        "pong": PongMessage,
        "authenticate": AuthenticateMessage,
        "list_sessions": ListSessionsMessage,
        "start_session": StartSessionMessage,
        "stop_session": StopSessionMessage,
        "delete_session": DeleteSessionMessage,
        "send_input": SendInputMessage,
    }

    message_class = message_types.get(message_type)
    if not message_class:
        raise ValueError(f"Unknown message type: {message_type}")

    return message_class(**data)


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    # 消息模型
    "BaseMessage",
    "PingMessage",
    "PongMessage",
    "AuthenticateMessage",
    "ListSessionsMessage",
    "StartSessionMessage",
    "StopSessionMessage",
    "DeleteSessionMessage",
    "SendInputMessage",
    # 响应模型
    "SessionsListResponse",
    "SessionStartedResponse",
    "SessionStoppedResponse",
    "SessionDeletedResponse",
    "OutputResponse",
    "ErrorResponse",
    "AuthSuccessResponse",
    # 会话模型
    "Session",
    "SessionInfo",
    # 工具模型
    "ToolInfo",
    "ToolRegistry",
    # 配置模型
    "ServerConfig",
    # 验证函数
    "validate_message",
]

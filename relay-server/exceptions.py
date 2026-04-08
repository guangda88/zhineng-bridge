#!/usr/bin/env python3
"""
智桥自定义异常类

定义所有自定义异常类型和错误代码映射
"""


# ============================================================================
# 基础异常类
# ============================================================================

class ZhinengBridgeException(Exception):
    """智桥基础异常类"""

    def __init__(self, message: str, code: int = 500, details: dict = None):
        """
        初始化异常

        Args:
            message: 错误消息
            code: HTTP 风格错误代码
            details: 额外错误详情
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "type": "error",
            "message": self.message,
            "code": self.code,
            **self.details
        }


# ============================================================================
# 验证异常 (4xx)
# ============================================================================

class ValidationError(ZhinengBridgeException):
    """消息验证错误"""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message, code=422, details=details)


class InvalidMessageTypeError(ZhinengBridgeException):
    """无效的消息类型"""

    def __init__(self, message_type: str):
        super().__init__(
            f"Unknown message type: {message_type}",
            code=400,
            details={"message_type": message_type}
        )


class InvalidToolNameError(ZhinengBridgeException):
    """无效的工具名称"""

    def __init__(self, tool_name: str, valid_tools: list):
        super().__init__(
            f"Invalid tool_name: {tool_name}",
            code=400,
            details={
                "tool_name": tool_name,
                "valid_tools": valid_tools
            }
        )


class InvalidSessionIdError(ZhinengBridgeException):
    """无效的会话ID"""

    def __init__(self, session_id: str):
        super().__init__(
            f"Invalid session_id: {session_id}",
            code=400,
            details={"session_id": session_id}
        )


class InvalidJSONError(ZhinengBridgeException):
    """无效的JSON格式"""

    def __init__(self, message: str = "Invalid JSON format"):
        super().__init__(message, code=400)


class MissingFieldError(ZhinengBridgeException):
    """缺少必需字段"""

    def __init__(self, field_name: str):
        super().__init__(
            f"Missing required field: {field_name}",
            code=400,
            details={"field": field_name}
        )


# ============================================================================
# 认证和授权异常 (4xx)
# ============================================================================

class AuthenticationError(ZhinengBridgeException):
    """认证失败"""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, code=401)


class AuthorizationError(ZhinengBridgeException):
    """授权失败"""

    def __init__(self, message: str = "Authorization failed"):
        super().__init__(message, code=403)


class RateLimitError(ZhinengBridgeException):
    """速率限制 exceeded"""

    def __init__(self, limit: int = None):
        message = "Rate limit exceeded"
        details = {}
        if limit:
            details["limit"] = limit
            message = f"Rate limit exceeded: {limit} requests"
        super().__init__(message, code=429, details=details)


# ============================================================================
# 资源异常 (4xx/5xx)
# ============================================================================

class SessionNotFoundError(ZhinengBridgeException):
    """会话未找到"""

    def __init__(self, session_id: str):
        super().__init__(
            f"Session not found: {session_id}",
            code=404,
            details={"session_id": session_id}
        )


class SessionAlreadyRunningError(ZhinengBridgeException):
    """会话已在运行"""

    def __init__(self, session_id: str):
        super().__init__(
            f"Session already running: {session_id}",
            code=409,
            details={"session_id": session_id}
        )


class MaxConnectionsError(ZhinengBridgeException):
    """超过最大连接数"""

    def __init__(self, current: int, max_connections: int):
        super().__init__(
            f"Maximum connections exceeded: {current}/{max_connections}",
            code=429,
            details={
                "current": current,
                "max_connections": max_connections
            }
        )


class MaxSessionsError(ZhinengBridgeException):
    """超过最大会话数"""

    def __init__(self, current: int, max_sessions: int):
        super().__init__(
            f"Maximum sessions exceeded: {current}/{max_sessions}",
            code=429,
            details={
                "current": current,
                "max_sessions": max_sessions
            }
        )


# ============================================================================
# 服务器异常 (5xx)
# ============================================================================

class ServerException(ZhinengBridgeException):
    """服务器内部错误"""

    def __init__(self, message: str = "Internal server error", details: dict = None):
        super().__init__(message, code=500, details=details)


class SessionManagerError(ZhinengBridgeException):
    """会话管理器错误"""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message, code=500, details=details)


class ToolExecutionError(ZhinengBridgeException):
    """工具执行错误"""

    def __init__(self, tool_name: str, error: str, exit_code: int = None):
        details = {"tool_name": tool_name, "error": error}
        if exit_code is not None:
            details["exit_code"] = exit_code
        super().__init__(
            f"Tool execution failed: {tool_name}",
            code=500,
            details=details
        )


class ConnectionError(ZhinengBridgeException):
    """连接错误"""

    def __init__(self, message: str = "Connection error", details: dict = None):
        super().__init__(message, code=503, details=details)


class TimeoutError(ZhinengBridgeException):
    """超时错误"""

    def __init__(self, operation: str, timeout: int):
        super().__init__(
            f"Timeout during {operation}: {timeout}s",
            code=504,
            details={"operation": operation, "timeout": timeout}
        )


# ============================================================================
# 配置异常 (5xx)
# ============================================================================

class ConfigurationError(ZhinengBridgeException):
    """配置错误"""

    def __init__(self, message: str, config_key: str = None):
        details = {}
        if config_key:
            details["config_key"] = config_key
        super().__init__(message, code=500, details=details)


# ============================================================================
# 错误代码映射
# ============================================================================

ERROR_CODE_MAP = {
    # 4xx - Client Errors
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    409: "Conflict",
    422: "Unprocessable Entity",
    429: "Too Many Requests",

    # 5xx - Server Errors
    500: "Internal Server Error",
    503: "Service Unavailable",
    504: "Gateway Timeout",
}


def get_error_message(code: int) -> str:
    """
    根据错误代码获取标准错误消息

    Args:
        code: 错误代码

    Returns:
        标准错误消息
    """
    return ERROR_CODE_MAP.get(code, "Unknown Error")


def exception_to_dict(exception: Exception) -> dict:
    """
    将异常转换为字典格式

    Args:
        exception: 异常对象

    Returns:
        错误字典
    """
    if isinstance(exception, ZhinengBridgeException):
        return exception.to_dict()
    else:
        return {
            "type": "error",
            "message": str(exception),
            "code": 500
        }


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    # 基础异常
    "ZhinengBridgeException",
    # 验证异常
    "ValidationError",
    "InvalidMessageTypeError",
    "InvalidToolNameError",
    "InvalidSessionIdError",
    "InvalidJSONError",
    "MissingFieldError",
    # 认证授权异常
    "AuthenticationError",
    "AuthorizationError",
    "RateLimitError",
    # 资源异常
    "SessionNotFoundError",
    "SessionAlreadyRunningError",
    "MaxConnectionsError",
    "MaxSessionsError",
    # 服务器异常
    "ServerException",
    "SessionManagerError",
    "ToolExecutionError",
    "ConnectionError",
    "TimeoutError",
    # 配置异常
    "ConfigurationError",
    # 工具函数
    "ERROR_CODE_MAP",
    "get_error_message",
    "exception_to_dict",
]

#!/usr/bin/env python3
"""
智桥日志系统

使用 structlog 进行结构化日志记录
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import structlog


def configure_logging(
    log_level: str = "INFO",
    log_format: str = "json",
    log_file: Optional[str] = None,
):
    """
    配置结构化日志

    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
        log_format: 日志格式 (json 或 console)
        log_file: 日志文件路径（可选）
    """

    # 配置标准库日志
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # 配置 structlog
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(
            structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev.plain_traceback,
            )
        )

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # 配置文件日志（如果指定）
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper()))

        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)


def get_logger(name: str = __name__) -> structlog.BoundLogger:
    """
    获取日志记录器

    Args:
        name: 日志记录器名称

    Returns:
        配置好的日志记录器
    """
    return structlog.get_logger(name)


# ============================================================================
# 日志装饰器
# ============================================================================


def log_execution(logger_name: Optional[str] = None):
    """
    记录函数执行的装饰器

    Args:
        logger_name: 日志记录器名称
    """

    def decorator(func):
        import functools
        import time

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = get_logger(logger_name or func.__module__)
            logger.info("Function started", function=func.__name__)

            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                elapsed = time.time() - start_time
                logger.info(
                    "Function completed",
                    function=func.__name__,
                    elapsed_ms=round(elapsed * 1000, 2),
                )
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(
                    "Function failed",
                    function=func.__name__,
                    elapsed_ms=round(elapsed * 1000, 2),
                    error=str(e),
                    exc_info=True,
                )
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = get_logger(logger_name or func.__module__)
            logger.info("Function started", function=func.__name__)

            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                logger.info(
                    "Function completed",
                    function=func.__name__,
                    elapsed_ms=round(elapsed * 1000, 2),
                )
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(
                    "Function failed",
                    function=func.__name__,
                    elapsed_ms=round(elapsed * 1000, 2),
                    error=str(e),
                    exc_info=True,
                )
                raise

        # 返回适当的包装器
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# ============================================================================
# 日志上下文管理器
# ============================================================================


class LogContext:
    """日志上下文管理器"""

    def __init__(self, **context):
        self.context = context
        self.token = None

    def __enter__(self):
        self.token = structlog.contextvars.bind_contextvars(**self.context)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.token:
            structlog.contextvars.unbind_contextvars(self.token)


def log_client_context(client_id: str, **additional_context):
    """客户端日志上下文管理器"""
    return LogContext(client_id=client_id, **additional_context)


def log_session_context(session_id: str, **additional_context):
    """会话日志上下文管理器"""
    return LogContext(session_id=session_id, **additional_context)


# ============================================================================
# 日志指标收集
# ============================================================================


class MetricsLogger:
    """日志指标收集器"""

    def __init__(self):
        self.metrics = {
            "websocket_connections": 0,
            "sessions_created": 0,
            "sessions_stopped": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "errors": 0,
        }
        self.logger = get_logger("metrics")

    def increment(self, metric_name: str, value: int = 1):
        """
        增加指标

        Args:
            metric_name: 指标名称
            value: 增加值
        """
        if metric_name in self.metrics:
            self.metrics[metric_name] += value
            self.logger.debug(
                "Metric incremented",
                metric=metric_name,
                value=self.metrics[metric_name],
            )

    def set(self, metric_name: str, value: int):
        """
        设置指标

        Args:
            metric_name: 指标名称
            value: 设置值
        """
        if metric_name in self.metrics:
            self.metrics[metric_name] = value
            self.logger.debug(
                "Metric set",
                metric=metric_name,
                value=value,
            )

    def log_metrics(self):
        """记录当前指标"""
        self.logger.info("Current metrics", **self.metrics)


# ============================================================================
# 全局指标收集器
# ============================================================================

metrics = MetricsLogger()


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    "configure_logging",
    "get_logger",
    "log_execution",
    "LogContext",
    "log_client_context",
    "log_session_context",
    "MetricsLogger",
    "metrics",
]

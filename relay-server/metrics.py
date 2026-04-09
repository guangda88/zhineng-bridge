#!/usr/bin/env python3
"""
Prometheus Metrics Collection Module
Provides Prometheus metrics for monitoring the Zhineng-bridge relay server
"""

import threading
import time
from threading import Lock
from types import TracebackType
from typing import Iterator, Optional, Type

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, generate_latest
from prometheus_client.core import GaugeMetricFamily
from prometheus_client.registry import REGISTRY

# Custom registry to avoid conflicts
REGISTRY = CollectorRegistry()


# Counter metrics - Monotonically increasing values
websocket_connections_total = Counter(
    "zhineng_bridge_websocket_connections_total",
    "Total number of WebSocket connections",
    ["status"],  # Labels: success, error
    registry=REGISTRY,
)

messages_received_total = Counter(
    "zhineng_bridge_messages_received_total",
    "Total number of messages received",
    ["message_type"],
    registry=REGISTRY,
)

messages_sent_total = Counter(
    "zhineng_bridge_messages_sent_total",
    "Total number of messages sent",
    ["message_type"],
    registry=REGISTRY,
)

sessions_created_total = Counter(
    "zhineng_bridge_sessions_created_total",
    "Total number of sessions created",
    ["tool_name", "status"],
    registry=REGISTRY,
)

errors_total = Counter(
    "zhineng_bridge_errors_total",
    "Total number of errors",
    ["error_type", "severity"],
    registry=REGISTRY,
)

authentication_attempts_total = Counter(
    "zhineng_bridge_authentication_attempts_total",
    "Total number of authentication attempts",
    ["status"],  # success, failed
    registry=REGISTRY,
)

rate_limit_violations_total = Counter(
    "zhineng_bridge_rate_limit_violations_total",
    "Total number of rate limit violations",
    ["client_id"],
    registry=REGISTRY,
)


# Gauge metrics - Values that can go up and down
active_websocket_connections = Gauge(
    "zhineng_bridge_active_websocket_connections",
    "Current number of active WebSocket connections",
    registry=REGISTRY,
)

active_sessions = Gauge(
    "zhineng_bridge_active_sessions",
    "Current number of active sessions",
    ["tool_name"],
    registry=REGISTRY,
)

pending_messages = Gauge(
    "zhineng_bridge_pending_messages", "Number of messages pending to be sent", registry=REGISTRY
)

memory_usage_bytes = Gauge(
    "zhineng_bridge_memory_usage_bytes", "Memory usage in bytes", registry=REGISTRY
)

cpu_usage_percent = Gauge(
    "zhineng_bridge_cpu_usage_percent", "CPU usage percentage", registry=REGISTRY
)

uptime_seconds = Gauge(
    "zhineng_bridge_uptime_seconds", "Server uptime in seconds", registry=REGISTRY
)

message_queue_depth = Gauge(
    "zhineng_bridge_message_queue_depth", "Current message queue depth", registry=REGISTRY
)

session_manager_status = Gauge(
    "zhineng_bridge_session_manager_status",
    "Session manager status (1=connected, 0=disconnected)",
    registry=REGISTRY,
)


# Histogram metrics - Track distributions
request_duration_seconds = Histogram(
    "zhineng_bridge_request_duration_seconds",
    "Request duration in seconds",
    ["request_type"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    registry=REGISTRY,
)

message_processing_duration_seconds = Histogram(
    "zhineng_bridge_message_processing_duration_seconds",
    "Message processing duration in seconds",
    ["message_type"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
    registry=REGISTRY,
)

session_creation_duration_seconds = Histogram(
    "zhineng_bridge_session_creation_duration_seconds",
    "Session creation duration in seconds",
    ["tool_name"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0),
    registry=REGISTRY,
)

websocket_connection_duration_seconds = Histogram(
    "zhineng_bridge_websocket_connection_duration_seconds",
    "WebSocket connection duration in seconds",
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0, 1800.0, 3600.0),
    registry=REGISTRY,
)


class MetricsCollector:
    """Custom metrics collector for dynamic metrics"""

    def __init__(self) -> None:
        self.lock: Lock = Lock()
        self.start_time: float = time.time()

    def collect(self) -> Iterator[GaugeMetricFamily]:
        """Collect metrics"""
        with self.lock:
            # Update uptime
            time.time() - self.start_time
            yield GaugeMetricFamily(
                "zhineng_bridge_start_time_seconds",
                "Server start time in seconds",
                value=self.start_time,
            )


# Create custom collector
metrics_collector = MetricsCollector()
REGISTRY.register(metrics_collector)


# Metrics update functions
def increment_websocket_connections(status: str = "success") -> None:
    """Increment WebSocket connection counter"""
    websocket_connections_total.labels(status=status).inc()
    if status == "success":
        active_websocket_connections.inc()
    else:
        active_websocket_connections.dec()


def decrement_websocket_connections() -> None:
    """Decrement active WebSocket connections"""
    active_websocket_connections.dec()


def increment_messages_received(message_type: str) -> None:
    """Increment messages received counter"""
    messages_received_total.labels(message_type=message_type).inc()


def increment_messages_sent(message_type: str) -> None:
    """Increment messages sent counter"""
    messages_sent_total.labels(message_type=message_type).inc()


def increment_sessions_created(tool_name: str, status: str = "success") -> None:
    """Increment sessions created counter"""
    sessions_created_total.labels(tool_name=tool_name, status=status).inc()
    if status == "success":
        active_sessions.labels(tool_name=tool_name).inc()


def decrement_sessions(tool_name: str) -> None:
    """Decrement active sessions"""
    active_sessions.labels(tool_name=tool_name).dec()


def increment_errors(error_type: str, severity: str = "error") -> None:
    """Increment errors counter"""
    errors_total.labels(error_type=error_type, severity=severity).inc()


def increment_authentication_attempts(status: str) -> None:
    """Increment authentication attempts counter"""
    authentication_attempts_total.labels(status=status).inc()


def increment_rate_limit_violations(client_id: str) -> None:
    """Increment rate limit violations counter"""
    rate_limit_violations_total.labels(client_id=client_id).inc()


def track_request_duration(request_type: str, duration: float) -> None:
    """Track request duration"""
    request_duration_seconds.labels(request_type=request_type).observe(duration)


def track_message_processing_duration(message_type: str, duration: float) -> None:
    """Track message processing duration"""
    message_processing_duration_seconds.labels(message_type=message_type).observe(duration)


def track_session_creation_duration(tool_name: str, duration: float) -> None:
    """Track session creation duration"""
    session_creation_duration_seconds.labels(tool_name=tool_name).observe(duration)


def track_websocket_connection_duration(duration: float) -> None:
    """Track WebSocket connection duration"""
    websocket_connection_duration_seconds.observe(duration)


def update_memory_usage() -> None:
    """Update memory usage metric"""
    try:
        import psutil

        process = psutil.Process()
        memory_usage_bytes.set(process.memory_info().rss)
    except ImportError:
        # psutil not available, use simple fallback
        memory_usage_bytes.set(0)


def update_cpu_usage() -> None:
    """Update CPU usage metric"""
    try:
        import psutil

        cpu_usage_percent.set(psutil.cpu_percent(interval=0.1))
    except ImportError:
        # psutil not available
        cpu_usage_percent.set(0)


def update_session_manager_status(status: bool) -> None:
    """Update session manager status"""
    session_manager_status.set(1 if status else 0)


def get_metrics() -> bytes:
    """Get Prometheus metrics in text format"""
    return generate_latest(REGISTRY)


class RequestDurationTracker:
    """Context manager for tracking request duration"""

    def __init__(self, request_type: str) -> None:
        self.request_type: str = request_type
        self.start_time: Optional[float] = None

    def __enter__(self) -> "RequestDurationTracker":
        self.start_time = time.time()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> bool:
        if self.start_time is not None:
            duration = time.time() - self.start_time
            track_request_duration(self.request_type, duration)
        return False


class MessageProcessingTracker:
    """Context manager for tracking message processing duration"""

    def __init__(self, message_type: str) -> None:
        self.message_type: str = message_type
        self.start_time: Optional[float] = None

    def __enter__(self) -> "MessageProcessingTracker":
        self.start_time = time.time()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> bool:
        if self.start_time is not None:
            duration = time.time() - self.start_time
            track_message_processing_duration(self.message_type, duration)
        return False


class SessionCreationTracker:
    """Context manager for tracking session creation duration"""

    def __init__(self, tool_name: str) -> None:
        self.tool_name: str = tool_name
        self.start_time: Optional[float] = None

    def __enter__(self) -> "SessionCreationTracker":
        self.start_time = time.time()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> bool:
        if self.start_time is not None:
            duration = time.time() - self.start_time
            track_session_creation_duration(self.tool_name, duration)
            status = "success" if exc_type is None else "error"
            increment_sessions_created(self.tool_name, status)
        return False


# Async context managers
class AsyncRequestDurationTracker:
    """Async context manager for tracking request duration"""

    def __init__(self, request_type: str) -> None:
        self.request_type: str = request_type
        self.start_time: Optional[float] = None

    async def __aenter__(self) -> "AsyncRequestDurationTracker":
        self.start_time = time.time()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> bool:
        if self.start_time is not None:
            duration = time.time() - self.start_time
            track_request_duration(self.request_type, duration)
        return False


class AsyncMessageProcessingTracker:
    """Async context manager for tracking message processing duration"""

    def __init__(self, message_type: str) -> None:
        self.message_type: str = message_type
        self.start_time: Optional[float] = None

    async def __aenter__(self) -> "AsyncMessageProcessingTracker":
        self.start_time = time.time()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> bool:
        if self.start_time is not None:
            duration = time.time() - self.start_time
            track_message_processing_duration(self.message_type, duration)
        return False


# Auto-update thread for system metrics
def start_metrics_updater(interval: int = 5) -> threading.Thread:
    """Start background thread to update system metrics"""
    import threading
    import time as time_module

    def update_loop() -> None:
        while True:
            try:
                update_memory_usage()
                update_cpu_usage()
                uptime_seconds.set(time.time() - metrics_collector.start_time)
                time_module.sleep(interval)
            except Exception as e:
                import logging

                logger = logging.getLogger(__name__)
                logger.error(f"Error updating metrics: {e}")
                time_module.sleep(interval)

    thread = threading.Thread(target=update_loop, daemon=True)
    thread.start()
    return thread


# Convenience functions
def track_connection_success() -> None:
    """Track successful WebSocket connection"""
    increment_websocket_connections("success")


def track_connection_error() -> None:
    """Track failed WebSocket connection"""
    increment_websocket_connections("error")


def track_message(message_type: str) -> None:
    """Track message received"""
    increment_messages_received(message_type)


def track_response(message_type: str) -> None:
    """Track message sent"""
    increment_messages_sent(message_type)


def track_error(error_type: str, severity: str = "error") -> None:
    """Track error"""
    increment_errors(error_type, severity)


def track_auth_success() -> None:
    """Track successful authentication"""
    increment_authentication_attempts("success")


def track_auth_failure() -> None:
    """Track failed authentication"""
    increment_authentication_attempts("failed")


def track_rate_limit_violation(client_id: str) -> None:
    """Track rate limit violation"""
    increment_rate_limit_violations(client_id)

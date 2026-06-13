"""
指标模块 - Prometheus指标 + 健康检查
"""

import structlog
from fastapi import Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

log = structlog.get_logger()

# Prometheus指标
REQUEST_COUNT = Counter(
    "zhibridge_requests_total",
    "Total requests",
    ["method", "path", "status"],
)
REQUEST_LATENCY = Histogram(
    "zhibridge_request_latency_seconds",
    "Request latency",
    ["method", "path"],
)
ACTIVE_REQUESTS = Gauge(
    "zhibridge_active_requests",
    "Active requests",
)

# 服务健康状态
SERVICE_HEALTH = Gauge(
    "zhibridge_service_health",
    "Backend service health (1=up, 0=down)",
    ["service"],
)


async def metrics_endpoint(request: Request):
    """Prometheus指标端点 - 需要鉴权"""
    from .auth import require_auth

    await require_auth(request)
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


def record_request(method: str, path: str, status: int, latency: float):
    """记录请求指标"""
    REQUEST_COUNT.labels(method=method, path=path, status=status).inc()
    REQUEST_LATENCY.labels(method=method, path=path).observe(latency)


def update_backend_health(service: str, is_healthy: bool):
    """更新后端服务健康状态"""
    SERVICE_HEALTH.labels(service=service).set(1 if is_healthy else 0)


# SDTH防御指标
URGENT_REQUEST_COUNT = Counter(
    "zhibridge_urgent_requests_total",
    "Urgent (user-priority) requests",
    ["method", "path"],
)
LATENCY_GAP = Histogram(
    "zhibridge_latency_gap_seconds",
    "Time between request arrival and processing start",
    ["method", "path"],
    buckets=[0.1, 0.5, 1, 5, 10, 30, 60, 120],
)
LATENCY_GAP_ALERTS = Counter(
    "zhibridge_latency_gap_alerts_total",
    "Requests where latency gap exceeded threshold",
    ["method", "path"],
)


def record_urgent_request(method: str, path: str):
    URGENT_REQUEST_COUNT.labels(method=method, path=path).inc()


def record_latency_gap(method: str, path: str, gap: float, threshold: float = 30.0):
    LATENCY_GAP.labels(method=method, path=path).observe(gap)
    if gap > threshold:
        LATENCY_GAP_ALERTS.labels(method=method, path=path).inc()

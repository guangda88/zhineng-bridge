"""
指标模块 - Prometheus指标 + 健康检查
"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from fastapi.responses import PlainTextResponse
import structlog

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
    """Prometheus指标端点"""
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
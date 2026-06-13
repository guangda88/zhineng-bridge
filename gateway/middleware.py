"""
中间件模块 - 限流 + CORS + 请求日志
"""

import time

import structlog
from fastapi import Request
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from .config import settings

log = structlog.get_logger()

# 限流器
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit])


async def log_requests(request: Request, call_next):
    """请求日志 + Prometheus指标 + SDTH优先级检测 + 延迟gap追踪"""
    from .metrics import ACTIVE_REQUESTS, record_latency_gap, record_request, record_urgent_request

    arrival_time = time.time()
    method = request.method
    path = request.url.path

    # SDTH: 检测urgent标记（用户请求优先）
    priority = request.headers.get(settings.priority_header, "normal")
    is_urgent = priority.lower() == "urgent"
    if is_urgent:
        record_urgent_request(method, path)
        log.info("urgent_request_detected", method=method, path=path)

    ACTIVE_REQUESTS.inc()
    try:
        response = await call_next(request)
    finally:
        ACTIVE_REQUESTS.dec()

    duration = time.time() - arrival_time
    record_request(method, path, response.status_code, duration)

    # SDTH: 延迟gap = 总耗时（含排队）。超过阈值记录告警
    record_latency_gap(method, path, duration, threshold=settings.latency_alert_threshold)
    if duration > settings.latency_alert_threshold:
        log.warning(
            "latency_gap_exceeded",
            method=method,
            path=path,
            gap_seconds=round(duration, 2),
            threshold=settings.latency_alert_threshold,
            priority=priority,
        )

    log.info(
        "request_completed",
        method=method,
        path=path,
        status=response.status_code,
        duration_ms=round(duration * 1000, 2),
        priority=priority,
    )
    return response


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """限流异常处理"""
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded", "retry_after": exc.detail},
    )


def setup_middleware(app):
    """配置所有中间件"""
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=bool(settings.cors_origins),
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["X-API-Key", "Content-Type", "Authorization", settings.priority_header],
    )

    # 请求日志
    app.middleware("http")(log_requests)

    # 限流异常处理
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

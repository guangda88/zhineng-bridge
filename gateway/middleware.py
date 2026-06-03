"""
中间件模块 - 限流 + CORS + 请求日志
"""
from fastapi import Request
from starlette.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.responses import JSONResponse
import structlog
import time

from .config import settings

log = structlog.get_logger()

# 限流器
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit])


async def log_requests(request: Request, call_next):
    """请求日志 + Prometheus指标中间件"""
    from .metrics import record_request, ACTIVE_REQUESTS

    start_time = time.time()
    method = request.method
    path = request.url.path

    ACTIVE_REQUESTS.inc()
    try:
        response = await call_next(request)
    finally:
        ACTIVE_REQUESTS.dec()

    duration = time.time() - start_time
    record_request(method, path, response.status_code, duration)

    log.info(
        "request_completed",
        method=method,
        path=path,
        status=response.status_code,
        duration_ms=round(duration * 1000, 2),
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
        allow_headers=["X-API-Key", "Content-Type", "Authorization"],
    )

    # 请求日志
    app.middleware("http")(log_requests)

    # 限流异常处理
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
"""
FastAPI应用入口
"""

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from .config import settings
from .metrics import metrics_endpoint
from .middleware import limiter, setup_middleware
from .proxy import retry_queue
from .router import router

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ]
)
log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    log.info("zhibridge_starting", host=settings.host, port=settings.port)
    await retry_queue.start()
    yield
    await retry_queue.stop()
    log.info("zhibridge_shutting_down")


def create_app() -> FastAPI:
    """创建FastAPI应用"""
    app = FastAPI(
        title="智桥 - 灵族对外统一网关",
        description="薄层API网关，只做路由、鉴权、限流，不做业务",
        version="2.1.0",
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    # 配置限流
    app.state.limiter = limiter

    # 配置中间件
    setup_middleware(app)

    # 注册路由
    app.include_router(router)

    # 指标端点
    app.add_api_route("/metrics", metrics_endpoint, methods=["GET"])

    return app


def main():
    """启动入口"""
    import uvicorn

    app = create_app()
    run_kwargs: dict = {
        "host": settings.host,
        "port": settings.port,
        "log_level": "info",
    }
    if settings.ssl_enabled:
        from pathlib import Path

        _cert = Path(settings.ssl_certfile)
        _key = Path(settings.ssl_keyfile)
        if not _cert.is_absolute():
            _cert = Path(__file__).resolve().parent.parent / _cert
        if not _key.is_absolute():
            _key = Path(__file__).resolve().parent.parent / _key
        if not _cert.exists():
            log.error("ssl_certfile_not_found", path=str(_cert), fallback="http")
        elif not _key.exists():
            log.error("ssl_keyfile_not_found", path=str(_key), fallback="http")
        else:
            run_kwargs["ssl_certfile"] = str(_cert)
            run_kwargs["ssl_keyfile"] = str(_key)
            log.info("ssl_enabled", certfile=str(_cert))
    uvicorn.run(app, **run_kwargs)


if __name__ == "__main__":
    main()

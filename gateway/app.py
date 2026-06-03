"""
FastAPI应用入口
"""
import structlog
from fastapi import FastAPI
from contextlib import asynccontextmanager

from .config import settings
from .router import router
from .middleware import setup_middleware, limiter
from .metrics import metrics_endpoint
from .proxy import retry_queue

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
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
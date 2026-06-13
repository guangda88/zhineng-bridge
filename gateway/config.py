"""
配置模块 - pydantic-settings配置
"""

from typing import Dict

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """智桥网关配置"""

    # 服务基础
    host: str = "127.0.0.1"
    port: int = 8767
    debug: bool = False

    # 现有内部服务
    lingtong_plus: str = "http://localhost:8765"
    lingzhi: str = "http://localhost:8000"
    lingtong_ask: str = "http://localhost:8902"
    lingresearch: str = "http://localhost:8903"
    llm_proxy: str = "http://localhost:8080"

    # 对外工程项目
    linghealth: str = "http://localhost:8200"  # 灵康(健康总平台)
    lingvision: str = "http://localhost:8781"  # 灵视(望诊)
    lingvoice: str = "http://localhost:8100"  # 灵声(闻诊)
    lingtouch: str = "http://localhost:8784"  # 灵触(切诊)
    sizhen: str = "http://localhost:8785"  # 四诊(调度平台)
    lingwear: str = "http://localhost:8787"  # 灵戴(穿戴设备)
    linglaw: str = "http://localhost:8002"  # 灵律(法律咨询API)
    lingyi: str = "http://localhost:8900"  # 灵依(已退出，linghealth/sizhen仍依赖)

    # API Key（生产环境必须设置，未设置时网关拒绝所有需认证请求）
    api_key: str = ""

    # API Key头（兼容灵族标准）
    api_key_header: str = "X-API-Key"

    # 限流
    rate_limit: str = "100/minute"
    rate_limit_burst: int = 20

    # SDTH防御 — 用户请求优先队列 + 响应时间差监控
    priority_header: str = "X-Priority"
    latency_alert_threshold: float = 30.0

    # CORS
    cors_origins: list[str] = []

    # E2E加密 — 敏感路由(linghealth/linglaw)强制客户端加密
    # 默认True(安全优先)，开发环境可通过 ZHIBRIDGE_REQUIRE_ENCRYPTION=false 关闭
    require_encryption: bool = True
    encryption_sensitive_backends: list[str] = ["linghealth", "linglaw"]

    # SSL/HTTPS
    ssl_certfile: str = "gateway/ssl/cert.pem"
    ssl_keyfile: str = "gateway/ssl/key.pem"
    ssl_enabled: bool = False

    class Config:
        env_prefix = "ZHIBRIDGE_"
        env_file = ".env"
        extra = "ignore"


settings = Settings()


# 后端服务路由表
BACKEND_SERVICES: Dict[str, str] = {
    # 内部服务
    "lingtong_plus": settings.lingtong_plus,
    "lingzhi": settings.lingzhi,
    "lingtong_ask": settings.lingtong_ask,
    "lingresearch": settings.lingresearch,
    "llm_proxy": settings.llm_proxy,
    # 对外工程项目
    "linghealth": settings.linghealth,
    "lingvision": settings.lingvision,
    "lingvoice": settings.lingvoice,
    "lingtouch": settings.lingtouch,
    "sizhen": settings.sizhen,
    "lingwear": settings.lingwear,
    "linglaw": settings.linglaw,
    "lingyi": settings.lingyi,  # backward compat: linghealth/sizhen still call lingyi
}

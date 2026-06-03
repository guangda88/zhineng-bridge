"""
鉴权模块 - API Key常量时间比对 + 透传

策略：网关用hmac.compare_digest验证key真伪，通过后透传给后端服务。
Key从环境变量ZHIBRIDGE_API_KEY读取（config.py的settings.api_key）。
"""
import hmac
from fastapi import Request, HTTPException, status
import structlog

from . import config

log = structlog.get_logger()

MIN_KEY_LENGTH = 20


def _extract_api_key(request: Request) -> str | None:
    """从请求头提取API Key"""
    api_key = request.headers.get(config.settings.api_key_header)
    if not api_key:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            api_key = auth_header[7:]
    return api_key or None


async def require_auth(request: Request) -> dict:
    """FastAPI依赖：验证API Key存在且与配置的key常量时间比对一致"""
    api_key = _extract_api_key(request)

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if len(api_key) < MIN_KEY_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format",
        )

    configured_key = config.settings.api_key
    if not configured_key:
        log.error("api_key_not_configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gateway not configured for authentication",
        )

    if not hmac.compare_digest(api_key.encode(), configured_key.encode()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return {"api_key": api_key, "source": "verified"}


async def optional_auth(request: Request) -> dict | None:
    """FastAPI依赖：可选鉴权（用于公开端点），有key时验证真伪"""
    api_key = _extract_api_key(request)
    if not api_key:
        return None
    if len(api_key) < MIN_KEY_LENGTH:
        return None

    configured_key = config.settings.api_key
    if not configured_key:
        return None

    if not hmac.compare_digest(api_key.encode(), configured_key.encode()):
        return None

    return {"api_key": api_key, "source": "verified"}

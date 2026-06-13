"""
路由模块 - 7个对外工程项目 + 灵族内部服务，统一通过智桥网关
"""

from typing import Optional
from urllib.parse import quote

import structlog
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from .auth import require_auth
from .config import BACKEND_SERVICES
from .crypto import ENCRYPTED_HEADER, is_encrypted_request, is_sensitive_backend

log = structlog.get_logger()
router = APIRouter()


class ProxyRequest(BaseModel):
    method: str = "POST"
    path: str
    headers: Optional[dict] = None
    body: Optional[dict] = None


class ProxyResponse(BaseModel):
    status: int
    headers: dict
    body: dict


async def _forward(
    backend_key: str, path: str, request: Request, user: dict = None, method: str = None
):
    """通用转发：根据backend_key查BACKEND_SERVICES，proxy_request到后端

    SDTH: 读取X-Priority头，urgent请求跳过重试队列、使用短超时。
    """
    from .config import settings
    from .proxy import proxy_request

    backend = BACKEND_SERVICES[backend_key]
    body = {}
    if method in (None, "POST", "PUT"):
        try:
            body = await request.json()
        except Exception:
            body = {}

    priority = request.headers.get(settings.priority_header, "normal") if request else "normal"
    is_urgent = priority.lower() == "urgent"

    if is_sensitive_backend(backend_key):
        headers = dict(request.headers) if request else {}
        encrypted = is_encrypted_request(headers)
        log.info(
            "sensitive_backend_access",
            backend=backend_key,
            path=path,
            encrypted=encrypted,
            urgent=is_urgent,
            user_id=user.get("api_key", "")[:8] if user else "",
        )
        if not encrypted:
            from fastapi.responses import JSONResponse

            log.warning("sensitive_route_unencrypted", backend=backend_key, path=path)
            return JSONResponse(
                status_code=400,
                content={
                    "error": "encryption_required",
                    "detail": f"Backend '{backend_key}' handles sensitive data. Set {ENCRYPTED_HEADER}: true and encrypt the request body.",
                },
            )

    return await proxy_request(
        backend=backend,
        path="/" + path.lstrip("/"),
        body=body,
        user=user or {"api_key": ""},
        method=method or request.method,
        urgent=is_urgent,
    )


# ============================================================
# P0: 网关健康检查
# ============================================================


@router.get("/")
async def root(user: dict = Depends(require_auth)):
    return {
        "service": "zhibridge",
        "version": "2.1.0",
        "description": "智桥 - 灵族对外统一网关",
        "endpoints": {
            "health": "/v1/health",
            "docs": "/docs",
            "metrics": "/metrics",
        },
        "auth": "X-API-Key header required for all endpoints",
    }


@router.get("/v1/health")
async def health_check(user: dict = Depends(require_auth)):
    from .circuit import get_backend_health_status
    from .proxy import retry_queue

    backends = await get_backend_health_status()
    return {
        "status": "healthy",
        "service": "zhibridge",
        "version": "2.1.0",
        "backends": backends,
        "retry_queue": {"pending": retry_queue.pending()},
    }


@router.post("/v1/crypto/generate-key")
async def generate_encryption_key(user: dict = Depends(require_auth)):
    """生成AES-256-GCM密钥（base64），供客户端-后端E2E加密预共享"""
    from .crypto import generate_key

    return {"key": generate_key(), "algorithm": "AES-256-GCM", "key_size": 256}


# ============================================================
# 灵族内部服务 — 供对外工程回调调用
# ============================================================


@router.post("/v1/chat/completions")
async def chat_completions(request: Request, user: dict = Depends(require_auth)):
    body = await request.json()
    from .proxy import proxy_request

    return await proxy_request(
        backend=BACKEND_SERVICES["lingtong_plus"],
        path="/v1/chat/completions",
        body=body,
        user=user,
    )


@router.post("/api/knowledge/query")
async def knowledge_query(request: Request, user: dict = Depends(require_auth)):
    body = await request.json()
    from .proxy import proxy_request

    query = body.get("query", "")
    category = body.get("category")
    limit = body.get("limit", 10)
    path = f"/api/v1/search?q={quote(query, safe='')}&limit={limit}"
    if category:
        path += f"&category={quote(category, safe='')}"
    return await proxy_request(
        backend=BACKEND_SERVICES["lingzhi"],
        path=path,
        body={},
        user=user,
        method="GET",
    )


@router.get("/api/status")
async def status_dashboard(user: dict = Depends(require_auth)):
    from .proxy import proxy_request

    return await proxy_request(
        backend=BACKEND_SERVICES["lingtong_plus"],
        path="/api/status",
        body={},
        user=user,
        method="GET",
    )


@router.get("/api/agents")
async def agents_list(user: dict = Depends(require_auth)):
    from .proxy import proxy_request

    return await proxy_request(
        backend=BACKEND_SERVICES["lingtong_plus"],
        path="/api/agents",
        body={},
        user=user,
        method="GET",
    )


@router.get("/api/podcast/episodes")
async def podcast_episodes(user: dict = Depends(require_auth)):
    return {"episodes": [], "source": "lingtong_ask"}


@router.get("/api/research/papers")
async def research_papers(user: dict = Depends(require_auth)):
    from .proxy import proxy_request

    return await proxy_request(
        backend=BACKEND_SERVICES["lingresearch"],
        path="/api/papers",
        body={},
        user=user,
        method="GET",
    )


@router.post("/v1/images/generations")
async def image_generations(request: Request, user: dict = Depends(require_auth)):
    body = await request.json()
    from .proxy import proxy_request

    return await proxy_request(
        backend=BACKEND_SERVICES["llm_proxy"],
        path="/v1/images/generations",
        body=body,
        user=user,
    )


# ============================================================
# 对外工程回调灵族内部资源 — /internal/{service}/{path}
# ============================================================

# ============================================================
# /internal/ 路径白名单 — P1-1修复 (R14-001)
# 认证后仍限制可访问的后端路径，防止管理接口暴露
# ============================================================

INTERNAL_PATH_WHITELIST: dict[str, list[str]] = {
    "lingtong_plus": ["/api/status", "/api/agents", "/v1/chat/completions"],
    "lingzhi": ["/api/v1/search", "/api/v1/knowledge", "/health"],
    "lingtong_ask": ["/api/episodes", "/api/scripts", "/health"],
    "lingresearch": ["/api/papers", "/api/stats", "/health"],
    "llm_proxy": ["/v1/chat/completions", "/v1/images/generations", "/health"],
    "linghealth": ["/api/v1/records", "/api/v1/search", "/api/v1/users", "/health"],
    "lingvision": ["/api/v1/diagnose", "/api/v1/teaching", "/health"],
    "lingvoice": ["/api/v1/analyze", "/health"],
    "lingtouch": ["/api/v1/diagnose", "/api/v1/pulse", "/health"],
    "sizhen": ["/api/v1/diagnose", "/api/v1/schedule", "/health"],
    "lingwear": ["/api/v1/data", "/api/v1/devices", "/api/v1/health", "/health"],
    "linglaw": ["/api/v1/consult", "/api/v1/cases", "/health"],
}


def _is_path_allowed(backend_key: str, path: str) -> bool:
    """检查路径是否在白名单中。path前缀匹配。"""
    whitelist = INTERNAL_PATH_WHITELIST.get(backend_key, [])
    clean_path = "/" + path.lstrip("/")
    for allowed in whitelist:
        if clean_path == allowed or clean_path.startswith(allowed + "/"):
            return True
    return False


@router.api_route("/internal/{backend_key}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def internal_passthrough(
    backend_key: str, path: str, request: Request, user: dict = Depends(require_auth)
):
    """对外工程通过智桥回调灵族内部服务的统一入口

    示例：linghealth 调用灵声 → POST /internal/lingvoice/analyze
          linghealth 调用灵知 → POST /internal/lingzhi/api/v1/knowledge/search
          sizhen 调度灵视     → POST /internal/lingvision/api/v1/diagnose
    """
    if backend_key not in BACKEND_SERVICES:
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=404,
            content={
                "error": "unknown_backend",
                "detail": f"backend '{backend_key}' not registered",
            },
        )
    if not _is_path_allowed(backend_key, path):
        from fastapi.responses import JSONResponse

        log.warning(
            "internal_path_denied",
            backend=backend_key,
            path=path,
            user_id=user.get("api_key", "")[:8],
        )
        return JSONResponse(
            status_code=403,
            content={
                "error": "path_not_allowed",
                "detail": f"path '{path}' not in whitelist for '{backend_key}'",
            },
        )
    return await _forward(backend_key, path, request, user)


# ============================================================
# 对外工程健康检查（无需认证，必须在通配路由之前注册）
# ============================================================


@router.get("/projects/linghealth/health")
async def linghealth_health():
    return await _forward("linghealth", "health", None, method="GET")


@router.get("/projects/lingvision/health")
async def lingvision_health():
    return await _forward("lingvision", "health", None, method="GET")


@router.get("/projects/lingvoice/health")
async def lingvoice_health():
    return await _forward("lingvoice", "health", None, method="GET")


@router.get("/projects/lingtouch/health")
async def lingtouch_health():
    return await _forward("lingtouch", "health", None, method="GET")


@router.get("/projects/sizhen/health")
async def sizhen_health():
    return await _forward("sizhen", "health", None, method="GET")


@router.get("/projects/lingwear/health")
async def lingwear_health():
    return await _forward("lingwear", "health", None, method="GET")


@router.get("/projects/linglaw/api/health")
async def linglaw_health():
    return await _forward("linglaw", "api/health", None, method="GET")


# ============================================================
# 7个对外工程项目 — 通过智桥统一暴露
# ============================================================
# 每个项目用通配路由 /projects/{project}/{path} 全量代理，
# 新增端点无需改router.py，自动透传。


@router.api_route("/projects/linghealth/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_linghealth(path: str, request: Request, user: dict = Depends(require_auth)):
    """灵康(健康总平台 :8200) — 用户管理/健康档案/AI分析/知识检索"""
    return await _forward("linghealth", path, request, user)


@router.api_route("/projects/lingvision/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_lingvision(path: str, request: Request, user: dict = Depends(require_auth)):
    """灵视(望诊+视觉教学 :8781)"""
    return await _forward("lingvision", path, request, user)


@router.api_route("/projects/lingvoice/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_lingvoice(path: str, request: Request, user: dict = Depends(require_auth)):
    """灵声(闻诊+五音辨证 :8100)"""
    return await _forward("lingvoice", path, request, user)


@router.api_route("/projects/lingtouch/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_lingtouch(path: str, request: Request, user: dict = Depends(require_auth)):
    """灵触(切诊+脉象分析 :8784)"""
    return await _forward("lingtouch", path, request, user)


@router.api_route("/projects/sizhen/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_sizhen(path: str, request: Request, user: dict = Depends(require_auth)):
    """四诊(综合会诊调度平台 :8785)"""
    return await _forward("sizhen", path, request, user)


@router.api_route("/projects/lingwear/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_lingwear(path: str, request: Request, user: dict = Depends(require_auth)):
    """灵戴(穿戴设备+康养 :8787)"""
    return await _forward("lingwear", path, request, user)


@router.api_route("/projects/linglaw/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_linglaw(path: str, request: Request, user: dict = Depends(require_auth)):
    """灵律(法律AI助手 :8002)"""
    return await _forward("linglaw", path, request, user)


# ============================================================
# 兼容旧路由（保留向后兼容，指向新的后端）
# ============================================================


@router.post("/lingvision/diagnose")
async def lingvision_diagnose_compat(request: Request, user: dict = Depends(require_auth)):
    return await _forward("lingvision", "api/v1/diagnose", request, user, "POST")


@router.post("/lingvision/teaching/analyze")
async def lingvision_teaching_compat(request: Request, user: dict = Depends(require_auth)):
    return await _forward("lingvision", "api/v1/teaching/analyze", request, user, "POST")


@router.post("/lingtouch/diagnose")
async def lingtouch_diagnose_compat(request: Request, user: dict = Depends(require_auth)):
    return await _forward("lingtouch", "api/v1/diagnose", request, user, "POST")


@router.post("/lingtouch/pulse/classify")
async def lingtouch_pulse_classify_compat(request: Request, user: dict = Depends(require_auth)):
    return await _forward("lingtouch", "api/v1/pulse/classify", request, user, "POST")


@router.post("/lingwear/data/upload")
async def lingwear_upload_compat(request: Request, user: dict = Depends(require_auth)):
    return await _forward("lingwear", "api/v1/data/upload", request, user, "POST")


@router.get("/lingwear/health/report")
async def lingwear_report_compat(user_id: str, user: dict = Depends(require_auth)):
    from .proxy import proxy_request

    return await proxy_request(
        backend=BACKEND_SERVICES["lingwear"],
        path=f"/api/v1/health/report?user_id={quote(user_id, safe='')}",
        body={},
        user=user,
        method="GET",
    )


@router.get("/lingwear/devices")
async def lingwear_devices_compat(user_id: str, user: dict = Depends(require_auth)):
    from .proxy import proxy_request

    return await proxy_request(
        backend=BACKEND_SERVICES["lingwear"],
        path=f"/api/v1/devices?user_id={quote(user_id, safe='')}",
        body={},
        user=user,
        method="GET",
    )


@router.post("/lingkang/knowledge/query")
async def lingkang_knowledge_compat(request: Request, user: dict = Depends(require_auth)):
    body = await request.json()
    from .proxy import proxy_request

    query = body.get("query", "")
    category = body.get("category")
    limit = body.get("limit", 10)
    path = f"/api/v1/search?q={quote(query, safe='')}&limit={limit}"
    if category:
        path += f"&category={quote(category, safe='')}"
    return await proxy_request(
        backend=BACKEND_SERVICES["lingzhi"],
        path=path,
        body={},
        user=user,
        method="GET",
    )


# ============================================================
# 决策面板API — 3F Phase 1内部入口（配合灵网WebUI）
# ============================================================
# 灵网决策面板的后端写入层。智桥负责auth+路由，内部成员各自实现服务接口。
# 当前状态：骨架——等内部成员服务就绪后激活转发。


class OutreachEmailAction(BaseModel):
    """灵扬外联邮件审核动作"""

    email_id: str
    action: str  # approve | reject | hold
    reviewer_note: Optional[str] = None


class ConfigSigningKey(BaseModel):
    """灵信签名密钥配置"""

    key_value: str
    rotation_period_days: int = 90


class PublishControl(BaseModel):
    """灵通问道发布控制"""

    target: str  # all | episode_id
    action: str  # resume | pause


class PodcastTopic(BaseModel):
    """灵通问道下一集主题指定"""

    topic: str
    notes: Optional[str] = None


@router.post("/api/decisions/outreach-email")
async def decisions_outreach_email(
    payload: OutreachEmailAction,
    user: dict = Depends(require_auth),
):
    """决策面板：审核灵扬P0邮件。

    转发目标：灵扬（HTTP服务待建）。当前返回202 Accepted+queued，
    等灵扬服务就绪后接入。
    """
    log.info(
        "decision_outreach_email",
        email_id=payload.email_id,
        action=payload.action,
        user_id=user.get("api_key", "")[:8],
    )
    return {
        "status": "accepted",
        "target_service": "lingyang",
        "note": "queued — lingyang HTTP service pending",
        "payload": payload.model_dump(),
    }


@router.post("/api/decisions/signing-key")
async def decisions_signing_key(
    payload: ConfigSigningKey,
    user: dict = Depends(require_auth),
):
    """决策面板：设置灵信SIGNING_KEY。

    转发目标：灵信（HTTP API待建）。
    """
    log.info(
        "decision_signing_key",
        rotation_days=payload.rotation_period_days,
        user_id=user.get("api_key", "")[:8],
    )
    # ⚠️ 不在日志中输出key_value
    return {
        "status": "accepted",
        "target_service": "lingmessage",
        "note": "queued — lingmessage config API pending",
        "rotation_period_days": payload.rotation_period_days,
    }


@router.post("/api/decisions/publish-control")
async def decisions_publish_control(
    payload: PublishControl,
    user: dict = Depends(require_auth),
):
    """决策面板：解除/暂停灵通问道内容发布。

    转发目标：灵通问道（HTTP服务待建）。
    """
    log.info(
        "decision_publish_control",
        target=payload.target,
        action=payload.action,
        user_id=user.get("api_key", "")[:8],
    )
    return {
        "status": "accepted",
        "target_service": "lingtongask",
        "note": "queued — lingtongask control API pending",
        "payload": payload.model_dump(),
    }


@router.post("/api/decisions/podcast-topic")
async def decisions_podcast_topic(
    payload: PodcastTopic,
    user: dict = Depends(require_auth),
):
    """决策面板：指定灵通问道下一集主题。

    转发目标：灵通问道（HTTP服务待建）。
    """
    log.info(
        "decision_podcast_topic",
        topic_len=len(payload.topic),
        user_id=user.get("api_key", "")[:8],
    )
    return {
        "status": "accepted",
        "target_service": "lingtongask",
        "note": "queued — lingtongask topic API pending",
        "topic": payload.topic,
    }


@router.get("/api/decisions/pending")
async def decisions_pending(user: dict = Depends(require_auth)):
    """决策面板：列出待决策项。

    数据来源：灵网聚合（LingBus线程/灵扬邮件/灵通问道状态）。
    当前返回占位结构——灵网接入后填充实际数据。
    """
    return {
        "pending_decisions": [],
        "note": "placeholder — lingweb aggregator pending",
    }


# 灵依已退出，路由保留但标记deprecated
@router.post("/lingyi/knowledge/query", deprecated=True)
async def lingyi_knowledge_compat(request: Request, user: dict = Depends(require_auth)):
    body = await request.json()
    from .proxy import proxy_request

    query = body.get("query", "")
    category = body.get("category")
    limit = body.get("limit", 10)
    path = f"/api/v1/search?q={quote(query, safe='')}&limit={limit}"
    if category:
        path += f"&category={quote(category, safe='')}"
    return await proxy_request(
        backend=BACKEND_SERVICES["lingzhi"],
        path=path,
        body={},
        user=user,
        method="GET",
    )

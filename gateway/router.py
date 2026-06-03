"""
路由模块 - 7个对外工程项目 + 灵族内部服务，统一通过智桥网关
"""
from fastapi import APIRouter, Request, Depends
from pydantic import BaseModel
from typing import Optional
from urllib.parse import quote
import structlog

from .config import BACKEND_SERVICES
from .auth import require_auth, optional_auth
from .crypto import is_encrypted_request, is_sensitive_backend, ENCRYPTED_HEADER

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


async def _forward(backend_key: str, path: str, request: Request,
                   user: dict = None, method: str = None):
    """通用转发：根据backend_key查BACKEND_SERVICES，proxy_request到后端"""
    from .proxy import proxy_request
    backend = BACKEND_SERVICES[backend_key]
    body = {}
    if method in (None, "POST", "PUT"):
        try:
            body = await request.json()
        except Exception:
            body = {}

    if is_sensitive_backend(backend_key):
        headers = dict(request.headers) if request else {}
        encrypted = is_encrypted_request(headers)
        log.info("sensitive_backend_access",
                 backend=backend_key, path=path,
                 encrypted=encrypted,
                 user_id=user.get("api_key", "")[:8] if user else "")
        if not encrypted:
            from fastapi.responses import JSONResponse
            log.warning("sensitive_route_unencrypted",
                        backend=backend_key, path=path)
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
    )


# ============================================================
# P0: 网关健康检查
# ============================================================

@router.get("/v1/health")
async def health_check():
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
async def podcast_episodes():
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

@router.api_route("/internal/{backend_key}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def internal_passthrough(backend_key: str, path: str, request: Request,
                                user: dict = Depends(require_auth)):
    """对外工程通过智桥回调灵族内部服务的统一入口

    示例：linghealth 调用灵声 → POST /internal/lingvoice/analyze
          linghealth 调用灵知 → POST /internal/lingzhi/api/v1/knowledge/search
          sizhen 调度灵视     → POST /internal/lingvision/api/v1/diagnose
    """
    if backend_key not in BACKEND_SERVICES:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=404,
            content={"error": f"unknown_backend", "detail": f"backend '{backend_key}' not registered"},
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

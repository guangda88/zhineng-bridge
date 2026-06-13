"""
反向代理核心模块
"""

import asyncio
import os
import time
import uuid
from typing import Any, Dict, Optional

import structlog
from fastapi import HTTPException, status
from httpx import AsyncClient, ConnectError, HTTPError, TimeoutException

from .circuit import CircuitState, get_circuit_state, record_circuit_failure, record_circuit_success
from .config import BACKEND_SERVICES

log = structlog.get_logger()


class RetryQueue:
    """离线消息队列 — 后端不可达时暂存请求，后台重试"""

    def __init__(self, max_size: int = 1000, max_retries: int = 3, retry_delay: float = 30.0):
        self._queue: list[Dict[str, Any]] = []
        self.max_size = max_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._task: Optional[asyncio.Task] = None

    def enqueue(
        self, backend: str, path: str, body: dict, user: dict, method: str
    ) -> Optional[str]:
        if len(self._queue) >= self.max_size:
            log.warning("retry_queue_full", size=len(self._queue))
            return None
        entry = {
            "id": str(uuid.uuid4())[:8],
            "backend": backend,
            "path": path,
            "body": body,
            "user": user,
            "method": method,
            "retries": 0,
            "enqueued_at": time.time(),
        }
        self._queue.append(entry)
        log.info("retry_enqueued", entry_id=entry["id"], backend=backend, path=path)
        return entry["id"]

    def pending(self) -> int:
        return len(self._queue)

    async def start(self):
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._process_loop())

    async def stop(self):
        if self._task and not self._task.done():
            self._task.cancel()

    async def _process_loop(self):
        while True:
            try:
                await self._process_one()
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error("retry_queue_error", error=str(e))
            await asyncio.sleep(self.retry_delay)

    async def _process_one(self):
        if not self._queue:
            return
        entry = self._queue[0]
        service_name = _get_service_name(entry["backend"])
        circuit = get_circuit_state(service_name)
        if circuit == CircuitState.OPEN:
            return
        try:
            async with AsyncClient(timeout=30.0) as client:
                url = f"{entry['backend']}{entry['path']}"
                headers = {
                    "X-API-Key": os.environ.get(
                        "ZHIBRIDGE_BACKEND_TOKEN", entry["user"].get("api_key", "")
                    ),
                    "X-Forwarded-By": "zhibridge",
                    "Content-Type": "application/json",
                }
                if entry["method"] == "POST":
                    resp = await client.post(url, json=entry["body"], headers=headers)
                elif entry["method"] == "GET":
                    resp = await client.get(url, headers=headers)
                elif entry["method"] == "PUT":
                    resp = await client.put(url, json=entry["body"], headers=headers)
                elif entry["method"] == "DELETE":
                    resp = await client.delete(url, headers=headers)
                else:
                    self._queue.pop(0)
                    return
                if resp.status_code < 500:
                    self._queue.pop(0)
                    record_circuit_success(service_name)
                    log.info("retry_delivered", entry_id=entry["id"], status=resp.status_code)
                else:
                    entry["retries"] += 1
                    if entry["retries"] >= self.max_retries:
                        self._queue.pop(0)
                        log.warning(
                            "retry_exhausted", entry_id=entry["id"], retries=entry["retries"]
                        )
                    else:
                        self._queue.append(self._queue.pop(0))
        except (TimeoutException, ConnectError, HTTPError) as e:
            entry["retries"] += 1
            if entry["retries"] >= self.max_retries:
                self._queue.pop(0)
                log.warning("retry_exhausted", entry_id=entry["id"], error=str(e))
            else:
                self._queue.append(self._queue.pop(0))


retry_queue = RetryQueue()


async def proxy_request(
    backend: str,
    path: str,
    body: dict,
    user: dict,
    method: str = "POST",
    urgent: bool = False,
) -> dict:
    """通用反向代理函数，内置熔断器。

    SDTH: urgent=True时，请求跳过重试队列（直接失败），使用更短超时快速反馈。
    """
    service_name = _get_service_name(backend)
    circuit = get_circuit_state(service_name)
    if circuit == CircuitState.OPEN:
        if urgent:
            log.warning("urgent_blocked_by_circuit", service=service_name, path=path)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Backend {service_name} circuit breaker open",
        )

    url = f"{backend}{path}"
    internal_token = os.environ.get("ZHIBRIDGE_BACKEND_TOKEN", user.get("api_key", ""))
    headers = {
        "X-API-Key": internal_token,
        "X-Forwarded-By": "zhibridge",
        "Content-Type": "application/json",
    }
    if urgent:
        headers["X-Priority"] = "urgent"
    timeout = 30.0 if urgent else 120.0
    try:
        async with AsyncClient(timeout=timeout) as client:
            if method == "POST":
                resp = await client.post(url, json=body, headers=headers)
            elif method == "GET":
                resp = await client.get(url, headers=headers)
            elif method == "PUT":
                resp = await client.put(url, json=body, headers=headers)
            elif method == "DELETE":
                resp = await client.delete(url, headers=headers)
            else:
                raise HTTPException(
                    status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                    detail=f"Method {method} not allowed",
                )

            if resp.status_code >= 500:
                log.error("proxy_backend_error", url=url, status=resp.status_code, urgent=urgent)
                record_circuit_failure(service_name)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Backend error: {resp.status_code}",
                )

            record_circuit_success(service_name)
            return resp.json()

    except TimeoutException:
        log.warning("proxy_timeout", url=url, urgent=urgent)
        record_circuit_failure(service_name)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Backend timeout" + (" (urgent)" if urgent else ""),
        )
    except ConnectError as e:
        log.warning("proxy_connect_error", url=url, error=str(e), urgent=urgent)
        record_circuit_failure(service_name)
        if not urgent and method == "POST":
            entry_id = retry_queue.enqueue(backend, path, body, user, method)
            if entry_id:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Backend unavailable. Request queued for retry (id={entry_id})",
                )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Backend unavailable",
        )
    except HTTPError as e:
        log.error("proxy_http_error", url=url, error=str(e), urgent=urgent)
        record_circuit_failure(service_name)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Proxy error: {str(e)}",
        )


def _get_service_name(backend: str) -> str:
    """从URL反查服务名"""
    for name, url in BACKEND_SERVICES.items():
        if url in backend:
            return name
    return backend

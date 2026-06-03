"""
后端健康检查 + 熔断器
"""
from httpx import AsyncClient, ConnectError, TimeoutException
from datetime import datetime, timedelta
from typing import Dict
import structlog

from .config import BACKEND_SERVICES

log = structlog.get_logger()

# 熔断器状态
class CircuitState:
    OPEN = "open"      # 熔断开启，请求直接返回503
    HALF_OPEN = "half_open"  # 测试状态
    CLOSED = "closed"  # 正常

_circuit_states: Dict[str, CircuitState] = {}
_last_failure: Dict[str, datetime] = {}
_circuit_window = timedelta(minutes=5)
_circuit_threshold = 3


def get_circuit_state(service: str) -> CircuitState:
    """获取服务熔断状态"""
    if service not in _circuit_states:
        return CircuitState.CLOSED

    state = _circuit_states[service]
    if state == CircuitState.OPEN:
        last_fail = _last_failure.get(service)
        if last_fail and datetime.now() - last_fail > _circuit_window:
            _circuit_states[service] = CircuitState.HALF_OPEN
            return CircuitState.HALF_OPEN
    return state


def record_circuit_failure(service: str):
    """记录失败，触发熔断"""
    failures = _circuit_states.get(f"{service}_failures", 0) + 1
    _circuit_states[f"{service}_failures"] = failures
    _last_failure[service] = datetime.now()

    if failures >= _circuit_threshold:
        _circuit_states[service] = CircuitState.OPEN
        log.warning("circuit_breaker_open", service=service, failures=failures)


def record_circuit_success(service: str):
    """记录成功，关闭熔断"""
    _circuit_states[service] = CircuitState.CLOSED
    _circuit_states[f"{service}_failures"] = 0


async def check_backend_health(service: str, url: str) -> bool:
    """检查后端服务健康状态，兼容灵族不同的健康检查端点"""
    health_endpoints = ["/health", "/api/status", "/api/health", "/"]

    for endpoint in health_endpoints:
        try:
            async with AsyncClient(timeout=2.0) as client:
                resp = await client.get(f"{url}{endpoint}")
                if resp.status_code == 200:
                    return True
        except (TimeoutException, ConnectError):
            continue
        except Exception:
            continue
    return False


async def get_backend_health_status() -> dict:
    """获取所有后端服务健康状态"""
    statuses = {}
    for name, url in BACKEND_SERVICES.items():
        is_healthy = await check_backend_health(name, url)
        circuit = get_circuit_state(name)
        statuses[name] = {
            "url": url,
            "healthy": is_healthy,
            "circuit": circuit,
        }
    return statuses
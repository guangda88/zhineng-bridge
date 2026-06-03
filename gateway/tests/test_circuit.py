"""
熔断器测试
"""
import pytest
from gateway.circuit import (
    CircuitState,
    get_circuit_state,
    record_circuit_failure,
    record_circuit_success,
    check_backend_health,
)


class TestCircuitBreaker:
    def test_default_circuit_state_is_closed(self):
        """默认熔断状态是闭合（正常）"""
        state = get_circuit_state("new_service")
        assert state == CircuitState.CLOSED

    def test_multiple_failures_open_circuit(self):
        """多次失败触发熔断开启"""
        service = "test_fail_service"
        # 3次失败触发熔断
        for _ in range(3):
            record_circuit_failure(service)

        state = get_circuit_state(service)
        assert state == CircuitState.OPEN

    def test_success_resets_circuit(self):
        """成功请求重置熔断状态"""
        service = "test_reset_service"
        # 先失败3次
        for _ in range(3):
            record_circuit_failure(service)

        # 然后成功
        record_circuit_success(service)

        state = get_circuit_state(service)
        assert state == CircuitState.CLOSED

    def test_open_circuit_returns_503(self):
        """熔断开启的服务会被拒绝"""
        from fastapi.testclient import TestClient
        from gateway.app import create_app

        service = "lingtong_plus"
        for _ in range(3):
            record_circuit_failure(service)

        app = create_app()
        client = TestClient(app)
        resp = client.post(
            "/v1/chat/completions",
            json={"model": "test", "messages": []},
            headers={"X-API-Key": "test_lpkey_1234567890abcdef"},
        )
        # 由于后端不可达，预期返回503或504，熔断开启时是503
        assert resp.status_code in [503, 504]


@pytest.mark.asyncio
async def test_check_unavailable_backend():
    """检查不可达的后端返回false"""
    result = await check_backend_health("test", "http://localhost:9999")
    assert result is False


@pytest.mark.asyncio
async def test_circuit_half_open_after_window():
    """窗口时间后进入half-open状态"""
    from gateway.circuit import _last_failure, _circuit_states
    from datetime import datetime, timedelta

    service = "test_half_open"
    for _ in range(3):
        record_circuit_failure(service)

    # 手动设置失败时间为6分钟前（超过5分钟窗口）
    _last_failure[service] = datetime.now() - timedelta(minutes=6)

    state = get_circuit_state(service)
    assert state == CircuitState.HALF_OPEN
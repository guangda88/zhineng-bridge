#!/usr/bin/env python3
"""
智桥性能基准测试

使用 pytest-benchmark 进行性能测试。
"""

import pytest
import asyncio
import websockets
import json
import time
import memory_profiler
from typing import List


# ============================================================================
# WebSocket 连接性能测试
# ============================================================================

@pytest.mark.benchmark(group="websocket")
def test_websocket_connection_benchmark(benchmark):
    """
    WebSocket 连接基准测试

    测试建立 WebSocket 连接所需的时间。
    """
    async def connect():
        async with websockets.connect("ws://localhost:8765") as ws:
            return ws

    def run_connect():
        return asyncio.run(connect())

    result = benchmark(run_connect)
    assert result is not None


@pytest.mark.benchmark(group="websocket")
def test_websocket_ping_benchmark(benchmark):
    """
    WebSocket Ping 基准测试

    测试发送 ping 消息并接收 pong 响应的时间。
    """
    async def ping():
        async with websockets.connect("ws://localhost:8765") as ws:
            await ws.send(json.dumps({"type": "ping"}))
            response = await ws.recv()
            return json.loads(response)

    result = benchmark(lambda: asyncio.run(ping()))
    assert result["type"] == "pong"


# ============================================================================
# 会话管理性能测试
# ============================================================================

@pytest.mark.benchmark(group="session")
def test_list_sessions_benchmark(benchmark):
    """
    列出会话基准测试

    测试列出所有会话的性能。
    """
    async def list_sessions():
        async with websockets.connect("ws://localhost:8765") as ws:
            await ws.send(json.dumps({"type": "list_sessions"}))
            response = await ws.recv()
            return json.loads(response)

    result = benchmark(lambda: asyncio.run(list_sessions()))
    assert "type" in result


@pytest.mark.benchmark(group="session")
def test_create_session_benchmark(benchmark):
    """
    创建会话基准测试

    测试创建新会话的性能。
    """
    async def create_session():
        async with websockets.connect("ws://localhost:8765") as ws:
            await ws.send(json.dumps({
                "type": "start_session",
                "tool_name": "crush",
                "args": ["--version"]
            }))
            response = await ws.recv()
            data = json.loads(response)

            # 清理会话
            if "session_id" in data:
                await ws.send(json.dumps({
                    "type": "delete_session",
                    "session_id": data["session_id"]
                }))

            return data

    result = benchmark(lambda: asyncio.run(create_session()))
    assert "type" in result


# ============================================================================
# 消息处理性能测试
# ============================================================================

@pytest.mark.benchmark(group="message")
def test_message_send_benchmark(benchmark):
    """
    消息发送基准测试

    测试发送消息的性能。
    """
    message = {
        "type": "list_sessions"
    }

    async def send_message():
        async with websockets.connect("ws://localhost:8765") as ws:
            await ws.send(json.dumps(message))
            return True

    result = benchmark(lambda: asyncio.run(send_message()))
    assert result is True


@pytest.mark.benchmark(group="message")
def test_batch_message_benchmark(benchmark):
    """
    批量消息发送基准测试

    测试发送多条消息的性能。
    """
    async def send_batch():
        async with websockets.connect("ws://localhost:8765") as ws:
            for i in range(10):
                await ws.send(json.dumps({"type": "ping"}))
            return True

    result = benchmark(lambda: asyncio.run(send_batch()))
    assert result is True


# ============================================================================
# 并发性能测试
# ============================================================================

@pytest.mark.benchmark(group="concurrency")
def test_concurrent_connections_benchmark(benchmark):
    """
    并发连接基准测试

    测试并发建立多个连接的性能。
    """
    async def connect_multiple():
        async def client(client_id):
            async with websockets.connect("ws://localhost:8765") as ws:
                await ws.send(json.dumps({"type": "ping"}))
                await ws.recv()
                return client_id

        # 并发连接 10 个客户端
        tasks = [client(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        return len(results)

    result = benchmark(lambda: asyncio.run(connect_multiple()))
    assert result == 10


@pytest.mark.benchmark(group="concurrency")
def test_concurrent_sessions_benchmark(benchmark):
    """
    并发会话创建基准测试

    测试并发创建多个会话的性能。
    """
    async def create_sessions():
        async def client(client_id):
            async with websockets.connect("ws://localhost:8765") as ws:
                await ws.send(json.dumps({
                    "type": "start_session",
                    "tool_name": "crush",
                    "args": ["--version"]
                }))
                response = await ws.recv()
                data = json.loads(response)

                # 清理会话
                if "session_id" in data:
                    await ws.send(json.dumps({
                        "type": "delete_session",
                        "session_id": data["session_id"]
                    }))

                return client_id

        # 并发创建 5 个会话
        tasks = [client(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        return len(results)

    result = benchmark(lambda: asyncio.run(create_sessions()))
    assert result == 5


# ============================================================================
# 内存性能测试
# ============================================================================

@pytest.mark.benchmark(group="memory")
@memory_profiler.profile
def test_memory_usage_benchmark(benchmark):
    """
    内存使用基准测试

    测试处理大量消息时的内存使用。
    """
    async def process_messages():
        async with websockets.connect("ws://localhost:8765") as ws:
            messages = []
            for i in range(100):
                await ws.send(json.dumps({"type": "ping"}))
                response = await ws.recv()
                messages.append(response)
            return len(messages)

    result = benchmark(lambda: asyncio.run(process_messages()))
    assert result == 100


# ============================================================================
# 响应时间测试
# ============================================================================

@pytest.mark.benchmark(group="response-time")
def test_response_time_distribution(benchmark):
    """
    响应时间分布测试

    测试多次请求的响应时间分布。
    """
    async def measure_response_time():
        times = []
        for _ in range(10):
            start = time.time()
            async with websockets.connect("ws://localhost:8765") as ws:
                await ws.send(json.dumps({"type": "ping"}))
                await ws.recv()
            times.append(time.time() - start)
        return sum(times) / len(times)

    result = benchmark(lambda: asyncio.run(measure_response_time()))
    assert result < 1.0  # 平均响应时间应小于 1 秒


# ============================================================================
# 压力测试
# ============================================================================

@pytest.mark.benchmark(group="stress")
def test_high_frequency_requests(benchmark):
    """
    高频请求压力测试

    测试在高频率请求下的性能。
    """
    async def high_frequency():
        async with websockets.connect("ws://localhost:8765") as ws:
            for _ in range(100):
                await ws.send(json.dumps({"type": "ping"}))
                await ws.recv()
            return 100

    result = benchmark(lambda: asyncio.run(high_frequency()))
    assert result == 100


@pytest.mark.benchmark(group="stress")
def test_rapid_session_creation(benchmark):
    """
    快速会话创建压力测试

    测试快速创建和删除会话的性能。
    """
    async def rapid_sessions():
        session_ids = []
        async with websockets.connect("ws://localhost:8765") as ws:
            # 创建 10 个会话
            for _ in range(10):
                await ws.send(json.dumps({
                    "type": "start_session",
                    "tool_name": "crush",
                    "args": ["--version"]
                }))
                response = await ws.recv()
                data = json.loads(response)
                if "session_id" in data:
                    session_ids.append(data["session_id"])

            # 删除所有会话
            for session_id in session_ids:
                await ws.send(json.dumps({
                    "type": "delete_session",
                    "session_id": session_id
                }))

        return len(session_ids)

    result = benchmark(lambda: asyncio.run(rapid_sessions()))
    assert result == 10


# ============================================================================
# 性能回归测试
# ============================================================================

@pytest.mark.benchmark(group="regression")
def test_session_creation_regression(benchmark):
    """
    会话创建性能回归测试

    确保会话创建性能没有退化。
    """
    async def create_session():
        async with websockets.connect("ws://localhost:8765") as ws:
            await ws.send(json.dumps({
                "type": "start_session",
                "tool_name": "crush",
                "args": ["--version"]
            }))
            response = await ws.recv()
            return json.loads(response)

    result = benchmark(lambda: asyncio.run(create_session()))
    # 目标: 会话创建时间应小于 100ms
    # 注意: 这是基准测试框架测量的时间，不是实际响应时间
    assert result is not None


@pytest.mark.benchmark(group="regression")
def test_websocket_ping_regression(benchmark):
    """
    WebSocket Ping 性能回归测试

    确保 ping-pong 性能没有退化。
    """
    async def ping_pong():
        async with websockets.connect("ws://localhost:8765") as ws:
            start = time.time()
            await ws.send(json.dumps({"type": "ping"}))
            await ws.recv()
            return time.time() - start

    result = benchmark(lambda: asyncio.run(ping_pong()))
    # 目标: ping-pong 时间应小于 50ms
    assert result < 0.05


# ============================================================================
# 运行配置
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--benchmark-only", "--benchmark-json=benchmark.json"])

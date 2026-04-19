#!/usr/bin/env python3
"""
智桥性能基准测试 — 自托管 AIRelayServer

测试指标:
- WebSocket 连接建立时间
- Ping/Pong 往返延迟
- 消息路由延迟
- 后端注册速度
- 并发连接吞吐量
"""

import asyncio
import json
import os
import socket
import sys
import time

import pytest
import pytest_asyncio
import websockets

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../relay-server"))
from server import AIRelayServer


def _find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest_asyncio.fixture
async def relay_server():
    port = _find_free_port()
    server = AIRelayServer(host="127.0.0.1", port=port)
    server.port = port

    async def _serve():
        try:
            async with await websockets.serve(
                server._handle_connection,
                server.host,
                server.port,
                ping_interval=30,
                ping_timeout=60,
            ) as ws_server:
                server.server = ws_server
                await asyncio.Future()
        except Exception:
            pass

    task = asyncio.create_task(_serve())
    await asyncio.sleep(0.3)
    yield server, port
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


@pytest.mark.benchmark
class TestConnectionPerformance:
    """连接性能测试"""

    @pytest.mark.asyncio
    async def test_connection_time(self, relay_server):
        server, port = relay_server
        uri = f"ws://127.0.0.1:{port}"

        times = []
        for _ in range(10):
            start = time.monotonic()
            async with websockets.connect(uri) as ws:
                await ws.send(json.dumps({"type": "ping"}))
                await ws.recv()
            elapsed = time.monotonic() - start
            times.append(elapsed)

        avg = sum(times) / len(times)
        assert avg < 0.5, f"连接+ping平均耗时 {avg:.3f}s > 0.5s"
        print(f"\n连接+ping 平均: {avg*1000:.1f}ms")

    @pytest.mark.asyncio
    async def test_connection_establishment_only(self, relay_server):
        server, port = relay_server
        uri = f"ws://127.0.0.1:{port}"

        times = []
        for _ in range(20):
            start = time.monotonic()
            async with websockets.connect(uri):
                pass
            times.append(time.monotonic() - start)

        avg = sum(times) / len(times)
        assert avg < 0.2, f"连接建立平均耗时 {avg:.3f}s > 0.2s"
        print(f"\n连接建立 平均: {avg*1000:.1f}ms")


@pytest.mark.benchmark
class TestPingPongPerformance:
    """Ping/Pong 性能测试"""

    @pytest.mark.asyncio
    async def test_ping_latency(self, relay_server):
        server, port = relay_server
        uri = f"ws://127.0.0.1:{port}"

        async with websockets.connect(uri) as ws:
            times = []
            for _ in range(50):
                start = time.monotonic()
                await ws.send(json.dumps({"type": "ping"}))
                resp = json.loads(await ws.recv())
                elapsed = time.monotonic() - start
                assert resp["type"] == "pong"
                times.append(elapsed)

        avg = sum(times) / len(times)
        p95 = sorted(times)[int(len(times) * 0.95)]
        assert avg < 0.05, f"ping平均耗时 {avg*1000:.1f}ms > 50ms"
        print(f"\nping/pong 平均: {avg*1000:.2f}ms, P95: {p95*1000:.2f}ms")

    @pytest.mark.asyncio
    async def test_batch_ping_throughput(self, relay_server):
        server, port = relay_server
        uri = f"ws://127.0.0.1:{port}"
        num = 100

        async with websockets.connect(uri) as ws:
            start = time.monotonic()
            for _ in range(num):
                await ws.send(json.dumps({"type": "ping"}))
            for _ in range(num):
                resp = json.loads(await ws.recv())
                assert resp["type"] == "pong"
            elapsed = time.monotonic() - start

        rate = num / elapsed
        print(f"\n吞吐量: {rate:.0f} msg/s ({num} msg in {elapsed:.3f}s)")
        assert rate > 100, f"吞吐量 {rate:.0f} < 100 msg/s"


@pytest.mark.benchmark
class TestChatRoutingPerformance:
    """消息路由性能测试"""

    @pytest.mark.asyncio
    async def test_chat_round_trip_latency(self, relay_server):
        server, port = relay_server
        uri = f"ws://127.0.0.1:{port}"

        async with websockets.connect(uri) as backend_ws:
            await backend_ws.send(
                json.dumps(
                    {
                        "type": "register_backend",
                        "backend_id": "perf-ai",
                    }
                )
            )
            await backend_ws.recv()

            async with websockets.connect(uri) as user_ws:
                times = []
                for i in range(20):
                    start = time.monotonic()
                    await user_ws.send(
                        json.dumps(
                            {
                                "type": "chat",
                                "target": "perf-ai",
                                "text": f"perf-{i}",
                            }
                        )
                    )

                    backend_msg = json.loads(await asyncio.wait_for(backend_ws.recv(), timeout=2))
                    request_id = backend_msg["request_id"]

                    await backend_ws.send(
                        json.dumps(
                            {
                                "type": "reply",
                                "request_id": request_id,
                                "text": f"reply-{i}",
                            }
                        )
                    )

                    user_reply = json.loads(await asyncio.wait_for(user_ws.recv(), timeout=2))
                    elapsed = time.monotonic() - start
                    assert user_reply["text"] == f"reply-{i}"
                    times.append(elapsed)

        avg = sum(times) / len(times)
        print(f"\nchat→reply 往返 平均: {avg*1000:.1f}ms")
        assert avg < 0.2, f"chat往返平均耗时 {avg*1000:.1f}ms > 200ms"


@pytest.mark.benchmark
class TestBackendRegistrationPerformance:
    """后端注册性能测试"""

    @pytest.mark.asyncio
    async def test_registration_speed(self, relay_server):
        server, port = relay_server
        uri = f"ws://127.0.0.1:{port}"

        times = []
        for i in range(10):
            start = time.monotonic()
            async with websockets.connect(uri) as ws:
                await ws.send(
                    json.dumps(
                        {
                            "type": "register_backend",
                            "backend_id": f"bench-{i}",
                        }
                    )
                )
                resp = json.loads(await ws.recv())
                elapsed = time.monotonic() - start
                assert resp["type"] == "backend_registered"
                times.append(elapsed)

        avg = sum(times) / len(times)
        print(f"\n后端注册 平均: {avg*1000:.1f}ms")
        assert avg < 0.2, f"后端注册平均耗时 {avg*1000:.1f}ms > 200ms"


@pytest.mark.benchmark
class TestConcurrentPerformance:
    """并发性能测试"""

    @pytest.mark.asyncio
    async def test_concurrent_ping_pong(self, relay_server):
        server, port = relay_server
        uri = f"ws://127.0.0.1:{port}"
        num_clients = 20

        async def client_ping(client_id):
            async with websockets.connect(uri) as ws:
                start = time.monotonic()
                await ws.send(json.dumps({"type": "ping"}))
                resp = json.loads(await ws.recv())
                elapsed = time.monotonic() - start
                assert resp["type"] == "pong"
                return elapsed

        start = time.monotonic()
        tasks = [asyncio.create_task(client_ping(i)) for i in range(num_clients)]
        results = await asyncio.gather(*tasks)
        total = time.monotonic() - start

        avg = sum(results) / len(results)
        print(f"\n并发 {num_clients} 客户端: 总耗时 {total:.3f}s, 平均 {avg*1000:.1f}ms")
        assert len(results) == num_clients
        assert total < 5.0, f"{num_clients} 并发总耗时 {total:.3f}s > 5s"

    @pytest.mark.asyncio
    async def test_concurrent_chat_throughput(self, relay_server):
        server, port = relay_server
        uri = f"ws://127.0.0.1:{port}"
        num_users = 10

        async with websockets.connect(uri) as backend_ws:
            await backend_ws.send(
                json.dumps(
                    {
                        "type": "register_backend",
                        "backend_id": "conc-ai",
                    }
                )
            )
            await backend_ws.recv()

            async def user_chat(uid):
                async with websockets.connect(uri) as ws:
                    await ws.send(
                        json.dumps(
                            {
                                "type": "chat",
                                "target": "conc-ai",
                                "text": f"user-{uid}",
                            }
                        )
                    )
                    return uid

            start = time.monotonic()
            tasks = [asyncio.create_task(user_chat(i)) for i in range(num_users)]
            await asyncio.gather(*tasks)

            received = []
            for _ in range(num_users):
                msg = json.loads(await asyncio.wait_for(backend_ws.recv(), timeout=5))
                received.append(msg["text"])
            elapsed = time.monotonic() - start

        print(f"\n并发 {num_users} 聊天: {elapsed:.3f}s")
        assert len(received) == num_users


@pytest.mark.benchmark
class TestStressPerformance:
    """压力性能测试"""

    @pytest.mark.asyncio
    async def test_high_frequency_pings(self, relay_server):
        server, port = relay_server
        uri = f"ws://127.0.0.1:{port}"
        num = 200

        async with websockets.connect(uri) as ws:
            start = time.monotonic()
            for _ in range(num):
                await ws.send(json.dumps({"type": "ping"}))
            for _ in range(num):
                resp = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
                assert resp["type"] == "pong"
            elapsed = time.monotonic() - start

        rate = num / elapsed
        print(f"\n高频 {num} ping: {elapsed:.3f}s, {rate:.0f} msg/s")
        assert rate > 50, f"吞吐量 {rate:.0f} < 50 msg/s"

    @pytest.mark.asyncio
    async def test_rapid_register_disconnect(self, relay_server):
        server, port = relay_server
        uri = f"ws://127.0.0.1:{port}"
        num = 20

        start = time.monotonic()
        for i in range(num):
            async with websockets.connect(uri) as ws:
                await ws.send(
                    json.dumps(
                        {
                            "type": "register_backend",
                            "backend_id": f"stress-{i}",
                        }
                    )
                )
                resp = json.loads(await ws.recv())
                assert resp["type"] == "backend_registered"
        elapsed = time.monotonic() - start

        rate = num / elapsed
        print(f"\n快速注册/断开 {num} 次: {elapsed:.3f}s, {rate:.1f} ops/s")
        await asyncio.sleep(0.3)
        assert len(server.backends) == 0

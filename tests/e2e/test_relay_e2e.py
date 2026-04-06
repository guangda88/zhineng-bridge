#!/usr/bin/env python3
"""
E2E 测试 — AIRelayServer 全链路测试

测试覆盖:
- WebSocket 连接/断开
- 消息路由: 用户 → AI后端 → 用户
- 后端注册/列表
- 广播/推送
- 心跳
"""

import asyncio
import json
import pytest
import pytest_asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../relay-server"))

from server import AIRelayServer

try:
    import websockets
    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False


def _find_free_port():
    import socket
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


@pytest.mark.skipif(not HAS_WEBSOCKETS, reason="websockets not installed")
class TestRelayE2E:
    """端到端 WebSocket 测试"""

    @pytest.mark.asyncio
    async def test_ping_pong(self, relay_server):
        server, port = relay_server
        uri = f"ws://127.0.0.1:{port}"

        async with websockets.connect(uri) as ws:
            await ws.send(json.dumps({"type": "ping"}))
            resp = json.loads(await ws.recv())
            assert resp["type"] == "pong"
            assert "timestamp" in resp

    @pytest.mark.asyncio
    async def test_register_backend_and_list(self, relay_server):
        server, port = relay_server
        uri = f"ws://127.0.0.1:{port}"

        async with websockets.connect(uri) as backend_ws:
            await backend_ws.send(json.dumps({
                "type": "register_backend",
                "backend_id": "test-ai",
                "name": "Test AI",
                "description": "Test backend",
            }))
            resp = json.loads(await backend_ws.recv())
            assert resp["type"] == "backend_registered"
            assert resp["backend_id"] == "test-ai"

            async with websockets.connect(uri) as user_ws:
                await user_ws.send(json.dumps({"type": "list_backends"}))
                resp = json.loads(await user_ws.recv())
                assert resp["type"] == "backends_list"
                assert len(resp["backends"]) == 1
                assert resp["backends"][0]["id"] == "test-ai"

    @pytest.mark.asyncio
    async def test_chat_route_to_backend(self, relay_server):
        server, port = relay_server
        uri = f"ws://127.0.0.1:{port}"

        async with websockets.connect(uri) as backend_ws:
            await backend_ws.send(json.dumps({
                "type": "register_backend",
                "backend_id": "chat-ai",
            }))
            await backend_ws.recv()

            async with websockets.connect(uri) as user_ws:
                await user_ws.send(json.dumps({
                    "type": "chat",
                    "target": "chat-ai",
                    "text": "Hello AI!",
                }))

                backend_msg = json.loads(await asyncio.wait_for(backend_ws.recv(), timeout=2))
                assert backend_msg["type"] == "chat"
                assert backend_msg["text"] == "Hello AI!"
                assert "request_id" in backend_msg

                request_id = backend_msg["request_id"]

                await backend_ws.send(json.dumps({
                    "type": "reply",
                    "request_id": request_id,
                    "text": "Hello human!",
                }))

                user_reply = json.loads(await asyncio.wait_for(user_ws.recv(), timeout=2))
                assert user_reply["type"] == "reply"
                assert user_reply["text"] == "Hello human!"

    @pytest.mark.asyncio
    async def test_switch_backend(self, relay_server):
        server, port = relay_server
        uri = f"ws://127.0.0.1:{port}"

        async with websockets.connect(uri) as ws:
            await ws.send(json.dumps({"type": "switch_backend", "target": "other-ai"}))
            resp = json.loads(await ws.recv())
            assert resp["type"] == "backend_switched"
            assert resp["backend_id"] == "other-ai"

    @pytest.mark.asyncio
    async def test_unknown_type_returns_error(self, relay_server):
        server, port = relay_server
        uri = f"ws://127.0.0.1:{port}"

        async with websockets.connect(uri) as ws:
            await ws.send(json.dumps({"type": "nonexistent"}))
            resp = json.loads(await ws.recv())
            assert resp["type"] == "error"
            assert "Unknown" in resp["message"]

    @pytest.mark.asyncio
    async def test_invalid_json(self, relay_server):
        server, port = relay_server
        uri = f"ws://127.0.0.1:{port}"

        async with websockets.connect(uri) as ws:
            await ws.send("not json{{{")
            resp = json.loads(await ws.recv())
            assert resp["type"] == "error"
            assert "Invalid JSON" in resp["message"]

    @pytest.mark.asyncio
    async def test_chat_no_backend_error(self, relay_server):
        server, port = relay_server
        uri = f"ws://127.0.0.1:{port}"

        async with websockets.connect(uri) as ws:
            await ws.send(json.dumps({"type": "chat", "text": "hello"}))
            resp = json.loads(await ws.recv())
            assert resp["type"] == "error"
            assert "没有可用的AI后端" in resp["message"]

    @pytest.mark.asyncio
    async def test_backend_disconnect_cleans_up(self, relay_server):
        server, port = relay_server
        uri = f"ws://127.0.0.1:{port}"

        async with websockets.connect(uri) as backend_ws:
            await backend_ws.send(json.dumps({
                "type": "register_backend",
                "backend_id": "temp-ai",
            }))
            await backend_ws.recv()
            assert "temp-ai" in server.backends

        await asyncio.sleep(0.2)
        assert "temp-ai" not in server.backends

    @pytest.mark.asyncio
    async def test_multiple_concurrent_chats(self, relay_server):
        server, port = relay_server
        uri = f"ws://127.0.0.1:{port}"

        async with websockets.connect(uri) as backend_ws:
            await backend_ws.send(json.dumps({
                "type": "register_backend",
                "backend_id": "multi-ai",
            }))
            await backend_ws.recv()

            async def user_chat(msg_text):
                async with websockets.connect(uri) as user_ws:
                    await user_ws.send(json.dumps({
                        "type": "chat",
                        "target": "multi-ai",
                        "text": msg_text,
                    }))
                    return msg_text

            tasks = [asyncio.create_task(user_chat(f"msg-{i}")) for i in range(5)]
            await asyncio.gather(*tasks)

            received = []
            for _ in range(5):
                msg = json.loads(await asyncio.wait_for(backend_ws.recv(), timeout=2))
                received.append(msg["text"])

            assert len(received) == 5
            assert set(received) == {f"msg-{i}" for i in range(5)}

#!/usr/bin/env python3
"""
WebSocket 通信 E2E 测试 — 基于 AIRelayServer 真实协议

自托管服务器，不依赖外部服务。
协议: ping/pong, register_backend, chat/reply, push, switch_backend, list_backends
"""

import asyncio
import json
import os
import sys

import pytest
import pytest_asyncio
import websockets

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../relay-server"))
from server import AIRelayServer


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


class TestWebSocketProtocol:
    """WebSocket 协议测试 — 验证 AIRelayServer 真实消息类型"""

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
    async def test_invalid_json(self, relay_server):
        server, port = relay_server
        uri = f"ws://127.0.0.1:{port}"

        async with websockets.connect(uri) as ws:
            await ws.send("not valid json {{{")
            resp = json.loads(await ws.recv())
            assert resp["type"] == "error"
            assert "Invalid JSON" in resp["message"]

    @pytest.mark.asyncio
    async def test_unknown_message_type(self, relay_server):
        server, port = relay_server
        uri = f"ws://127.0.0.1:{port}"

        async with websockets.connect(uri) as ws:
            await ws.send(json.dumps({"type": "nonexistent_xyz"}))
            resp = json.loads(await ws.recv())
            assert resp["type"] == "error"
            assert "Unknown message type" in resp["message"]

    @pytest.mark.asyncio
    async def test_register_backend(self, relay_server):
        server, port = relay_server
        uri = f"ws://127.0.0.1:{port}"

        async with websockets.connect(uri) as ws:
            await ws.send(
                json.dumps(
                    {
                        "type": "register_backend",
                        "backend_id": "test-ai",
                        "name": "Test AI",
                        "description": "A test backend",
                    }
                )
            )
            resp = json.loads(await ws.recv())
            assert resp["type"] == "backend_registered"
            assert resp["backend_id"] == "test-ai"
            assert "test-ai" in server.backends

    @pytest.mark.asyncio
    async def test_register_backend_missing_id(self, relay_server):
        server, port = relay_server
        uri = f"ws://127.0.0.1:{port}"

        async with websockets.connect(uri) as ws:
            await ws.send(json.dumps({"type": "register_backend"}))
            resp = json.loads(await ws.recv())
            assert resp["type"] == "error"
            assert "backend_id" in resp["message"]

    @pytest.mark.asyncio
    async def test_list_backends(self, relay_server):
        server, port = relay_server
        uri = f"ws://127.0.0.1:{port}"

        async with websockets.connect(uri) as backend_ws:
            await backend_ws.send(
                json.dumps(
                    {
                        "type": "register_backend",
                        "backend_id": "lingyi",
                        "name": "灵依",
                    }
                )
            )
            await backend_ws.recv()

            async with websockets.connect(uri) as user_ws:
                await user_ws.send(json.dumps({"type": "list_backends"}))
                resp = json.loads(await user_ws.recv())
                assert resp["type"] == "backends_list"
                assert len(resp["backends"]) == 1
                assert resp["backends"][0]["id"] == "lingyi"
                assert resp["backends"][0]["name"] == "灵依"
                assert resp["backends"][0]["online"] is True

    @pytest.mark.asyncio
    async def test_list_backends_empty(self, relay_server):
        server, port = relay_server
        uri = f"ws://127.0.0.1:{port}"

        async with websockets.connect(uri) as ws:
            await ws.send(json.dumps({"type": "list_backends"}))
            resp = json.loads(await ws.recv())
            assert resp["type"] == "backends_list"
            assert resp["backends"] == []

    @pytest.mark.asyncio
    async def test_chat_routes_to_backend(self, relay_server):
        server, port = relay_server
        uri = f"ws://127.0.0.1:{port}"

        async with websockets.connect(uri) as backend_ws:
            await backend_ws.send(
                json.dumps(
                    {
                        "type": "register_backend",
                        "backend_id": "chat-ai",
                    }
                )
            )
            await backend_ws.recv()

            async with websockets.connect(uri) as user_ws:
                await user_ws.send(
                    json.dumps(
                        {
                            "type": "chat",
                            "target": "chat-ai",
                            "text": "Hello!",
                        }
                    )
                )

                backend_msg = json.loads(await asyncio.wait_for(backend_ws.recv(), timeout=2))
                assert backend_msg["type"] == "chat"
                assert backend_msg["text"] == "Hello!"
                assert "request_id" in backend_msg
                assert "from" in backend_msg

    @pytest.mark.asyncio
    async def test_chat_reply_round_trip(self, relay_server):
        server, port = relay_server
        uri = f"ws://127.0.0.1:{port}"

        async with websockets.connect(uri) as backend_ws:
            await backend_ws.send(
                json.dumps(
                    {
                        "type": "register_backend",
                        "backend_id": "reply-ai",
                    }
                )
            )
            await backend_ws.recv()

            async with websockets.connect(uri) as user_ws:
                await user_ws.send(
                    json.dumps(
                        {
                            "type": "chat",
                            "target": "reply-ai",
                            "text": "Ping",
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
                            "text": "Pong",
                        }
                    )
                )

                user_reply = json.loads(await asyncio.wait_for(user_ws.recv(), timeout=2))
                assert user_reply["type"] == "reply"
                assert user_reply["text"] == "Pong"

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
    async def test_chat_empty_text_ignored(self, relay_server):
        server, port = relay_server
        uri = f"ws://127.0.0.1:{port}"

        async with websockets.connect(uri) as backend_ws:
            await backend_ws.send(
                json.dumps(
                    {
                        "type": "register_backend",
                        "backend_id": "empty-ai",
                    }
                )
            )
            await backend_ws.recv()

            async with websockets.connect(uri) as user_ws:
                await user_ws.send(json.dumps({"type": "chat", "text": "   "}))

                with pytest.raises(asyncio.TimeoutError):
                    await asyncio.wait_for(backend_ws.recv(), timeout=0.5)

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
    async def test_push_broadcast(self, relay_server):
        server, port = relay_server
        uri = f"ws://127.0.0.1:{port}"

        async with websockets.connect(uri) as backend_ws:
            await backend_ws.send(
                json.dumps(
                    {
                        "type": "register_backend",
                        "backend_id": "push-ai",
                    }
                )
            )
            await backend_ws.recv()

            async with websockets.connect(uri) as user1:
                async with websockets.connect(uri) as user2:
                    await user1.send(json.dumps({"type": "chat", "text": "hi"}))
                    await user2.send(json.dumps({"type": "chat", "text": "hi"}))
                    await asyncio.sleep(0.1)
                    for _ in range(2):
                        await asyncio.wait_for(backend_ws.recv(), timeout=2)

                    await backend_ws.send(
                        json.dumps(
                            {
                                "type": "push",
                                "category": "alert",
                                "text": "broadcast msg",
                                "backend": "push-ai",
                            }
                        )
                    )

                    msg1 = json.loads(await asyncio.wait_for(user1.recv(), timeout=2))
                    assert msg1["type"] == "push"
                    assert msg1["text"] == "broadcast msg"

                    msg2 = json.loads(await asyncio.wait_for(user2.recv(), timeout=2))
                    assert msg2["type"] == "push"
                    assert msg2["text"] == "broadcast msg"

    @pytest.mark.asyncio
    async def test_push_targeted(self, relay_server):
        server, port = relay_server
        uri = f"ws://127.0.0.1:{port}"

        async with websockets.connect(uri) as backend_ws:
            await backend_ws.send(
                json.dumps(
                    {
                        "type": "register_backend",
                        "backend_id": "target-ai",
                    }
                )
            )
            await backend_ws.recv()

            async with websockets.connect(uri) as user_ws:
                await user_ws.send(json.dumps({"type": "chat", "text": "register me"}))
                await asyncio.wait_for(backend_ws.recv(), timeout=2)

                conn_ids = list(server.users.keys())
                assert len(conn_ids) >= 1
                target_id = conn_ids[0]

                await backend_ws.send(
                    json.dumps(
                        {
                            "type": "push",
                            "target_client": target_id,
                            "category": "info",
                            "text": "targeted msg",
                        }
                    )
                )

                msg = json.loads(await asyncio.wait_for(user_ws.recv(), timeout=2))
                assert msg["type"] == "push"
                assert msg["text"] == "targeted msg"

    @pytest.mark.asyncio
    async def test_backend_disconnect_cleanup(self, relay_server):
        server, port = relay_server
        uri = f"ws://127.0.0.1:{port}"

        async with websockets.connect(uri) as backend_ws:
            await backend_ws.send(
                json.dumps(
                    {
                        "type": "register_backend",
                        "backend_id": "temp-ai",
                    }
                )
            )
            await backend_ws.recv()
            assert "temp-ai" in server.backends

        await asyncio.sleep(0.2)
        assert "temp-ai" not in server.backends

    @pytest.mark.asyncio
    async def test_multiple_messages_sequence(self, relay_server):
        server, port = relay_server
        uri = f"ws://127.0.0.1:{port}"

        async with websockets.connect(uri) as ws:
            await ws.send(json.dumps({"type": "ping"}))
            r1 = json.loads(await ws.recv())
            assert r1["type"] == "pong"

            await ws.send(json.dumps({"type": "list_backends"}))
            r2 = json.loads(await ws.recv())
            assert r2["type"] == "backends_list"

            await ws.send(json.dumps({"type": "switch_backend", "target": "x"}))
            r3 = json.loads(await ws.recv())
            assert r3["type"] == "backend_switched"

            await ws.send(json.dumps({"type": "unknown_xyz"}))
            r4 = json.loads(await ws.recv())
            assert r4["type"] == "error"

    @pytest.mark.asyncio
    async def test_concurrent_connections(self, relay_server):
        server, port = relay_server
        uri = f"ws://127.0.0.1:{port}"

        async def ping_pong(client_id):
            async with websockets.connect(uri) as ws:
                await ws.send(json.dumps({"type": "ping"}))
                resp = json.loads(await ws.recv())
                assert resp["type"] == "pong"
                return client_id

        tasks = [asyncio.create_task(ping_pong(i)) for i in range(10)]
        results = await asyncio.gather(*tasks)
        assert len(results) == 10


class TestWebSocketStress:
    """WebSocket 压力测试"""

    @pytest.mark.asyncio
    async def test_many_concurrent_messages(self, relay_server):
        server, port = relay_server
        uri = f"ws://127.0.0.1:{port}"
        num_messages = 50

        async with websockets.connect(uri) as ws:
            for _ in range(num_messages):
                await ws.send(json.dumps({"type": "ping"}))

            responses = []
            for _ in range(num_messages):
                resp = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
                responses.append(resp)

            assert len(responses) == num_messages
            for r in responses:
                assert r["type"] == "pong"

    @pytest.mark.asyncio
    async def test_rapid_register_disconnect(self, relay_server):
        server, port = relay_server
        uri = f"ws://127.0.0.1:{port}"

        for i in range(10):
            async with websockets.connect(uri) as ws:
                await ws.send(
                    json.dumps(
                        {
                            "type": "register_backend",
                            "backend_id": f"rapid-{i}",
                        }
                    )
                )
                resp = json.loads(await ws.recv())
                assert resp["type"] == "backend_registered"

            await asyncio.sleep(0.05)

        assert len(server.backends) == 0

    @pytest.mark.asyncio
    async def test_concurrent_chat_flood(self, relay_server):
        server, port = relay_server
        uri = f"ws://127.0.0.1:{port}"

        async with websockets.connect(uri) as backend_ws:
            await backend_ws.send(
                json.dumps(
                    {
                        "type": "register_backend",
                        "backend_id": "flood-ai",
                    }
                )
            )
            await backend_ws.recv()

            async def send_chat(msg_id):
                async with websockets.connect(uri) as user_ws:
                    await user_ws.send(
                        json.dumps(
                            {
                                "type": "chat",
                                "target": "flood-ai",
                                "text": f"msg-{msg_id}",
                            }
                        )
                    )
                    return msg_id

            tasks = [asyncio.create_task(send_chat(i)) for i in range(20)]
            await asyncio.gather(*tasks)

            received = []
            for _ in range(20):
                msg = json.loads(await asyncio.wait_for(backend_ws.recv(), timeout=5))
                received.append(msg["text"])

            assert len(received) == 20
            assert set(received) == {f"msg-{i}" for i in range(20)}

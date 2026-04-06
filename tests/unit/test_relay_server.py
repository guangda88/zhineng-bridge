#!/usr/bin/env python3
"""
relay-server 单元测试 — 测试 AIRelayServer 实际 API
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../relay-server'))

import websockets

from server import AIRelayServer


class TestAIRelayServer:

    @pytest.fixture
    def server(self):
        return AIRelayServer(host="localhost", port=8765)

    def test_init(self, server):
        assert server.host == "localhost"
        assert server.port == 8765
        assert server.server is None
        assert len(server.users) == 0
        assert len(server.backends) == 0
        assert len(server.routing) == 0
        assert len(server.pending) == 0
        assert len(server.backend_meta) == 0

    @pytest.mark.asyncio
    async def test_register_backend(self, server):
        mock_ws = AsyncMock()
        msg = {"type": "register_backend", "backend_id": "test-backend", "name": "Test"}

        await server._dispatch("conn-1", mock_ws, msg)

        assert "test-backend" in server.backends
        assert server.backend_meta["test-backend"]["name"] == "Test"
        mock_ws.send.assert_called_once()
        sent = json.loads(mock_ws.send.call_args[0][0])
        assert sent["type"] == "backend_registered"
        assert sent["backend_id"] == "test-backend"

    @pytest.mark.asyncio
    async def test_register_backend_missing_id(self, server):
        mock_ws = AsyncMock()
        msg = {"type": "register_backend"}

        await server._dispatch("conn-1", mock_ws, msg)

        assert len(server.backends) == 0
        sent = json.loads(mock_ws.send.call_args[0][0])
        assert sent["type"] == "error"
        assert "backend_id" in sent["message"]

    @pytest.mark.asyncio
    async def test_list_backends(self, server):
        server.backends["b1"] = AsyncMock()
        server.backend_meta["b1"] = {"name": "Backend1", "description": "desc"}
        mock_ws = AsyncMock()

        msg = {"type": "list_backends"}
        await server._dispatch("conn-1", mock_ws, msg)

        mock_ws.send.assert_called_once()
        sent = json.loads(mock_ws.send.call_args[0][0])
        assert sent["type"] == "backends_list"
        assert len(sent["backends"]) == 1
        assert sent["backends"][0]["id"] == "b1"
        assert sent["backends"][0]["online"] is True

    @pytest.mark.asyncio
    async def test_chat_routes_to_backend(self, server):
        backend_ws = AsyncMock()
        server.backends["b1"] = backend_ws
        user_ws = AsyncMock()

        msg = {"type": "chat", "target": "b1", "text": "hello"}
        await server._dispatch("user-1", user_ws, msg)

        backend_ws.send.assert_called_once()
        sent = json.loads(backend_ws.send.call_args[0][0])
        assert sent["type"] == "chat"
        assert sent["from"] == "user-1"
        assert sent["text"] == "hello"
        assert "request_id" in sent
        assert "user-1" in server.users
        assert server.routing["user-1"] == "b1"

    @pytest.mark.asyncio
    async def test_chat_no_backend_returns_error(self, server):
        user_ws = AsyncMock()

        msg = {"type": "chat", "text": "hello"}
        await server._dispatch("user-1", user_ws, msg)

        sent = json.loads(user_ws.send.call_args[0][0])
        assert sent["type"] == "error"
        assert "没有可用的AI后端" in sent["message"]

    @pytest.mark.asyncio
    async def test_reply_forwards_to_user(self, server):
        user_ws = AsyncMock()
        server.users["user-1"] = user_ws
        server.pending["req-1"] = "user-1"

        msg = {"type": "reply", "request_id": "req-1", "text": "world", "audio": None}
        await server._dispatch("b1", AsyncMock(), msg)

        user_ws.send.assert_called_once()
        sent = json.loads(user_ws.send.call_args[0][0])
        assert sent["type"] == "reply"
        assert sent["text"] == "world"
        assert "req-1" not in server.pending

    @pytest.mark.asyncio
    async def test_switch_backend(self, server):
        mock_ws = AsyncMock()
        server.backends["b2"] = AsyncMock()

        msg = {"type": "switch_backend", "target": "b2"}
        await server._dispatch("u1", mock_ws, msg)

        assert server.routing["u1"] == "b2"
        sent = json.loads(mock_ws.send.call_args[0][0])
        assert sent["type"] == "backend_switched"
        assert sent["backend_id"] == "b2"

    @pytest.mark.asyncio
    async def test_ping(self, server):
        mock_ws = AsyncMock()
        msg = {"type": "ping"}
        await server._dispatch("conn-1", mock_ws, msg)

        mock_ws.send.assert_called_once()
        sent = json.loads(mock_ws.send.call_args[0][0])
        assert sent["type"] == "pong"
        assert "timestamp" in sent

    @pytest.mark.asyncio
    async def test_unknown_message_type_returns_error(self, server):
        mock_ws = AsyncMock()
        msg = {"type": "unknown_type_xyz", "data": {}}

        await server._dispatch("conn-1", mock_ws, msg)

        mock_ws.send.assert_called_once()
        sent = json.loads(mock_ws.send.call_args[0][0])
        assert sent["type"] == "error"
        assert "Unknown message type" in sent["message"]

    @pytest.mark.asyncio
    async def test_cleanup_on_user_disconnect(self, server):
        mock_ws = AsyncMock()
        server.backends["b1"] = AsyncMock()
        server.backend_meta["b1"] = {"name": "b1"}

        async def fake_aiter():
            yield json.dumps({"type": "chat", "target": "b1", "text": "hi"})
            raise websockets.exceptions.ConnectionClosed(1000, "bye")

        mock_ws.__aiter__ = fake_aiter

        await server._handle_connection(mock_ws)

        assert len(server.users) == 0
        assert len(server.routing) == 0

    @pytest.mark.asyncio
    async def test_stop(self, server):
        user_ws = AsyncMock()
        backend_ws = AsyncMock()
        server.users["u1"] = user_ws
        server.backends["b1"] = backend_ws
        server.routing["u1"] = "b1"
        server.pending["req-1"] = "u1"
        server.server = AsyncMock()
        server.server.wait_closed = AsyncMock()

        await server.stop()

        assert len(server.users) == 0
        assert len(server.backends) == 0
        assert len(server.routing) == 0
        assert len(server.pending) == 0
        user_ws.close.assert_called_once()
        backend_ws.close.assert_called_once()

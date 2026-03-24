#!/usr/bin/env python3
"""
relay-server 单元测试
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# 添加 relay-server 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../relay-server'))

from server import CrushRelayServer


class TestCrushRelayServer:
    """测试 CrushRelayServer 类"""

    @pytest.fixture
    def server(self):
        """创建服务器实例"""
        return CrushRelayServer(host="localhost", port=8765)

    def test_init(self, server):
        """测试服务器初始化"""
        assert server.host == "localhost"
        assert server.port == 8765
        assert server.manager is None
        assert len(server.websockets) == 0
        assert server.server is None

    @pytest.mark.asyncio
    async def test_handle_ping(self, server):
        """测试心跳处理"""
        response = await server.handle_ping()

        assert response["type"] == "pong"
        assert "timestamp" in response

    @pytest.mark.asyncio
    async def test_handle_list_sessions(self, server):
        """测试列出会话"""
        response = await server.handle_list_sessions()

        assert response["type"] == "sessions_list"
        assert "sessions" in response
        assert "count" in response
        assert isinstance(response["sessions"], list)
        assert isinstance(response["count"], int)

    @pytest.mark.asyncio
    async def test_handle_start_session(self, server):
        """测试启动会话"""
        data = {
            "tool_name": "crush",
            "args": ["--help"]
        }

        response = await server.handle_start_session(data)

        assert response["type"] == "session_started"
        assert "session_id" in response
        assert response["tool_name"] == "crush"
        assert response["status"] == "running"

    @pytest.mark.asyncio
    async def test_handle_start_session_default_args(self, server):
        """测试启动会话（默认参数）"""
        data = {
            "tool_name": "cursor"
        }

        response = await server.handle_start_session(data)

        assert response["type"] == "session_started"
        assert response["tool_name"] == "cursor"

    @pytest.mark.asyncio
    async def test_handle_stop_session(self, server):
        """测试停止会话"""
        data = {
            "session_id": "test-session-id"
        }

        response = await server.handle_stop_session(data)

        assert response["type"] == "session_stopped"
        assert response["session_id"] == "test-session-id"
        assert response["status"] == "stopped"

    @pytest.mark.asyncio
    async def test_handle_delete_session(self, server):
        """测试删除会话"""
        data = {
            "session_id": "test-session-id"
        }

        response = await server.handle_delete_session(data)

        assert response["type"] == "session_deleted"
        assert response["session_id"] == "test-session-id"

    @pytest.mark.asyncio
    async def test_send_error(self, server):
        """测试发送错误消息"""
        # 创建模拟的 websocket
        mock_websocket = AsyncMock()
        mock_websocket.send = AsyncMock()

        # 添加到 websockets 字典
        server.websockets["test-client"] = mock_websocket

        # 调用 send_error
        await server.send_error("test-client", "Test error message")

        # 验证发送了正确的消息
        mock_websocket.send.assert_called_once()
        sent_message = json.loads(mock_websocket.send.call_args[0][0])

        assert sent_message["type"] == "error"
        assert sent_message["message"] == "Test error message"

    @pytest.mark.asyncio
    async def test_send_to_client(self, server):
        """测试发送消息给客户端"""
        # 创建模拟的 websocket
        mock_websocket = AsyncMock()
        mock_websocket.send = AsyncMock()

        # 添加到 websockets 字典
        server.websockets["test-client"] = mock_websocket

        # 准备消息
        message = {
            "type": "test",
            "data": "test data"
        }

        # 调用 send_to_client
        await server.send_to_client("test-client", message)

        # 验证发送了正确的消息
        mock_websocket.send.assert_called_once()
        sent_message = json.loads(mock_websocket.send.call_args[0][0])

        assert sent_message["type"] == "test"
        assert sent_message["data"] == "test data"

    @pytest.mark.asyncio
    async def test_send_to_client_not_found(self, server):
        """测试发送消息给不存在的客户端"""
        message = {
            "type": "test",
            "data": "test data"
        }

        # 调用 send_to_client（客户端不存在）
        # 应该静默失败，不抛出异常
        await server.send_to_client("non-existent-client", message)

        # 验证没有抛出异常（测试通过即表示没有异常）

    @pytest.mark.asyncio
    async def test_handle_message_invalid_json(self, server, capsys):
        """测试处理无效 JSON 消息"""
        # 创建模拟的 websocket
        mock_websocket = AsyncMock()
        mock_websocket.send = AsyncMock()
        server.websockets["test-client"] = mock_websocket

        # 处理无效 JSON
        await server.handle_message("test-client", "invalid json{{")

        # 验证发送了错误消息
        mock_websocket.send.assert_called_once()
        sent_message = json.loads(mock_websocket.send.call_args[0][0])

        assert sent_message["type"] == "error"

    @pytest.mark.asyncio
    async def test_handle_message_unknown_type(self, server, capsys):
        """测试处理未知消息类型"""
        # 创建模拟的 websocket
        mock_websocket = AsyncMock()
        mock_websocket.send = AsyncMock()
        server.websockets["test-client"] = mock_websocket

        # 处理未知消息类型
        message = {
            "type": "unknown_type",
            "data": {}
        }

        await server.handle_message("test-client", json.dumps(message))

        # 验证发送了错误消息
        mock_websocket.send.assert_called_once()
        sent_message = json.loads(mock_websocket.send.call_args[0][0])

        assert sent_message["type"] == "error"
        assert "Unknown message type" in sent_message["message"]

    @pytest.mark.asyncio
    async def test_handle_message_ping(self, server, capsys):
        """测试处理 ping 消息"""
        # 创建模拟的 websocket
        mock_websocket = AsyncMock()
        mock_websocket.send = AsyncMock()
        server.websockets["test-client"] = mock_websocket

        # 处理 ping 消息
        message = {
            "type": "ping"
        }

        await server.handle_message("test-client", json.dumps(message))

        # 验证发送了 pong 响应
        mock_websocket.send.assert_called_once()
        sent_message = json.loads(mock_websocket.send.call_args[0][0])

        assert sent_message["type"] == "pong"
        assert "timestamp" in sent_message

    @pytest.mark.asyncio
    async def test_handle_message_list_sessions(self, server):
        """测试处理 list_sessions 消息"""
        # 创建模拟的 websocket
        mock_websocket = AsyncMock()
        mock_websocket.send = AsyncMock()
        server.websockets["test-client"] = mock_websocket

        # 处理 list_sessions 消息
        message = {
            "type": "list_sessions"
        }

        await server.handle_message("test-client", json.dumps(message))

        # 验证发送了会话列表
        mock_websocket.send.assert_called_once()
        sent_message = json.loads(mock_websocket.send.call_args[0][0])

        assert sent_message["type"] == "sessions_list"
        assert "sessions" in sent_message
        assert "count" in sent_message

    @pytest.mark.asyncio
    async def test_handle_message_start_session(self, server):
        """测试处理 start_session 消息"""
        # 创建模拟的 websocket
        mock_websocket = AsyncMock()
        mock_websocket.send = AsyncMock()
        server.websockets["test-client"] = mock_websocket

        # 处理 start_session 消息
        message = {
            "type": "start_session",
            "tool_name": "cursor",
            "args": ["--help"]
        }

        await server.handle_message("test-client", json.dumps(message))

        # 验证发送了会话启动响应
        mock_websocket.send.assert_called_once()
        sent_message = json.loads(mock_websocket.send.call_args[0][0])

        assert sent_message["type"] == "session_started"
        assert sent_message["tool_name"] == "cursor"
        assert "session_id" in sent_message

    @pytest.mark.asyncio
    async def test_handle_message_stop_session(self, server):
        """测试处理 stop_session 消息"""
        # 创建模拟的 websocket
        mock_websocket = AsyncMock()
        mock_websocket.send = AsyncMock()
        server.websockets["test-client"] = mock_websocket

        # 处理 stop_session 消息
        message = {
            "type": "stop_session",
            "session_id": "test-session-id"
        }

        await server.handle_message("test-client", json.dumps(message))

        # 验证发送了会话停止响应
        mock_websocket.send.assert_called_once()
        sent_message = json.loads(mock_websocket.send.call_args[0][0])

        assert sent_message["type"] == "session_stopped"
        assert sent_message["session_id"] == "test-session-id"

    @pytest.mark.asyncio
    async def test_handle_message_delete_session(self, server):
        """测试处理 delete_session 消息"""
        # 创建模拟的 websocket
        mock_websocket = AsyncMock()
        mock_websocket.send = AsyncMock()
        server.websockets["test-client"] = mock_websocket

        # 处理 delete_session 消息
        message = {
            "type": "delete_session",
            "session_id": "test-session-id"
        }

        await server.handle_message("test-client", json.dumps(message))

        # 验证发送了会话删除响应
        mock_websocket.send.assert_called_once()
        sent_message = json.loads(mock_websocket.send.call_args[0][0])

        assert sent_message["type"] == "session_deleted"
        assert sent_message["session_id"] == "test-session-id"

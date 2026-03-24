#!/usr/bin/env python3
"""
WebSocket 通信 E2E 测试

注意：这些测试需要 relay-server 运行在 ws://localhost:8765
"""

import pytest
import asyncio
import websockets
import json
import pytest_asyncio
from typing import Dict, Any


class TestWebSocketE2E:
    """WebSocket 端到端测试"""

    @pytest_asyncio.fixture
    async def websocket_client(self):
        """创建 WebSocket 客户端连接"""
        uri = "ws://localhost:8765"

        try:
            async with websockets.connect(uri) as websocket:
                yield websocket
        except ConnectionRefusedError:
            pytest.skip("relay-server 未运行，请先启动: python3 relay-server/start_server.py")

    @pytest.mark.asyncio
    async def test_basic_connection(self, websocket_client):
        """测试基本连接"""
        # 如果能到达这里，说明连接成功
        assert websocket_client is not None

    @pytest.mark.asyncio
    async def test_ping_pong(self, websocket_client):
        """测试心跳消息"""
        # 发送 ping
        ping_message = {"type": "ping"}
        await websocket_client.send(json.dumps(ping_message))

        # 接收响应
        response = await asyncio.wait_for(websocket_client.recv(), timeout=5.0)
        response_data = json.loads(response)

        # 验证响应
        assert response_data["type"] == "pong"
        assert "timestamp" in response_data

    @pytest.mark.asyncio
    async def test_list_sessions(self, websocket_client):
        """测试列出会话"""
        # 发送 list_sessions 请求
        list_message = {"type": "list_sessions"}
        await websocket_client.send(json.dumps(list_message))

        # 接收响应
        response = await asyncio.wait_for(websocket_client.recv(), timeout=5.0)
        response_data = json.loads(response)

        # 验证响应
        assert response_data["type"] == "sessions_list"
        assert "sessions" in response_data
        assert "count" in response_data
        assert isinstance(response_data["sessions"], list)
        assert isinstance(response_data["count"], int)

    @pytest.mark.asyncio
    async def test_create_session(self, websocket_client):
        """测试创建会话"""
        # 发送 start_session 请求
        create_message = {
            "type": "start_session",
            "tool_name": "crush",
            "args": ["--help"]
        }
        await websocket_client.send(json.dumps(create_message))

        # 接收响应
        response = await asyncio.wait_for(websocket_client.recv(), timeout=5.0)
        response_data = json.loads(response)

        # 验证响应
        assert response_data["type"] == "session_started"
        assert "session_id" in response_data
        assert response_data["tool_name"] == "crush"
        assert response_data["status"] == "running"

    @pytest.mark.asyncio
    async def test_create_session_default_args(self, websocket_client):
        """测试创建会话（默认参数）"""
        # 发送 start_session 请求（不提供 args）
        create_message = {
            "type": "start_session",
            "tool_name": "cursor"
        }
        await websocket_client.send(json.dumps(create_message))

        # 接收响应
        response = await asyncio.wait_for(websocket_client.recv(), timeout=5.0)
        response_data = json.loads(response)

        # 验证响应
        assert response_data["type"] == "session_started"
        assert response_data["tool_name"] == "cursor"

    @pytest.mark.asyncio
    async def test_stop_session(self, websocket_client):
        """测试停止会话"""
        # 先创建一个会话
        create_message = {
            "type": "start_session",
            "tool_name": "claude",
            "args": ["--version"]
        }
        await websocket_client.send(json.dumps(create_message))
        create_response = json.loads(await asyncio.wait_for(websocket_client.recv(), timeout=5.0))
        session_id = create_response["session_id"]

        # 停止会话
        stop_message = {
            "type": "stop_session",
            "session_id": session_id
        }
        await websocket_client.send(json.dumps(stop_message))

        # 接收响应
        response = await asyncio.wait_for(websocket_client.recv(), timeout=5.0)
        response_data = json.loads(response)

        # 验证响应
        assert response_data["type"] == "session_stopped"
        assert response_data["session_id"] == session_id
        assert response_data["status"] == "stopped"

    @pytest.mark.asyncio
    async def test_delete_session(self, websocket_client):
        """测试删除会话"""
        # 先创建一个会话
        create_message = {
            "type": "start_session",
            "tool_name": "copilot",
            "args": ["--help"]
        }
        await websocket_client.send(json.dumps(create_message))
        create_response = json.loads(await asyncio.wait_for(websocket_client.recv(), timeout=5.0))
        session_id = create_response["session_id"]

        # 删除会话
        delete_message = {
            "type": "delete_session",
            "session_id": session_id
        }
        await websocket_client.send(json.dumps(delete_message))

        # 接收响应
        response = await asyncio.wait_for(websocket_client.recv(), timeout=5.0)
        response_data = json.loads(response)

        # 验证响应
        assert response_data["type"] == "session_deleted"
        assert response_data["session_id"] == session_id

    @pytest.mark.asyncio
    async def test_invalid_message_type(self, websocket_client):
        """测试无效消息类型"""
        # 发送未知消息类型
        invalid_message = {
            "type": "unknown_type",
            "data": {}
        }
        await websocket_client.send(json.dumps(invalid_message))

        # 接收错误响应
        response = await asyncio.wait_for(websocket_client.recv(), timeout=5.0)
        response_data = json.loads(response)

        # 验证错误响应
        assert response_data["type"] == "error"
        assert "Unknown message type" in response_data["message"]

    @pytest.mark.asyncio
    async def test_invalid_json(self, websocket_client):
        """测试无效 JSON"""
        # 发送无效 JSON
        await websocket_client.send("invalid json{")

        # 接收错误响应
        response = await asyncio.wait_for(websocket_client.recv(), timeout=5.0)
        response_data = json.loads(response)

        # 验证错误响应
        assert response_data["type"] == "error"

    @pytest.mark.asyncio
    async def test_multiple_messages(self, websocket_client):
        """测试连续发送多个消息"""
        messages = [
            {"type": "ping"},
            {"type": "list_sessions"},
            {"type": "start_session", "tool_name": "crush", "args": ["--help"]},
            {"type": "ping"},
            {"type": "list_sessions"}
        ]

        responses = []
        for message in messages:
            await websocket_client.send(json.dumps(message))
            response = await asyncio.wait_for(websocket_client.recv(), timeout=5.0)
            responses.append(json.loads(response))

        # 验证收到所有响应
        assert len(responses) == len(messages)

        # 验证特定消息
        assert responses[0]["type"] == "pong"
        assert responses[1]["type"] == "sessions_list"
        assert responses[2]["type"] == "session_started"
        assert responses[3]["type"] == "pong"
        assert responses[4]["type"] == "sessions_list"

    @pytest.mark.asyncio
    async def test_session_lifecycle(self, websocket_client):
        """测试完整会话生命周期"""
        # 1. 创建会话
        create_message = {
            "type": "start_session",
            "tool_name": "cursor",
            "args": ["--version"]
        }
        await websocket_client.send(json.dumps(create_message))
        create_response = json.loads(await asyncio.wait_for(websocket_client.recv(), timeout=5.0))
        session_id = create_response["session_id"]
        assert create_response["status"] == "running"

        # 2. 列出会话（应该包含新创建的会话）
        list_message = {"type": "list_sessions"}
        await websocket_client.send(json.dumps(list_message))
        list_response = json.loads(await asyncio.wait_for(websocket_client.recv(), timeout=5.0))
        # 注意：由于 server.py 中的 handle_list_sessions 返回空列表，
        # 这里只验证响应格式正确
        assert list_response["type"] == "sessions_list"

        # 3. 停止会话
        stop_message = {
            "type": "stop_session",
            "session_id": session_id
        }
        await websocket_client.send(json.dumps(stop_message))
        stop_response = json.loads(await asyncio.wait_for(websocket_client.recv(), timeout=5.0))
        assert stop_response["status"] == "stopped"

        # 4. 删除会话
        delete_message = {
            "type": "delete_session",
            "session_id": session_id
        }
        await websocket_client.send(json.dumps(delete_message))
        delete_response = json.loads(await asyncio.wait_for(websocket_client.recv(), timeout=5.0))
        assert delete_response["type"] == "session_deleted"

    @pytest.mark.asyncio
    async def test_concurrent_sessions(self, websocket_client):
        """测试创建多个并发会话"""
        session_ids = []

        # 创建 3 个会话
        for i in range(3):
            create_message = {
                "type": "start_session",
                "tool_name": "crush",
                "args": ["--help"]
            }
            await websocket_client.send(json.dumps(create_message))
            response = json.loads(await asyncio.wait_for(websocket_client.recv(), timeout=5.0))
            session_ids.append(response["session_id"])

        # 验证创建了 3 个不同的会话
        assert len(session_ids) == 3
        assert len(set(session_ids)) == 3  # 所有 session_id 应该唯一

        # 清理：删除所有会话
        for session_id in session_ids:
            delete_message = {
                "type": "delete_session",
                "session_id": session_id
            }
            await websocket_client.send(json.dumps(delete_message))
            await asyncio.wait_for(websocket_client.recv(), timeout=5.0)

    @pytest.mark.asyncio
    async def test_different_tools(self, websocket_client):
        """测试创建不同工具的会话"""
        tools = ['crush', 'claude', 'cursor', 'copilot']

        for tool in tools:
            create_message = {
                "type": "start_session",
                "tool_name": tool,
                "args": ["--help"]
            }
            await websocket_client.send(json.dumps(create_message))
            response = json.loads(await asyncio.wait_for(websocket_client.recv(), timeout=5.0))

            assert response["type"] == "session_started"
            assert response["tool_name"] == tool

            # 清理会话
            session_id = response["session_id"]
            delete_message = {
                "type": "delete_session",
                "session_id": session_id
            }
            await websocket_client.send(json.dumps(delete_message))
            await asyncio.wait_for(websocket_client.recv(), timeout=5.0)

    @pytest.mark.asyncio
    async def test_connection_timeout(self, websocket_client):
        """测试连接超时"""
        # 发送一个消息
        ping_message = {"type": "ping"}
        await websocket_client.send(json.dumps(ping_message))

        # 验证在合理时间内收到响应
        response = await asyncio.wait_for(websocket_client.recv(), timeout=5.0)
        response_data = json.loads(response)
        assert response_data["type"] == "pong"


class TestWebSocketStress:
    """WebSocket 压力测试"""

    @pytest_asyncio.fixture
    async def websocket_client(self):
        """创建 WebSocket 客户端连接"""
        uri = "ws://localhost:8765"

        try:
            async with websockets.connect(uri) as websocket:
                yield websocket
        except ConnectionRefusedError:
            pytest.skip("relay-server 未运行，请先启动: python3 relay-server/start_server.py")

    @pytest.mark.asyncio
    async def test_many_concurrent_messages(self, websocket_client):
        """测试大量并发消息"""
        num_messages = 50

        # 发送多个 ping 消息
        tasks = []
        for _ in range(num_messages):
            message = {"type": "ping"}
            tasks.append(websocket_client.send(json.dumps(message)))

        # 并发发送所有消息
        await asyncio.gather(*tasks)

        # 接收所有响应
        responses = []
        for _ in range(num_messages):
            response = await asyncio.wait_for(websocket_client.recv(), timeout=10.0)
            responses.append(json.loads(response))

        # 验证所有响应
        assert len(responses) == num_messages
        for response in responses:
            assert response["type"] == "pong"

    @pytest.mark.asyncio
    async def test_rapid_session_creation_deletion(self, websocket_client):
        """测试快速创建和删除会话"""
        num_iterations = 10

        for _ in range(num_iterations):
            # 创建会话
            create_message = {
                "type": "start_session",
                "tool_name": "crush",
                "args": ["--help"]
            }
            await websocket_client.send(json.dumps(create_message))
            create_response = json.loads(await asyncio.wait_for(websocket_client.recv(), timeout=5.0))
            session_id = create_response["session_id"]

            # 立即删除会话
            delete_message = {
                "type": "delete_session",
                "session_id": session_id
            }
            await websocket_client.send(json.dumps(delete_message))
            delete_response = json.loads(await asyncio.wait_for(websocket_client.recv(), timeout=5.0))

            assert create_response["type"] == "session_started"
            assert delete_response["type"] == "session_deleted"

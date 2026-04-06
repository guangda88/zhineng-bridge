#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
zhineng-bridge 端到端测试 - 基于 LingFlow 测试框架
使用 AI 场景运行器进行综合测试
"""

import pytest
import asyncio
import websockets
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

try:
    sys.path.insert(0, str(Path("/home/ai/LingFlow")))
    from lingflow.testing import (
        CodeTestScenario,
        CapturedToolCall,
        TestInteractionType
    )
    from lingflow.testing.ai_runner import AIScenarioRunner
    HAS_LINGFLOW = True
except ImportError:
    HAS_LINGFLOW = False

requires_lingflow = pytest.mark.skipif(
    not HAS_LINGFLOW,
    reason="LingFlow framework not available"
)


def _check_ws_server():
    """检查 WS 服务器是否可达"""
    import asyncio
    async def _probe():
        try:
            async with websockets.connect("ws://localhost:8765", close_timeout=1):
                return True
        except Exception:
            return False
    return asyncio.run(_probe())


requires_ws = pytest.mark.skipif(
    not _check_ws_server(),
    reason="WebSocket server not available (WSS on :8765 is not WS)"
)


# ============================================
# 测试工具定义
# ============================================

class ZhinengBridgeTestTool:
    """zhineng-bridge 测试工具"""

    def __init__(self):
        self.websocket_uri = "ws://localhost:8765"
        self.connected = False

    async def connect_websocket(self) -> Dict[str, Any]:
        """测试 WebSocket 连接"""
        try:
            async with websockets.connect(self.websocket_uri) as websocket:
                self.connected = True
                return {
                    "status": "connected",
                    "uri": self.websocket_uri,
                    "timestamp": asyncio.get_event_loop().time()
                }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "uri": self.websocket_uri
            }

    async def test_session_creation(self) -> Dict[str, Any]:
        """测试会话创建"""
        try:
            async with websockets.connect(self.websocket_uri) as websocket:
                message = {
                    "type": "start_session",
                    "tool_name": "crush",
                    "args": []
                }
                await websocket.send(json.dumps(message))
                response = await websocket.recv()
                response_data = json.loads(response)

                return {
                    "status": "created",
                    "response": response_data,
                    "session_id": response_data.get("session_id")
                }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }

    async def test_session_listing(self) -> Dict[str, Any]:
        """测试会话列表"""
        try:
            async with websockets.connect(self.websocket_uri) as websocket:
                message = {
                    "type": "list_sessions",
                    "data": {}
                }
                await websocket.send(json.dumps(message))
                response = await websocket.recv()
                response_data = json.loads(response)

                return {
                    "status": "listed",
                    "sessions": response_data.get("sessions", []),
                    "count": response_data.get("count", 0)
                }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }

    async def test_message_exchange(self) -> Dict[str, Any]:
        """测试消息交换"""
        try:
            async with websockets.connect(self.websocket_uri) as websocket:
                # 发送 ping
                ping_message = {"type": "ping"}
                await websocket.send(json.dumps(ping_message))

                # 接收 pong
                response = await websocket.recv()
                response_data = json.loads(response)

                return {
                    "status": "exchanged",
                    "response_type": response_data.get("type"),
                    "success": response_data.get("type") == "pong"
                }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }


# ============================================
# 测试场景定义
# ============================================

WEBSOCKET_CONNECTION_SCENARIO = CodeTestScenario(
    name="websocket_connection",
    description="测试 WebSocket 连接",
    prompt="验证 zhineng-bridge 的 WebSocket 服务器能够正常接受连接",
    code_content="async with websockets.connect('ws://localhost:8765') as ws:\n    pass",
    max_turns=2,
    expected_tools=["connect_websocket"],
    category=TestInteractionType.CODE_ANALYSIS,
    tags=["websocket", "connection"]
)

SESSION_CREATION_SCENARIO = CodeTestScenario(
    name="session_creation",
    description="测试会话创建",
    prompt="验证能够成功创建新的 AI 工具会话",
    code_content='message = {"type": "start_session", "tool_name": "crush", "args": []}\nawait websocket.send(json.dumps(message))',
    max_turns=3,
    expected_tools=["test_session_creation"],
    category=TestInteractionType.CODE_GENERATION,
    tags=["session", "creation"]
)

SESSION_LISTING_SCENARIO = CodeTestScenario(
    name="session_listing",
    description="测试会话列表",
    prompt="验证能够获取所有活跃会话的列表",
    code_content='message = {"type": "list_sessions", "data": {}}\nawait websocket.send(json.dumps(message))',
    max_turns=2,
    expected_tools=["test_session_listing"],
    category=TestInteractionType.CODE_ANALYSIS,
    tags=["session", "listing"]
)

MESSAGE_EXCHANGE_SCENARIO = CodeTestScenario(
    name="message_exchange",
    description="测试消息交换",
    prompt="验证 WebSocket 能够正确处理 ping/pong 消息",
    code_content='message = {"type": "ping"}\nawait websocket.send(json.dumps(message))',
    max_turns=2,
    expected_tools=["test_message_exchange"],
    category=TestInteractionType.CODE_ANALYSIS,
    tags=["websocket", "ping-pong"]
)

# 综合测试场景
COMPREHENSIVE_E2E_SCENARIO = CodeTestScenario(
    name="comprehensive_e2e",
    description="综合端到端测试",
    prompt="执行完整的端到端测试流程，包括连接、会话创建、消息交换",
    code_content="""
# 连接 WebSocket
async with websockets.connect('ws://localhost:8765') as websocket:
    # 创建会话
    await websocket.send(json.dumps({
        "type": "start_session",
        "tool_name": "crush",
        "args": []
    }))

    # 列出会话
    await websocket.send(json.dumps({
        "type": "list_sessions",
        "data": {}
    }))

    # 测试 ping-pong
    await websocket.send(json.dumps({"type": "ping"}))
""",
    max_turns=5,
    expected_tools=[
        "connect_websocket",
        "test_session_creation",
        "test_session_listing",
        "test_message_exchange"
    ],
    required_tools=["connect_websocket"],
    category=TestInteractionType.CODE_REFACTORING,
    tags=["comprehensive", "e2e"],
    priority=5
)


# ============================================
# 测试类定义
# ============================================

@requires_lingflow
@requires_ws
class TestZhinengBridgeE2E:
    """zhineng-bridge 端到端测试套件"""

    @pytest.fixture
    def test_tool(self):
        """测试工具 fixture"""
        return ZhinengBridgeTestTool()

    @pytest.mark.asyncio
    async def test_websocket_connection_scenario(self, test_tool):
        """测试 WebSocket 连接场景"""
        print("\n📡 测试 WebSocket 连接场景...")

        # 运行场景
        runner = AIScenarioRunner(timeout=30)
        result = await test_tool.connect_websocket()

        print(f"连接状态: {result['status']}")
        assert result['status'] == "connected", f"WebSocket 连接失败: {result}"

    @pytest.mark.asyncio
    async def test_session_creation_scenario(self, test_tool):
        """测试会话创建场景"""
        print("\n➕ 测试会话创建场景...")

        result = await test_tool.test_session_creation()

        print(f"创建状态: {result['status']}")
        assert result['status'] == "created", f"会话创建失败: {result}"

    @pytest.mark.asyncio
    async def test_session_listing_scenario(self, test_tool):
        """测试会话列表场景"""
        print("\n📋 测试会话列表场景...")

        result = await test_tool.test_session_listing()

        print(f"列表状态: {result['status']}")
        print(f"会话数量: {result.get('count', 0)}")
        assert result['status'] == "listed", f"会话列表获取失败: {result}"

    @pytest.mark.asyncio
    async def test_message_exchange_scenario(self, test_tool):
        """测试消息交换场景"""
        print("\n💬 测试消息交换场景...")

        result = await test_tool.test_message_exchange()

        print(f"交换状态: {result['status']}")
        print(f"响应类型: {result.get('response_type')}")
        assert result['status'] == "exchanged", f"消息交换失败: {result}"
        assert result.get('success'), "ping-pong 测试失败"

    @pytest.mark.asyncio
    async def test_comprehensive_e2e_scenario(self, test_tool):
        """综合端到端测试"""
        print("\n🚀 运行综合端到端测试...")

        results = []

        # 1. WebSocket 连接
        print("\n1️⃣ 测试 WebSocket 连接...")
        conn_result = await test_tool.connect_websocket()
        results.append(("websocket", conn_result))
        assert conn_result['status'] == "connected"

        # 2. 会话创建
        print("\n2️⃣ 测试会话创建...")
        create_result = await test_tool.test_session_creation()
        results.append(("session_creation", create_result))
        assert create_result['status'] == "created"

        # 3. 会话列表
        print("\n3️⃣ 测试会话列表...")
        list_result = await test_tool.test_session_listing()
        results.append(("session_listing", list_result))
        assert list_result['status'] == "listed"

        # 4. 消息交换
        print("\n4️⃣ 测试消息交换...")
        exchange_result = await test_tool.test_message_exchange()
        results.append(("message_exchange", exchange_result))
        assert exchange_result['status'] == "exchanged"
        assert exchange_result.get('success')

        # 打印结果摘要
        print("\n" + "=" * 70)
        print("综合测试结果摘要")
        print("=" * 70)
        for name, result in results:
            status_icon = "✅" if result.get('status') not in ["failed", "error"] else "❌"
            print(f"{status_icon} {name}: {result['status']}")

        print("\n✅ 所有端到端测试通过!")


# ============================================
# 主测试入口
# ============================================

if __name__ == "__main__":
    print("=" * 70)
    print("zhineng-bridge 端到端测试 - LingFlow")
    print("=" * 70)
    print()

    # 运行 pytest
    pytest.main([__file__, "-v", "-s", "--tb=short"])

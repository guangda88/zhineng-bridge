#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
zhineng-bridge 场景驱动的 AI 测试
基于 LingFlow 场景测试框架
"""

import pytest
import asyncio
import websockets
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, field

try:
    sys.path.insert(0, str(Path("/home/ai/LingFlow")))
    from lingflow.testing import (
        CodeTestScenario,
        CapturedToolCall,
        TestInteractionType
    )
    from lingflow.testing.ai_runner import AIScenarioRunner, ScenarioStatus, ScenarioResult
    from lingflow.testing.tool_definition import (
        ToolDefinition,
        ToolCategory,
        ToolRequest,
        ToolResponse,
        TestContext
    )
    HAS_LINGFLOW = True
except ImportError:
    HAS_LINGFLOW = False

requires_lingflow = pytest.mark.skipif(
    not HAS_LINGFLOW,
    reason="LingFlow framework not available"
)


# ============================================
# zhineng-bridge 测试工具
# ============================================

@dataclass
class ZhinengBridgeContext:
    """zhineng-bridge 测试上下文"""
    websocket_uri: str = "ws://localhost:8765"
    session_ids: List[str] = field(default_factory=list)
    test_results: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)


class WebSocketConnectTool(ToolDefinition):
    """WebSocket 连接工具"""

    def __init__(self):
        super().__init__(
            name="websocket_connect",
            description="测试 WebSocket 连接",
            category=ToolCategory.ANALYSIS
        )

    async def handle(self, request: ToolRequest, response: ToolResponse, context: TestContext):
        """处理 WebSocket 连接"""
        uri = request.arguments.get("uri", "ws://localhost:8765")

        try:
            async with websockets.connect(uri):
                response.data = {
                    "status": "connected",
                    "uri": uri,
                    "latency": 0.01  # 模拟延迟
                }
                response.success = True
                response.execution_time = 0.05
        except Exception as e:
            response.data = {
                "status": "failed",
                "error": str(e),
                "uri": uri
            }
            response.success = False


class SessionCreateTool(ToolDefinition):
    """会话创建工具"""

    def __init__(self):
        super().__init__(
            name="session_create",
            description="创建新的 AI 工具会话",
            category=ToolCategory.GENERATION
        )

    async def handle(self, request: ToolRequest, response: ToolResponse, context: TestContext):
        """处理会话创建"""
        tool_name = request.arguments.get("tool_name", "crush")
        args = request.arguments.get("args", [])
        uri = request.arguments.get("uri", "ws://localhost:8765")

        try:
            async with websockets.connect(uri) as websocket:
                message = {
                    "type": "start_session",
                    "tool_name": tool_name,
                    "args": args
                }
                await websocket.send(json.dumps(message))
                ws_response = await websocket.recv()
                response_data = json.loads(ws_response)

                response.data = {
                    "status": "created",
                    "tool_name": tool_name,
                    "session_id": response_data.get("session_id"),
                    "response": response_data
                }
                response.success = True
                response.execution_time = 0.1
        except Exception as e:
            response.data = {
                "status": "failed",
                "error": str(e),
                "tool_name": tool_name
            }
            response.success = False


class SessionListTool(ToolDefinition):
    """会话列表工具"""

    def __init__(self):
        super().__init__(
            name="session_list",
            description="获取所有活跃会话列表",
            category=ToolCategory.ANALYSIS
        )

    async def handle(self, request: ToolRequest, response: ToolResponse, context: TestContext):
        """处理会话列表查询"""
        uri = request.arguments.get("uri", "ws://localhost:8765")

        try:
            async with websockets.connect(uri) as websocket:
                message = {
                    "type": "list_sessions",
                    "data": {}
                }
                await websocket.send(json.dumps(message))
                ws_response = await websocket.recv()
                response_data = json.loads(ws_response)

                response.data = {
                    "status": "listed",
                    "sessions": response_data.get("sessions", []),
                    "count": response_data.get("count", 0)
                }
                response.success = True
                response.execution_time = 0.05
        except Exception as e:
            response.data = {
                "status": "failed",
                "error": str(e)
            }
            response.success = False


class MessageExchangeTool(ToolDefinition):
    """消息交换工具"""

    def __init__(self):
        super().__init__(
            name="message_exchange",
            description="测试 ping/pong 消息交换",
            category=ToolCategory.TESTING
        )

    async def handle(self, request: ToolRequest, response: ToolResponse, context: TestContext):
        """处理消息交换"""
        uri = request.arguments.get("uri", "ws://localhost:8765")

        try:
            async with websockets.connect(uri) as websocket:
                ping_message = {"type": "ping"}
                await websocket.send(json.dumps(ping_message))
                ws_response = await websocket.recv()
                response_data = json.loads(ws_response)

                response.data = {
                    "status": "exchanged",
                    "response_type": response_data.get("type"),
                    "success": response_data.get("type") == "pong"
                }
                response.success = response.data["success"]
                response.execution_time = 0.02
        except Exception as e:
            response.data = {
                "status": "failed",
                "error": str(e)
            }
            response.success = False


# ============================================
# 场景定义
# ============================================

FULL_WORKFLOW_SCENARIO = CodeTestScenario(
    name="full_workflow",
    description="完整工作流测试",
    prompt="执行完整的 zhineng-bridge 工作流，包括连接、会话创建、列表查询和消息交换",
    code_content="""
# 完整工作流
1. 连接 WebSocket
2. 创建会话
3. 查询会话列表
4. 测试消息交换
""",
    max_turns=5,
    expected_tools=[
        "websocket_connect",
        "session_create",
        "session_list",
        "message_exchange"
    ],
    required_tools=["websocket_connect"],
    category=TestInteractionType.CODE_GENERATION,
    tags=["workflow", "comprehensive"],
    priority=5
)

PERFORMANCE_SCENARIO = CodeTestScenario(
    name="performance_test",
    description="性能测试",
    prompt="测试 zhineng-bridge 的性能指标，包括连接延迟、会话创建时间等",
    code_content="""
# 性能测试
- 连接延迟 < 100ms
- 会话创建时间 < 200ms
- 消息交换延迟 < 50ms
""",
    max_turns=4,
    expected_tools=[
        "websocket_connect",
        "session_create",
        "message_exchange"
    ],
    category=TestInteractionType.PERFORMANCE_TEST,
    tags=["performance", "benchmark"],
    priority=4
)


# ============================================
# 测试类
# ============================================

@requires_lingflow
@pytest.mark.skip(reason="Production WS server uses WSS, not compatible with ws:// client")
class TestZhinengBridgeScenarios:
    """zhineng-bridge 场景测试套件"""

    @pytest.fixture
    def tool_registry(self):
        """创建工具注册表"""
        return {
            "websocket_connect": WebSocketConnectTool(),
            "session_create": SessionCreateTool(),
            "session_list": SessionListTool(),
            "message_exchange": MessageExchangeTool()
        }

    @pytest.fixture
    def runner(self):
        """创建场景运行器"""
        return AIScenarioRunner(timeout=30)

    @pytest.mark.asyncio
    async def test_full_workflow_scenario(self, runner, tool_registry):
        """测试完整工作流场景"""
        print("\n🚀 运行完整工作流场景...")

        result = await runner.run_scenario(FULL_WORKFLOW_SCENARIO, tool_registry)

        print(f"\n场景名称: {result.scenario_name}")
        print(f"状态: {result.status.value}")
        print(f"执行时间: {result.execution_time:.3f}s")
        print(f"捕获调用: {len(result.captured_calls)}")
        print(f"期望满足: {result.tool_expectations_met}")

        assert result.status == ScenarioStatus.PASSED
        assert result.tool_expectations_met
        assert len(result.captured_calls) >= 4

    @pytest.mark.asyncio
    async def test_performance_scenario(self, runner, tool_registry):
        """测试性能场景"""
        print("\n⚡ 运行性能测试场景...")

        result = await runner.run_scenario(PERFORMANCE_SCENARIO, tool_registry)

        print(f"\n场景名称: {result.scenario_name}")
        print(f"状态: {result.status.value}")
        print(f"执行时间: {result.execution_time:.3f}s")

        assert result.status == ScenarioStatus.PASSED
        assert result.execution_time < 10.0  # 整个测试应该在 10 秒内完成

    @pytest.mark.asyncio
    async def test_batch_scenarios(self, runner, tool_registry):
        """批量运行场景"""
        print("\n📦 批量运行场景...")

        scenarios = [FULL_WORKFLOW_SCENARIO, PERFORMANCE_SCENARIO]
        await runner.run_batch(scenarios, tool_registry)

        print("\n运行摘要:")
        summary = runner.get_summary()
        print(f"  总场景数: {summary['total_scenarios']}")
        print(f"  通过: {summary['passed']}")
        print(f"  失败: {summary['failed']}")
        print(f"  超时: {summary['timeout']}")
        print(f"  成功率: {summary['success_rate']:.1%}")

        assert summary['passed'] == len(scenarios)
        assert summary['success_rate'] == 1.0


# ============================================
# 综合测试报告生成
# ============================================

def generate_test_report(results: List[ScenarioResult]) -> str:
    """生成测试报告"""
    report = []
    report.append("=" * 70)
    report.append("zhineng-bridge 测试报告")
    report.append("=" * 70)
    report.append("")

    passed = sum(1 for r in results if r.status == ScenarioStatus.PASSED)
    failed = sum(1 for r in results if r.status == ScenarioStatus.FAILED)
    total = len(results)

    report.append(f"总测试数: {total}")
    report.append(f"通过: {passed}")
    report.append(f"失败: {failed}")
    report.append(f"成功率: {passed/total:.1%}")
    report.append("")

    report.append("-" * 70)
    report.append("详细结果:")
    report.append("-" * 70)

    for result in results:
        status_icon = "✅" if result.status == ScenarioStatus.PASSED else "❌"
        report.append(f"{status_icon} {result.scenario_name}")
        report.append(f"   状态: {result.status.value}")
        report.append(f"   执行时间: {result.execution_time:.3f}s")
        report.append(f"   工具调用: {len(result.captured_calls)}")
        if result.error_message:
            report.append(f"   错误: {result.error_message}")
        report.append("")

    return "\n".join(report)


# ============================================
# 主测试入口
# ============================================

if __name__ == "__main__":
    print("=" * 70)
    print("zhineng-bridge 场景驱动的 AI 测试 - LingFlow")
    print("=" * 70)
    print()

    async def main():
        """主测试函数"""
        # 创建运行器和工具
        runner = AIScenarioRunner(timeout=30)
        tools = {
            "websocket_connect": WebSocketConnectTool(),
            "session_create": SessionCreateTool(),
            "session_list": SessionListTool(),
            "message_exchange": MessageExchangeTool()
        }

        # 运行所有场景
        scenarios = [FULL_WORKFLOW_SCENARIO, PERFORMANCE_SCENARIO]
        results = await runner.run_batch(scenarios, tools)

        # 生成报告
        report = generate_test_report(results)
        print(report)

        # 保存报告
        report_path = Path("/home/ai/zhineng-bridge/test_report_lingflow.txt")
        with open(report_path, "w") as f:
            f.write(report)

        print(f"\n📄 报告已保存到: {report_path}")

    asyncio.run(main())

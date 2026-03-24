#!/usr/bin/env python3
"""
智桥基础使用示例

演示如何使用 Python API 与智桥交互
"""

import asyncio
import websockets
import json
from typing import Dict, Any
import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../phase1/session_manager'))

from session_manager import SessionManager


class ZhinengBridgeClient:
    """智桥客户端"""

    def __init__(self, host: str = "localhost", port: int = 8765):
        """
        初始化客户端

        Args:
            host: WebSocket 服务器主机
            port: WebSocket 服务器端口
        """
        self.host = host
        self.port = port
        self.websocket = None

    async def connect(self):
        """连接到服务器"""
        uri = f"ws://{self.host}:{self.port}"
        print(f"📡 连接到服务器: {uri}")

        self.websocket = await websockets.connect(uri)
        print("✅ 连接成功")

    async def disconnect(self):
        """断开连接"""
        if self.websocket:
            await self.websocket.close()
            print("⏹️  已断开连接")

    async def send_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送消息到服务器

        Args:
            message: 消息字典

        Returns:
            响应字典
        """
        if not self.websocket:
            raise RuntimeError("未连接到服务器")

        # 发送消息
        message_str = json.dumps(message)
        await self.websocket.send(message_str)
        print(f"📤 发送消息: {message.get('type', 'unknown')}")

        # 接收响应
        response_str = await self.websocket.recv()
        response = json.loads(response_str)
        print(f"📥 收到响应: {response.get('type', 'unknown')}")

        return response

    async def list_sessions(self) -> Dict[str, Any]:
        """列出所有会话"""
        message = {"type": "list_sessions"}
        return await self.send_message(message)

    async def create_session(self, tool_name: str, args: list = None) -> Dict[str, Any]:
        """
        创建会话

        Args:
            tool_name: 工具名称
            args: 参数列表

        Returns:
            会话信息
        """
        message = {
            "type": "start_session",
            "tool_name": tool_name,
            "args": args or []
        }
        return await self.send_message(message)

    async def stop_session(self, session_id: str) -> Dict[str, Any]:
        """
        停止会话

        Args:
            session_id: 会话 ID

        Returns:
            响应
        """
        message = {
            "type": "stop_session",
            "session_id": session_id
        }
        return await self.send_message(message)

    async def delete_session(self, session_id: str) -> Dict[str, Any]:
        """
        删除会话

        Args:
            session_id: 会话 ID

        Returns:
            响应
        """
        message = {
            "type": "delete_session",
            "session_id": session_id
        }
        return await self.send_message(message)

    async def ping(self) -> Dict[str, Any]:
        """发送心跳"""
        message = {"type": "ping"}
        return await self.send_message(message)


async def example_1_basic_connection():
    """示例 1: 基本连接"""
    print("\n=== 示例 1: 基本连接 ===\n")

    client = ZhinengBridgeClient()

    try:
        # 连接到服务器
        await client.connect()

        # 发送心跳
        await client.ping()

    finally:
        # 断开连接
        await client.disconnect()


async def example_2_list_sessions():
    """示例 2: 列出会话"""
    print("\n=== 示例 2: 列出会话 ===\n")

    client = ZhinengBridgeClient()

    try:
        await client.connect()

        # 列出会话
        response = await client.list_sessions()
        print(f"\n会话列表: {response}")
        print(f"会话数量: {response.get('count', 0)}")

    finally:
        await client.disconnect()


async def example_3_create_and_delete_session():
    """示例 3: 创建和删除会话"""
    print("\n=== 示例 3: 创建和删除会话 ===\n")

    client = ZhinengBridgeClient()

    try:
        await client.connect()

        # 创建会话
        print("\n创建会话...")
        session_response = await client.create_session("crush", ["--help"])
        session_id = session_response.get("session_id")
        print(f"✅ 会话已创建: {session_id}")

        # 停止会话
        print("\n停止会话...")
        await client.stop_session(session_id)
        print("✅ 会话已停止")

        # 删除会话
        print("\n删除会话...")
        await client.delete_session(session_id)
        print("✅ 会话已删除")

    finally:
        await client.disconnect()


async def example_4_multiple_sessions():
    """示例 4: 多个会话"""
    print("\n=== 示例 4: 多个会话 ===\n")

    client = ZhinengBridgeClient()

    try:
        await client.connect()

        # 创建多个会话
        tools = ["crush", "claude", "cursor"]
        session_ids = []

        print("\n创建多个会话...")
        for tool in tools:
            response = await client.create_session(tool, ["--help"])
            session_id = response.get("session_id")
            session_ids.append(session_id)
            print(f"✅ {tool} 会话已创建: {session_id}")

        # 列出会话
        print("\n列出所有会话...")
        response = await client.list_sessions()
        print(f"会话数量: {response.get('count', 0)}")

        # 清理会话
        print("\n清理会话...")
        for session_id in session_ids:
            await client.delete_session(session_id)
            print(f"✅ 会话已删除: {session_id}")

    finally:
        await client.disconnect()


async def example_5_session_manager():
    """示例 5: 使用 SessionManager"""
    print("\n=== 示例 5: 使用 SessionManager ===\n")

    # 创建 Session Manager
    manager = SessionManager(base_dir="/tmp/zhineng-bridge-example")

    # 列出工具
    print("\n可用工具:")
    tools = manager.list_tools()
    for tool_key, tool_info in tools.items():
        print(f"  - {tool_key}: {tool_info['name']}")

    # 创建会话
    print("\n创建会话...")
    try:
        session_id = manager.create_session('crush', args=['--help'])
        print(f"✅ 会话已创建: {session_id}")

        # 获取会话信息
        session = manager.get_session(session_id)
        print(f"会话信息: {session}")

        # 列出所有会话
        sessions = manager.list_sessions()
        print(f"\n会话数量: {len(sessions)}")

        # 获取活动会话
        active_session = manager.get_active_session()
        print(f"活动会话: {active_session}")

    except Exception as e:
        print(f"❌ 错误: {e}")


async def main():
    """主函数"""
    print("=" * 70)
    print("智桥基础使用示例")
    print("=" * 70)

    # 运行示例
    await example_1_basic_connection()
    await example_2_list_sessions()
    await example_3_create_and_delete_session()
    await example_4_multiple_sessions()
    await example_5_session_manager()

    print("\n" + "=" * 70)
    print("✅ 所有示例执行完成")
    print("=" * 70)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  用户中断")
        exit(0)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        exit(1)

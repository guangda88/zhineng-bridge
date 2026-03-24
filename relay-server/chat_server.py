#!/usr/bin/env python3
"""
zhineng-bridge 聊天中继服务器
支持 AI 对话功能
"""

import asyncio
import websockets
import json
from datetime import datetime
from typing import Dict, List
import re


class ChatRelayServer:
    """聊天中继服务器"""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        """初始化服务器
        
        Args:
            host: 主机地址
            port: 端口号
        """
        self.host = host
        self.port = port
        self.clients: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.server = None
        
        # AI 响应系统
        self.ai_responses = {
            '你好': '你好！我是智桥 AI 助手。有什么可以帮助您的吗？',
            'hi': 'Hi! 我是智桥 AI 助手。有什么可以帮助您的吗？',
            '你是谁': '我是智桥 AI 助手，一个跨平台的实时同步和通信SDK的智能助手。我可以帮助您管理会话、优化性能、解答问题等。',
            'zhineng-bridge': '智桥是一个跨平台的实时同步和通信SDK，支持多种AI编码工具和IDE，提供统一的接口和用户体验。',
            '功能': '智桥的主要功能包括：\n1. 多工具支持（8个AI工具）\n2. 会话管理\n3. 端到端加密\n4. 离线支持\n5. 性能优化\n6. 团队协作',
            '工具': '智桥支持以下AI工具：\n1. Crush - Charmbracelet Crush\n2. Claude Code - Anthropic Claude Code\n3. iFlow CLI - 阿里巴巴心流\n4. Cursor - Anysphere Cursor\n5. Trae - 字节跳动 Trae\n6. Droid - Factory Droid\n7. OpenClaw - OpenClaw\n8. GitHub Copilot - GitHub Copilot',
            '性能': '智桥的性能指标：\n- 会话创建时间: < 100ms\n- WebSocket 连接时间: < 50ms\n- 页面加载时间: < 2s\n- 内存使用: < 100MB',
            'LingMinOpt': 'LingMinOpt（灵极优）是一个极简自优化框架，用于自动优化系统参数。它是智桥的核心优化引擎。',
            '优化': '智桥使用 LingMinOpt 框架进行自动优化，包括：\n1. WebSocket 参数优化\n2. 性能参数优化\n3. 会话参数优化',
            '帮助': '我可以帮助您：\n1. 了解智桥的功能\n2. 管理会话\n3. 优化性能\n4. 解答技术问题\n5. 提供使用建议',
            'default': '谢谢您的消息！我是智桥 AI 助手，正在学习中。您可以询问我关于智桥的功能、工具、性能等问题。'
        }
    
    async def start(self):
        """启动服务器"""
        print(f"🚀 启动聊天中继服务器")
        print(f"   地址: {self.host}:{self.port}")
        print()
        
        self.server = await websockets.serve(
            self.handle_connection,
            self.host,
            self.port
        )
        
        print(f"✅ 聊天中继服务器已启动")
        print(f"   监听地址: ws://{self.host}:{self.port}")
        print()
        
        # 等待服务器停止
        await self.server.wait_closed()
    
    async def handle_connection(self, websocket: websockets.WebSocketServerProtocol):
        """处理客户端连接
        
        Args:
            websocket: WebSocket 连接
        """
        client_id = str(id(websocket))
        self.clients[client_id] = websocket
        
        print(f"📡 客户端已连接: {client_id}")
        
        try:
            async for message in websocket:
                await self.handle_message(client_id, message)
        except websockets.exceptions.ConnectionClosed:
            print(f"📡 客户端已断开: {client_id}")
        except Exception as e:
            print(f"❌ 处理客户端错误: {e}")
        finally:
            if client_id in self.clients:
                del self.clients[client_id]
    
    async def handle_message(self, client_id: str, message: str):
        """处理客户端消息
        
        Args:
            client_id: 客户端 ID
            message: 消息内容
        """
        try:
            data = json.loads(message)
            message_type = data.get("type", "unknown")
            
            print(f"📨 收到消息: {client_id} - {message_type}")
            
            # 根据消息类型处理
            if message_type == "message":
                await self.handle_chat_message(client_id, data)
            elif message_type == "list_sessions":
                response = await self.handle_list_sessions()
                await self.send_to_client(client_id, response)
            elif message_type == "start_session":
                response = await self.handle_start_session(data)
                await self.send_to_client(client_id, response)
            elif message_type == "stop_session":
                response = await self.handle_stop_session(data)
                await self.send_to_client(client_id, response)
            elif message_type == "delete_session":
                response = await self.handle_delete_session(data)
                await self.send_to_client(client_id, response)
            elif message_type == "ping":
                response = await self.handle_ping()
                await self.send_to_client(client_id, response)
            else:
                response = {
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                }
                await self.send_to_client(client_id, response)
            
        except json.JSONDecodeError:
            print(f"❌ 消息解析失败: {client_id}")
            await self.send_error(client_id, "Invalid JSON")
        except Exception as e:
            print(f"❌ 处理消息错误: {e}")
            await self.send_error(client_id, str(e))
    
    async def handle_chat_message(self, client_id: str, data: dict):
        """处理聊天消息
        
        Args:
            client_id: 客户端 ID
            data: 消息数据
        """
        user_message = data.get("message", "")
        
        if not user_message:
            return
        
        print(f"💬 用户消息: {user_message}")
        
        # 生成 AI 响应
        ai_response = self.generate_ai_response(user_message)
        
        # 发送 AI 响应
        response = {
            "type": "message",
            "message": ai_response,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.send_to_client(client_id, response)
    
    def generate_ai_response(self, message: str) -> str:
        """生成 AI 响应
        
        Args:
            message: 用户消息
            
        Returns:
            AI 响应
        """
        # 转换为小写
        message_lower = message.lower()
        
        # 查找匹配的响应
        for keyword, response in self.ai_responses.items():
            if keyword in message_lower:
                return response
        
        # 默认响应
        return self.ai_responses['default']
    
    async def handle_list_sessions(self):
        """处理列出会话请求"""
        print("📋 列出会话")
        
        # 模拟会话列表
        sessions = []
        
        return {
            "type": "sessions_list",
            "sessions": sessions,
            "count": len(sessions)
        }
    
    async def handle_start_session(self, data: dict):
        """处理启动会话请求
        
        Args:
            data: 请求数据
        """
        tool_name = data.get("tool_name", "unknown")
        args = data.get("args", [])
        
        print(f"➕ 启动会话: {tool_name}")
        
        # 模拟会话创建
        session_id = str(hash(datetime.now().isoformat()))
        session = {
            "session_id": session_id,
            "tool_name": tool_name,
            "status": "running",
            "created_at": datetime.now().isoformat(),
            "args": args
        }
        
        return {
            "type": "session_started",
            "session_id": session_id,
            "tool_name": tool_name,
            "status": "running"
        }
    
    async def handle_stop_session(self, data: dict):
        """处理停止会话请求
        
        Args:
            data: 请求数据
        """
        session_id = data.get("session_id")
        
        print(f"⏹️  停止会话: {session_id}")
        
        return {
            "type": "session_stopped",
            "session_id": session_id,
            "status": "stopped"
        }
    
    async def handle_delete_session(self, data: dict):
        """处理删除会话请求
        
        Args:
            data: 请求数据
        """
        session_id = data.get("session_id")
        
        print(f"🗑️  删除会话: {session_id}")
        
        return {
            "type": "session_deleted",
            "session_id": session_id
        }
    
    async def handle_ping(self):
        """处理心跳请求"""
        print("💓 心跳")
        
        return {
            "type": "pong",
            "timestamp": datetime.now().isoformat()
        }
    
    async def send_to_client(self, client_id: str, message: dict):
        """发送消息给客户端
        
        Args:
            client_id: 客户端 ID
            message: 消息内容
        """
        if client_id in self.clients:
            websocket = self.clients[client_id]
            try:
                await websocket.send(json.dumps(message))
                print(f"📤 发送消息: {client_id}")
            except Exception as e:
                print(f"❌ 发送消息失败: {e}")
    
    async def send_error(self, client_id: str, error_message: str):
        """发送错误消息给客户端
        
        Args:
            client_id: 客户端 ID
            error_message: 错误消息
        """
        await self.send_to_client(client_id, {
            "type": "error",
            "message": error_message
        })


async def main():
    """主函数"""
    server = ChatRelayServer(host="0.0.0.0", port=8765)
    await server.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  服务器已停止")

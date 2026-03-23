#!/usr/bin/env python3
"""
zhineng-bridge 中继服务器
"""

import asyncio
import websockets
import json
from datetime import datetime
from typing import Dict, List
import uuid


class CrushRelayServer:
    """Crush 中继服务器"""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        """初始化服务器
        
        Args:
            host: 主机地址
            port: 端口号
        """
        self.host = host
        self.port = port
        self.manager = None
        self.websockets: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.server = None
    
    async def start(self):
        """启动服务器"""
        print(f"🚀 启动中继服务器")
        print(f"   地址: {self.host}:{self.port}")
        print()
        
        self.server = await websockets.serve(
            self.handle_connection,
            self.host,
            self.port
        )
        
        print(f"✅ 中继服务器已启动")
        print(f"   监听地址: ws://{self.host}:{self.port}")
        print()
        
        # 等待服务器停止
        await self.server.wait_closed()
    
    async def handle_connection(self, websocket: websockets.WebSocketServerProtocol):
        """处理客户端连接
        
        Args:
            websocket: WebSocket 连接
        """
        client_id = str(uuid.uuid4())
        self.websockets[client_id] = websocket
        
        print(f"📡 客户端已连接: {client_id}")
        
        try:
            async for message in websocket:
                await self.handle_message(client_id, message)
        except websockets.exceptions.ConnectionClosed:
            print(f"📡 客户端已断开: {client_id}")
        except Exception as e:
            print(f"❌ 处理客户端错误: {e}")
        finally:
            if client_id in self.websockets:
                del self.websockets[client_id]
    
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
            if message_type == "list_sessions":
                response = await self.handle_list_sessions()
            elif message_type == "start_session":
                response = await self.handle_start_session(data)
            elif message_type == "stop_session":
                response = await self.handle_stop_session(data)
            elif message_type == "delete_session":
                response = await self.handle_delete_session(data)
            elif message_type == "ping":
                response = await self.handle_ping()
            else:
                response = {
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                }
            
            # 发送响应
            await self.send_to_client(client_id, response)
            
        except json.JSONDecodeError:
            print(f"❌ 消息解析失败: {client_id}")
            await self.send_error(client_id, "Invalid JSON")
        except Exception as e:
            print(f"❌ 处理消息错误: {e}")
            await self.send_error(client_id, str(e))
    
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
        session_id = str(uuid.uuid4())
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
        
        print(f"⏹️ 停止会话: {session_id}")
        
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
        
        print(f"🗑️ 删除会话: {session_id}")
        
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
        if client_id in self.websockets:
            websocket = self.websockets[client_id]
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
    
    async def stop(self):
        """停止服务器"""
        print("⏹️ 停止中继服务器")
        
        # 关闭所有连接
        for client_id, websocket in self.websockets.items():
            try:
                await websocket.close()
            except Exception as e:
                print(f"❌ 关闭连接失败: {e}")
        
        self.websockets.clear()
        
        # 关闭服务器
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        
        print("✅ 中继服务器已停止")


async def main():
    """主函数"""
    server = CrushRelayServer(host="0.0.0.0", port=8765)
    await server.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  服务器已停止")

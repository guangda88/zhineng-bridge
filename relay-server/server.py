#!/usr/bin/env python3
"""
智桥中继服务器 - Crush 专用

用于连接 Web 界面和 Crush 工具。
"""

import asyncio
import websockets
import json
from typing import Dict, Any
from pathlib import Path

# 添加 Session Manager 路径
sys.path.insert(0, str(Path(__file__).parent.parent / "phase1" / "session_manager"))

from session_manager import SessionManager


class CrushRelayServer:
    """Crush 中继服务器"""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        """
        初始化服务器
        
        Args:
            host: 主机
            port: 端口
        """
        self.host = host
        self.port = port
        self.manager = SessionManager()
        self.websockets: Dict[str, Any] = {}
    
    async def handle_websocket(self, websocket, path):
        """处理 WebSocket 连接"""
        print(f"✅ 新连接: {websocket.remote_address}")
        
        try:
            async for message in websocket:
                # 解析消息
                data = json.loads(message)
                
                # 处理不同类型的消息
                message_type = data.get('type')
                
                if message_type == 'start_session':
                    await self.handle_start_session(websocket, data)
                
                elif message_type == 'stop_session':
                    await self.handle_stop_session(websocket, data)
                
                elif message_type == 'send_command':
                    await self.handle_send_command(websocket, data)
                
                elif message_type == 'read_output':
                    await self.handle_read_output(websocket, data)
                
                else:
                    print(f"⚠️  未知消息类型: {message_type}")
        
        except websockets.exceptions.ConnectionClosed:
            print(f"❌ 连接关闭: {websocket.remote_address}")
        
        except Exception as e:
            print(f"❌ 错误: {e}")
    
    async def handle_start_session(self, websocket, data: Dict[str, Any]):
        """处理启动会话"""
        tool_name = data.get('tool_name', 'crush')
        args = data.get('args', [])
        
        # 创建会话
        session_id = self.manager.create_session(tool_name, args)
        
        # 启动会话
        await self.manager.start_session(session_id)
        
        # 发送响应
        response = {
            'type': 'session_started',
            'session_id': session_id,
            'tool_name': tool_name
        }
        
        await websocket.send(json.dumps(response))
        
        print(f"✅ 会话已启动: {session_id}")
    
    async def handle_stop_session(self, websocket, data: Dict[str, Any]):
        """处理停止会话"""
        session_id = data.get('session_id')
        
        # 停止会话
        await self.manager.stop_session(session_id)
        
        # 发送响应
        response = {
            'type': 'session_stopped',
            'session_id': session_id
        }
        
        await websocket.send(json.dumps(response))
        
        print(f"✅ 会话已停止: {session_id}")
    
    async def handle_send_command(self, websocket, data: Dict[str, Any]):
        """处理发送命令"""
        session_id = data.get('session_id')
        command = data.get('command')
        
        # 发送命令
        await self.manager.send_command(session_id, command)
        
        # 发送响应
        response = {
            'type': 'command_sent',
            'session_id': session_id,
            'command': command
        }
        
        await websocket.send(json.dumps(response))
        
        print(f"✅ 命令已发送: {command}")
    
    async def handle_read_output(self, websocket, data: Dict[str, Any]):
        """处理读取输出"""
        session_id = data.get('session_id')
        
        # 读取输出
        output = await self.manager.read_output(session_id)
        
        if output:
            # 发送输出
            response = {
                'type': 'output',
                'session_id': session_id,
                'output': output
            }
            
            await websocket.send(json.dumps(response))
            
            print(f"✅ 输出已发送")
    
    async def start(self):
        """启动服务器"""
        print(f"🚀 启动服务器: {self.host}:{self.port}")
        
        server = await websockets.serve(
            self.handle_websocket,
            self.host,
            self.port
        )
        
        print(f"✅ 服务器已启动")
        
        await server.wait_closed()


async def main():
    """主函数"""
    server = CrushRelayServer()
    await server.start()


if __name__ == "__main__":
    asyncio.run(main())

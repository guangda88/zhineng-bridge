#!/usr/bin/env python3
"""
zhineng-bridge Session Manager
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any


class SessionManager:
    """Session Manager - 会话管理器"""
    
    def __init__(self, base_dir: str = "/tmp"):
        """
        初始化 Session Manager
        
        Args:
            base_dir: 基础目录
        """
        self.base_dir = base_dir
        self.sessions: Dict[str, Session] = {}
        self.active_session_id: Optional[str] = None
        
        # 工具列表
        self.tools = {
            'crush': {
                'name': 'Crush',
                'description': 'Charmbracelet Crush - AI 编码助手',
                'executable': '/usr/local/bin/crush',
                'icon': '💎',
                'color': '#FFE66D'
            },
            'claude': {
                'name': 'Claude Code',
                'description': 'Anthropic Claude Code - AI 编码助手',
                'executable': '/usr/local/bin/claude',
                'icon': '🤖',
                'color': '#FF6B6B'
            },
            'iflow': {
                'name': 'iFlow CLI',
                'description': '阿里巴巴心流 iFlow CLI - AI 编码助手',
                'executable': '/usr/local/bin/iflow',
                'icon': '🌊',
                'color': '#4ECDC4'
            },
            'cursor': {
                'name': 'Cursor',
                'description': 'Anysphere Cursor - AI IDE',
                'executable': '/usr/local/bin/cursor',
                'icon': '👆',
                'color': '#45B7D1'
            },
            'trae': {
                'name': 'Trae',
                'description': '字节跳动 Trae - AI IDE（国产）',
                'executable': '/usr/local/bin/trae',
                'icon': '🌊',
                'color': '#96CEB4'
            },
            'factroydroid': {
                'name': 'Droid',
                'description': 'Factory Droid - AI Agent',
                'executable': '/usr/local/bin/droid',
                'icon': '🤖',
                'color': '#FFEEAD'
            },
            'openclaw': {
                'name': 'OpenClaw',
                'description': 'OpenClaw - AI 助手',
                'executable': '/usr/local/bin/openclaw',
                'icon': '🦞',
                'color': '#D4A5A5'
            },
            'copilot': {
                'name': 'GitHub Copilot',
                'description': 'GitHub Copilot - AI 助手',
                'executable': '/usr/local/bin/copilot',
                'icon': '🤖',
                'color': '#F0F0F0'
            }
        }
        
        print("✅ SessionManager 已初始化")
        print(f"   基础目录: {base_dir}")
        print(f"   可用工具: {len(self.tools)}")
    
    def list_tools(self) -> Dict[str, Dict[str, Any]]:
        """
        列出所有工具
        
        Returns:
            工具字典
        """
        return self.tools
    
    def get_tool_info(self, tool_key: str) -> Optional[Dict[str, Any]]:
        """
        获取工具信息
        
        Args:
            tool_key: 工具键
        
        Returns:
            工具信息或 None
        """
        return self.tools.get(tool_key)
    
    def create_session(self, tool_name: str, args: List[str] = None) -> str:
        """
        创建会话
        
        Args:
            tool_name: 工具名称
            args: 参数列表
        
        Returns:
            会话 ID
        """
        # 检查工具是否存在
        if tool_name not in self.tools:
            raise ValueError(f"工具不存在: {tool_name}")
        
        # 生成会话 ID
        session_id = str(uuid.uuid4())
        
        # 创建会话
        session = Session(
            session_id=session_id,
            tool_name=tool_name,
            args=args or [],
            base_dir=self.base_dir
        )
        
        # 添加到会话列表
        self.sessions[session_id] = session
        
        # 设置为活动会话
        self.active_session_id = session_id
        
        print(f"✅ 会话已创建: {session_id}")
        print(f"   工具: {tool_name}")
        print(f"   状态: {session.status}")
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话
        
        Args:
            session_id: 会话 ID
        
        Returns:
            会话信息或 None
        """
        session = self.sessions.get(session_id)
        if session:
            return session.to_dict()
        return None
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        列出所有会话
        
        Returns:
            会话列表
        """
        return [session.to_dict() for session in self.sessions.values()]
    
    def get_active_session(self) -> Optional[Dict[str, Any]]:
        """
        获取活动会话
        
        Returns:
            活动会话信息或 None
        """
        if self.active_session_id:
            return self.get_session(self.active_session_id)
        return None
    
    def set_active_session(self, session_id: str) -> None:
        """
        设置活动会话
        
        Args:
            session_id: 会话 ID
        """
        if session_id in self.sessions:
            self.active_session_id = session_id
            print(f"✅ 活动会话已设置: {session_id}")
        else:
            raise ValueError(f"会话不存在: {session_id}")


class Session:
    """Session - 会话类"""
    
    def __init__(self, session_id: str, tool_name: str, args: List[str], base_dir: str = "/tmp"):
        """
        初始化会话
        
        Args:
            session_id: 会话 ID
            tool_name: 工具名称
            args: 参数列表
            base_dir: 基础目录
        """
        self.session_id = session_id
        self.tool_name = tool_name
        self.args = args
        self.base_dir = base_dir
        self.status = "created"
        self.created_at = datetime.now().isoformat()
        self.wrapper = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        Returns:
            会话字典
        """
        return {
            'session_id': self.session_id,
            'tool_name': self.tool_name,
            'status': self.status,
            'created_at': self.created_at,
            'args': self.args
        }


if __name__ == "__main__":
    # 测试
    manager = SessionManager()
    
    # 列出工具
    print("\n📋 可用工具:")
    tools = manager.list_tools()
    for tool_key, tool_info in tools.items():
        print(f"  - {tool_key}: {tool_info['name']}")
    
    # 创建会话
    print("\n➕ 创建会话...")
    try:
        session_id = manager.create_session('crush', args=['--help'])
        print(f"✅ 会话已创建: {session_id}")
    except Exception as e:
        print(f"⚠️  创建会话失败（预期行为）: {e}")
    
    # 列出会话
    print("\n📋 会话列表:")
    sessions = manager.list_sessions()
    if sessions:
        for session in sessions:
            print(f"  - {session['session_id']}: {session['tool_name']}")
    else:
        print("  (无会话）")

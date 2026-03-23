#!/usr/bin/env python3
"""
智桥 Phase 1: Session Manager

会话管理器，用于整合通用包装器、管理多个会话、实现输出转发。
"""

import os
import sys
import asyncio
import json
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field, asdict
from pathlib import Path

# 添加通用包装器路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "tools"))

from universal_wrapper import create_wrapper, UniversalToolWrapper


@dataclass
class Session:
    """会话数据类"""
    
    session_id: str
    tool_name: str
    work_dir: str
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    wrapper: Optional[UniversalToolWrapper] = None
    status: str = "created"  # created, running, stopped, paused
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    stopped_at: Optional[str] = None
    output_events: List[Dict[str, Any]] = field(default_factory=list)
    commands: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['wrapper'] = None  # 不序列化 wrapper
        return data


class SessionManager:
    """会话管理器"""
    
    # 可用工具列表
    AVAILABLE_TOOLS = {
        'claude': {
            'name': 'Claude Code',
            'description': 'Anthropic Claude Code - AI 编码助手',
            'executable': 'claude',
            'icon': '🤖',
            'color': '#FF6B6B'
        },
        'iflow': {
            'name': 'iFlow CLI',
            'description': '阿里巴巴心流 iFlow CLI - AI 编码助手（国产）',
            'executable': 'iflow',
            'icon': '🌊',
            'color': '#4ECDC4'
        },
        'crush': {
            'name': 'Crush',
            'description': 'Charmbracelet Crush - AI 编码助手',
            'executable': 'crush',
            'icon': '💎',
            'color': '#FFE66D'
        },
        'cursor': {
            'name': 'Cursor',
            'description': 'Anysphere Cursor - AI IDE',
            'executable': 'cursor',
            'icon': '👆',
            'color': '#45B7D1'
        },
        'trae': {
            'name': 'Trae',
            'description': '字节跳动 Trae - AI IDE（国产）',
            'executable': 'trae',
            'icon': '🌊',
            'color': '#96CEB4'
        },
        'factroydroid': {
            'name': 'Droid',
            'description': 'Factory Droid - AI Agent',
            'executable': 'factroydroid',
            'icon': '🤖',
            'color': '#FFEEAD'
        },
        'openclaw': {
            'name': 'OpenClaw',
            'description': 'OpenClaw - AI 助手',
            'executable': 'openclaw',
            'icon': '🦞',
            'color': '#D4A5A5'
        },
        'copilot': {
            'name': 'GitHub Copilot',
            'description': 'GitHub Copilot - AI 助手',
            'executable': 'copilot',
            'icon': '🤖',
            'color': '#F0F0F0'
        }
    }
    
    def __init__(self, base_dir: str = "/home/ai"):
        """
        初始化会话管理器
        
        Args:
            base_dir: 基础目录
        """
        self.base_dir = Path(base_dir)
        self.sessions: Dict[str, Session] = {}
        self.active_session_id: Optional[str] = None
        self.output_queue = asyncio.Queue()
        
        # 创建工作目录
        self.work_dir = self.base_dir / ".zhineng-bridge-sessions"
        self.work_dir.mkdir(exist_ok=True)
        
        print(f"✅ SessionManager 已初始化")
        print(f"   基础目录: {self.base_dir}")
        print(f"   工作目录: {self.work_dir}")
    
    def list_tools(self) -> Dict[str, Dict[str, str]]:
        """
        列出所有可用工具
        
        Returns:
            工具列表
        """
        return self.AVAILABLE_TOOLS
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, str]]:
        """
        获取工具信息
        
        Args:
            tool_name: 工具名称
            
        Returns:
            工具信息
        """
        return self.AVAILABLE_TOOLS.get(tool_name)
    
    def create_session(
        self,
        tool_name: str,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        work_dir: Optional[str] = None
    ) -> str:
        """
        创建会话
        
        Args:
            tool_name: 工具名称
            args: 参数列表
            env: 环境变量
            work_dir: 工作目录
            
        Returns:
            会话 ID
        """
        # 验证工具
        if tool_name not in self.AVAILABLE_TOOLS:
            raise ValueError(f"未知工具: {tool_name}")
        
        # 生成会话 ID
        session_id = str(uuid.uuid4())
        
        # 设置工作目录
        if work_dir is None:
            session_work_dir = self.work_dir / session_id
            session_work_dir.mkdir(exist_ok=True)
        else:
            session_work_dir = Path(work_dir)
        
        # 设置参数
        if args is None:
            args = []
        
        # 设置环境变量
        if env is None:
            env = {}
        
        # 创建会话
        session = Session(
            session_id=session_id,
            tool_name=tool_name,
            work_dir=str(session_work_dir),
            args=args,
            env=env
        )
        
        # 保存会话
        self.sessions[session_id] = session
        
        # 设置为活动会话
        self.active_session_id = session_id
        
        print(f"✅ 会话已创建: {session_id}")
        print(f"   工具: {tool_name}")
        print(f"   工作目录: {session_work_dir}")
        
        return session_id
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        列出所有会话
        
        Returns:
            会话列表
        """
        return [session.to_dict() for session in self.sessions.values()]
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话信息
        
        Args:
            session_id: 会话 ID
            
        Returns:
            会话信息
        """
        session = self.sessions.get(session_id)
        if session:
            return session.to_dict()
        return None
    
    def get_active_session(self) -> Optional[Dict[str, Any]]:
        """
        获取活动会话
        
        Returns:
            会话信息
        """
        if self.active_session_id:
            return self.get_session(self.active_session_id)
        return None


# 便捷函数
def create_session_manager(base_dir: str = "/home/ai") -> SessionManager:
    """
    创建会话管理器
    
    Args:
        base_dir: 基础目录
        
    Returns:
        会话管理器
    """
    return SessionManager(base_dir)


if __name__ == "__main__":
    # 测试
    import sys
    
    print("=" * 70)
    print("🚀 Session Manager 测试")
    print("=" * 70)
    print()
    
    # 创建会话管理器
    manager = create_session_manager()
    
    # 列出工具
    print("📋 可用工具:")
    tools = manager.list_tools()
    for tool_key, tool_info in tools.items():
        print(f"  {tool_info['icon']} {tool_key}: {tool_info['name']}")
        print(f"     描述: {tool_info['description']}")
    print()
    
    print("✅ Session Manager 测试完成")
    print("=" * 70)

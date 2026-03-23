#!/usr/bin/env python3
"""
Session Manager 单元测试
"""

import unittest
import sys
import os
from pathlib import Path

# 添加 Session Manager 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "phase1" / "session_manager"))

from session_manager import SessionManager, Session
from datetime import datetime


class TestSessionManager(unittest.TestCase):
    """Session Manager 测试类"""
    
    def setUp(self):
        """设置测试环境"""
        self.manager = SessionManager(base_dir="/tmp/test_zhineng_bridge")
    
    def tearDown(self):
        """清理测试环境"""
        import shutil
        if os.path.exists("/tmp/test_zhineng_bridge"):
            shutil.rmtree("/tmp/test_zhineng_bridge")
    
    def test_list_tools(self):
        """测试工具列表"""
        tools = self.manager.list_tools()
        
        # 检查工具列表不为空
        self.assertIsNotNone(tools)
        self.assertGreater(len(tools), 0)
        
        # 检查必要工具存在
        self.assertIn('crush', tools)
        self.assertIn('claude', tools)
        self.assertIn('iflow', tools)
        
        # 检查工具信息完整
        for tool_key, tool_info in tools.items():
            self.assertIn('name', tool_info)
            self.assertIn('description', tool_info)
            self.assertIn('executable', tool_info)
            self.assertIn('icon', tool_info)
            self.assertIn('color', tool_info)
    
    def test_get_tool_info(self):
        """测试获取工具信息"""
        # 测试存在的工具
        crush_info = self.manager.get_tool_info('crush')
        self.assertIsNotNone(crush_info)
        self.assertEqual(crush_info['name'], 'Crush')
        
        # 测试不存在的工具
        fake_info = self.manager.get_tool_info('fake_tool')
        self.assertIsNone(fake_info)
    
    def test_create_session(self):
        """测试创建会话"""
        # 创建会话
        session_id = self.manager.create_session('crush', args=['--help'])
        
        # 检查会话 ID 不为空
        self.assertIsNotNone(session_id)
        self.assertGreater(len(session_id), 0)
        
        # 检查会话已创建
        self.assertIn(session_id, self.manager.sessions)
        
        # 检查会话状态
        session = self.manager.sessions[session_id]
        self.assertEqual(session.tool_name, 'crush')
        self.assertEqual(session.status, 'created')
        self.assertEqual(session.args, ['--help'])
    
    def test_create_session_invalid_tool(self):
        """测试创建会话（无效工具）"""
        with self.assertRaises(ValueError):
            self.manager.create_session('invalid_tool')
    
    def test_list_sessions(self):
        """测试列会话"""
        # 创建多个会话
        session_id1 = self.manager.create_session('crush')
        session_id2 = self.manager.create_session('claude')
        
        # 列出会话
        sessions = self.manager.list_sessions()
        
        # 检查会话列表不为空
        self.assertIsNotNone(sessions)
        self.assertEqual(len(sessions), 2)
        
        # 检查会话信息完整
        for session in sessions:
            self.assertIn('session_id', session)
            self.assertIn('tool_name', session)
            self.assertIn('status', session)
            self.assertIn('created_at', session)
    
    def test_get_session(self):
        """测试获取会话"""
        # 创建会话
        session_id = self.manager.create_session('crush')
        
        # 获取会话
        session = self.manager.get_session(session_id)
        
        # 检查会话信息完整
        self.assertIsNotNone(session)
        self.assertEqual(session['session_id'], session_id)
        self.assertEqual(session['tool_name'], 'crush')
        
        # 获取不存在的会话
        fake_session = self.manager.get_session('fake_session_id')
        self.assertIsNone(fake_session)
    
    def test_get_active_session(self):
        """测试获取活动会话"""
        # 创建会话（自动设置为活动会话）
        session_id = self.manager.create_session('crush')
        
        # 获取活动会话
        active_session = self.manager.get_active_session()
        
        # 检查活动会话
        self.assertIsNotNone(active_session)
        self.assertEqual(active_session['session_id'], session_id)
    
    def test_set_active_session(self):
        """测试设置活动会话"""
        # 创建多个会话
        session_id1 = self.manager.create_session('crush')
        session_id2 = self.manager.create_session('claude')
        
        # 设置活动会话
        self.manager.set_active_session(session_id1)
        
        # 检查活动会话
        self.assertEqual(self.manager.active_session_id, session_id1)


class TestSession(unittest.TestCase):
    """Session 测试类"""
    
    def test_session_creation(self):
        """测试 Session 创建"""
        session = Session(
            session_id="test-session-id",
            tool_name="crush",
            work_dir="/tmp/test"
        )
        
        # 检查 Session 属性
        self.assertEqual(session.session_id, "test-session-id")
        self.assertEqual(session.tool_name, "crush")
        self.assertEqual(session.work_dir, "/tmp/test")
        self.assertEqual(session.status, "created")
    
    def test_session_to_dict(self):
        """测试 Session 转换为字典"""
        session = Session(
            session_id="test-session-id",
            tool_name="crush",
            work_dir="/tmp/test"
        )
        
        # 转换为字典
        session_dict = session.to_dict()
        
        # 检查字典属性
        self.assertEqual(session_dict['session_id'], "test-session-id")
        self.assertEqual(session_dict['tool_name'], "crush")
        self.assertEqual(session_dict['status'], "created")
        
        # 检查 wrapper 不被序列化
        self.assertIsNone(session_dict['wrapper'])


if __name__ == '__main__':
    unittest.main(verbosity=2)

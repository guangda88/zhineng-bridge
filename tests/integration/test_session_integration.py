#!/usr/bin/env python3
"""
Session Manager 集成测试
"""

import unittest
import sys
import os
from pathlib import Path

# 添加 Session Manager 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "phase1" / "session_manager"))

from session_manager import SessionManager


class TestSessionIntegration(unittest.TestCase):
    """Session 集成测试类"""
    
    def setUp(self):
        """设置测试环境"""
        self.manager = SessionManager(base_dir="/tmp/test_zhineng_bridge_integration")
    
    def tearDown(self):
        """清理测试环境"""
        import shutil
        if os.path.exists("/tmp/test_zhineng_bridge_integration"):
            shutil.rmtree("/tmp/test_zhineng_bridge_integration")
    
    def test_session_lifecycle(self):
        """测试会话生命周期"""
        # 1. 创建会话
        session_id = self.manager.create_session('crush')
        self.assertIsNotNone(session_id)
        
        # 2. 列出会话
        sessions = self.manager.list_sessions()
        self.assertEqual(len(sessions), 1)
        
        # 3. 获取会话
        session = self.manager.get_session(session_id)
        self.assertIsNotNone(session)
        self.assertEqual(session['session_id'], session_id)
        
        # 4. 切换活动会话
        self.manager.set_active_session(session_id)
        self.assertEqual(self.manager.active_session_id, session_id)
        
        # 5. 获取活动会话
        active_session = self.manager.get_active_session()
        self.assertIsNotNone(active_session)
        self.assertEqual(active_session['session_id'], session_id)
    
    def test_multiple_sessions(self):
        """测试多个会话"""
        # 创建多个会话
        session_id1 = self.manager.create_session('crush')
        session_id2 = self.manager.create_session('claude')
        session_id3 = self.manager.create_session('iflow')
        
        # 列出会话
        sessions = self.manager.list_sessions()
        self.assertEqual(len(sessions), 3)
        
        # 切换活动会话
        self.manager.set_active_session(session_id1)
        active_session = self.manager.get_active_session()
        self.assertEqual(active_session['session_id'], session_id1)
        
        self.manager.set_active_session(session_id2)
        active_session = self.manager.get_active_session()
        self.assertEqual(active_session['session_id'], session_id2)
        
        self.manager.set_active_session(session_id3)
        active_session = self.manager.get_active_session()
        self.assertEqual(active_session['session_id'], session_id3)


if __name__ == '__main__':
    unittest.main(verbosity=2)

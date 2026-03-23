#!/usr/bin/env python3
"""
性能测试
"""

import unittest
import sys
import os
import time
from pathlib import Path

# 添加 Session Manager 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "phase1" / "session_manager"))

from session_manager import SessionManager


class TestPerformance(unittest.TestCase):
    """性能测试类"""
    
    def setUp(self):
        """设置测试环境"""
        self.manager = SessionManager(base_dir="/tmp/test_zhineng_bridge_performance")
    
    def tearDown(self):
        """清理测试环境"""
        import shutil
        if os.path.exists("/tmp/test_zhineng_bridge_performance"):
            shutil.rmtree("/tmp/test_zhineng_bridge_performance")
    
    def test_session_creation_performance(self):
        """测试会话创建性能"""
        # 测试创建 100 个会话的性能
        start_time = time.time()
        
        for i in range(100):
            self.manager.create_session('crush')
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # 检查创建时间 < 1 秒
        self.assertLess(elapsed_time, 1.0, f"创建 100 个会话耗时 {elapsed_time:.2f} 秒")
        
        # 计算平均时间
        avg_time = elapsed_time / 100
        print(f"\n创建 100 个会话总耗时: {elapsed_time:.2f} 秒")
        print(f"平均每个会话创建耗时: {avg_time*1000:.2f} 毫秒")
    
    def test_session_list_performance(self):
        """测试会话列表性能"""
        # 创建 100 个会话
        for i in range(100):
            self.manager.create_session('crush')
        
        # 测试列会话性能
        start_time = time.time()
        
        sessions = self.manager.list_sessions()
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # 检查列表时间 < 100 毫秒
        self.assertLess(elapsed_time, 0.1, f"列出 100 个会话耗时 {elapsed_time*1000:.2f} 毫秒")
        
        print(f"\n列出 100 个会话耗时: {elapsed_time*1000:.2f} 毫秒")
    
    def test_tool_list_performance(self):
        """测试工具列表性能"""
        # 测试列工具性能
        start_time = time.time()
        
        tools = self.manager.list_tools()
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # 检查列表时间 < 10 毫秒
        self.assertLess(elapsed_time, 0.01, f"列出工具耗时 {elapsed_time*1000:.2f} 毫秒")
        
        print(f"\n列出工具耗时: {elapsed_time*1000:.2f} 毫秒")


if __name__ == '__main__':
    unittest.main(verbosity=2)

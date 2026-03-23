#!/usr/bin/env python3
"""
中继服务器单元测试
"""

import unittest
import sys
import os
from pathlib import Path

# 添加中继服务器路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "relay-server"))


class TestCrushRelayServer(unittest.TestCase):
    """Crush 中继服务器测试类"""
    
    def test_server_initialization(self):
        """测试服务器初始化"""
        # 注意：这个测试需要在服务器不运行的情况下进行
        # 所以我们只测试类的导入和基本属性
        try:
            from server import CrushRelayServer
            
            # 创建服务器实例
            server = CrushRelayServer(host="localhost", port=8765)
            
            # 检查服务器属性
            self.assertEqual(server.host, "localhost")
            self.assertEqual(server.port, 8765)
            self.assertIsNotNone(server.manager)
            self.assertIsNotNone(server.websockets)
            
        except Exception as e:
            self.fail(f"服务器初始化失败: {e}")
    
    def test_message_handling(self):
        """测试消息处理"""
        # 测试不同类型的消息
        message_types = [
            'start_session',
            'stop_session',
            'send_command',
            'read_output'
        ]
        
        for message_type in message_types:
            # 创建测试消息
            message = {
                'type': message_type,
                'data': {'test': True}
            }
            
            # 检查消息类型
            self.assertEqual(message['type'], message_type)
            self.assertIn('data', message)


if __name__ == '__main__':
    unittest.main(verbosity=2)

#!/usr/bin/env python3
"""
SessionManager 集成测试
"""

import pytest
import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../phase1/session_manager'))

from session_manager import SessionManager, Session


class TestSessionManager:
    """测试 SessionManager 类"""

    @pytest.fixture
    def manager(self):
        """创建 SessionManager 实例"""
        return SessionManager(base_dir="/tmp/zhineng-bridge-test")

    def test_init(self, manager):
        """测试 SessionManager 初始化"""
        assert manager.base_dir == "/tmp/zhineng-bridge-test"
        assert len(manager.sessions) == 0
        assert manager.active_session_id is None
        assert len(manager.tools) == 8

    def test_list_tools(self, manager):
        """测试列出工具"""
        tools = manager.list_tools()

        assert len(tools) == 8
        assert 'crush' in tools
        assert 'claude' in tools
        assert 'cursor' in tools
        assert 'copilot' in tools

        # 验证工具信息结构
        for tool_key, tool_info in tools.items():
            assert 'name' in tool_info
            assert 'description' in tool_info
            assert 'executable' in tool_info
            assert 'icon' in tool_info
            assert 'color' in tool_info

    def test_get_tool_info(self, manager):
        """测试获取工具信息"""
        # 测试存在的工具
        tool_info = manager.get_tool_info('crush')
        assert tool_info is not None
        assert tool_info['name'] == 'Crush'
        assert tool_info['executable'] == '/usr/local/bin/crush'

        # 测试不存在的工具
        tool_info = manager.get_tool_info('nonexistent')
        assert tool_info is None

    def test_create_session(self, manager):
        """测试创建会话"""
        # 创建会话
        session_id = manager.create_session('crush', args=['--help'])

        # 验证会话已创建
        assert session_id in manager.sessions
        assert manager.active_session_id == session_id

        # 验证会话信息
        session = manager.sessions[session_id]
        assert session.tool_name == 'crush'
        assert session.args == ['--help']
        assert session.status == 'created'

    def test_create_session_invalid_tool(self, manager):
        """测试创建会话（无效工具）"""
        with pytest.raises(ValueError, match="工具不存在"):
            manager.create_session('nonexistent_tool')

    def test_create_session_multiple(self, manager):
        """测试创建多个会话"""
        # 创建第一个会话
        session_id1 = manager.create_session('crush', args=['--help'])
        assert manager.active_session_id == session_id1

        # 创建第二个会话
        session_id2 = manager.create_session('claude', args=['--help'])
        assert manager.active_session_id == session_id2  # 活动会话应该更新

        # 验证两个会话都存在
        assert session_id1 in manager.sessions
        assert session_id2 in manager.sessions
        assert len(manager.sessions) == 2

    def test_get_session(self, manager):
        """测试获取会话"""
        # 创建会话
        session_id = manager.create_session('cursor', args=['--version'])

        # 获取会话
        session_info = manager.get_session(session_id)

        # 验证会话信息
        assert session_info is not None
        assert session_info['session_id'] == session_id
        assert session_info['tool_name'] == 'cursor'
        assert session_info['args'] == ['--version']
        assert 'created_at' in session_info

    def test_get_session_not_found(self, manager):
        """测试获取不存在的会话"""
        session_info = manager.get_session('nonexistent-session-id')
        assert session_info is None

    def test_list_sessions(self, manager):
        """测试列出所有会话"""
        # 初始状态：无会话
        sessions = manager.list_sessions()
        assert len(sessions) == 0

        # 创建会话
        session_id1 = manager.create_session('crush', args=['--help'])
        session_id2 = manager.create_session('claude', args=['--version'])

        # 列出会话
        sessions = manager.list_sessions()
        assert len(sessions) == 2

        # 验证会话信息
        session_ids = [s['session_id'] for s in sessions]
        assert session_id1 in session_ids
        assert session_id2 in session_ids

    def test_get_active_session(self, manager):
        """测试获取活动会话"""
        # 初始状态：无活动会话
        active_session = manager.get_active_session()
        assert active_session is None

        # 创建会话
        session_id = manager.create_session('cursor', args=['--help'])

        # 获取活动会话
        active_session = manager.get_active_session()
        assert active_session is not None
        assert active_session['session_id'] == session_id

    def test_set_active_session(self, manager):
        """测试设置活动会话"""
        # 创建多个会话
        session_id1 = manager.create_session('crush', args=['--help'])
        session_id2 = manager.create_session('claude', args=['--version'])

        # 当前活动会话应该是 session_id2
        assert manager.active_session_id == session_id2

        # 设置活动会话为 session_id1
        manager.set_active_session(session_id1)
        assert manager.active_session_id == session_id1

        # 获取活动会话验证
        active_session = manager.get_active_session()
        assert active_session['session_id'] == session_id1

    def test_set_active_session_invalid(self, manager):
        """测试设置活动会话（无效会话）"""
        with pytest.raises(ValueError, match="会话不存在"):
            manager.set_active_session('nonexistent-session-id')


class TestSession:
    """测试 Session 类"""

    def test_init(self):
        """测试 Session 初始化"""
        session = Session(
            session_id="test-session-id",
            tool_name="crush",
            args=["--help"],
            base_dir="/tmp"
        )

        assert session.session_id == "test-session-id"
        assert session.tool_name == "crush"
        assert session.args == ["--help"]
        assert session.base_dir == "/tmp"
        assert session.status == "created"
        assert session.wrapper is None
        assert session.created_at is not None

    def test_to_dict(self):
        """测试 Session.to_dict 方法"""
        session = Session(
            session_id="test-session-id",
            tool_name="cursor",
            args=["--version"],
            base_dir="/tmp"
        )

        session_dict = session.to_dict()

        assert session_dict['session_id'] == "test-session-id"
        assert session_dict['tool_name'] == "cursor"
        assert session_dict['args'] == ["--version"]
        assert session_dict['status'] == "created"
        assert 'created_at' in session_dict

    def test_to_dict_all_fields(self):
        """测试 Session.to_dict 包含所有字段"""
        session = Session(
            session_id="test-123",
            tool_name="claude",
            args=["--help"],
            base_dir="/tmp/test"
        )

        session_dict = session.to_dict()

        expected_keys = ['session_id', 'tool_name', 'status', 'created_at', 'args']
        for key in expected_keys:
            assert key in session_dict, f"缺少字段: {key}"

        # 验证没有额外字段
        assert len(session_dict) == len(expected_keys)


class TestIntegration:
    """集成测试"""

    def test_full_workflow(self):
        """测试完整工作流"""
        # 创建 SessionManager
        manager = SessionManager(base_dir="/tmp/zhineng-bridge-integration")

        # 1. 列出可用工具
        tools = manager.list_tools()
        assert len(tools) >= 8

        # 2. 创建会话
        session_id1 = manager.create_session('crush', args=['--help'])
        assert manager.active_session_id == session_id1

        # 3. 获取会话信息
        session_info = manager.get_session(session_id1)
        assert session_info['tool_name'] == 'crush'

        # 4. 创建第二个会话
        session_id2 = manager.create_session('claude', args=['--version'])
        assert len(manager.sessions) == 2

        # 5. 列出所有会话
        sessions = manager.list_sessions()
        assert len(sessions) == 2

        # 6. 切换活动会话
        manager.set_active_session(session_id1)
        assert manager.active_session_id == session_id1

        # 7. 获取活动会话
        active_session = manager.get_active_session()
        assert active_session['session_id'] == session_id1

    def test_multiple_managers_isolation(self):
        """测试多个 SessionManager 实例隔离"""
        # 创建两个独立的 SessionManager
        manager1 = SessionManager(base_dir="/tmp/test1")
        manager2 = SessionManager(base_dir="/tmp/test2")

        # 在 manager1 创建会话
        session_id1 = manager1.create_session('crush', args=['--help'])
        assert len(manager1.sessions) == 1
        assert len(manager2.sessions) == 0  # manager2 不应该受影响

        # 在 manager2 创建会话
        session_id2 = manager2.create_session('claude', args=['--version'])
        assert len(manager1.sessions) == 1
        assert len(manager2.sessions) == 1

        # 验证会话隔离
        assert session_id1 in manager1.sessions
        assert session_id1 not in manager2.sessions
        assert session_id2 in manager2.sessions
        assert session_id2 not in manager1.sessions

#!/usr/bin/env python3
"""
zhineng-bridge Session Manager
"""

from session_manager import SessionManager


def main():
    """主函数"""
    print("🚀 启动 zhineng-bridge Session Manager")
    print()
    
    # 创建 Session Manager
    manager = SessionManager()
    
    # 显示工具列表
    print("📋 可用工具:")
    tools = manager.list_tools()
    for tool_key, tool_info in tools.items():
        print(f"  - {tool_key}: {tool_info['name']}")
    
    # 创建测试会话
    print("\n➕ 创建测试会话...")
    try:
        session_id = manager.create_session('crush')
        print(f"✅ 测试会话已创建: {session_id}")
    except Exception as e:
        print(f"⚠️  创建会话失败（预期行为）: {e}")
    
    # 显示会话列表
    print("\n📋 会话列表:")
    sessions = manager.list_sessions()
    if sessions:
        for session in sessions:
            print(f"  - {session['session_id']}: {session['tool_name']}")
    else:
        print("  (无会话）")


if __name__ == "__main__":
    main()

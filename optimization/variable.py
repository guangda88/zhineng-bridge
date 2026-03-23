"""
zhineng-bridge 优化变量定义
使用 LingMinOpt 优化 zhineng-bridge 的各种参数
"""

import sys
from pathlib import Path

# 添加 zhineng-bridge 路径
sys.path.insert(0, str(Path(__file__).parent.parent / "phase1" / "session_manager"))

from lingminopt import SearchSpace


def create_session_search_space():
    """
    创建会话管理搜索空间
    
    Returns:
        SearchSpace: 会话管理搜索空间
    """
    search_space = SearchSpace()
    
    # 会话管理参数
    search_space.add_discrete(
        "max_sessions",
        [5, 10, 20, 50, 100]
    )
    
    search_space.add_discrete(
        "session_timeout",
        [300, 600, 900, 1800, 3600]
    )
    
    search_space.add_continuous(
        "output_buffer_size",
        1000,
        100000
    )
    
    return search_space


def create_websocket_search_space():
    """
    创建 WebSocket 搜索空间
    
    Returns:
        SearchSpace: WebSocket 搜索空间
    """
    search_space = SearchSpace()
    
    # WebSocket 参数
    search_space.add_discrete(
        "max_connections",
        [10, 20, 50, 100, 200]
    )
    
    search_space.add_discrete(
        "ping_interval",
        [5, 10, 30, 60]
    )
    
    search_space.add_discrete(
        "message_queue_size",
        [100, 500, 1000, 5000]
    )
    
    return search_space


def create_performance_search_space():
    """
    创建性能优化搜索空间
    
    Returns:
        SearchSpace: 性能优化搜索空间
    """
    search_space = SearchSpace()
    
    # 性能参数
    search_space.add_continuous(
        "output_update_interval",
        10,
        1000
    )
    
    search_space.add_discrete(
        "compression_enabled",
        [True, False]
    )
    
    search_space.add_discrete(
        "batch_size",
        [10, 50, 100, 500, 1000]
    )
    
    return search_space


if __name__ == "__main__":
    # 测试搜索空间创建
    print("创建会话管理搜索空间...")
    session_space = create_session_search_space()
    print(f"会话管理搜索空间: {len(session_space.parameters)} 个变量")
    
    print("\n创建 WebSocket 搜索空间...")
    websocket_space = create_websocket_search_space()
    print(f"WebSocket 搜索空间: {len(websocket_space.parameters)} 个变量")
    
    print("\n创建性能优化搜索空间...")
    performance_space = create_performance_search_space()
    print(f"性能优化搜索空间: {len(performance_space.parameters)} 个变量")
    
    print("\n✅ 所有搜索空间创建成功！")

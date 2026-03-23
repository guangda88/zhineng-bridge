import sys
from pathlib import Path

# 添加 LingMinOpt 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "LingMinOpt"))

from lingminopt.core.searcher import SearchSpace


def create_websocket_search_space():
    """创建 WebSocket 搜索空间"""
    search_space = SearchSpace()
    search_space.add_discrete("max_connections", [10, 20, 50, 100, 200])
    search_space.add_discrete("ping_interval", [5, 10, 30, 60])
    search_space.add_discrete("message_queue_size", [100, 500, 1000, 5000])
    return search_space


def create_performance_search_space():
    """创建性能搜索空间"""
    search_space = SearchSpace()
    search_space.add_continuous("output_update_interval", 10, 1000)
    search_space.add_discrete("compression_enabled", [True, False])
    search_space.add_discrete("batch_size", [10, 50, 100, 500, 1000])
    return search_space


if __name__ == "__main__":
    # 测试搜索空间创建
    print("创建 WebSocket 搜索空间...")
    ws_space = create_websocket_search_space()
    print(f"WebSocket 搜索空间: {len(ws_space.parameters)} 个变量")
    
    print("\n创建性能搜索空间...")
    perf_space = create_performance_search_space()
    print(f"性能搜索空间: {len(perf_space.parameters)} 个变量")
    
    print("\n✅ 所有搜索空间创建成功！")

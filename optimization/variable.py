import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "LingMinOpt"))

from lingminopt.core.searcher import SearchSpace

def create_websocket_search_space():
    search_space = SearchSpace()
    search_space.add_discrete("max_connections", [10, 20, 50, 100, 200])
    search_space.add_discrete("ping_interval", [5, 10, 30, 60])
    search_space.add_discrete("message_queue_size", [100, 500, 1000, 5000])
    return search_space

def create_performance_search_space():
    search_space = SearchSpace()
    search_space.add_continuous("output_update_interval", 10, 1000)
    search_space.add_discrete("compression_enabled", [True, False])
    search_space.add_discrete("batch_size", [10, 50, 100, 500, 1000])
    return search_space

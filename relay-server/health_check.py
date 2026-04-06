#!/usr/bin/env python3
"""健康检查服务器入口（兼容旧调用方式）

新代码请使用: python3 -m health
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
session_manager_path = Path(__file__).parent.parent / "phase1" / "session_manager"
sys.path.insert(0, str(session_manager_path))

from health.__main__ import main

if __name__ == "__main__":
    main()

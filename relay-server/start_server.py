#!/usr/bin/env python3
"""
zhineng-bridge 中继服务器
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from server import CrushRelayServer


async def main():
    """主函数"""
    print("🚀 启动 zhineng-bridge 中继服务器")
    print()
    
    # 创建服务器
    server = CrushRelayServer(host="0.0.0.0", port=8765)
    
    # 启动服务器
    await server.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  服务器已停止")

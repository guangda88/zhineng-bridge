#!/usr/bin/env python3
"""
zhineng-bridge 中继服务器
"""

import asyncio
import json
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from server import AIRelayServer


async def _health_server(host: str, port: int):
    from aiohttp import web

    async def health(request):
        return web.json_response({"status": "ok"})

    app = web.Application()
    app.router.add_get("/health", health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    print(f"  健康检查: http://{host}:{port}/health")


async def main():
    """主函数"""
    print("🚀 启动 zhineng-bridge 中继服务器")
    print()

    server = AIRelayServer(host="0.0.0.0", port=8765)

    try:
        await _health_server("0.0.0.0", 8080)
    except Exception:
        print("  (健康检查服务未启动)")

    await server.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  服务器已停止")

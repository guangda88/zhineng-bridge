#!/usr/bin/env python3
"""
测试公网访问 100.66.1.8
"""

import asyncio
import json
import socket
import sys
from datetime import datetime

import websockets

# 公网配置
PUBLIC_IP = "100.66.1.8"
HTTP_PORT = 8080
WS_PORT = 8765


async def test_websocket():
    """测试WebSocket连接"""
    print("\n📡 测试WebSocket连接: ws://100.66.1.8:8765")

    try:
        async with websockets.connect("ws://100.66.1.8:8765") as ws:
            print("✅ WebSocket连接成功")

            # 发送ping
            await ws.send(json.dumps({"type": "ping"}))
            print("📤 已发送ping")

            # 等待pong
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5)
                data = json.loads(response)
                if data.get("type") == "pong":
                    print("📥 收到pong响应")
                    print("✅ WebSocket通信正常")
                    return True
            except asyncio.TimeoutError:
                print("⚠️  未收到pong响应")
                return False

    except Exception as e:
        print(f"❌ WebSocket连接失败: {e}")
        return False


def test_ports():
    """测试端口连通性"""
    print("\n🔍 测试端口连通性:")

    ports = [
        (PUBLIC_IP, HTTP_PORT, "HTTP服务"),
        (PUBLIC_IP, WS_PORT, "WebSocket"),
    ]

    results = []
    for host, port, name in ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((host, port))
            sock.close()

            if result == 0:
                print(f"✅ {name} ({port}): 开放")
                results.append(True)
            else:
                print(f"❌ {name} ({port}): 关闭")
                results.append(False)
        except Exception as e:
            print(f"❌ {name} ({port}): 错误 - {e}")
            results.append(False)

    return all(results)


async def main():
    print("=" * 60)
    print("  智桥公网访问测试")
    print("=" * 60)
    print(f"公网IP: {PUBLIC_IP}")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 测试端口
    ports_ok = test_ports()

    # 测试WebSocket
    ws_ok = await test_websocket()

    # 汇总
    print("\n" + "=" * 60)
    print("  测试结果")
    print("=" * 60)
    print(f"端口测试: {'✅ 通过' if ports_ok else '❌ 失败'}")
    print(f"WebSocket测试: {'✅ 通过' if ws_ok else '❌ 失败'}")

    if ports_ok and ws_ok:
        print("\n✅ 所有测试通过！公网访问正常")
        print("\n访问地址: http://100.66.1.8:8080/web/ui/index.html")
        return True
    else:
        print("\n❌ 部分测试失败，请检查服务状态")
        return False


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n测试被中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n测试发生错误: {e}")
        sys.exit(1)

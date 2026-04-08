#!/usr/bin/env python3
"""
会话创建问题诊断脚本
"""

import asyncio
import websockets
import json
import sys

async def test_websocket():
    """测试 WebSocket 连接和会话创建"""
    print("=" * 60)
    print("WebSocket 连接和会话创建测试")
    print("=" * 60)

    try:
        # 连接到 WebSocket
        url = "ws://10.113.22.99:8765"
        print(f"\n1. 连接到 {url}...")
        async with websockets.connect(url, ping_interval=5) as ws:
            print("   ✅ WebSocket 连接成功")

            # 等待一下
            await asyncio.sleep(0.5)

            # 测试 ping
            print("\n2. 发送 ping...")
            await ws.send(json.dumps({"type": "ping"}))
            response = await asyncio.wait_for(ws.recv(), timeout=2)
            print(f"   ✅ 收到响应: {response[:100]}...")

            # 测试 list_sessions
            print("\n3. 列出所有会话...")
            await ws.send(json.dumps({"type": "list_sessions"}))
            response = await asyncio.wait_for(ws.recv(), timeout=2)
            data = json.loads(response)
            print(f"   ✅ 当前会话数: {data.get('count', 0)}")

            # 测试会话创建
            print("\n4. 创建新会话...")
            message = {
                "type": "start_session",
                "tool_name": "crush",
                "args": ["--help"]
            }
            await ws.send(json.dumps(message))
            print(f"   📤 发送: {json.dumps(message)}")

            # 等待响应
            response = await asyncio.wait_for(ws.recv(), timeout=3)
            data = json.loads(response)
            print(f"   📥 收到: {json.dumps(data)}")

            if data.get('type') == 'session_started':
                session_id = data.get('session_id')
                print(f"   ✅ 会话创建成功: {session_id}")

                # 等待输出
                print("\n5. 等待会话输出...")
                try:
                    output = await asyncio.wait_for(ws.recv(), timeout=5)
                    output_data = json.loads(output)
                    if output_data.get('type') == 'output':
                        print(f"   ✅ 收到输出: {output_data.get('output', '')[:100]}...")
                except asyncio.TimeoutError:
                    print("   ⚠️ 等待输出超时（会话可能还在运行）")

                # 测试会话列表
                print("\n6. 再次列出会话...")
                await ws.send(json.dumps({"type": "list_sessions"}))
                response = await asyncio.wait_for(ws.recv(), timeout=2)
                data = json.loads(response)
                print(f"   ✅ 当前会话数: {data.get('count', 0)}")

            print("\n" + "=" * 60)
            print("✅ 所有测试通过！")
            print("=" * 60)
            return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        print("\n" + "=" * 60)
        print("❌ 测试失败")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return False

def check_frontend_files():
    """检查前端文件"""
    print("\n" + "=" * 60)
    print("前端文件检查")
    print("=" * 60)

    import os

    files_to_check = [
        "web/ui/index.html",
        "web/ui/js/settings.js",
        "web/ui/js/tools.js",
        "web/ui/js/sessions.js",
        "web/ui/js/client.js",
        "web/ui/js/improvements.js",
        "web/ui/js/app.js"
    ]

    base_path = "/home/ai/zhineng-bridge"

    for file_path in files_to_check:
        full_path = os.path.join(base_path, file_path)
        if os.path.exists(full_path):
            size = os.path.getsize(full_path)
            print(f"   ✅ {file_path} ({size} 字节)")
        else:
            print(f"   ❌ {file_path} (文件不存在)")

    # 检查关键函数
    print("\n检查关键函数...")

    sessions_file = os.path.join(base_path, "web/ui/js/sessions.js")
    with open(sessions_file, 'r') as f:
        content = f.read()
        if 'function newSession' in content:
            print("   ✅ newSession 函数存在")
        else:
            print("   ❌ newSession 函数不存在")

        if 'pendingSessionStart' in content:
            print("   ✅ pendingSessionStart 设置存在")
        else:
            print("   ❌ pendingSessionStart 设置不存在")

    client_file = os.path.join(base_path, "web/ui/js/client.js")
    with open(client_file, 'r') as f:
        content = f.read()
        if 'function handleMessage' in content:
            print("   ✅ handleMessage 函数存在")
        else:
            print("   ❌ handleMessage 函数不存在")

        if 'window.handleMessage' in content:
            print("   ✅ handleMessage 已导出到 window")
        else:
            print("   ❌ handleMessage 未导出到 window")

    app_file = os.path.join(base_path, "web/ui/js/app.js")
    with open(app_file, 'r') as f:
        content = f.read()
        if 'function connectWebSocket' in content:
            print("   ⚠️ app.js 中存在 connectWebSocket（应该被删除）")
        else:
            print("   ✅ app.js 中不存在 connectWebSocket")

        if 'function handleMessage' in content:
            print("   ⚠️ app.js 中存在 handleMessage（应该被删除）")
        else:
            print("   ✅ app.js 中不存在 handleMessage")

    print("\n" + "=" * 60)

def main():
    """主函数"""
    print("\n🔍 会话创建问题诊断工具\n")

    # 检查前端文件
    check_frontend_files()

    # 测试 WebSocket
    print("\n")
    success = asyncio.run(test_websocket())

    # 输出访问信息
    if success:
        print("\n📱 访问地址:")
        print("   主界面: http://10.113.22.99:8080/web/ui/index.html")
        print("   诊断页面: http://10.113.22.99:8080/web/ui/diagnose.html")
        print("   简单测试: http://10.113.22.99:8080/web/ui/simple-test-v2.html")
        print("   测试页面: http://10.113.22.99:8080/web/ui/test-session-creation.html")

    print("\n📋 浏览器开发者工具控制台:")
    print("   按 F12 打开开发者工具")
    print("   查看 Console 标签页")
    print("   查看是否有 JavaScript 错误")

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

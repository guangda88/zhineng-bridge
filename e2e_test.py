#!/usr/bin/env python3
"""
zhineng-bridge 端到端测试
"""

import asyncio
import websockets
import json
import time


async def test_websocket_connection():
    """测试 WebSocket 连接"""
    print("📡 测试 WebSocket 连接...")
    
    uri = "ws://localhost:8765"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket 连接成功")
            
            # 测试消息发送
            print("\n📤 发送测试消息...")
            test_message = {
                "type": "list_sessions",
                "data": {}
            }
            await websocket.send(json.dumps(test_message))
            print("✅ 测试消息已发送")
            
            # 接收响应
            print("\n📥 接收响应...")
            response = await websocket.recv()
            print(f"✅ 收到响应: {response[:100]}...")
            
            return True
    except Exception as e:
        print(f"❌ WebSocket 连接失败: {e}")
        return False


async def test_session_creation():
    """测试会话创建"""
    print("\n➕ 测试会话创建...")
    
    uri = "ws://localhost:8765"
    
    try:
        async with websockets.connect(uri) as websocket:
            # 发送创建会话请求
            create_message = {
                "type": "start_session",
                "tool_name": "crush",
                "args": []
            }
            await websocket.send(json.dumps(create_message))
            print("✅ 创建会话请求已发送")
            
            # 接收响应
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"✅ 收到响应: {response_data}")
            
            if "session_id" in response_data or "session_id" in str(response_data):
                print("✅ 会话创建成功")
                return True
            else:
                print("❌ 会话创建失败")
                return False
    except Exception as e:
        print(f"❌ 会话创建失败: {e}")
        return False


async def run_e2e_tests():
    """运行端到端测试"""
    print("=" * 70)
    print("zhineng-bridge 端到端测试")
    print("=" * 70)
    print()
    
    results = {}
    
    # 测试 1: WebSocket 连接
    print("测试 1: WebSocket 连接")
    print("-" * 70)
    results['websocket'] = await test_websocket_connection()
    print()
    
    # 测试 2: 会话创建
    print("测试 2: 会话创建")
    print("-" * 70)
    results['session_creation'] = await test_session_creation()
    print()
    
    # 测试结果
    print("=" * 70)
    print("测试结果")
    print("=" * 70)
    print()
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    print()
    print(f"总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有端到端测试通过！")
        return True
    else:
        print("\n❌ 部分端到端测试失败")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(run_e2e_tests())
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 端到端测试异常: {e}")
        exit(1)

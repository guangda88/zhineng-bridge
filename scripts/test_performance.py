#!/usr/bin/env python3
"""
智桥 PWA 性能测试脚本

测试内容:
- WebSocket 连接性能
- 文件 API 性能
- 推送 API 性能
- 整体响应时间
"""

import requests
import websockets
import asyncio
import json
import time

class PerformanceTester:
    def __init__(self, base_url: str = "http://localhost:8080", ws_url: str = "ws://localhost:8765"):
        self.base_url = base_url
        self.ws_url = ws_url
        self.results = []

    def print_header(self, title: str):
        """打印测试标题"""
        print(f"\n{'=' * 60}")
        print(f"{title}")
        print('=' * 60)

    def measure(self, name: str, target_ms: float, actual_ms: float, details: str = ""):
        """测量并记录结果"""
        passed = actual_ms <= target_ms
        status = "✅" if passed else "⚠️"
        self.results.append({
            'name': name,
            'target_ms': target_ms,
            'actual_ms': actual_ms,
            'passed': passed
        })
        print(f"{status} {name}: {actual_ms:.2f}ms (目标: <{target_ms}ms)")
        if details:
            print(f"   {details}")

    def test_websocket_connection(self):
        """测试 WebSocket 连接性能"""
        self.print_header("WebSocket 连接性能测试")

        async def connect_and_measure():
            try:
                start = time.time()
                async with websockets.connect(self.ws_url) as ws:
                    connect_time = time.time() - start

                    # 发送 ping
                    start = time.time()
                    await ws.send(json.dumps({"type": "ping"}))
                    await ws.recv()
                    ping_time = time.time() - start

                    return connect_time, ping_time
            except Exception as e:
                print(f"❌ WebSocket 连接失败: {e}")
                return None, None

        # 多次测试取平均值
        connect_times = []
        ping_times = []
        for i in range(5):
            result = asyncio.run(connect_and_measure())
            if result[0] is not None:
                connect_times.append(result[0])
                ping_times.append(result[1])
            time.sleep(0.5)

        if connect_times:
            avg_connect = (sum(connect_times) / len(connect_times)) * 1000
            avg_ping = (sum(ping_times) / len(ping_times)) * 1000

            self.measure("WebSocket 连接", 50.0, avg_connect, "5次测试平均")
            self.measure("WebSocket Ping-Pong", 100.0, avg_ping, "5次测试平均")

    def test_file_api(self):
        """测试文件 API 性能"""
        self.print_header("文件 API 性能测试")

        # 文件读取测试
        start = time.time()
        r = requests.get(f"{self.base_url}/api/files/read?path=/home/ai/zhineng-bridge/relay-server/server.py", timeout=10)
        read_time = (time.time() - start) * 1000
        self.measure("文件读取", 100.0, read_time, f"大小: {len(r.text)} 字节")

        # 文件搜索测试
        start = time.time()
        r = requests.get(f"{self.base_url}/api/files/search?query=server&limit=10", timeout=10)
        search_time = (time.time() - start) * 1000
        result = r.json()
        self.measure("文件搜索", 200.0, search_time, f"找到: {result.get('count', 0)} 个文件")

        # 文件列表测试
        start = time.time()
        r = requests.get(f"{self.base_url}/api/files/list?path=/home/ai/zhineng-bridge/relay-server&limit=20", timeout=10)
        list_time = (time.time() - start) * 1000
        result = r.json()
        self.measure("文件列表", 200.0, list_time, f"列出: {len(result.get('items', []))} 个项目")

        # 文件统计测试
        start = time.time()
        r = requests.get(f"{self.base_url}/api/files/stats?path=/home/ai/zhineng-bridge/relay-server/server.py", timeout=10)
        stats_time = (time.time() - start) * 1000
        self.measure("文件统计", 50.0, stats_time)

    def test_push_api(self):
        """测试推送 API 性能"""
        self.print_header("推送 API 性能测试")

        # 订阅测试
        start = time.time()
        r = requests.post(f"{self.base_url}/api/notifications/subscribe",
            json={
                'subscription': {
                    'endpoint': 'https://fcm.googleapis.com/test',
                    'keys': {'p256dh': 'test', 'auth': 'test'}
                }
            },
            timeout=5
        )
        subscribe_time = (time.time() - start) * 1000
        self.measure("推送订阅", 200.0, subscribe_time, f"状态: {r.status_code}")

        # 取消订阅测试
        start = time.time()
        r = requests.post(f"{self.base_url}/api/notifications/unsubscribe",
            json={'subscription_id': 'test'},
            timeout=5
        )
        unsubscribe_time = (time.time() - start) * 1000
        self.measure("推送取消订阅", 200.0, unsubscribe_time, f"状态: {r.status_code}")

    def test_health_check(self):
        """测试健康检查性能"""
        self.print_header("健康检查性能测试")

        start = time.time()
        r = requests.get(f"{self.base_url}/health", timeout=5)
        health_time = (time.time() - start) * 1000
        self.measure("健康检查", 50.0, health_time, f"状态: {r.json().get('status', 'unknown')}")

    def print_summary(self):
        """打印测试总结"""
        self.print_header("性能测试总结")

        total = len(self.results)
        passed = sum(1 for r in self.results if r['passed'])
        failed = total - passed
        pass_rate = (passed / total * 100) if total > 0 else 0

        print(f"总测试数: {total}")
        print(f"通过: {passed}")
        print(f"失败: {failed}")
        print(f"通过率: {pass_rate:.1f}%")

        if failed > 0:
            print(f"\n⚠️  {failed} 个测试未达到目标:")
            for r in self.results:
                if not r['passed']:
                    print(f"   - {r['name']}: {r['actual_ms']:.2f}ms (目标: <{r['target_ms']}ms)")
        else:
            print("\n🎉 所有性能测试均达到目标！")

    def run_all_tests(self):
        """运行所有性能测试"""
        print("\n" + "🚀" * 30)
        print("   智桥 PWA 性能测试")
        print("🚀" * 30)

        # 检查服务器状态
        try:
            r = requests.get(f"{self.base_url}/health", timeout=5)
            if r.status_code != 200:
                print("❌ 服务器未就绪，请先启动服务")
                return
        except:
            print("❌ 无法连接到服务器，请检查服务器是否运行")
            return

        # 运行测试
        self.test_health_check()
        self.test_websocket_connection()
        self.test_file_api()
        self.test_push_api()

        # 打印总结
        self.print_summary()

if __name__ == "__main__":
    tester = PerformanceTester(
        base_url="http://localhost:8080",
        ws_url="ws://localhost:8765"
    )
    tester.run_all_tests()

#!/usr/bin/env python3
"""
智桥 Web UI 快速测试工具

在命令行中测试 Web UI 的各种功能
"""

import asyncio
import json
from datetime import datetime

import requests
import websockets


class WebUITester:
    def __init__(
        self, base_url: str = "http://10.113.22.99:8080", ws_url: str = "ws://10.113.22.99:8765"
    ):
        self.base_url = base_url
        self.ws_url = ws_url
        self.results = []

    def print_header(self, title: str):
        """打印测试标题"""
        print(f"\n{'='*60}")
        print(f"{title}")
        print("=" * 60)

    def test_page_access(self):
        """测试页面访问"""
        self.print_header("1. 页面访问测试")

        test_urls = [
            (f"{self.base_url}/web/ui/index.html", "主页"),
            (f"{self.base_url}/web/ui/manifest.json", "PWA Manifest"),
            (f"{self.base_url}/health", "健康检查"),
            (f"{self.base_url}/docs", "API 文档"),
        ]

        for url, name in test_urls:
            try:
                r = requests.get(url, timeout=5)
                if r.status_code == 200:
                    print(f"✅ {name}: HTTP {r.status_code} ({len(r.text)} 字节)")
                    self.results.append(True)
                else:
                    print(f"❌ {name}: HTTP {r.status_code}")
                    self.results.append(False)
            except Exception as e:
                print(f"❌ {name}: {str(e)}")
                self.results.append(False)

    def test_static_resources(self):
        """测试静态资源"""
        self.print_header("2. 静态资源测试")

        resources = [
            "/web/ui/css/base.css",
            "/web/ui/css/components.css",
            "/web/ui/js/client.js",
            "/web/ui/js/app.js",
            "/web/ui/sw.js",
        ]

        for resource in resources:
            url = f"{self.base_url}{resource}"
            try:
                r = requests.get(url, timeout=5)
                if r.status_code == 200:
                    print(f"✅ {resource}: {len(r.text)} 字节")
                    self.results.append(True)
                else:
                    print(f"❌ {resource}: HTTP {r.status_code}")
                    self.results.append(False)
            except Exception as e:
                print(f"❌ {resource}: {str(e)}")
                self.results.append(False)

    def test_pwa_icons(self):
        """测试 PWA 图标"""
        self.print_header("3. PWA 图标测试")

        icons = [
            "/web/ui/icons/icon-192x192.png",
            "/web/ui/icons/icon-512x512.png",
        ]

        for icon in icons:
            url = f"{self.base_url}{icon}"
            try:
                r = requests.get(url, timeout=5)
                if r.status_code == 200:
                    size_kb = len(r.content) / 1024
                    print(f"✅ {icon}: {size_kb:.2f} KB")
                    self.results.append(True)
                else:
                    print(f"❌ {icon}: HTTP {r.status_code}")
                    self.results.append(False)
            except Exception as e:
                print(f"❌ {icon}: {str(e)}")
                self.results.append(False)

    async def test_websocket(self):
        """测试 WebSocket"""
        self.print_header("4. WebSocket 测试")

        try:
            async with websockets.connect(self.ws_url, ping_interval=5) as ws:
                print(f"✅ 连接到 {self.ws_url}")
                self.results.append(True)

                # 测试 ping-pong
                await ws.send(json.dumps({"type": "ping"}))
                response = await ws.recv()
                data = json.loads(response)

                if data.get("type") == "pong":
                    print("✅ Ping-Pong 测试成功")
                    print(f"   响应: {response}")
                    self.results.append(True)
                else:
                    print(f"❌ Ping-Pong 测试失败: {response}")
                    self.results.append(False)

                # 测试会话列表
                await ws.send(json.dumps({"type": "list_sessions", "data": {}}))
                response = await ws.recv()
                data = json.loads(response)

                print("✅ 会话列表请求发送")
                print(f"   响应类型: {data.get('type')}")
                self.results.append(True)

                if data.get("type") == "sessions_list":
                    sessions = data.get("sessions", [])
                    print(f"   当前会话数: {len(sessions)}")

                if data.get("type") == "error":
                    print(f"   ⚠️  错误消息: {data.get('message')}")

        except Exception as e:
            print(f"❌ WebSocket 测试失败: {str(e)}")
            self.results.append(False)

    def test_file_api(self):
        """测试文件 API"""
        self.print_header("5. 文件 API 测试")

        # 测试文件列表
        try:
            r = requests.get(
                f"{self.base_url}/api/files/list",
                params={"path": "/home/ai/zhineng-bridge/relay-server", "limit": 5},
                timeout=10,
            )
            if r.status_code == 200:
                data = r.json()
                count = len(data.get("items", []))
                print(f"✅ 文件列表 API: 找到 {count} 个项目")
                self.results.append(True)
            else:
                print(f"❌ 文件列表 API: HTTP {r.status_code}")
                self.results.append(False)
        except Exception as e:
            print(f"❌ 文件列表 API: {str(e)}")
            self.results.append(False)

        # 测试文件搜索
        try:
            r = requests.get(
                f"{self.base_url}/api/files/search",
                params={"query": "server", "limit": 5},
                timeout=10,
            )
            if r.status_code == 200:
                data = r.json()
                count = data.get("count", 0)
                print(f"✅ 文件搜索 API: 找到 {count} 个文件")
                self.results.append(True)
            else:
                print(f"❌ 文件搜索 API: HTTP {r.status_code}")
                self.results.append(False)
        except Exception as e:
            print(f"❌ 文件搜索 API: {str(e)}")
            self.results.append(False)

    def print_summary(self):
        """打印测试总结"""
        self.print_header("测试总结")

        total = len(self.results)
        passed = sum(self.results)
        failed = total - passed
        pass_rate = (passed / total * 100) if total > 0 else 0

        print(f"总测试数: {total}")
        print(f"通过: {passed}")
        print(f"失败: {failed}")
        print(f"通过率: {pass_rate:.1f}%")

        if failed == 0:
            print("\n🎉 所有测试通过！Web UI 可以正常使用。")
        else:
            print(f"\n⚠️  {failed} 个测试失败，需要检查。")

        # 提供访问信息
        print("\n访问地址:")
        print(f"  Web UI: {self.base_url}/web/ui/index.html")
        print(f"  API 文档: {self.base_url}/docs")
        print(f"  WebSocket: {self.ws_url}")

    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "🚀" * 30)
        print("   智桥 Web UI 快速测试")
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

        print(f"\n测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"测试地址: {self.base_url}")
        print(f"WebSocket: {self.ws_url}")

        # 运行测试
        self.test_page_access()
        self.test_static_resources()
        self.test_pwa_icons()
        asyncio.run(self.test_websocket())
        self.test_file_api()

        # 打印总结
        self.print_summary()


if __name__ == "__main__":
    tester = WebUITester(base_url="http://10.113.22.99:8080", ws_url="ws://10.113.22.99:8765")
    tester.run_all_tests()

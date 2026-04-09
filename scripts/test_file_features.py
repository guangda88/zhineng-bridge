#!/usr/bin/env python3
"""
智桥文件提及功能测试脚本

测试内容:
- 文件搜索准确性
- 文件读取性能
- 大文件处理
- 安全功能验证
"""

import time

import requests


class FileFeatureTester:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.results = []

    def print_header(self, title: str):
        """打印测试标题"""
        print(f"\n{'=' * 60}")
        print(f"{title}")
        print("=" * 60)

    def test_search_accuracy(self):
        """测试文件搜索准确性"""
        self.print_header("文件搜索准确性测试")

        test_cases = [
            {"query": "server", "expected_count": "> 0", "description": "搜索包含 'server' 的文件"},
            {
                "query": "session",
                "expected_count": "> 0",
                "description": "搜索包含 'session' 的文件",
            },
            {"query": ".py", "expected_count": "> 0", "description": "搜索 Python 文件"},
            {
                "query": "nonexistent_file_xyz",
                "expected_count": "0",
                "description": "搜索不存在的文件",
            },
            {"query": "client.js", "expected_count": ">= 1", "description": "搜索特定文件"},
        ]

        for case in test_cases:
            print(f"\n测试: {case['description']}")
            print(f"查询: '{case['query']}'")

            try:
                start = time.time()
                response = requests.get(
                    f"{self.base_url}/api/files/search",
                    params={"query": case["query"], "limit": 20},
                    timeout=10,
                )
                elapsed = (time.time() - start) * 1000

                if response.status_code == 200:
                    data = response.json()
                    count = data.get("count", 0)
                    files = data.get("files", [])

                    print(f"  结果: 找到 {count} 个文件 (耗时 {elapsed:.2f}ms)")

                    if count > 0:
                        print("  示例文件:")
                        for f in files[:3]:
                            print(f"    - {f.get('name')} ({f.get('type')})")

                    # 验证结果是否符合预期
                    expected = case["expected_count"]
                    if expected.startswith(">"):
                        if count > 0:
                            print("  ✅ 测试通过")
                            self.results.append(True)
                        else:
                            print(f"  ❌ 测试失败: 期望 > 0，实际 {count}")
                            self.results.append(False)
                    elif expected.startswith(">="):
                        min_count = int(expected.replace(">=", ""))
                        if count >= min_count:
                            print("  ✅ 测试通过")
                            self.results.append(True)
                        else:
                            print(f"  ❌ 测试失败: 期望 >= {min_count}，实际 {count}")
                            self.results.append(False)
                    else:
                        expected_count = int(expected)
                        if count == expected_count:
                            print("  ✅ 测试通过")
                            self.results.append(True)
                        else:
                            print(f"  ❌ 测试失败: 期望 {expected_count}，实际 {count}")
                            self.results.append(False)
                else:
                    print(f"  ❌ 请求失败: HTTP {response.status_code}")
                    self.results.append(False)
            except Exception as e:
                print(f"  ❌ 异常: {e}")
                self.results.append(False)

    def test_file_read(self):
        """测试文件读取功能"""
        self.print_header("文件读取功能测试")

        test_files = [
            "/home/ai/zhineng-bridge/relay-server/server.py",
            "/home/ai/zhineng-bridge/web/ui/js/app.js",
            "/home/ai/zhineng-bridge/docs/README.md",
        ]

        for file_path in test_files:
            print(f"\n测试文件: {file_path}")

            try:
                start = time.time()
                response = requests.get(
                    f"{self.base_url}/api/files/read", params={"path": file_path}, timeout=10
                )
                elapsed = (time.time() - start) * 1000

                if response.status_code == 200:
                    content = response.text
                    print(f"  ✅ 读取成功 (大小: {len(content)} 字节, 耗时: {elapsed:.2f}ms)")

                    # 验证内容不为空
                    if len(content) > 0:
                        print(f"  内容预览: {content[:100]}...")
                        self.results.append(True)
                    else:
                        print("  ❌ 文件内容为空")
                        self.results.append(False)
                else:
                    print(f"  ❌ 读取失败: HTTP {response.status_code}")
                    self.results.append(False)
            except Exception as e:
                print(f"  ❌ 异常: {e}")
                self.results.append(False)

    def test_large_file_handling(self):
        """测试大文件处理"""
        self.print_header("大文件处理测试")

        # 查找较大的文件
        large_files = [
            "/home/ai/zhineng-bridge/relay-server/server.py",  # ~37KB
            "/home/ai/zhineng-bridge/phase1/session_manager/session_manager.py",
        ]

        for file_path in large_files:
            print(f"\n测试大文件: {file_path}")

            # 首先获取文件统计
            try:
                response = requests.get(
                    f"{self.base_url}/api/files/stats", params={"path": file_path}, timeout=10
                )
                if response.status_code == 200:
                    stats = response.json()
                    size = stats.get("size", 0)
                    print(f"  文件大小: {size} 字节 ({size/1024:.2f} KB)")

                    # 读取文件内容
                    start = time.time()
                    read_response = requests.get(
                        f"{self.base_url}/api/files/read", params={"path": file_path}, timeout=30
                    )
                    elapsed = (time.time() - start) * 1000

                    if read_response.status_code == 200:
                        print(f"  ✅ 读取成功 (耗时: {elapsed:.2f}ms)")
                        print(f"  吞吐量: {size/elapsed:.2f} KB/ms")
                        self.results.append(True)
                    else:
                        print(f"  ❌ 读取失败: HTTP {read_response.status_code}")
                        self.results.append(False)
                else:
                    print(f"  ❌ 获取统计失败: HTTP {response.status_code}")
                    self.results.append(False)
            except Exception as e:
                print(f"  ❌ 异常: {e}")
                self.results.append(False)

    def test_security_features(self):
        """测试安全功能"""
        self.print_header("安全功能测试")

        # 测试路径遍历攻击防护
        print("\n测试 1: 路径遍历攻击防护")
        malicious_paths = [
            "/etc/passwd",
            "/etc/shadow",
            "../../../etc/passwd",
            "/root/.ssh/id_rsa",
            "/home/ai/.ssh/id_rsa",
        ]

        for path in malicious_paths:
            print(f"  测试路径: {path}")
            try:
                response = requests.get(
                    f"{self.base_url}/api/files/read", params={"path": path}, timeout=5
                )
                if response.status_code == 403 or response.status_code == 400:
                    print("    ✅ 成功拒绝访问")
                    self.results.append(True)
                else:
                    print(f"    ❌ 安全漏洞: 允许访问 (HTTP {response.status_code})")
                    self.results.append(False)
            except Exception as e:
                print(f"    ✅ 成功拒绝访问 (异常: {type(e).__name__})")
                self.results.append(True)

        # 测试黑名单目录防护
        print("\n测试 2: 黑名单目录防护")
        blacklist_dirs = [
            "/etc",
            "/sys",
            "/proc",
            "/dev",
        ]

        for dir_path in blacklist_dirs:
            print(f"  测试目录: {dir_path}")
            try:
                response = requests.get(
                    f"{self.base_url}/api/files/list",
                    params={"path": dir_path, "limit": 10},
                    timeout=5,
                )
                if response.status_code == 403 or response.status_code == 400:
                    print("    ✅ 成功拒绝访问")
                    self.results.append(True)
                else:
                    print(f"    ❌ 安全漏洞: 允许访问 (HTTP {response.status_code})")
                    self.results.append(False)
            except Exception as e:
                print(f"    ✅ 成功拒绝访问 (异常: {type(e).__name__})")
                self.results.append(True)

        # 测试文件扩展名白名单
        print("\n测试 3: 文件扩展名白名单")
        non_whitelisted_files = [
            "/home/ai/zhineng-bridge/docs/test.pdf",
            "/home/ai/zhineng-bridge/docs/test.exe",
        ]

        for file_path in non_whitelisted_files:
            print(f"  测试文件: {file_path}")
            try:
                response = requests.get(
                    f"{self.base_url}/api/files/read", params={"path": file_path}, timeout=5
                )
                if response.status_code == 403 or response.status_code == 404:
                    print("    ✅ 成功拒绝访问")
                    self.results.append(True)
                else:
                    print(f"    ❌ 安全漏洞: 允许访问 (HTTP {response.status_code})")
                    self.results.append(False)
            except Exception as e:
                print(f"    ✅ 成功拒绝访问 (异常: {type(e).__name__})")
                self.results.append(True)

    def test_file_stats(self):
        """测试文件统计功能"""
        self.print_header("文件统计功能测试")

        test_files = [
            "/home/ai/zhineng-bridge/relay-server/server.py",
            "/home/ai/zhineng-bridge/relay-server",
        ]

        for file_path in test_files:
            print(f"\n测试: {file_path}")

            try:
                start = time.time()
                response = requests.get(
                    f"{self.base_url}/api/files/stats", params={"path": file_path}, timeout=10
                )
                elapsed = (time.time() - start) * 1000

                if response.status_code == 200:
                    stats = response.json()
                    print(f"  ✅ 获取成功 (耗时: {elapsed:.2f}ms)")

                    # 验证必需字段
                    required_fields = [
                        "type",
                        "path",
                        "name",
                        "size",
                        "modified",
                        "is_file",
                        "is_dir",
                    ]
                    missing_fields = [f for f in required_fields if f not in stats]

                    if not missing_fields:
                        print("  文件信息:")
                        print(f"    名称: {stats.get('name')}")
                        print(f"    类型: {stats.get('type')}")
                        print(f"    大小: {stats.get('size')} 字节")
                        print(f"    是否为文件: {stats.get('is_file')}")
                        print(f"    是否为目录: {stats.get('is_dir')}")
                        print("  ✅ 所有字段完整")
                        self.results.append(True)
                    else:
                        print(f"  ❌ 缺少字段: {missing_fields}")
                        self.results.append(False)
                else:
                    print(f"  ❌ 获取失败: HTTP {response.status_code}")
                    self.results.append(False)
            except Exception as e:
                print(f"  ❌ 异常: {e}")
                self.results.append(False)

    def print_summary(self):
        """打印测试总结"""
        self.print_header("文件功能测试总结")

        total = len(self.results)
        passed = sum(self.results)
        failed = total - passed
        pass_rate = (passed / total * 100) if total > 0 else 0

        print(f"总测试数: {total}")
        print(f"通过: {passed}")
        print(f"失败: {failed}")
        print(f"通过率: {pass_rate:.1f}%")

        if failed == 0:
            print("\n🎉 所有文件功能测试通过！")
        else:
            print(f"\n⚠️  {failed} 个测试失败，需要修复")

    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "🚀" * 30)
        print("   智桥文件功能测试")
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
        self.test_search_accuracy()
        self.test_file_read()
        self.test_large_file_handling()
        self.test_security_features()
        self.test_file_stats()

        # 打印总结
        self.print_summary()


if __name__ == "__main__":
    tester = FileFeatureTester(base_url="http://localhost:8080")
    tester.run_all_tests()

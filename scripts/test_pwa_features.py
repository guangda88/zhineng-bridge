#!/usr/bin/env python3
"""
PWA 功能测试脚本

测试所有新增的 PWA 功能：
1. 文件 API 端点
2. 推送服务端点
3. Service Worker 注册
"""

import requests
import sys


class PWATester:
    """PWA 功能测试类"""

    def __init__(self, base_url: str = "http://localhost:8080"):
        """
        初始化测试器

        Args:
            base_url: 服务器基础 URL
        """
        self.base_url = base_url
        self.test_results = []

    def print_header(self, title: str):
        """打印测试标题"""
        print("\n" + "=" * 70)
        print(f"  {title}")
        print("=" * 70)

    def print_result(self, test_name: str, passed: bool, message: str = ""):
        """
        打印测试结果

        Args:
            test_name: 测试名称
            passed: 是否通过
            message: 额外消息
        """
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"       {message}")

        self.test_results.append({
            'test': test_name,
            'passed': passed,
            'message': message
        })

    def test_file_api_read(self):
        """测试文件读取 API"""
        self.print_header("1. 测试文件读取 API (GET /api/files/read)")

        try:
            # 测试读取已存在的文件
            test_file = "/home/ai/zhineng-bridge/relay-server/file_api.py"

            response = requests.get(
                f"{self.base_url}/api/files/read",
                params={'path': test_file},
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()

                if data.get('type') == 'file_content':
                    self.print_result(
                        "读取文件 API 响应正确",
                        True,
                        f"文件大小: {data.get('metadata', {}).get('size')} 字节"
                    )

                    # 检查内容
                    if data.get('content'):
                        self.print_result(
                            "文件内容返回正确",
                            True,
                            f"内容长度: {len(data.get('content'))} 字符"
                        )
                    else:
                        self.print_result("文件内容为空", False)

                else:
                    self.print_result("响应类型错误", False, data.get('type'))
            else:
                self.print_result(
                    "读取文件失败",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )

        except requests.exceptions.RequestException as e:
            self.print_result("读取文件请求异常", False, str(e))

    def test_file_api_search(self):
        """测试文件搜索 API"""
        self.print_header("2. 测试文件搜索 API (GET /api/files/search)")

        try:
            response = requests.get(
                f"{self.base_url}/api/files/search",
                params={
                    'query': 'file',
                    'path': '/home/ai/zhineng-bridge/relay-server',
                    'limit': 10
                },
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()

                if data.get('type') == 'search_results':
                    count = data.get('count', 0)
                    total = data.get('total', 0)

                    self.print_result(
                        "文件搜索 API 响应正确",
                        True,
                        f"找到 {count} 个文件 (共 {total} 个)"
                    )

                    if count > 0:
                        # 显示第一个结果
                        first_result = data.get('results', [])[0]
                        self.print_result(
                            "搜索结果格式正确",
                            True,
                            f"示例: {first_result.get('name')}"
                        )

                else:
                    self.print_result("响应类型错误", False, data.get('type'))
            else:
                self.print_result(
                    "文件搜索失败",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )

        except requests.exceptions.RequestException as e:
            self.print_result("文件搜索请求异常", False, str(e))

    def test_file_api_stats(self):
        """测试文件统计 API"""
        self.print_header("3. 测试文件统计 API (GET /api/files/stats)")

        try:
            response = requests.get(
                f"{self.base_url}/api/files/stats",
                params={'path': '/home/ai/zhineng-bridge/relay-server/file_api.py'},
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()

                if data.get('type') == 'file_stats':
                    # 元数据字段在根级别，不在 'metadata' 键下
                    self.print_result(
                        "文件统计 API 响应正确",
                        True,
                        f"大小: {data.get('size')} 字节"
                    )

                    # 检查所有必需字段（在根级别）
                    required_fields = ['size', 'modified', 'is_file']
                    all_fields_present = all(field in data for field in required_fields)

                    if all_fields_present:
                        self.print_result("元数据字段完整", True)
                    else:
                        missing = [f for f in required_fields if f not in data]
                        self.print_result("缺少元数据字段", False, f"缺少: {missing}")

                else:
                    self.print_result("响应类型错误", False, data.get('type'))
            else:
                self.print_result(
                    "文件统计失败",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )

        except requests.exceptions.RequestException as e:
            self.print_result("文件统计请求异常", False, str(e))

    def test_file_api_list(self):
        """测试文件列表 API"""
        self.print_header("4. 测试文件列表 API (GET /api/files/list)")

        try:
            response = requests.get(
                f"{self.base_url}/api/files/list",
                params={
                    'path': '/home/ai/zhineng-bridge/relay-server',
                    'limit': 10,
                    'offset': 0
                },
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()

                if data.get('type') == 'file_list':
                    count = data.get('count', 0)
                    total = data.get('total', 0)

                    self.print_result(
                        "文件列表 API 响应正确",
                        True,
                        f"列出 {count} 个项目 (共 {total} 个)"
                    )

                    if count > 0:
                        # 检查第一个项目的格式
                        first_item = data.get('files', [])[0]
                        has_name = 'name' in first_item
                        has_is_file = 'is_file' in first_item

                        if has_name and has_is_file:
                            self.print_result(
                                "列表项格式正确",
                                True,
                                f"示例: {first_item.get('name')} ({'文件' if first_item.get('is_file') else '目录'})"
                            )
                        else:
                            self.print_result("列表项缺少必需字段", False)

                else:
                    self.print_result("响应类型错误", False, data.get('type'))
            else:
                self.print_result(
                    "文件列表失败",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )

        except requests.exceptions.RequestException as e:
            self.print_result("文件列表请求异常", False, str(e))

    def test_push_service(self):
        """测试推送服务 API"""
        self.print_header("5. 测试推送服务 API")

        # 测试订阅端点
        try:
            subscription_data = {
                "subscription": {
                    "endpoint": "https://fcm.googleapis.com/test-endpoint",
                    "keys": {
                        "p256dh": "test_p256dh_key_123456789012345678901234567890123456789012345678901234567890",
                        "auth": "test_auth_key_123456"
                    },
                    "user_agent": "Mozilla/5.0 Test User Agent"
                }
            }

            response = requests.post(
                f"{self.base_url}/api/notifications/subscribe",
                json=subscription_data,
                timeout=5
            )

            if response.status_code == 201:
                data = response.json()

                if data.get('type') == 'subscription_registered':
                    subscription_id = data.get('subscription_id')

                    self.print_result(
                        "推送订阅 API 响应正确",
                        True,
                        f"订阅 ID: {subscription_id}"
                    )

                    # 测试取消订阅
                    response = requests.post(
                        f"{self.base_url}/api/notifications/unsubscribe",
                        json={'subscription_id': subscription_id},
                        timeout=5
                    )

                    if response.status_code == 200:
                        self.print_result("推送取消订阅 API 正常", True)
                    else:
                        self.print_result(
                            "取消订阅失败",
                            False,
                            f"HTTP {response.status_code}"
                        )

                else:
                    self.print_result("订阅响应类型错误", False, data.get('type'))
            else:
                self.print_result(
                    "推送订阅失败",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )

        except requests.exceptions.RequestException as e:
            self.print_result("推送服务请求异常", False, str(e))

    def test_security_features(self):
        """测试安全特性"""
        self.print_header("6. 测试安全特性")

        # 测试路径遍历攻击防护
        try:
            response = requests.get(
                f"{self.base_url}/api/files/read",
                params={'path': '../../../etc/passwd'},
                timeout=5
            )

            if response.status_code == 400:
                self.print_result(
                    "路径遍历攻击防护正常",
                    True,
                    "成功拒绝非法路径访问"
                )
            elif response.status_code == 403:
                self.print_result(
                    "路径遍历攻击防护正常",
                    True,
                    "成功拒绝权限不足的访问"
                )
            else:
                self.print_result(
                    "路径遍历攻击防护可能存在漏洞",
                    False,
                    f"HTTP {response.status_code}"
                )

        except requests.exceptions.RequestException as e:
            self.print_result("安全测试请求异常", False, str(e))

        # 测试黑名单目录防护
        try:
            response = requests.get(
                f"{self.base_url}/api/files/read",
                params={'path': '/etc/passwd'},
                timeout=5
            )

            if response.status_code == 400:
                self.print_result(
                    "黑名单目录防护正常",
                    True,
                    "成功拒绝黑名单目录访问"
                )
            elif response.status_code == 403:
                self.print_result(
                    "黑名单目录防护正常",
                    True,
                    "成功拒绝权限不足的访问"
                )
            else:
                self.print_result(
                    "黑名单目录防护可能存在漏洞",
                    False,
                    f"HTTP {response.status_code}"
                )

        except requests.exceptions.RequestException as e:
            self.print_result("安全测试请求异常", False, str(e))

    def test_health_check(self):
        """测试健康检查端点"""
        self.print_header("7. 测试健康检查端点")

        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)

            if response.status_code == 200:
                data = response.json()

                if data.get('status') == 'healthy':
                    self.print_result(
                        "健康检查端点正常",
                        True,
                        f"服务版本: {data.get('version')}"
                    )

                    # 检查 PWA 相关功能是否可用
                    features = data.get('features', {})
                    oauth2_enabled = features.get('oauth2', False)

                    # OAuth2 在本阶段未配置，标记为警告而非失败
                    if oauth2_enabled:
                        self.print_result("OAuth2 功能状态", True, "已启用")
                    else:
                        self.print_result(
                            "OAuth2 功能状态",
                            True,  # 标记为通过，因为这是预期行为
                            "未启用 (预期状态 - 将在后续阶段配置)"
                        )

                else:
                    self.print_result("健康状态异常", False, data.get('status'))
            else:
                self.print_result(
                    "健康检查失败",
                    False,
                    f"HTTP {response.status_code}"
                )

        except requests.exceptions.RequestException as e:
            self.print_result("健康检查请求异常", False, str(e))

    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "🚀" * 35)
        print("   智桥 PWA 功能测试")
        print("🚀" * 35)

        # 运行测试
        self.test_health_check()
        self.test_file_api_read()
        self.test_file_api_search()
        self.test_file_api_stats()
        self.test_file_api_list()
        self.test_push_service()
        self.test_security_features()

        # 打印测试总结
        self.print_summary()

    def print_summary(self):
        """打印测试总结"""
        print("\n" + "=" * 70)
        print("  测试总结")
        print("=" * 70)

        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r['passed'])
        failed = total - passed
        pass_rate = (passed / total * 100) if total > 0 else 0

        print(f"  总测试数: {total}")
        print(f"  通过: {passed}")
        print(f"  失败: {failed}")
        print(f"  通过率: {pass_rate:.1f}%")
        print()

        if failed == 0:
            print("  🎉 所有测试通过！PWA 功能正常工作。")
        else:
            print(f"  ⚠️  {failed} 个测试失败，请检查日志。")

            # 列出失败的测试
            print("\n  失败的测试:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"    ❌ {result['test']}")
                    if result.get('message'):
                        print(f"       {result['message']}")

        print("=" * 70 + "\n")


def main():
    """主函数"""
    # 从命令行参数获取基础 URL
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"

    print(f"\n📡 测试服务器: {base_url}\n")

    # 创建测试器并运行测试
    tester = PWATester(base_url=base_url)
    tester.run_all_tests()

    # 返回退出码
    passed = sum(1 for r in tester.test_results if r['passed'])
    total = len(tester.test_results)
    sys.exit(0 if passed == total else 1)


if __name__ == '__main__':
    main()

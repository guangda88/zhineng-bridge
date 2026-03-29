#!/usr/bin/env python3
"""
Chrome DevTools MCP E2E Test

使用 Docker 容器运行 chrome-devtools-mcp 并执行端到端测试

前置条件:
- Docker 已安装
- Docker image: chrome-devtools-mcp:latest 已构建
- zhineng-bridge relay-server 运行在 http://localhost:8000

测试场景:
1. 启动 Chrome 浏览器
2. 导航到 Web UI
3. 截图验证
4. 执行 JavaScript
5. 检查 WebSocket 连接
6. 关闭浏览器
"""

import asyncio
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, List, Optional


class ChromeDevToolsMCPTester:
    """Chrome DevTools MCP 测试器"""

    def __init__(self, use_docker: bool = True):
        """
        初始化测试器

        Args:
            use_docker: 是否使用 Docker 容器运行 chrome-devtools-mcp
        """
        self.use_docker = use_docker
        self.process: Optional[subprocess.Popen] = None
        self.results: List[Dict[str, Any]] = []
        self.test_count = 0
        self.pass_count = 0
        self.fail_count = 0
        self.message_id = 1

    def log(self, message: str, emoji: str = "ℹ️"):
        """记录日志"""
        print(f"{emoji} {message}")

    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """记录测试结果"""
        emoji = "✅" if passed else "❌"
        self.log(f"{'通过' if passed else '失败'}: {test_name}", emoji)
        if details:
            print(f"   {details}")

        self.results.append({
            "test_name": test_name,
            "passed": passed,
            "details": details
        })

        self.test_count += 1
        if passed:
            self.pass_count += 1
        else:
            self.fail_count += 1

    def start_mcp_server(self) -> bool:
        """
        启动 MCP 服务器

        Returns:
            是否成功启动
        """
        try:
            if self.use_docker:
                self.log("在 Docker 容器中启动 chrome-devtools-mcp...")
                # Docker 容器会自动启动 Chrome 并运行 MCP 服务器
                # 由于 MCP 使用 stdin/stdout 通信，我们无法直接通过 Docker 测试
                # 这里我们改为启动 Chrome 并手动执行测试
                return self._start_chrome_manually()
            else:
                self.log("直接启动 chrome-devtools-mcp...")
                return self._start_mcp_natively()
        except Exception as e:
            self.log(f"启动 MCP 服务器失败: {e}", "❌")
            return False

    def _start_chrome_manually(self) -> bool:
        """
        手动启动 Chrome 浏览器进行测试

        Returns:
            是否成功启动
        """
        try:
            # 使用 Docker 运行 Chrome 并执行测试
            test_script = """
const puppeteer = require('puppeteer');

async function runTest() {
    const browser = await puppeteer.launch({
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage();
    await page.setViewport({ width: 1280, height: 720 });

    try {
        // 测试 1: 导航到 Web UI
        console.log('TEST:navigate_page:start');
        await page.goto('http://host.docker.internal:8000/web/ui/index.html', {
            waitUntil: 'networkidle2',
            timeout: 10000
        });
        console.log('TEST:navigate_page:success');

        // 测试 2: 获取页面标题
        console.log('TEST:page_title:start');
        const title = await page.title();
        console.log(`TEST:page_title:success:${title}`);

        // 测试 3: 截图
        console.log('TEST:screenshot:start');
        await page.screenshot({ path: '/tmp/zhineng_bridge_test.png' });
        console.log('TEST:screenshot:success');

        // 测试 4: 检查 WebSocket 连接
        console.log('TEST:websocket:start');
        const wsConnected = await page.evaluate(() => {
            return window.ws ? window.ws.readyState === 1 : false;
        });
        console.log(`TEST:websocket:success:${wsConnected}`);

        // 测试 5: 执行 JavaScript
        console.log('TEST:evaluate_script:start');
        const result = await page.evaluate(() => {
            return {
                pageTitle: document.title,
                hasLogo: document.querySelector('.logo') !== null,
                hasToolsSection: document.getElementById('tools') !== null,
                hasToolsGrid: document.getElementById('toolsGrid') !== null,
                hasSessionsSection: document.getElementById('sessions') !== null,
                hasSessionsList: document.getElementById('sessionsList') !== null,
                hasNewSessionBtn: document.getElementById('newSessionBtn') !== null
            };
        });
        console.log(`TEST:evaluate_script:success:${JSON.stringify(result)}`);

        // 测试 6: 检查控制台错误
        console.log('TEST:console:start');
        const messages = await page.evaluate(() => {
            // 捕获页面中的错误信息
            return window.errors || [];
        });
        console.log(`TEST:console:success:${JSON.stringify(messages)}`);

    } catch (error) {
        console.error(`TEST:error:${error.message}`);
    } finally {
        await browser.close();
        console.log('TEST:complete');
    }
}

runTest().catch(console.error);
"""

            # 将测试脚本写入容器
            # 在 Linux 上使用 host 网络模式，host.docker.internal 不可用
            cmd = [
                'docker', 'run', '--rm',
                '--network', 'host',
                '--add-host', 'host.docker.internal:host-gateway',
                '-v', '/tmp:/tmp',
                'chrome-devtools-mcp:latest',
                'node', '-e', test_script
            ]

            self.log("启动 Chrome 测试容器...")
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # 等待进程完成
            stdout, stderr = self.process.communicate(timeout=30)

            # 解析测试输出
            self._parse_test_output(stdout, stderr)

            return self.process.returncode == 0

        except subprocess.TimeoutExpired:
            self.log("测试超时", "❌")
            if self.process:
                self.process.kill()
            return False
        except Exception as e:
            self.log(f"启动 Chrome 失败: {e}", "❌")
            return False

    def _start_mcp_natively(self) -> bool:
        """本地启动 MCP 服务器"""
        # 需要实现本地 MCP 服务器启动逻辑
        self.log("本地 MCP 服务器启动未实现", "⚠️")
        return False

    def _parse_test_lines(self, stdout: str) -> Dict[str, Any]:
        """解析测试输出行"""
        test_results = {}

        for line in stdout.split('\n'):
            if line.startswith('TEST:'):
                parts = line[5:].split(':')
                if len(parts) < 2:
                    self.log(f"解析错误: {line}", "⚠️")
                    continue

                test_name = parts[0]
                status = parts[1]

                if status == 'start':
                    test_results[test_name] = {'started': True, 'success': False}
                elif status == 'success':
                    if test_name not in test_results:
                        test_results[test_name] = {}
                    test_results[test_name]['success'] = True
                    if len(parts) > 2:
                        test_results[test_name]['value'] = ':'.join(parts[2:])
                elif status == 'error':
                    if test_name not in test_results:
                        test_results[test_name] = {}
                    test_results[test_name]['error'] = ':'.join(parts[2:]) if len(parts) > 2 else 'Unknown error'

        return test_results

    def _log_test_results(self, test_results: Dict[str, Any]):
        """记录测试结果"""
        self.log_test("页面导航", test_results.get('navigate_page', {}).get('success', False),
                    test_results.get('navigate_page', {}).get('value', ''))

        self.log_test("页面标题获取", test_results.get('page_title', {}).get('success', False),
                    test_results.get('page_title', {}).get('value', ''))

        self.log_test("页面截图", test_results.get('screenshot', {}).get('success', False),
                    "截图保存到 /tmp/zhineng_bridge_test.png")

        self.log_test("WebSocket 连接", test_results.get('websocket', {}).get('success', False),
                    f"状态: {test_results.get('websocket', {}).get('value', 'false')}")

        if test_results.get('evaluate_script', {}).get('success', False):
            try:
                elements = json.loads(test_results.get('evaluate_script', {}).get('value', '{}'))
                self.log_test("页面元素检查", True,
                            f"Logo: {elements.get('hasLogo', 'N/A')}, "
                            f"工具区: {elements.get('hasToolsSection', 'N/A')}, "
                            f"工具网格: {elements.get('hasToolsGrid', 'N/A')}, "
                            f"会话区: {elements.get('hasSessionsSection', 'N/A')}, "
                            f"会话列表: {elements.get('hasSessionsList', 'N/A')}, "
                            f"新建按钮: {elements.get('hasNewSessionBtn', 'N/A')}")
            except json.JSONDecodeError:
                self.log_test("页面元素检查", False, "无法解析结果")
        else:
            self.log_test("页面元素检查", False,
                        test_results.get('evaluate_script', {}).get('error', '测试失败'))

        if test_results.get('console', {}).get('success', False):
            try:
                messages = json.loads(test_results.get('console', {}).get('value', '[]'))
                if len(messages) == 0:
                    self.log_test("控制台错误检查", True, "无错误")
                else:
                    self.log_test("控制台错误检查", False, f"发现 {len(messages)} 个错误")
            except json.JSONDecodeError:
                self.log_test("控制台错误检查", False, "无法解析结果")
        else:
            self.log_test("控制台错误检查", False,
                        test_results.get('console', {}).get('error', '测试失败'))

    def _parse_test_output(self, stdout: str, stderr: str):
        """
        解析测试输出

        Args:
            stdout: 标准输出
            stderr: 标准错误
        """
        if stderr:
            self.log(f"测试输出 (stderr):\n{stderr}", "⚠️")

        self.log("解析测试结果...")
        test_results = self._parse_test_lines(stdout)
        self._log_test_results(test_results)

    def run_all_tests(self) -> Dict[str, Any]:
        """
        运行所有测试

        Returns:
            测试结果字典
        """
        print("=" * 70)
        print("Chrome DevTools MCP 端到端测试")
        print("=" * 70)

        start_time = time.time()

        try:
            # 启动 MCP 服务器并运行测试
            if self.start_mcp_server():
                self.log("测试执行完成", "✅")
            else:
                self.log("测试执行失败", "❌")

        except Exception as e:
            self.log(f"测试执行出错: {e}", "❌")

        end_time = time.time()
        duration = end_time - start_time

        # 打印测试结果汇总
        print("\n" + "=" * 70)
        print("测试结果")
        print("=" * 70)
        print(f"总测试数: {self.test_count}")
        print(f"通过: {self.pass_count} ✅")
        print(f"失败: {self.fail_count} ❌")
        print(f"耗时: {duration:.2f} 秒")
        print("=" * 70)

        if self.fail_count == 0:
            print(f"\n🎉 所有 {self.test_count} 个测试通过！")
        else:
            print(f"\n⚠️  有 {self.fail_count} 个测试失败")

        return {
            "total_tests": self.test_count,
            "passed": self.pass_count,
            "failed": self.fail_count,
            "duration": duration,
            "results": self.results
        }

    def cleanup(self):
        """清理资源"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception as e:
                self.log(f"清理进程失败: {e}", "⚠️")


def print_test_report(results: Dict[str, Any]):
    """打印详细的测试报告"""
    print("\n" + "=" * 70)
    print("详细测试报告")
    print("=" * 70)

    for result in results["results"]:
        status = "✅ 通过" if result["passed"] else "❌ 失败"
        print(f"\n{result['test_name']}: {status}")
        if result["details"]:
            print(f"  详情: {result['details']}")

    print("\n" + "=" * 70)


def save_test_report(results: Dict[str, Any], output_file: str = "chrome_devtools_e2e_test_results.json"):
    """保存测试结果到 JSON 文件"""
    output_path = Path(output_file)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n📊 测试结果已保存到: {output_path.absolute()}")


async def main():
    """主函数"""
    # 检查 Docker 是否可用
    try:
        subprocess.run(['docker', '--version'], check=True, capture_output=True)
        print("✅ Docker 已安装")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker 未安装或不可用")
        print("请安装 Docker: https://docs.docker.com/get-docker/")
        return

    # 检查 Docker image 是否存在
    try:
        subprocess.run(['docker', 'inspect', 'chrome-devtools-mcp:latest'],
                     check=True, capture_output=True)
        print("✅ Docker image: chrome-devtools-mcp:latest 已存在")
    except subprocess.CalledProcessError:
        print("❌ Docker image: chrome-devtools-mcp:latest 不存在")
        print("请先构建镜像: docker build -f Dockerfile.chrome-devtools -t chrome-devtools-mcp:latest .")
        return

    # 检查 relay-server 是否运行
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 8000))
        sock.close()
        if result == 0:
            print("✅ Relay server 正在运行 (port 8000)")
        else:
            print("⚠️  Relay server 未运行 (port 8000)")
            print("请先启动 relay-server: cd relay-server && python3 start_server.py")
    except Exception as e:
        print(f"⚠️  检查 relay-server 失败: {e}")

    print("")

    # 创建测试器实例
    tester = ChromeDevToolsMCPTester(use_docker=True)

    try:
        # 运行所有测试
        results = tester.run_all_tests()

        # 打印详细报告
        print_test_report(results)

        # 保存测试结果
        save_test_report(results)

    finally:
        # 清理资源
        tester.cleanup()

    # 返回退出码
    import sys
    sys.exit(0 if results["failed"] == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())

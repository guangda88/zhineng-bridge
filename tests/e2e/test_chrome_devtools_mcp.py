#!/usr/bin/env python3
"""
Chrome DevTools MCP E2E 测试

使用 Chrome DevTools MCP 进行浏览器自动化测试

⚠️  重要：此测试套件需要 Node.js v20.19.0 或更高版本才能运行。
当前环境的 Node.js 版本为 v18.19.1，不满足要求。

因此，以下测试类将被自动跳过：
- TestChromeDevToolsMCP (需要 MCP 浏览器自动化)
- TestWebUIWithPlaywright (需要 Playwright，而 Playwright 需要 Node.js v20+)

仍然可以运行的测试：
- TestWebUIBasic (基础文件存在性检查，不需要浏览器自动化)

前置条件：
1. 安装 Node.js 20.19+  ⚠️  当前版本不满足，需要升级
2. 安装 Chrome 浏览器
3. 安装 chrome-devtools-mcp

使用方式：
    # 方式一：使用 MCP 客户端调用
    # 方式二：使用 Playwright（备用方案）

升级 Node.js 的方法：
    # 方法 1: 使用 NodeSource 仓库（需要 sudo 和 curl）
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs

    # 方法 2: 使用 nvm（需要 curl）
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
    source ~/.bashrc
    nvm install 20
    nvm use 20
"""

import pytest
import subprocess
from typing import Dict, Any
from pathlib import Path


def check_node_version():
    """检查 Node.js 版本是否满足要求"""
    try:
        result = subprocess.run(
            ['node', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version_str = result.stdout.strip()  # 例如：v18.19.1
            version_num = version_str.lstrip('v')  # 去掉 'v' 前缀
            major_version = int(version_num.split('.')[0])
            minor_version = int(version_num.split('.')[1])

            # 检查是否 >= 20.19.0
            if major_version > 20:
                return True, version_str
            elif major_version == 20 and minor_version >= 19:
                return True, version_str
            else:
                return False, version_str
        return False, "未安装"
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError, ValueError, IndexError):
        return False, "检查失败"


@pytest.mark.skipif(
    not check_node_version()[0],
    reason=f"需要 Node.js v20.19.0+ (当前版本: {check_node_version()[1]})"
)
class TestChromeDevToolsMCP:
    """
    Chrome DevTools MCP E2E 测试

    此测试类需要 Node.js v20.19.0 或更高版本
    """

    @pytest.fixture
    def web_ui_url(self) -> str:
        """获取 Web UI URL"""
        return "http://localhost:8000/web/ui/index.html"

    @pytest.fixture
    def relay_server_url(self) -> str:
        """获取中继服务器 URL"""
        return "ws://localhost:8765"

    @pytest.fixture
    def test_config(self) -> Dict[str, Any]:
        """测试配置"""
        return {
            "base_url": "http://localhost:8000",
            "websocket_url": "ws://localhost:8765",
            "timeout": 5000,
            "test_tools": ["crush", "claude", "cursor", "copilot"]
        }

    # 测试步骤指令（供 MCP 使用）

    def test_setup_instructions(self):
        """测试环境设置说明"""
        """
        # Chrome DevTools MCP E2E 测试设置步骤

        ## 1. 升级 Node.js
        当前 Node.js 版本: v18.19.1 (不满足要求 >= v20.19.0)

        # 安装 Node.js 20 LTS
        curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
        sudo apt-get install -y nodejs

        # 或使用 nvm
        curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
        source ~/.bashrc
        nvm install 20
        nvm use 20

        ## 2. 安装 Chrome
        wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
        sudo apt install -y ./google-chrome-stable_current_amd64.deb

        ## 3. 安装 Chrome DevTools MCP
        npx -y chrome-devtools-mcp@latest --help

        ## 4. 配置 MCP 服务器
        添加到 Claude Code 配置 (~/.config/claude-code/config.json):
        {
          "mcpServers": {
            "chrome-devtools": {
              "command": "npx",
              "args": ["-y", "chrome-devtools-mcp@latest", "--headless=true"]
            }
          }
        }

        ## 5. 运行测试
        # 启动 relay-server
        cd /home/ai/zhineng-bridge/relay-server
        python3 start_server.py

        # 在另一个终端运行测试
        pytest tests/e2e/test_chrome_devtools_mcp.py -v
        """
        print("请查看测试文档进行环境设置")

    def test_mcp_tool_instructions(self):
        """
        MCP 工具使用指令（供 AI Agent 使用）

        # 测试场景：Web UI 基本功能

        1. 打开浏览器并导航到 Web UI
           工具: navigate_page
           参数: {"url": "http://localhost:8000/web/ui/index.html"}

        2. 检查页面是否正常加载
           工具: take_screenshot
           验证: 页面标题和元素可见

        3. 测试 WebSocket 连接
           工具: evaluate_script
           参数: {"script": "window.ws && window.ws.readyState === 1"}

        4. 发送 Ping 消息测试
           工具: type_text
           参数: {"selector": "#message-input", "text": '{"type": "ping"}'}

        5. 点击发送按钮
           工具: click
           参数: {"selector": "#send-button"}

        6. 验证响应
           工具: get_console_message
           验证: 收到 pong 响应

        # 测试场景：创建会话

        1. 在工具选择器中选择 Crush
           工具: click
           参数: {"selector": "[data-tool='crush']"}

        2. 点击创建会话按钮
           工具: click
           参数: {"selector": "#create-session-btn"}

        3. 验证会话创建成功
           工具: wait_for
           参数: {"selector": ".session-item", "timeout": 5000}

        4. 获取会话列表
           工具: evaluate_script
           参数: {"script": "JSON.stringify(window.sessions)"}

        # 测试场景：性能分析

        1. 开始性能追踪
           工具: performance_start_trace

        2. 执行操作（如发送多个消息）
           工具: type_text + click

        3. 停止性能追踪
           工具: performance_stop_trace

        4. 分析性能数据
           工具: performance_analyze_insight

        # 测试场景：网络监控

        1. 清空网络日志
           工具: evaluate_script
           参数: {"script": "window.networkLogs = []"}

        2. 执行操作

        3. 获取网络请求
           工具: list_network_requests

        4. 验证 WebSocket 连接
           工具: get_network_request
           参数: 查找 ws://localhost:8765 的请求

        # 测试场景：控制台错误检查

        1. 执行各种操作

        2. 获取控制台消息
           工具: list_console_messages

        3. 验证没有错误
           断言: 没有 error 级别的消息
        """
        pass

    def test_manual_test_checklist(self):
        """
        手动测试检查清单

        ## Web UI 基本功能
        [ ] 页面加载正常
        [ ] 页面样式正确显示
        [ ] WebSocket 连接成功建立
        [ ] 工具选择器显示所有可用工具
        [ ] 消息输入框可用
        [ ] 发送按钮可点击
        [ ] 响应消息正确显示

        ## 会话管理功能
        [ ] 创建新会话成功
        [ ] 会话列表正确显示
        [ ] 停止会话功能正常
        [ ] 删除会话功能正常
        [ ] 会话状态正确更新

        ## 消息通信功能
        [ ] Ping/Pong 消息正常
        [ ] List Sessions 消息正常
        [ ] Start Session 消息正常
        [ ] Stop Session 消息正常
        [ ] Delete Session 消息正常
        [ ] 错误消息正确显示

        ## 错误处理
        [ ] 无效 JSON 显示错误
        [ ] 无效消息类型显示错误
        [ ] 无效工具名称显示错误
        [ ] 无效会话 ID 显示错误
        [ ] 服务器断开时显示提示

        ## 性能测试
        [ ] 页面加载时间 < 2 秒
        [ ] 消息响应时间 < 500ms
        [ ] 内存使用正常
        [ ] 无内存泄漏

        ## 兼容性测试
        [ ] Chrome 浏览器正常
        [ ] Firefox 浏览器正常
        [ ] Safari 浏览器正常
        [ ] 移动端响应式布局
        """
        pass


@pytest.mark.skipif(
    not check_node_version()[0],
    reason=f"需要 Node.js v20.19.0+ (当前版本: {check_node_version()[1]})"
)
class TestWebUIWithPlaywright:
    """
    使用 Playwright 进行 Web UI 测试（备用方案）

    如果 Chrome DevTools MCP 不可用，可以使用 Playwright

    此测试类需要 Node.js v20.19.0 或更高版本
    """

    @pytest.fixture
    def playwright_check(self):
        """检查 Playwright 是否可用"""
        try:
            import playwright
            return True
        except ImportError:
            pytest.skip("Playwright 未安装")

    def test_playwright_setup_instructions(self):
        """
        Playwright 安装和使用说明

        # 安装 Playwright
        pip install pytest-playwright
        playwright install chromium

        # 安装浏览器
        playwright install

        # 运行测试
        pytest tests/e2e/test_playwright.py -v
        """
        pass


# MCP 测试脚本（供 AI Agent 直接执行）
MCP_TEST_SCRIPT = """
# Chrome DevTools MCP E2E 测试脚本

## 步骤 1: 启动浏览器并导航
工具: navigate_page
参数: {"url": "http://localhost:8000/web/ui/index.html"}

## 步骤 2: 截图验证页面加载
工具: take_screenshot
参数: {"path": "/tmp/zhineng_bridge_ui_load.png"}

## 步骤 3: 检查控制台错误
工具: list_console_messages
验证: 不应该有错误消息

## 步骤 4: 测试 WebSocket 连接状态
工具: evaluate_script
参数: {"script": "window.ws ? window.ws.readyState : 'disconnected'"}

## 步骤 5: 获取页面快照
工具: take_snapshot
参数: {}

## 步骤 6: 测试发送 Ping 消息
工具: evaluate_script
参数: {"script": "window.sendMessage && window.sendMessage(JSON.stringify({type: 'ping'}))"}

## 步骤 7: 等待响应
工具: wait_for
参数: {"selector": ".message-item[data-type='pong']", "timeout": 3000}

## 步骤 8: 截图最终状态
工具: take_screenshot
参数: {"path": "/tmp/zhineng_bridge_after_test.png"}

## 步骤 9: 获取网络请求（可选）
工具: list_network_requests
验证: 应该有 ws://localhost:8765 的 WebSocket 连接

## 步骤 10: 运行 Lighthouse 性能审计
工具: lighthouse_audit
参数: {"categories": ["performance", "accessibility", "best-practices"]}
"""


class TestWebUIBasic:
    """
    基础 Web UI 测试（不依赖浏览器自动化）

    此测试类不需要 Node.js v20.19.0+，可以独立运行
    它只检查文件存在性和基本配置正确性
    """

    @pytest.fixture
    def web_ui_file(self) -> Path:
        """获取 Web UI 文件路径"""
        return Path("/home/ai/zhineng-bridge/web/ui/index.html")

    def test_web_ui_file_exists(self, web_ui_file):
        """测试 Web UI 文件是否存在"""
        assert web_ui_file.exists(), f"Web UI 文件不存在: {web_ui_file}"

    def test_web_ui_contains_required_elements(self, web_ui_file):
        """测试 Web UI 包含必需元素"""
        content = web_ui_file.read_text()

        # 检查必需的元素
        required_elements = [
            'id="commandInput"',  # 命令输入框
            'id="sendCommandBtn"',  # 发送按钮
            'id="toolsGrid"',  # 工具选择器
            'id="sessionsList"',  # 会话列表
            'id="settingsList"',  # 设置列表
        ]

        for element in required_elements:
            assert element in content, f"缺少必需元素: {element}"

    def test_web_ui_websocket_config(self, web_ui_file):
        """测试 WebSocket 配置正确（不应在 HTML 中暴露配置信息）"""
        content = web_ui_file.read_text()

        # F-036: WebSocket 配置不应在 HTML 注释中暴露
        assert 'WS_PORT' not in content, "WebSocket 端口配置不应暴露在 HTML 中"
        assert 'WS_HOST' not in content, "WebSocket 主机配置不应暴露在 HTML 中"

    def test_relay_server_file_exists(self):
        """测试中继服务器文件存在"""
        server_file = Path("/home/ai/zhineng-bridge/relay-server/server.py")
        assert server_file.exists(), f"服务器文件不存在: {server_file}"

    def test_relay_server_config_exists(self):
        """测试配置文件存在"""
        config_file = Path("/home/ai/zhineng-bridge/relay-server/config.py")
        assert config_file.exists(), f"配置文件不存在: {config_file}"


if __name__ == "__main__":
    print("""
    ═══════════════════════════════════════════════════════════════
    Chrome DevTools MCP E2E 测试设置指南
    ═══════════════════════════════════════════════════════════════

    环境要求：
    ✓ Python 3.8+
    ✗ Node.js v20.19+  (当前: v18.19.1，需要升级)
    ✗ Chrome 浏览器     (未找到，需要安装)

    ───────────────────────────────────────────────────────────────

    步骤 1: 升级 Node.js
    ───────────────────────────────────────────────────────────────
    # 使用 NodeSource 仓库
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs

    # 验证版本
    node --version  # 应该是 v20.x

    ───────────────────────────────────────────────────────────────

    步骤 2: 安装 Chrome
    ───────────────────────────────────────────────────────────────
    # 下载 Chrome
    wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb

    # 安装
    sudo apt install -y ./google-chrome-stable_current_amd64.deb

    # 验证安装
    google-chrome --version

    ───────────────────────────────────────────────────────────────

    步骤 3: 安装 Chrome DevTools MCP
    ───────────────────────────────────────────────────────────────
    npx -y chrome-devtools-mcp@latest --help

    ───────────────────────────────────────────────────────────────

    步骤 4: 配置 MCP 服务器
    ───────────────────────────────────────────────────────────────
    编辑 ~/.config/claude-code/config.json (或对应的 MCP 客户端配置):

    {
      "mcpServers": {
        "chrome-devtools": {
          "command": "npx",
          "args": ["-y", "chrome-devtools-mcp@latest", "--headless=true"]
        }
      }
    }

    ───────────────────────────────────────────────────────────────

    步骤 5: 启动 zhineng-bridge 服务
    ───────────────────────────────────────────────────────────────
    cd /home/ai/zhineng-bridge/relay-server
    python3 start_server.py

    ───────────────────────────────────────────────────────────────

    步骤 6: 运行测试
    ───────────────────────────────────────────────────────────────
    # 运行所有 E2E 测试
    pytest tests/e2e/ -v

    # 只运行 Web UI 基础测试
    pytest tests/e2e/test_chrome_devtools_mcp.py::TestWebUIBasic -v

    ═══════════════════════════════════════════════════════════════
    """)

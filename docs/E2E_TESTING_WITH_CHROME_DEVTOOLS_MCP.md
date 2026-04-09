# Chrome DevTools MCP E2E 测试指南

**更新日期**: 2026-03-25
**项目**: zhineng-bridge

---

## 目录

1. [环境准备](#环境准备)
2. [安装步骤](#安装步骤)
3. [MCP 配置](#mcp-配置)
4. [E2E 测试场景](#e2e-测试场景)
5. [手动测试步骤](#手动测试步骤)
6. [故障排查](#故障排查)

---

## 环境准备

### 当前环境状态

| 组件 | 当前状态 | 要求 | 操作 |
|------|----------|------|------|
| Node.js | v18.19.1 | v20.19.0+ | ⚠️ 需要升级 |
| Chrome | 未安装 | Chrome Stable | ⚠️ 需要安装 |
| Python | 3.x | 3.8+ | ✅ 满足 |

### 快速安装

```bash
# 运行自动安装脚本
bash /home/ai/zhineng-bridge/scripts/install_chrome_devtools_mcp.sh
```

---

## 安装步骤

### 步骤 1: 升级 Node.js

```bash
# 使用 NodeSource 安装 Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# 验证版本
node --version  # 应该是 v20.x
```

### 步骤 2: 安装 Chrome

```bash
# 下载 Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb

# 安装
sudo apt install -y ./google-chrome-stable_current_amd64.deb

# 验证安装
google-chrome --version
```

### 步骤 3: 验证 MCP

```bash
npx -y chrome-devtools-mcp@latest --help
```

---

## MCP 配置

### Claude Code 配置

配置文件: `~/.config/claude-code/config.json`

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": [
        "-y",
        "chrome-devtools-mcp@latest",
        "--headless=false",
        "--viewport=1280x720"
      ]
    }
  }
}
```

### 无头模式配置

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": [
        "-y",
        "chrome-devtools-mcp@latest",
        "--headless=true",
        "--viewport=1920x1080"
      ]
    }
  }
}
```

### 连接到现有 Chrome 实例

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": [
        "-y",
        "chrome-devtools-mcp@latest",
        "--browser-url=http://127.0.0.1:9222"
      ]
    }
  }
}
```

---

## E2E 测试场景

### 场景 1: Web UI 基本功能

**目标**: 验证 Web UI 可以正常加载和使用

**测试步骤**:

1. **打开 Web UI**
   ```
   navigate_page({"url": "http://localhost:8000/web/ui/index.html"})
   ```

2. **截图验证**
   ```
   take_screenshot({"path": "/tmp/ui_load.png"})
   ```

3. **检查控制台错误**
   ```
   list_console_messages()
   ```

### 场景 2: WebSocket 通信

**目标**: 验证 WebSocket 连接和消息传递

**测试步骤**:

1. **检查 WebSocket 连接状态**
   ```javascript
   evaluate_script({"script": "window.ws ? window.ws.readyState : 'disconnected'"})
   ```

2. **发送 Ping 消息**
   ```javascript
   evaluate_script({"script": "window.sendMessage && window.sendMessage(JSON.stringify({type: 'ping'}))"})
   ```

3. **等待 Pong 响应**
   ```
   wait_for({"selector": ".message-item[data-type='pong']", "timeout": 3000})
   ```

### 场景 3: 会话管理

**目标**: 验证会话创建、停止和删除

**测试步骤**:

1. **选择工具**
   ```
   click({"selector": "[data-tool='crush']"})
   ```

2. **创建会话**
   ```
   click({"selector": "#create-session-btn"})
   ```

3. **等待会话创建成功**
   ```
   wait_for({"selector": ".session-item", "timeout": 5000})
   ```

4. **获取会话列表**
   ```javascript
   evaluate_script({"script": "JSON.stringify(window.sessions || [])"})
   ```

### 场景 4: 性能分析

**目标**: 分析 Web UI 性能

**测试步骤**:

1. **开始性能追踪**
   ```
   performance_start_trace()
   ```

2. **执行操作** (如发送多个消息)

3. **停止性能追踪**
   ```
   performance_stop_trace()
   ```

4. **分析性能数据**
   ```
   performance_analyze_insight()
   ```

### 场景 5: Lighthouse 审计

**目标**: 运行 Lighthouse 性能审计

**测试步骤**:

1. **运行完整审计**
   ```
   lighthouse_audit({"categories": ["performance", "accessibility", "best-practices", "seo"]})
   ```

2. **只运行性能审计**
   ```
   lighthouse_audit({"categories": ["performance"]})
   ```

---

## 手动测试步骤

### 准备工作

1. 启动 relay-server:
   ```bash
   cd /home/ai/zhineng-bridge/relay-server
   python3 start_server.py
   ```

2. 打开浏览器访问:
   ```
   http://localhost:8000/web/ui/index.html
   ```

### 测试清单

#### 基本功能

- [ ] 页面加载正常
- [ ] 工具选择器显示所有工具
- [ ] 消息输入框可用
- [ ] 发送按钮可点击
- [ ] 消息列表显示响应

#### 消息通信

- [ ] Ping → Pong 正常
- [ ] List Sessions 正常
- [ ] Start Session 正常
- [ ] Stop Session 正常
- [ ] Delete Session 正常

#### 错误处理

- [ ] 无效 JSON 显示错误
- [ ] 无效工具名称提示
- [ ] 服务器断开提示

#### 性能

- [ ] 页面加载 < 2 秒
- [ ] 消息响应 < 500ms
- [ ] 无明显卡顿

---

## MCP 工具参考

### 导航工具

| 工具 | 说明 |
|------|------|
| `navigate_page` | 导航到指定 URL |
| `new_page` | 打开新页面/标签 |
| `close_page` | 关闭页面 |
| `list_pages` | 列出所有页面 |

### 交互工具

| 工具 | 说明 |
|------|------|
| `click` | 点击元素 |
| `type_text` | 输入文本 |
| `fill` | 填写表单 |
| `hover` | 鼠标悬停 |
| `press_key` | 按键 |
| `drag` | 拖拽 |

### 调试工具

| 工具 | 说明 |
|------|------|
| `evaluate_script` | 执行 JavaScript |
| `list_console_messages` | 获取控制台消息 |
| `get_console_message` | 获取特定控制台消息 |
| `take_screenshot` | 截图 |
| `take_snapshot` | 获取页面快照 |
| `snapshot` | 获取 DOM 快照 |

### 网络工具

| 工具 | 说明 |
|------|------|
| `list_network_requests` | 列出网络请求 |
| `get_network_request` | 获取网络请求详情 |

### 性能工具

| 工具 | 说明 |
|------|------|
| `performance_start_trace` | 开始性能追踪 |
| `performance_stop_trace` | 停止性能追踪 |
| `performance_analyze_insight` | 分析性能 |
| `lighthouse_audit` | Lighthouse 审计 |

---

## 故障排查

### 问题 1: Node.js 版本过低

**症状**:
```
ERROR: `chrome-devtools-mcp` does not support Node v18.19.1
```

**解决方案**:
```bash
# 升级 Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### 问题 2: Chrome 未找到

**症状**: Chrome 相关命令失败

**解决方案**:
```bash
# 安装 Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y ./google-chrome-stable_current_amd64.deb
```

### 问题 3: MCP 服务器连接失败

**症状**: 无法连接到 Chrome DevTools MCP

**解决方案**:
1. 确保 relay-server 正在运行
2. 检查防火墙设置
3. 检查 WebSocket 端口 (8765) 是否开放

### 问题 4: 页面加载失败

**症状**: 无法访问 http://localhost:8000

**解决方案**:
1. 检查 HTTP 服务器是否运行
2. 检查端口 8000 是否被占用
3. 检查文件路径是否正确

---

## 附录

### A. 快速命令参考

```bash
# 运行所有 E2E 测试
pytest tests/e2e/ -v

# 运行特定测试文件
pytest tests/e2e/test_chrome_devtools_mcp.py -v

# 运行特定测试类
pytest tests/e2e/test_chrome_devtools_mcp.py::TestWebUIBasic -v

# 带覆盖率运行
pytest tests/e2e/ --cov=relay-server --cov-report=html

# 生成 HTML 报告
pytest tests/e2e/ --html-report=e2e_report.html
```

### B. 相关文档

- [Chrome DevTools MCP README](https://github.com/ChromeDevTools/chrome-devtools-mcp)
- [Web UI 使用指南](../USAGE_GUIDE.md)
- [开发规则](../DEVELOPMENT_RULES.md)
- [故障排查指南](../TROUBLESHOOTING.md)

---

**最后更新**: 2026-03-25
**维护者**: Zhineng-bridge Team

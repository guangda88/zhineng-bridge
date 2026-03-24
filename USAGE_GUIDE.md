# 智桥（Zhineng-bridge）使用指南

## 📖 目录

1. [简介](#简介)
2. [安装](#安装)
3. [配置](#配置)
4. [使用 Web UI](#使用-web-ui)
5. [使用 API](#使用-api)
6. [会话管理](#会话管理)
7. [支持的 AI 工具](#支持的-ai-工具)
8. [安全特性](#安全特性)
9. [性能优化](#性能优化)
10. [常见问题](#常见问题)
11. [故障排查](#故障排查)

---

## 🌟 简介

**智桥（Zhineng-bridge）** 是一个跨平台的实时同步和通信 SDK，支持多种 AI 编码工具和 IDE，提供统一的接口和用户体验。

### 核心功能

- 🎯 **多工具支持**: 支持 8 个 AI 编码工具
- 📱 **移动端优先**: 响应式设计，移动端优化
- 🔒 **端到端加密**: 安全的通信和存储
- 💾 **离线支持**: IndexedDB 存储，离线可用
- ⚡ **高性能**: 优化的性能和响应速度
- 🚀 **易于使用**: 简洁的 API 和友好的 UI

---

## 📦 安装

### 系统要求

- Python 3.8+
- Node.js 16+（用于 Web UI）
- 现代浏览器（Chrome、Firefox、Safari、Edge）

### 安装步骤

#### 方式一：从 GitHub 克隆

```bash
# 克隆仓库
git clone https://github.com/guangda88/zhineng-bridge.git
cd zhineng-bridge

# 安装 Python 依赖
pip install websockets asyncio

# 安装 JavaScript 依赖（用于 Web UI）
npm install
```

#### 方式二：使用快速开始脚本

```bash
# 克隆仓库
git clone https://github.com/guangda88/zhineng-bridge.git
cd zhineng-bridge

# 运行快速开始脚本
bash quickstart.sh  # 需要创建
```

### 验证安装

```bash
# 检查 Python 版本
python3 --version

# 检查 Node.js 版本
node --version

# 运行测试
python3 -m pytest tests/ -v
```

---

## 🔧 配置

### WebSocket 配置

**中继服务器配置** (`relay-server/server.py`):
```python
server = CrushRelayServer(
    host="0.0.0.0",  # 监听地址
    port=8765        # 端口号
)
```

**Web UI 配置** (`web/ui/js/client.js`):
```javascript
const config = {
    ws_host: "localhost",
    ws_port: 8765,
    auto_reconnect: true,
    reconnect_interval: 5,
    ping_interval: 10
};
```

### Session Manager 配置

**基础目录配置** (`phase1/session_manager/session_manager.py`):
```python
manager = SessionManager(base_dir="/tmp/zhineng-bridge")
```

### 工具配置

智桥支持 8 个 AI 工具，每个工具都有独立的配置：

```python
self.tools = {
    'crush': {
        'name': 'Crush',
        'description': 'Charmbracelet Crush - AI 编码助手',
        'executable': '/usr/local/bin/crush',
        'icon': '💎',
        'color': '#FFE66D'
    },
    # ... 其他工具
}
```

---

## 🌐 使用 Web UI

### 启动服务

**启动中继服务器**:
```bash
cd relay-server
python3 start_server.py
```

**启动 Session Manager**:
```bash
cd phase1/session_manager
python3 start_manager.py
```

**访问 Web UI**:
```
http://localhost:8000/web/ui/index.html
```

### Web UI 功能

#### 1. 工具选择

在 Web UI 中，你可以：

- 从下拉菜单中选择 AI 工具
- 查看工具的图标和描述
- 查看工具的状态（可用/不可用）

#### 2. 会话管理

- **创建会话**: 选择工具，输入参数，创建新会话
- **查看会话**: 查看所有活跃会话列表
- **切换会话**: 在不同会话之间切换
- **删除会话**: 删除不需要的会话

#### 3. 命令执行

- 在输入框中输入命令或自然语言描述
- 智桥会自动解析并执行命令
- 查看命令输出和结果

#### 4. 日志查看

- 实时查看操作日志
- 查看 WebSocket 消息
- 查看错误和警告

---

## 🔌 使用 API

### WebSocket API

智桥提供基于 WebSocket 的 API，支持实时双向通信。

#### 连接到服务器

```javascript
const ws = new WebSocket('ws://localhost:8765');

ws.onopen = () => {
    console.log('WebSocket 连接成功');
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('收到消息:', data);
};

ws.onerror = (error) => {
    console.error('WebSocket 错误:', error);
};

ws.onclose = () => {
    console.log('WebSocket 连接关闭');
};
```

#### 消息格式

所有消息都遵循以下格式：

```json
{
  "type": "message_type",
  "data": { ... }
}
```

#### 可用的消息类型

##### 1. 列出会话

**请求**:
```json
{
  "type": "list_sessions"
}
```

**响应**:
```json
{
  "type": "sessions_list",
  "sessions": [
    {
      "session_id": "xxx-xxx-xxx",
      "tool_name": "crush",
      "status": "running",
      "created_at": "2026-03-25T00:00:00Z"
    }
  ],
  "count": 1
}
```

##### 2. 创建会话

**请求**:
```json
{
  "type": "start_session",
  "tool_name": "crush",
  "args": ["--help"]
}
```

**响应**:
```json
{
  "type": "session_started",
  "session_id": "xxx-xxx-xxx",
  "tool_name": "crush",
  "status": "running"
}
```

##### 3. 停止会话

**请求**:
```json
{
  "type": "stop_session",
  "session_id": "xxx-xxx-xxx"
}
```

**响应**:
```json
{
  "type": "session_stopped",
  "session_id": "xxx-xxx-xxx",
  "status": "stopped"
}
```

##### 4. 删除会话

**请求**:
```json
{
  "type": "delete_session",
  "session_id": "xxx-xxx-xxx"
}
```

**响应**:
```json
{
  "type": "session_deleted",
  "session_id": "xxx-xxx-xxx"
}
```

##### 5. 心跳

**请求**:
```json
{
  "type": "ping"
}
```

**响应**:
```json
{
  "type": "pong",
  "timestamp": "2026-03-25T00:00:00Z"
}
```

### Python API

#### SessionManager API

```python
from phase1.session_manager.session_manager import SessionManager

# 创建 Session Manager
manager = SessionManager(base_dir="/tmp/zhineng-bridge")

# 列出工具
tools = manager.list_tools()

# 创建会话
session_id = manager.create_session('crush', args=['--help'])

# 获取会话
session = manager.get_session(session_id)

# 列出所有会话
sessions = manager.list_sessions()

# 获取活动会话
active_session = manager.get_active_session()

# 设置活动会话
manager.set_active_session(session_id)
```

---

## 🎯 会话管理

### 创建会话

```bash
# 通过 Web UI
选择工具 -> 输入参数 -> 点击"创建会话"

# 通过 API
ws.send(JSON.stringify({
    "type": "start_session",
    "tool_name": "crush",
    "args": ["--help"]
}));
```

### 查看会话

```bash
# 通过 Web UI
点击"会话列表"查看所有会话

# 通过 API
ws.send(JSON.stringify({
    "type": "list_sessions"
}));
```

### 切换会话

```bash
# 通过 Web UI
点击会话卡片切换活动会话

# 通过 API
# 智桥会自动将最新创建的会话设为活动会话
```

### 删除会话

```bash
# 通过 Web UI
点击会话卡片上的"删除"按钮

# 通过 API
ws.send(JSON.stringify({
    "type": "delete_session",
    "session_id": "xxx-xxx-xxx"
}));
```

### 会话状态

- `created`: 会话已创建
- `running`: 会话正在运行
- `stopped`: 会话已停止
- `deleted`: 会话已删除

---

## 🤖 支持的 AI 工具

### 1. Crush 💎

**名称**: Charmbracelet Crush
**描述**: AI 编码助手
**可执行文件**: `/usr/local/bin/crush`
**颜色**: #FFE66D

### 2. Claude Code 🤖

**名称**: Anthropic Claude Code
**描述**: AI 编码助手
**可执行文件**: `/usr/local/bin/claude`
**颜色**: #FF6B6B

### 3. iFlow CLI 🌊

**名称**: 阿里巴巴心流 iFlow CLI
**描述**: AI 编码助手
**可执行文件**: `/usr/local/bin/iflow`
**颜色**: #4ECDC4

### 4. Cursor 👆

**名称**: Anysphere Cursor
**描述**: AI IDE
**可执行文件**: `/usr/local/bin/cursor`
**颜色**: #45B7D1

### 5. Trae 🌊

**名称**: 字节跳动 Trae
**描述**: AI IDE（国产）
**可执行文件**: `/usr/local/bin/trae`
**颜色**: #96CEB4

### 6. Droid 🤖

**名称**: Factory Droid
**描述**: AI Agent
**可执行文件**: `/usr/local/bin/droid`
**颜色**: #FFEEAD

### 7. OpenClaw 🦞

**名称**: OpenClaw
**描述**: AI 助手
**可执行文件**: `/usr/local/bin/openclaw`
**颜色**: #D4A5A5

### 8. GitHub Copilot 🤖

**名称**: GitHub Copilot
**描述**: AI 助手
**可执行文件**: `/usr/local/bin/copilot`
**颜色**: #F0F0F0

---

## 🔒 安全特性

### 通信安全

- **WebSocket 加密**: 支持 WSS 加密连接
- **端到端加密**: 使用 Web Crypto API 进行加密
- **密钥管理**: 安全的密钥存储和管理

### 访问控制

- **用户认证**: 支持用户注册/登录（计划中）
- **权限管理**: 细粒度的权限控制（计划中）
- **会话隔离**: 每个会话独立运行，互不干扰

### 数据安全

- **离线存储**: 使用 IndexedDB 安全存储
- **数据加密**: 敏感数据加密存储
- **安全删除**: 安全删除敏感数据

---

## ⚡ 性能优化

### 当前性能指标

- 会话创建时间: < 100ms ⚡
- WebSocket 连接时间: < 50ms ⚡
- 页面加载时间: < 2s ⚡
- 内存使用: < 100MB 💚

### 优化目标

- 会话创建时间: < 50ms
- WebSocket 连接时间: < 20ms
- 页面加载时间: < 1s
- 内存使用: < 50MB

### 优化建议

1. **使用 Web Workers**: 将耗时任务放到 Web Workers 中执行
2. **实现缓存策略**: 缓存常用数据，减少网络请求
3. **代码分割**: 使用 Webpack 进行代码分割，减少初始加载时间
4. **懒加载**: 按需加载模块和资源
5. **Service Workers**: 使用 Service Workers 实现离线功能

---

## ❓ 常见问题

### 安装和配置

**Q1: 如何修改端口？**

A: 编辑 `relay-server/server.py` 文件：
```python
server = CrushRelayServer(host="0.0.0.0", port=8765)  # 修改端口
```

**Q2: 端口被占用怎么办？**

A: 停止占用端口的程序，或使用其他端口：
```bash
# 查看占用端口的程序
lsof -i :8765

# 停止程序
kill -9 <PID>
```

**Q3: 如何配置防火墙？**

A: 确保 WebSocket 端口（默认 8765）允许访问：
```bash
# Ubuntu/Debian
sudo ufw allow 8765

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=8765/tcp
sudo firewall-cmd --reload
```

### 使用和操作

**Q4: 如何创建多个会话？**

A: 在 Web UI 中多次创建会话，或通过 API 创建：
```javascript
ws.send(JSON.stringify({
    "type": "start_session",
    "tool_name": "crush",
    "args": ["--help"]
}));
```

**Q5: 如何查看会话状态？**

A: 使用 `list_sessions` 消息：
```javascript
ws.send(JSON.stringify({
    "type": "list_sessions"
}));
```

**Q6: 如何切换会话？**

A: 在 Web UI 中点击会话卡片，或通过 API 设置活动会话：
```javascript
// 最新创建的会话自动成为活动会话
// 或通过 SessionManager.set_active_session() 设置
```

### 故障排查

**Q7: WebSocket 连接失败？**

A: 检查以下几点：
1. 中继服务器是否正在运行
2. 端口是否正确
3. 防火墙是否允许连接
4. 查看浏览器控制台错误信息

**Q8: 命令执行失败？**

A: 检查以下几点：
1. 工具可执行文件是否存在
2. 工具是否有执行权限
3. 参数是否正确
4. 查看服务器日志

**Q9: 页面加载缓慢？**

A: 尝试以下优化：
1. 清除浏览器缓存
2. 使用 CDN 加速资源加载
3. 启用 Gzip 压缩
4. 优化图片和资源大小

### 性能和优化

**Q10: 如何提高性能？**

A: 参考以下优化建议：
1. 使用 Web Workers
2. 实现缓存策略
3. 代码分割
4. 懒加载
5. 使用 Service Workers

**Q11: 如何减少内存使用？**

A: 参考以下建议：
1. 定期清理不需要的会话
2. 使用对象池重用对象
3. 避免内存泄漏
4. 使用 Profiler 工具分析内存使用

**Q12: 如何提高响应速度？**

A: 参考以下建议：
1. 减少网络请求
2. 使用缓存
3. 优化数据库查询
4. 使用异步操作

---

## 🔧 故障排查

### 诊断工具

#### 1. 查看日志

**中继服务器日志**:
```bash
tail -f /tmp/relay-server.log
```

**Session Manager 日志**:
```bash
tail -f /tmp/session-manager.log
```

#### 2. 检查连接

**检查 WebSocket 连接**:
```bash
# 使用 websocat
websocat ws://localhost:8765

# 或使用浏览器控制台
const ws = new WebSocket('ws://localhost:8765');
```

#### 3. 运行测试

```bash
# 运行所有测试
python3 -m pytest tests/ -v

# 运行特定测试
python3 -m pytest tests/unit/test_relay_server.py -v

# 运行测试并生成覆盖率报告
python3 -m pytest tests/ --cov=. --cov-report=html
```

### 常见问题和解决方案

#### 问题 1: WebSocket 连接失败

**症状**: 浏览器控制台显示 "WebSocket connection failed"

**可能原因**:
- 中继服务器未启动
- 端口被占用
- 防火墙阻止连接

**解决方案**:
```bash
# 1. 检查服务器是否运行
ps aux | grep start_server.py

# 2. 启动服务器
cd relay-server
python3 start_server.py

# 3. 检查端口
lsof -i :8765

# 4. 检查防火墙
sudo ufw status
```

#### 问题 2: 会话创建失败

**症状**: 创建会话后没有响应，或显示错误

**可能原因**:
- 工具可执行文件不存在
- 工具没有执行权限
- 参数错误

**解决方案**:
```bash
# 1. 检查工具是否存在
which crush

# 2. 检查执行权限
ls -l /usr/local/bin/crush

# 3. 添加执行权限
chmod +x /usr/local/bin/crush

# 4. 测试工具
crush --help
```

#### 问题 3: 内存使用过高

**症状**: 内存使用持续增长，导致性能下降

**可能原因**:
- 内存泄漏
- 会话未清理
- 缓存未清理

**解决方案**:
```bash
# 1. 删除不需要的会话
# 在 Web UI 中点击"删除"按钮

# 2. 重启服务
kill -9 <PID>
python3 start_server.py

# 3. 使用 Profiler 分析内存
python3 -m memory_profiler your_script.py
```

#### 问题 4: 页面加载缓慢

**症状**: 页面加载时间过长，用户体验差

**可能原因**:
- 资源文件过大
- 网络延迟
- 服务器性能问题

**解决方案**:
```bash
# 1. 优化资源文件
# 使用图片压缩工具
# 使用代码压缩工具

# 2. 启用 Gzip 压缩
# 在 Nginx 配置中添加：
gzip on;
gzip_types text/css application/javascript;

# 3. 使用 CDN
# 将静态资源部署到 CDN

# 4. 使用缓存
# 配置浏览器缓存和服务器缓存
```

---

## 📚 更多资源

### 文档

- 📘 [README](docs/README.md) - 项目概览
- 📗 [API 文档](docs/API.md) - API 参考
- 📙 [开发指南](AGENTS.md) - 开发者指南
- 📕 [快速入门](QUICKSTART.md) - 5 分钟快速开始
- 📒 [测试报告](TEST_REPORT.md) - 测试覆盖率

### 项目信息

- 🏠 **GitHub**: https://github.com/guangda88/zhineng-bridge
- 🌍 **Gitea**: http://zhinenggitea.iepose.cn/guangda/zhineng-bridge
- 📧 **Issues**: https://github.com/guangda88/zhineng-bridge/issues

### 社区

- 💬 **讨论**: GitHub Discussions
- 🐛 **问题报告**: GitHub Issues
- 🤝 **贡献**: Pull Requests

---

## 🎯 最佳实践

1. **定期清理会话**: 删除不需要的会话，节省内存
2. **使用日志**: 启用日志记录，便于故障排查
3. **监控性能**: 定期检查性能指标
4. **备份数据**: 定期备份重要数据
5. **更新版本**: 及时更新到最新版本

---

**智桥（Zhineng-bridge） - 连接多个 AI 编码工具的桥梁** 🚀

有任何问题欢迎在 GitHub 提交 Issue！

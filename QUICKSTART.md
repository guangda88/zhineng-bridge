# 智桥快速入门指南

## 🚀 5 分钟快速开始

### 第一步：安装

```bash
# 克隆仓库
git clone https://github.com/guangda88/zhineng-bridge.git
cd zhineng-bridge

# 安装 Python 依赖
pip install websockets asyncio

# 安装 JavaScript 依赖（用于 Web UI）
npm install
```

### 第二步：启动服务

打开两个终端窗口：

**终端 1：启动中继服务器**
```bash
cd relay-server
python3 start_server.py
```

**终端 2：启动 Session Manager**
```bash
cd phase1/session_manager
python3 start_manager.py
```

### 第三步：访问 Web UI

打开浏览器访问：

```
http://localhost:8000/web/ui/index.html
```

你将看到智桥的 Web 界面，可以选择不同的 AI 工具进行交互！

---

## 💡 常用示例

### 1. 查看当前目录的文件

在 Web UI 中输入：
```
查看当前目录的文件列表
```

智桥会自动执行 `ls -la` 命令并返回结果！

### 2. 创建新会话

```
创建一个 Crush 会话
```

### 3. 查看 Git 状态

```
查看当前的 git 状态
```

### 4. 安装 npm 包

```
帮我安装 react 包
```

### 5. 运行项目

```
启动这个项目
```

---

## 🔧 配置选项

### 修改端口

**中继服务器端口**：
编辑 `relay-server/server.py`:
```python
server = CrushRelayServer(host="0.0.0.0", port=8765)  # 修改端口
```

**Web UI 端口**：
编辑 `web/ui/index.html` 中的 WebSocket URL：
```javascript
const ws_host = "localhost";
const ws_port = 8765;  // 修改端口
```

---

## ⚡ 性能

- 会话创建时间: < 100ms ⚡
- WebSocket 连接时间: < 50ms ⚡
- 页面加载时间: < 2s ⚡
- 内存使用: < 100MB 💚

---

## 🧪 测试

运行测试确保一切正常：

```bash
# 运行所有测试
python3 -m pytest tests/ -v

# 运行测试并生成覆盖率报告
python3 -m pytest tests/ --cov=. --cov-report=html
```

测试覆盖率：82% ✅

---

## 📚 更多文档

- [完整使用指南](docs/README.md)
- [API 文档](docs/API.md)
- [开发指南](AGENTS.md)
- [测试报告](TEST_REPORT.md)
- [项目主页](https://github.com/guangda88/zhineng-bridge)

---

## ❓ 遇到问题？

### 常见问题

**Q: 端口被占用怎么办？**
A: 修改 `relay-server/server.py` 中的端口号，或停止占用端口的程序。

**Q: WebSocket 连接失败？**
A: 确保中继服务器正在运行，并检查防火墙设置。

**Q: 如何查看日志？**
A: 查看终端输出，或检查 `/tmp/relay-server.log` 文件。

**Q: 如何停止服务？**
A: 在终端中按 `Ctrl + C` 停止服务。

---

## 🎯 支持的 AI 工具

智桥目前支持以下 8 个 AI 编码工具：

1. 💎 **Crush** - Charmbracelet Crush
2. 🤖 **Claude Code** - Anthropic Claude Code
3. 🌊 **iFlow CLI** - 阿里巴巴心流 iFlow CLI
4. 👆 **Cursor** - Anysphere Cursor
5. 🌊 **Trae** - 字节跳动 Trae
6. 🤖 **Droid** - Factory Droid
7. 🦞 **OpenClaw** - OpenClaw
8. 🤖 **GitHub Copilot** - GitHub Copilot

---

## 🚀 下一步

- 阅读 [完整使用指南](docs/README.md)
- 查看 [API 文档](docs/API.md)
- 了解 [开发指南](AGENTS.md)
- 运行 [测试套件](TEST_REPORT.md)

---

**智桥（Zhineng-bridge） - 连接多个 AI 编码工具的桥梁** 🚀

有任何问题欢迎在 GitHub 提交 Issue！

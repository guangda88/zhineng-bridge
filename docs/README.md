# 智桥 (Zhineng-Bridge)

跨平台实时同步和通信SDK

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub issues](https://img.shields.io/github/issues/guangda88/zhineng-bridge)](https://github.com/guangda88/zhineng-bridge/issues)
[![GitHub forks](https://img.shields.io/github/forks/guangda88/zhineng-bridge)](https://github.com/guangda88/zhineng-bridge/network)

## 🌟 项目简介

**智桥** 是一个跨平台的实时同步和通信SDK，支持多种AI编码工具和IDE，提供统一的接口和用户体验。

### 核心特性

- 🎯 **多工具支持**: 支持8个AI编码工具
- 📱 **移动端优先**: 响应式设计，移动端优化
- 🔒 **端到端加密**: 安全的通信和存储
- 💾 **离线支持**: IndexedDB存储，离线可用
- ⚡ **高性能**: 优化的性能和响应速度
- 🚀 **易于使用**: 简洁的API和友好的UI

### 支持的工具

1. 💎 **Crush** - Charmbracelet Crush
2. 🤖 **Claude Code** - Anthropic Claude Code
3. 🌊 **iFlow CLI** - 阿里巴巴心流 iFlow CLI
4. 👆 **Cursor** - Anysphere Cursor
5. 🌊 **Trae** - 字节跳动 Trae
6. 🤖 **Droid** - Factory Droid
7. 🦞 **OpenClaw** - OpenClaw
8. 🤖 **GitHub Copilot** - GitHub Copilot

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/guangda88/zhineng-bridge.git
cd zhineng-bridge

# 安装依赖
pip install -r requirements.txt
```

### 启动服务

```bash
# 启动中继服务器
cd relay-server
python3 start_server.py

# 启动 Session Manager
cd phase1/session_manager
python3 start_manager.py
```

### 访问 Web UI

打开浏览器访问：`http://localhost:8000/web/ui/index.html`

## 📖 使用文档

### API 文档

详见：[API 文档](docs/API.md)

### 用户指南

详见：[用户指南](docs/USER_GUIDE.md)

### 开发指南

详见：[开发指南](docs/DEVELOPMENT.md)

## 🏗️ 项目结构

```
zhineng-bridge/
├── phase1/                # Phase 1: Session Manager
│   └── session_manager/   # 会话管理器
├── phase2/                # Phase 2: 移动端 UI
│   └── web/ui/            # Web UI
├── phase3/                # Phase 3: 加密和离线
│   ├── encryption/        # 加密模块
│   └── storage/           # 存储模块
├── phase4/                # Phase 4: 优化和发布
│   ├── optimization/      # 性能优化
│   └── security/          # 安全加固
├── relay-server/          # 中继服务器
├── optimization/          # 优化项目
└── docs/                  # 文档
```

## 🔧 配置

### WebSocket 配置

```json
{
  "ws_host": "localhost",
  "ws_port": 8765,
  "auto_reconnect": true,
  "reconnect_interval": 5,
  "ping_interval": 10
}
```

### 会话配置

```json
{
  "max_sessions": 100,
  "session_timeout": 3600,
  "output_buffer_size": 100000
}
```

## 🧪 测试

```bash
# 运行测试
cd tests
pytest

# 运行端到端测试
cd ..
python3 e2e_test.py
```

## 📊 性能

### 优化指标

- 🚀 会话创建时间: < 100ms
- 🚀 WebSocket 连接时间: < 50ms
- 🚀 页面加载时间: < 2s
- 🚀 内存使用: < 100MB

### LingMinOpt 优化结果

- WebSocket 连接优化: 1.0000 (max_connections=200, ping_interval=5, message_queue_size=5000)
- 性能参数优化: 1.0866 (output_update_interval=51ms, compression_enabled=False, batch_size=1000)

## 🤝 贡献

欢迎贡献！请随时提交 Pull Request。

1. Fork 仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📝 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- LingMinOpt - 极简自优化框架
- LingFlow - 灵研流式AI框架
- 灵研 - 极简自主研究哲学

## 📞 联系方式

- GitHub: https://github.com/guangda88/zhineng-bridge
- Gitea: http://zhinenggitea.iepose.cn/guangda/zhineng-bridge

---

**智桥 - 连接AI工具的桥梁** 🌉

**由 Guangda 用 ❤️ 制作**

**版本: 1.0.0**
**发布日期: 2026-03-24**

# 配置演示文档索引

欢迎！本目录包含智桥配置功能的完整演示文档和脚本。

## 🚀 快速导航

### 我想快速开始
→ [快速参考卡片](CONFIG_QUICK_REFERENCE.md) (30秒上手)

### 我想了解所有场景
→ [完整配置指南](CONFIGURATION_GUIDE.md)

### 我想了解技术实现
→ [本地主机移除总结](LOCALHOST_REMOVAL_SUMMARY.md)

### 我想运行演示脚本
→ [演示文档总结](DEMO_SUMMARY.md)

---

## 📚 文档总览

### 1. 快速参考卡片 ⭐ 推荐首次阅读

**文件**: [CONFIG_QUICK_REFERENCE.md](CONFIG_QUICK_REFERENCE.md)

**适合人群**:
- 需要快速启动项目的开发者
- 查找特定配置项的用户
- 排查连接问题的运维人员

**主要内容**:
- 30秒快速启动
- 常用配置项表格
- 3种配置方法
- 配置验证命令
- 典型场景示例
- 常见问题解答

**预计阅读时间**: 3-5 分钟

---

### 2. 完整配置指南

**文件**: [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md)

**适合人群**:
- 首次配置项目的开发者
- 准备部署到生产环境的工程师
- 需要全面了解配置功能的用户

**主要内容**:
- 开发环境配置
- 环境变量配置
- 生产环境部署
- 多环境管理
- 配置项详细说明
- 验证和故障排查
- 最佳实践

**预计阅读时间**: 15-20 分钟

---

### 3. 本地主机移除总结

**文件**: [LOCALHOST_REMOVAL_SUMMARY.md](LOCALHOST_REMOVAL_SUMMARY.md)

**适合人群**:
- 需要了解技术实现的开发者
- 进行代码审查的工程师
- 技术决策者

**主要内容**:
- 技术实现细节
- 代码变更说明
- 测试结果
- 迁移指南
- 未来增强建议

**预计阅读时间**: 10-15 分钟

---

### 4. 演示文档总结

**文件**: [DEMO_SUMMARY.md](DEMO_SUMMARY.md)

**适合人群**:
- 想要运行所有演示的用户
- 需要了解演示脚本的开发者
- 项目维护者

**主要内容**:
- 所有演示脚本说明
- 文档结构介绍
- 使用建议（按经验水平）
- 配置优先级
- 验证清单

**预计阅读时间**: 5-10 分钟

---

## 🎬 演示脚本

项目包含4个演示脚本，可以直接运行查看效果：

### 1. 默认配置演示

```bash
./demo_default_config.sh
```

**展示内容**:
- 默认配置如何工作
- 无需额外设置即可启动
- 服务器绑定地址和客户端连接地址

**使用场景**: 本地开发环境首次使用

---

### 2. 环境变量配置演示

```bash
./demo_env_config.sh
```

**展示内容**:
- 如何使用环境变量覆盖配置
- 验证配置是否生效
- 实际配置效果

**使用场景**:
- 快速测试不同配置
- 不想创建配置文件的情况
- Docker 容器配置

---

### 3. 前端配置演示

```bash
./demo_frontend_config.sh
```

**展示内容**:
- 前端配置文件的位置和格式
- 如何创建和编辑配置
- 配置文件的加载机制

**使用场景**:
- 自定义 Web UI 界面
- 修改主题、语言等设置

---

### 4. 生产环境配置演示

```bash
./demo_production_config.sh
```

**展示内容**:
- 完整的生产环境配置示例
- 后端 .env.prod 文件
- 前端 config.js 文件
- 部署命令

**使用场景**:
- 首次部署到生产环境
- 参考生产配置模板

---

## 🎯 学习路径

### 路径 1: 快速上手（5分钟）

1. 阅读 [快速参考卡片](CONFIG_QUICK_REFERENCE.md)
2. 运行 `./demo_default_config.sh`
3. 启动服务器: `python3 relay-server/start_server.py`
4. 访问 Web UI

### 路径 2: 深入学习（20分钟）

1. 阅读 [完整配置指南](CONFIGURATION_GUIDE.md)
2. 运行所有演示脚本
3. 尝试不同的配置场景
4. 实际部署一个测试环境

### 路径 3: 技术研究（30分钟）

1. 阅读 [本地主机移除总结](LOCALHOST_REMOVAL_SUMMARY.md)
2. 查看 [演示文档总结](DEMO_SUMMARY.md)
3. 运行所有演示脚本
4. 查看相关代码文件

### 路径 4: 生产部署（40分钟）

1. 阅读 [生产部署指南](docs/PRODUCTION_DEPLOYMENT.md)
2. 阅读 [完整配置指南](CONFIGURATION_GUIDE.md)
3. 运行 `./demo_production_config.sh`
4. 自定义配置文件
5. 验证配置
6. 部署

---

## 📊 配置系统概览

### 配置层次

```
┌─────────────────────────────────────┐
│   前端 JavaScript 配置 (最高优先级)   │
│   web/ui/config/config.js           │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│   环境变量                          │
│   ZHINENG_BRIDGE_WS_HOST=...       │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│   .env 文件                         │
│   ZHINENG_BRIDGE_WS_HOST=...       │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│   默认值 (最低优先级)                │
│   ws_host: str = "localhost"       │
└─────────────────────────────────────┘
```

### 关键配置项

| 后端环境变量 | 前端配置项 | 说明 | 默认值 |
|-------------|-----------|------|--------|
| `ZHINENG_BRIDGE_WS_HOST` | `WS_HOST` | WebSocket 服务器地址 | `localhost` |
| `ZHINENG_BRIDGE_SERVER_PORT` | `WS_PORT` | 端口号 | `8765` |
| `ZHINENG_BRIDGE_ENABLE_WSS` | - | 启用 WSS | `false` |

---

## 🔍 常见任务

### 任务 1: 修改服务器地址

**后端**:
```bash
export ZHINENG_BRIDGE_WS_HOST="my-server.com"
python3 relay-server/start_server.py
```

**前端** (web/ui/config/config.js):
```javascript
window.ZHINENG_BRIDGE_CONFIG = {
    WS_HOST: 'my-server.com'
};
```

### 任务 2: 修改端口

**后端**:
```bash
export ZHINENG_BRIDGE_SERVER_PORT=9000
python3 relay-server/start_server.py
```

**前端**:
```javascript
window.ZHINENG_BRIDGE_CONFIG = {
    WS_PORT: 9000
};
```

### 任务 3: 启用 WSS (HTTPS)

**后端**:
```bash
export ZHINENG_BRIDGE_ENABLE_WSS=true
export ZHINENG_BRIDGE_CERT_FILE=/path/to/cert.pem
export ZHINENG_BRIDGE_KEY_FILE=/path/to/key.pem
python3 relay-server/start_server.py
```

### 任务 4: 切换主题

编辑 `web/ui/config/config.js`:
```javascript
window.ZHINENG_BRIDGE_CONFIG = {
    THEME: 'dark'  // 或 'light'
};
```

---

## 🛠️ 工具和命令

### 验证后端配置

```bash
python3 -c "
import sys
sys.path.insert(0, 'relay-server')
from config import settings
print(f'ws_host: {settings.server.ws_host}')
print(f'port: {settings.server.port}')
"
```

### 验证前端配置

在浏览器控制台：
```javascript
console.log(window.ZHINENG_BRIDGE_CONFIG);
```

### 查看环境变量

```bash
env | grep ZHINENG_BRIDGE
```

---

## 📖 相关文档

### 项目文档
- [README.md](README.md) - 项目概述和快速开始
- [AGENTS.md](AGENTS.md) - 开发者指南
- [docs/API.md](docs/API.md) - API 参考文档
- [docs/PRODUCTION_DEPLOYMENT.md](docs/PRODUCTION_DEPLOYMENT.md) - 生产部署指南
- [docs/SSL_SETUP.md](docs/SSL_SETUP.md) - SSL/TLS 设置

### 配置示例
- [.env.example](.env.example) - 后端配置示例
- [web/ui/config/config.js.example](web/ui/config/config.js.example) - 前端配置示例

---

## ❓ 获取帮助

### 问题排查流程

1. **查看快速参考** - [CONFIG_QUICK_REFERENCE.md](CONFIG_QUICK_REFERENCE.md)
2. **查看常见问题** - 快速参考中的"常见问题"部分
3. **查看完整指南** - [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md)
4. **验证配置** - 使用验证命令确认配置正确

### 联系方式

- GitHub Issues: [提交问题](https://github.com/guangda88/zhineng-bridge/issues)
- 文档反馈: 提交 Pull Request 或 Issue

---

## 📝 更新日志

### v1.0 (2026-03-25)
- ✅ 初始版本
- ✅ 移除硬编码 localhost 引用
- ✅ 创建配置系统
- ✅ 添加4个演示脚本
- ✅ 创建4个文档文件
- ✅ 完成测试和验证

---

**文档版本**: 1.0
**最后更新**: 2026-03-25
**维护者**: Crush AI Assistant

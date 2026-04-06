# 智桥（Zhineng-bridge）

> 连接多个 AI 编码工具的统一桥梁

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-82%25-brightgreen.svg)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-82%25-brightgreen.svg)](htmlcov/)

---

## 项目简介

**智桥（Zhineng-bridge）** 是一个跨平台的实时同步和通信 SDK，支持多种 AI 编码工具和 IDE，提供统一的接口和用户体验。

### 核心特性

- **多工具支持**: 支持 8 个主流 AI 编码工具
- **WebSocket 通信**: 实时双向通信
- **会话管理**: 统一的会话生命周期管理
- **安全认证**: JWT + OAuth2 + CSRF + 速率限制 (v1.1 已集成)
- **高性能**: 优化的性能和响应速度
- **易于集成**: 简洁的 API 和友好的 UI
- **安全加固**: 48 项安全审计发现已全部修复 (v1.1)

---

## 支持的 AI 工具

| 工具 | 说明 | 状态 |
|------|------|------|
| Crush | Charmbracelet Crush | ✅ |
| Claude Code | Anthropic Claude Code | ✅ |
| iFlow CLI | 阿里巴巴心流 iFlow CLI | ✅ |
| Cursor | Anysphere Cursor | ✅ |
| Trae | 字节跳动 Trae | ✅ |
| Droid | Factory Droid | ✅ |
| OpenClaw | OpenClaw | ✅ |
| GitHub Copilot | GitHub Copilot | ✅ |

---

## 快速开始

### 环境要求

- Python 3.8+
- Node.js 16+（用于 Web UI 开发）
- 现代浏览器

### 安装

```bash
# 克隆仓库
git clone https://github.com/guangda88/zhineng-bridge.git
cd zhineng-bridge

# 安装 Python 依赖
pip install -r requirements.txt

# 安装 JavaScript 依赖（可选）
npm install
```

### 启动服务

```bash
# 终端 1：启动中继服务器
cd relay-server
python3 start_server.py

# 终端 2：启动 Session Manager
cd phase1/session_manager
python3 start_manager.py
```

### 访问 Web UI

```
http://localhost:8000/web/ui/index.html
```

---

## 项目结构

```
zhineng-bridge/
├── relay-server/          # WebSocket 中继服务器
│   ├── server.py          # 主服务器 (含认证集成)
│   ├── auth.py            # 认证模块
│   ├── auth_jwt.py        # JWT 令牌管理 (含缓存)
│   ├── auth_hash.py       # 密码哈希 (PBKDF2 可配置)
│   ├── auth_manager.py    # 用户管理
│   ├── http_server.py     # HTTP 服务 (OAuth2 回调)
│   ├── push_service.py    # 推送通知服务
│   ├── sharded_lock.py    # 分片锁 + 分片数据存储
│   ├── models.py          # 数据模型 (Pydantic)
│   ├── config.py          # 配置管理
│   └── start_server.py    # 启动脚本 (WS + HTTP)
├── phase1/                # 第一阶段功能
│   └── session_manager/   # 会话管理器
├── phase3/                # 第三阶段功能
│   ├── encryption/        # 加密模块
│   └── storage/           # 存储模块
├── phase4/                # 第四阶段功能
│   ├── security/          # 安全模块 (CSP/CSRF/速率限制)
│   ├── optimization/      # 性能优化
│   └── monitoring/        # 监控面板
├── web/ui/                # Web UI
│   ├── index.html         # 主页面
│   ├── css/               # 样式
│   └── js/                # JavaScript 模块
├── tests/                 # 测试代码
│   ├── unit/              # 单元测试
│   ├── integration/       # 集成测试
│   ├── e2e/               # 端到端测试
│   └── performance/       # 性能测试
├── docs/                  # 文档
│   ├── DEEP_AUDIT_REPORT.md  # 安全审计报告
│   ├── API.md             # API 文档
│   └── CHANGELOG.md       # 更新日志
└── config/                # 配置文件
```

---

## 性能指标

| 指标 | 值 |
|------|-----|
| 会话创建时间 | < 100ms |
| WebSocket 连接时间 | < 50ms |
| 页面加载时间 | < 2s |
| 内存使用 | < 100MB |
| 测试通过率 | 73/73 (100%) |
| 安全审计修复 | 48/48 (100%) |

---

## 生产环境部署

智桥提供完整的 Docker 化生产环境部署方案，支持以下特性：

### 部署特性

- **Docker Compose 编排**: 一键部署所有服务
- **PostgreSQL 数据库**: 生产级数据库支持
- **Redis 缓存**: 高性能缓存层
- **Nginx 反向代理**: SSL 终止和负载均衡
- **Prometheus + Grafana**: 完整的监控和可视化
- **自动化脚本**: 部署、备份、恢复、更新

### 快速部署

```bash
# 1. 配置环境变量
cp .env.example .env.prod
vim .env.prod  # 修改必要的配置

# 2. 配置 SSL 证书（可选但推荐）
# 参考 docs/SSL_SETUP.md

# 3. 运行部署脚本
chmod +x scripts/*.sh
./scripts/deploy.sh

# 4. 验证部署
./scripts/verify_deployment.sh
```

### 文档

- 📘 [生产环境部署指南](docs/PRODUCTION_DEPLOYMENT.md) - 完整的部署文档
- 🔐 [SSL 证书设置指南](docs/SSL_SETUP.md) - SSL/TLS 配置说明

### 管理命令

```bash
# 查看服务状态
docker-compose -f docker-compose.prod.yml ps

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f

# 停止服务
docker-compose -f docker-compose.prod.yml down

# 备份数据
./scripts/backup.sh -t full

# 恢复数据
./scripts/restore.sh backups/full_backup_*.tar.gz

# 更新服务
./scripts/update.sh

# 验证部署
./scripts/verify_deployment.sh
```

---

## 文档

### 用户文档

- [API 文档](docs/API.md) - WebSocket API 参考
- [认证文档](docs/AUTHENTICATION.md) - JWT/OAuth2 认证说明
- [更新日志](docs/CHANGELOG.md) - 版本变更记录

### 开发文档

- [安全审计报告](docs/DEEP_AUDIT_REPORT.md) - 48 项安全发现及修复记录
- [测试审计报告](docs/TEST_AUDIT_REPORT.md) - 测试质量审计
- [贡献指南](CONTRIBUTING.md) - 贡献流程和规范
- [开发指南](AGENTS.md) - Agent 配置说明

---

## 安全

v1.1 完成了全面安全审计，修复 48 项发现（4 P0 + 20 P1 + 16 P2 + 8 P3）：

- **WebSocket 认证**: 首消息 token 验证 + 后端注册密钥
- **XSS 防护**: 全前端 DOM-based escapeHtml + CSP
- **OAuth2 安全**: HTTP-only cookie + state 验证
- **CSRF 防护**: 令牌 + fetch 拦截链
- **密码安全**: PBKDF2-HMAC-SHA256 可配置迭代次数
- **信息泄露**: 移除 HTML 注释中的配置信息
- **内存安全**: pending 字典 TTL 自动清理

详见 [安全审计报告](docs/DEEP_AUDIT_REPORT.md)。

---

## 开发

### 运行测试

```bash
# 运行所有测试
python3 -m pytest tests/ -v

# 运行测试并生成覆盖率报告
python3 -m pytest tests/ --cov=. --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html
```

### 代码规范

项目遵循以下规范：

- **PEP 8** - Python 代码风格
- **Conventional Commits** - 提交消息规范
- **Google 风格** - 文档字符串规范
- **Black** - 代码格式化
- **isort** - 导入排序

### 提交规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

| Type | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档更新 |
| `style` | 代码格式 |
| `refactor` | 重构 |
| `test` | 测试相关 |
| `chore` | 构建/工具 |

---

## 贡献

欢迎贡献代码！请查看 [贡献指南](CONTRIBUTING.md) 了解详情。

### 贡献流程

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 许可证

[MIT License](LICENSE)

---

## 联系方式

- GitHub: https://github.com/guangda88/zhineng-bridge
- Issues: https://github.com/guangda88/zhineng-bridge/issues

---

**智桥（Zhineng-bridge） - 让 AI 编码工具更易用** 🚀

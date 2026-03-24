# 智桥（Zhineng-bridge）变更日志

本文件记录智桥所有值得注意的更改。格式基于 [Keep a Changelog](https://keepachangelog.com/)，
版本号遵循 [语义化版本](https://semver.org/)。

## [Unreleased]

### Added
- 添加单元测试套件（17 个测试）
- 添加集成测试套件（17 个测试）
- 添加 E2E 测试套件（16 个测试）
- 添加 pytest 配置文件
- 添加测试覆盖率报告
- 添加 QUICKSTART.md 文档（5 分钟快速开始）
- 添加 USAGE_GUIDE.md 文档（完整使用指南）
- 添加 TROUBLESHOOTING.md 文档（故障排查指南）
- 添加 RELEASE_CHECKLIST.md（发布检查清单）
- 添加发布验证脚本（scripts/verify-publish.py）
- 添加示例文件（examples/basic_usage.py）
- 添加 Cursor IDE 配置示例（examples/cursor_config.md）
- 添加 Claude Desktop 配置示例（examples/claude_config.md）
- 添加 examples/README.md
- 添加 scripts/README.md
- 添加测试报告文档（TEST_REPORT.md）
- 添加优化进度文档（OPTIMIZATION_PROGRESS.md）

### Changed
- 提高测试覆盖率至 82%（目标: >=70%）
- 优化测试执行速度至 0.55 秒
- 改进文档结构和内容

## [1.0.0] - 2026-03-24

### Added
- 初始版本发布
- 跨平台实时同步和通信 SDK
- 支持 8 个 AI 编码工具：Crush、Claude Code、iFlow CLI、Cursor、Trae、Droid、OpenClaw、GitHub Copilot
- WebSocket 中继服务器（relay-server）
- 会话管理器（SessionManager）
- Web UI（响应式设计，移动端优化）
- 端到端加密功能（Web Crypto API）
- IndexedDB 离线存储
- Service Worker 支持
- 性能监控 Dashboard
- 代码分割和懒加载
- 网络优化（防抖、节流、连接池）

### Performance
- Session 创建时间: < 100ms
- WebSocket 连接时间: < 50ms
- 页面加载时间: < 2s
- 内存使用: < 100MB

### Documentation
- README.md（项目介绍）
- docs/API.md（API 文档）
- docs/README.md（用户文档）
- docs/CHANGELOG.md（历史变更）
- COMPREHENSIVE_DEVELOPMENT_PLAN.md（开发计划）
- ZHINENGBRIDGE_V1.0.0_RELEASE.md（发布说明）

## [0.9.0] - 2026-03-20

### Added
- Phase 4: 优化和发布
- 性能优化框架（LingMinOpt）
- 参数优化系统
- 性能监控仪表板
- 代码分割和懒加载
- Service Worker 支持

## [0.8.0] - 2026-03-15

### Added
- Phase 3: 安全特性
- 端到端加密（RSA-OAEP + AES-GCM）
- IndexedDB 存储管理
- QR 码生成和扫描
- 安全密钥管理

## [0.7.0] - 2026-03-10

### Added
- Phase 2: 移动端 UI
- 响应式设计
- 移动端优化
- 触摸事件支持
- 移动端特定样式

## [0.6.0] - 2026-03-05

### Added
- Phase 1: 会话管理
- SessionManager 类
- 工具注册系统
- 会话生命周期管理
- 活动会话跟踪

## [0.5.0] - 2026-02-28

### Added
- WebSocket 中继服务器
- CrushRelayServer 类
- 消息路由系统
- 心跳机制
- 自动重连

## [0.4.0] - 2026-02-20

### Added
- Web UI 基础框架
- HTML5 结构
- CSS 样式系统
- JavaScript 模块

## [0.3.0] - 2026-02-15

### Added
- WebSocket 客户端实现
- 消息发送和接收
- 错误处理
- 连接管理

## [0.2.0] - 2026-02-10

### Added
- AI 工具集成框架
- 工具注册接口
- 命令执行系统

## [0.1.0] - 2026-02-01

### Added
- 项目初始化
- 基础架构
- 开发计划

---

## 版本说明

### 语义化版本

智桥遵循 [语义化版本 2.0.0](https://semver.org/) 规范：

- **主版本号（MAJOR）**：不兼容的 API 变更
- **次版本号（MINOR）**：向后兼容的功能新增
- **修订号（PATCH）**：向后兼容的问题修复

### 变更类型

- **Added**: 新增功能
- **Changed**: 现有功能的变更
- **Deprecated**: 即将移除的功能
- **Removed**: 已移除的功能
- **Fixed**: 问题修复
- **Security**: 安全相关修复

### 发布流程

智桥使用标准发布流程：

1. 开发新功能和修复问题
2. 更新 CHANGELOG.md
3. 运行测试套件（单元、集成、E2E）
4. 运行发布验证脚本（`python3 scripts/verify-publish.py`）
5. 创建 Git 标签
6. 发布到 GitHub 和 Gitea
7. 发布到 PyPI（如果适用）

### 如何贡献

如果您想为智桥做贡献：

1. Fork 本仓库
2. 创建特性分支（`git checkout -b feature/AmazingFeature`）
3. 提交更改（`git commit -m 'feat: Add some AmazingFeature'`）
4. 推送到分支（`git push origin feature/AmazingFeature`）
5. 开启 Pull Request

详细贡献指南请参见 [CONTRIBUTING.md](./CONTRIBUTING.md)（如果存在）

### 获取帮助

如果您需要帮助或有问题：

- 📖 查看 [USAGE_GUIDE.md](./USAGE_GUIDE.md)
- 🔧 查看 [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
- 🚀 查看 [QUICKSTART.md](./QUICKSTART.md)
- 💬 在 GitHub 提交 [Issue](https://github.com/guangda88/zhineng-bridge/issues)

---

**项目**: 智桥（Zhineng-bridge）
**许可证**: MIT License
**主页**: https://github.com/guangda88/zhineng-bridge
**镜像**: http://zhinenggitea.iepose.cn/guangda/zhineng-bridge

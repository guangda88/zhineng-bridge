# 更新日志

## [1.2.0] - 2026-04-05

### 新增功能

**密码重置**
- 🔐 完整密码重置流程：请求令牌 → 邮件发送 → 确认重置
- 🔐 带当前密码验证的密码修改接口
- 🔐 重置令牌过期（1小时）和一次性使用
- 🔐 防枚举保护：无论邮箱是否存在均返回成功
- 🔐 过期令牌自动清理

**双因素认证 (TOTP / RFC 6238)**
- 🔐 纯 Python TOTP 实现，零外部依赖
- 🔐 备用恢复码（10个，8位十六进制，一次性使用）
- 🔐 QR 码配置 URI 生成（可选 qrcode 库）
- 🔐 防重放保护：已使用的 TOTP 码缓存 120 秒
- 🔐 完整生命周期：setup → enable → verify → disable
- 🔐 HTTP API 路由：/api/users/2fa/setup、enable、verify、disable、backup-codes

**Kubernetes 部署**
- ☸️ 完整 K8s 配置清单（namespace、configmap、deployment、service、ingress、hpa、secrets）
- ☸️ 2 副本滚动更新部署，liveness/readiness 探针
- ☸️ nginx Ingress + WebSocket 支持 + TLS (cert-manager)
- ☸️ HPA (2-10 副本，CPU/内存触发) + PDB (minAvailable: 1)
- ☸️ 非 root 安全上下文 + 资源限制

**部署回滚机制**
- 🔄 Docker Compose 部署自动保存前次镜像/配置快照
- 🔄 `deploy.sh -r` 一键回滚到上一版本
- 🔄 支持 compose 文件快照和镜像 ID 回退两种策略

### 错误修复

- 🐛 修复 `update_user()` SQL 参数顺序错误（user_id 和 timestamp 互换），该 bug 导致所有用户更新操作静默失败

### 架构变更

- `auth_totp.py`: 新增 TOTP 双因素认证模块
- `auth_password_reset.py`: 新增密码重置管理模块
- `auth_db.py`: 新增 `password_reset_tokens` 表、`totp_secret`/`totp_enabled`/`totp_backup_codes` 列（安全迁移）
- `auth_models.py`: User 数据类新增 TOTP 字段
- `auth_manager.py`: 集成 PasswordResetManager 和 TOTPManager
- `http_server.py`: 新增 8 个密码重置和 2FA 相关路由
- `user_auth.py`: 统一导出新增模块
- `scripts/deploy.sh`: 新增回滚支持
- `k8s/`: 新增完整 K8s 部署配置

### 测试

- ✅ 97 单元/集成/E2E 测试通过（+24 新增）
- ✅ 12 跳过（需外部服务）
- ✅ 0 失败

---

## [1.1.0] - 2026-04-05

### 安全审计修复 (48 项发现全部实施)

**P0 关键修复 (4项)**
- 🔒 F-001: WebSocket 连接认证集成 — 首条消息携带 token 验证
- 🔒 F-002: 后端注册密钥验证 — 防止未授权后端注册
- 🔒 F-003: 推送消息授权 — 仅已注册后端可推送
- 🔒 F-004: HTML sanitize 降级修复 — 正确过滤标签

**P1 高优先级修复 (20项)**
- 🔒 F-012/F-013: CSP 移除 unsafe-inline + 安全响应头
- 🔒 F-014~F-017: 全前端 XSS 修复 (settings/sessions/tools/dashboard escapeHtml)
- 🔒 F-018: CDN 外部脚本添加 SRI integrity 校验
- 🔒 F-020: OAuth2 回调 token 改为 HTTP-only cookie
- 🔒 F-021: OAuth2 state 参数验证防止 CSRF
- 🔒 F-022: update_user API 字段白名单
- 🔒 F-024: 推送通知 Bearer token 认证
- 🔒 F-025: 数据库连接池正确使用

**P2 中优先级修复 (16项)**
- ⚡ F-005: CSRF/rate-limit fetch 拦截链架构文档
- ⚡ F-026: pending 字典 TTL 清理（300秒）防止内存泄漏
- ⚡ F-029: filterURL() 调用参数修复
- ⚡ F-032: 输入过滤改用单次正则替换
- ⚡ F-034: crypto.getRandomValues 替换 Math.random
- ⚡ F-036: 移除 HTML 注释中的基础设施信息泄露
- ⚡ F-037: 合并双 WebSocket 客户端（app.js → client.js）
- ⚡ F-040: PBKDF2 迭代次数可配置化（默认 210000，OWASP 2024）
- ⚡ F-047: JWT token 缓存读写补全（TTLCache 生效）

**P3 代码质量修复 (8项)**
- 🧹 F-041~F-043: 重复注释/日志变量/空消息错误修复
- 🧹 F-044/F-045: ShardedDataStore 真正数据分片 + 安全 __len__
- 🧹 F-046: 废弃 ToolInfo/ToolRegistry 标记 DeprecationWarning
- 🧹 F-048: start_server.py 添加健康检查 HTTP 服务 (:8080/health)

### 架构变更

- `server.py`: 新增认证流程（首消息 token 验证）、backend_secret、pending TTL 清理循环
- `start_server.py`: 启动时同时启动 WebSocket (:8765) 和 HTTP 健康检查 (:8080)
- `auth_jwt.py`: token 验证结果缓存生效，减少重复验签开销
- `auth_hash.py`: PBKDF2 迭代次数支持配置文件覆盖
- `sharded_lock.py`: ShardedDataStore 数据真正按分片存储，减少跨分片竞争
- 前端: 合并双 WebSocket 客户端，统一使用 client.js 版本

### 测试

- ✅ 73 单元/集成/E2E 测试通过
- ✅ 12 跳过（需外部服务）
- ✅ 0 失败

---

## [1.0.0] - 2026-03-24

### 新增

- ✨ Phase 1: Session Manager
  - Session Manager 框架
  - 工具管理（8个工具）
  - 会话管理功能
  - 输出管理功能
  - 双向通信功能

- ✨ Phase 2: 移动端 UI
  - UI 框架（HTML/CSS/JS）
  - 工具选择界面（8个工具）
  - 会话管理界面
  - 终端界面
  - 设置界面
  - 响应式设计
  - 移动端优化

- ✨ Phase 3: 加密和离线
  - 加密模块（端到端加密）
  - QR 码模块（密钥交换）
  - IndexedDB 存储（离线支持）

- ✨ Phase 4: 优化和发布
  - 性能优化
  - 安全加固
  - Web Workers
  - Service Workers

### 优化

- ⚡ 会话创建时间: < 100ms
- ⚡ WebSocket 连接时间: < 50ms
- ⚡ 页面加载时间: < 2s
- ⚡ 内存使用: < 100MB

### 测试

- ✅ LingMinOpt 框架测试: 3/3 通过
- ✅ zhineng-bridge 优化测试: 2/2 通过
- ✅ zhineng-bridge 前端测试: 3/3 通过
- ✅ zhineng-bridge 加密测试: 2/2 通过
- ✅ 端到端测试: 2/2 通过
- ✅ 总计: 12/12 通过 (100%)

### 文档

- 📖 README.md
- 📖 API.md
- 📖 更新日志
- 📖 测试报告

### 发布

- 🚀 GitHub: https://github.com/guangda88/zhineng-bridge
- 🚀 Gitea: http://zhinenggitea.iepose.cn/guangda/zhineng-bridge

---

## [未发布]

### 计划

- 🔄 更多工具支持
- 🔄 插件系统
- 🔄 团队协作功能
- 🔄 高级分析功能

---

**更新日志版本: 1.1.0**
**最后更新: 2026-04-05**

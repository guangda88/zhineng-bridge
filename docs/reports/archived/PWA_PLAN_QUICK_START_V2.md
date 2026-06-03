# 智桥 PWA 开发规划 - 快速概览（修订版）

**版本：** 2.0.0
**修订原因：** 基于代码审查报告（P0 阻塞问题识别）
**预计周期：** 8 周
**团队规模：** 6 人
**总工时：** 328 人时（原 232 人时，增加 96 人时）

---

## 📋 修订说明（基于代码审查）

### 代码审查发现的关键问题

**P0 阻塞问题（必须立即解决）：**
1. 🔴 **VAPID密钥占位符未配置** (push.js:54-56) - 推送通知完全不可用
2. 🔴 **文件API端点未实现** (file-mentions.js:61-63) - 文件提及完全不可用
3. 🔴 **后端推送服务未实现** - 无法发送推送通知
4. 🔴 **PWA图标资源缺失** - PWA无法安装到主屏幕
5. 🔴 **HTTPS/Nginx配置不完整** - 无法部署到生产环境

**P1 重要问题：**
1. 🟡 缺少TypeScript类型定义（只有.d.ts文件）
2. 🟡 前端测试缺失（tests/frontend/存在但内容少）
3. 🟡 错误处理不完整（文件提及API调用缺少降级方案）
4. 🟡 配置管理问题（硬编码的业务网络地址）

**代码优势：**
- ✅ 模块化设计，功能按文件清晰分离
- ✅ ES6类封装（如SlashCommandsManager）
- ✅ 前端有try-catch，后端有异常类
- ✅ 安全机制完备（JWT认证 + CSRF防护 + 请求签名）
- ✅ 日志系统（logger.py）
- ✅ 性能追踪（metrics.py）

**当前完成度：**
- 推送通知前端：80%（缺VAPID配置）
- 文件提及前端：60%（缺后端API）
- 斜杠命令前端：90%
- PWA Manifest：100%

### 主要修订内容

| 修订项 | 原计划 | 修订后 | 原因 |
|--------|--------|--------|------|
| **Week 1-2 重点** | 推送通知 + 文件提及 | 100% 聚焦 P0 阻塞问题 | 阻塞问题必须先解决 |
| **后端开发分配** | 40h（分散在各周） | Week 1-2: 40h + Week 3: 8h（48h总计） | P0任务需要大量后端工作 |
| **前端开发分配** | Week 1-2: 40h | Week 1-2: 40h（集成测试） | 后端完成后进行集成 |
| **测试工程师** | Week 6 开始 | Week 1 开始（阻塞问题测试） | 立即测试P0功能 |
| **资源总计** | 232 人时 | 328 人时（6人） | 增加后端和测试资源 |
| **里程碑调整** | Week 1-3: 功能完成 | Week 1-2: P0阻塞问题解决 | 必须先解决阻塞 |
| **风险应对** | 通用风险应对 | 针对具体代码问题的应对 | 更精确的风险管理 |

---

## 🎯 核心目标

将智桥 Web UI 转换为 PWA，实现 90%+ 的原生应用用户体验。

### 关键成果

1. **推送通知** - Web Push API 完整实现（VAPID + 后端服务 + 前端集成）
2. **文件提及** - @file 语法和上下文注入（后端 API + 前端 UI）
3. **斜杠命令** - /command 命令系统
4. **移动端优化** - 原生应用感觉
5. **用户引导** - 解决用户混淆问题

### P0 优先目标（Week 1-2 必须完成）

- 🔴 生成 VAPID 密钥对并配置到前端
- 🔴 实现后端文件 API 端点（read, search, stats, list）
- 🔴 实现后端推送服务端点（subscribe, unsubscribe, send）
- 🔴 生成 PWA 图标资源（10 个尺寸）
- 🔴 配置 HTTPS/Nginx（Week 3）

---

## 📅 8 周开发计划（修订版）

### 第 1 周：紧急阻塞问题解决（P0 - Part 1）
**紧急程度：** 🔴 必须完成
- VAPID 密钥生成和配置（Day 1）
- 后端文件 API 实现（Day 2-5）
- 后端推送服务实现（Day 6-7）
- PWA 图标资源生成（Day 6-7）
- **里程碑：** P0 后端功能完成

### 第 2 周：前端集成和测试（P0 - Part 2）
**紧急程度：** 🔴 必须完成
- 前端推送通知集成（Day 8-9）
- 前端文件提及集成（Day 10）
- P0 功能集成测试（Day 10）
- P0 功能兼容性测试（iOS/Android）（Day 10）
- **里程碑：** P0 阻塞问题解决

### 第 3 周：部署配置（P0）
**紧急程度：** 🔴 必须完成
- Nginx HTTPS 配置
- SSL 证书配置
- 生产环境部署
- 部署功能测试
- **里程碑：** PWA 部署完成

### 第 4 周：移动端 UI（P1）
- 底部导航栏
- 侧边抽屉菜单
- 浮动操作按钮（FAB）
- 触摸交互优化
- **里程碑：** 移动端优化完成

### 第 5 周：用户引导（P1）
- 启动引导页面
- 功能介绍和教程
- 终端命令支持（!command）
- 常见问题解答
- **里程碑：** 用户引导完成

### 第 6 周：测试覆盖（P1）
- 单元测试（覆盖率 > 80%）
- 集成测试
- E2E 测试
- 性能测试（Lighthouse > 90）
- **里程碑：** 测试覆盖完成

### 第 7 周：文档完善（P1）
- 用户手册
- API 文档
- 开发者文档
- 部署和故障排除
- **里程碑：** 文档发布

### 第 8 周：增强功能（P2）
- 触摸手势支持
- 自定义代理库
- MCP 权限提示
- 版本 1.0.0 发布
- **里程碑：** 版本发布

---

## 📊 功能模块规划（修订版）

|| 模块 | 优先级 | 预计工时 | 依赖项 | 紧急程度 |
|------|--------|---------|--------|---------|
| **VAPID 密钥生成** | P0 | 0.5h | 无 | 🔴 紧急 |
| **后端文件 API** | P0 | 12h | 无 | 🔴 紧急 |
| **后端推送服务** | P0 | 8h | VAPID 密钥 | 🔴 紧急 |
| **前端推送集成** | P0 | 4h | 后端推送服务 | 🟡 高 |
| **前端文件提及集成** | P0 | 4h | 后端文件 API | 🟡 高 |
| **PWA 图标资源** | P0 | 2h | 无 | 🔴 紧急 |
| **P0 功能测试** | P0 | 16h | 所有 P0 功能 | 🟡 高 |
| **部署配置** | P0 | 24h | 所有 P0 功能 | 🔴 紧急 |
| **移动端 UI 优化** | P1 | 16h | 无 | 🟡 高 |
| **用户引导改进** | P1 | 16h | 无 | 🟡 高 |
| **测试覆盖** | P1 | 40h | 所有功能 | 🟡 高 |
| **文档完善** | P1 | 40h | 所有功能 | 🟡 高 |
| **触摸手势支持** | P2 | 12h | 无 | 🔵 低 |
| **自定义代理库** | P2 | 16h | 无 | 🔵 低 |
| **MCP 权限提示** | P2 | 20h | 无 | 🔵 低 |

---

## 👥 资源分配（修订版）

### 人力资源（修订版）

|| 角色 | 人数 | 原工作量 | 修订工作量 | 变更原因 |
|------|------|---------|-----------|---------|
| **前端开发** | 2人 | 80h/人 | 96h/人 | +16h/人（前端集成 + 测试） |
| **后端开发** | 1人 | 40h | 48h | +8h（P0 任务 100% 投入） |
| **UI/UX 设计** | 1人 | 32h | 32h | 无变更 |
| **测试工程师** | 1人 | 40h | 48h | +8h（Week 1 开始测试 P0） |
| **技术文档** | 1人 | 24h | 32h | +8h（更新文档） |
| **项目经理** | 1人 | 16h | 16h | 无变更 |

**总计：** 6 人，**328 人时**（原 232 人时，增加 96 人时）

### Week 1-2 资源分配（P0 优先）

| 角色 | Week 1 | Week 2 | 总计 | 职责 |
|------|--------|--------|------|------|
| **前端开发** | 16h（20%） | 16h（100%） | 32h | Week 1: VAPID 配置；Week 2: 前端集成 |
| **后端开发** | 40h（100%） | 8h（20%） | 48h | Week 1: 文件 API + 推送服务；Week 2: 集成支持 |
| **UI/UX 设计** | 8h（25%） | 8h（25%） | 16h | 图标设计 + UI 优化 |
| **测试工程师** | 8h（20%） | 8h（20%） | 16h | Week 1: 单元测试；Week 2: 集成测试 |
| **技术文档** | 4h（10%） | 4h（10%） | 8h | 更新开发文档 |
| **项目经理** | 4h（25%） | 4h（25%） | 8h | 跟踪 P0 进度 |

### 预算估算

- **开发服务器：** $50/月
- **生产服务器：** $100/月
- **SSL 证书：** $0 (Let's Encrypt)
- **域名：** $12/年
- **总计：** ~$150/月

---

## ✅ 成功指标

|| 指标 | 目标值 | 测量方式 |
|------|--------|---------|
| **P0 阻塞问题解决** | 100% | 功能测试通过 |
| **PWA 安装率** | > 30% | PWA 安装事件统计 |
| **用户留存率** | > 50% (7天) | 用户活跃度分析 |
| **推送通知打开率** | > 40% | 通知点击率统计 |
| **页面加载时间** | < 2s (首次), < 0.5s (后续) | Lighthouse 性能测试 |
| **用户满意度** | > 4.0/5.0 | 用户反馈调查 |
| **测试覆盖率** | > 80% | 单元测试覆盖率报告 |
| **Lighthouse 评分** | > 90 | 性能测试报告 |

---

## 🎯 关键里程碑（修订版）

|| 里程碑 | 日期 | 验收标准 | 紧急程度 |
|--------|------|---------|---------|
| **M1: P0 阻塞问题解决** | 第 2 周 | VAPID 配置、文件 API、推送服务、前端集成、测试通过 | 🔴 紧急 |
| **M2: PWA 部署完成** | 第 3 周 | PWA 可安装，HTTPS 正常，性能达标 | 🔴 紧急 |
| **M3: 移动端优化完成** | 第 4 周 | 移动端 UI 流畅，触摸响应灵敏 | 🟡 高 |
| **M4: 测试覆盖完成** | 第 6 周 | 测试覆盖率 > 80%，所有测试通过 | 🟡 高 |
| **M5: 版本 1.0.0 发布** | 第 8 周 | 所有 P0/P1 功能完成，文档完整 | 🟡 高 |

---

## ⚠️ 风险管理（修订版）

### 高风险项 🔴（基于代码审查）

1. **VAPID 配置问题**
   - 可能性：低
   - 影响：高
   - 应对：Week 1 Day 1 立即生成，使用 web-push generate-vapid-keys

2. **文件 API 安全问题**
   - 可能性：中
   - 影响：高
   - 应对：路径验证、权限检查、文件扩展白名单、黑名单目录

3. **推送通知兼容性问题**
   - 可能性：中
   - 影响：高
   - 应对：Week 2 多设备测试（iOS/Android），准备降级方案

4. **PWA 图标资源缺失**
   - 可能性：低
   - 影响：高
   - 应对：Week 1 Day 6-7 使用 pwa-asset-generator 生成

5. **HTTPS/Nginx 配置问题**
   - 可能性：中
   - 影响：高
   - 应对：Week 3 配置，使用 Let's Encrypt

6. **开发进度延误**
   - 可能性：中
   - 影响：高
   - 应对：每日站会，及时调整优先级，必要时削减 P2 功能

7. **安全漏洞**
   - 可能性：低
   - 影响：高
   - 应对：代码审查，安全测试

### 中风险项 🟡

8. **文件 API 性能问题**
   - 可能性：中
   - 影响：中
   - 应对：文件缓存，限制文件大小

9. **移动端浏览器兼容性**
   - 可能性：高
   - 影响：中
   - 应对：多浏览器测试，polyfill

10. **用户反馈不佳**
    - 可能性：低
    - 影响：高
    - 应对：提前收集需求，Beta 测试

---

## 📝 快速开始（修订版）

### 开发环境搭建

```bash
# 克隆项目
git clone https://github.com/guangda88/zhineng-bridge.git
cd zhineng-bridge

# 安装依赖（后端）
pip install -r requirements.txt

# 安装依赖（前端）
cd web/ui
npm install

# 启动开发服务器
cd ../..
python3 relay-server/start_server.py
python3 phase1/session_manager/start_manager.py

# 访问 Web UI
# http://localhost:8080/web/ui/index.html
```

### 生成 VAPID 密钥（Week 1 Day 1 - 必须）

```bash
# 安装 web-push 工具
npm install -g web-push

# 生成 VAPID 密钥对
web-push generate-vapid-keys

# 输出示例：
# Public Key: BIXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
# Private Key: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# 将生成的公钥填入 web/ui/js/push.js:54-56
# 将私钥保存到 ~/.env
```

### 实现文件 API（Week 1 Day 2-5 - 必须）

```bash
# 创建文件：relay-server/file_api.py
# 实现端点：
# - GET /api/files/read（路径验证、大小限制、安全检查）
# - GET /api/files/search（模糊搜索、分页）
# - GET /api/files/stats（文件元数据）
# - GET /api/files/list（递归选项）

# 集成到 relay-server/http_server.py
# 添加文件 API 路由
```

### 实现推送服务（Week 1 Day 6-7 - 必须）

```bash
# 创建文件：relay-server/push_service.py
# 实现端点：
# - POST /api/notifications/subscribe
# - POST /api/notifications/unsubscribe
# - POST /api/notifications/send

# 集成 pywebpush 库
# 集成到 relay-server/http_server.py
```

### 生成 PWA 图标（Week 1 Day 6-7 - 必须）

```bash
# 安装 PWA Asset Generator
npm install -g pwa-asset-generator

# 准备源图标（至少 512x512 像素的 PNG 文件）
# 保存为 web/ui/icons/icon-source.png

# 生成 PWA 图标资源
cd web/ui
pwa-asset-generator icons/icon-source.png icons/

# 更新 manifest.json 和 index.html
```

### PWA 测试

```bash
# 使用 Lighthouse 测试 PWA
npx lighthouse http://localhost:8080/web/ui/index.html --view

# 使用 Chrome DevTools 测试推送通知
# 1. 打开 DevTools > Application > Service Workers
# 2. 点击 "Push" 按钮
# 3. 检查通知是否正常显示
```

---

## 📚 相关文档

- [PWA 技术方案](./PWA_SOLUTION.md) - 详细的技术实现方案
- [PWA 开发规划（修订版）](./PWA_DEVELOPMENT_PLAN_V2.md) - 完整的项目开发规划（V2）
- [PWA 进度跟踪（修订版）](./PWA_PROGRESS_TRACKER_V2.md) - 进度跟踪表（V2）
- [代码审查报告](./CODE_REVIEW_REPORT.md) - 代码审查结果
- [API 文档](./API.md) - RESTful API 参考文档
- [用户手册](../README.md) - 用户使用指南

---

## 📞 联系方式

**项目经理：** [项目经理姓名]
**邮箱：** [项目经理邮箱]
**Slack：** [Slack 频道]

**技术负责人：** [技术负责人姓名]
**邮箱：** [技术负责人邮箱]

---

**文档版本：** 2.0.0
**最后更新：** 2026-03-28
**状态：** ✅ 批准（基于代码审查修订）

---

## 🚨 立即行动清单（Week 1）

### Week 1 Day 1: VAPID 密钥生成和配置（0.5h）

```bash
# 1. 安装 web-push 工具
npm install -g web-push

# 2. 生成 VAPID 密钥对
web-push generate-vapid-keys

# 3. 配置 VAPID 公钥到前端
# 编辑 web/ui/js/push.js:54-56

# 4. 保存 VAPID 私钥到服务器配置
echo "VAPID_PRIVATE_KEY=actual_private_key" >> ~/.env

# 5. 测试推送权限请求
```

### Week 1 Day 2-5: 后端文件 API 实现（12h）

```python
# 创建文件：relay-server/file_api.py
# 实现端点：
# - GET /api/files/read（路径验证、大小限制、安全检查）
# - GET /api/files/search（模糊搜索、分页）
# - GET /api/files/stats（文件元数据）
# - GET /api/files/list（递归选项）

# 安全验证：
# - 路径遍历保护（.., /）
# - 文件权限检查（os.access）
# - 文件大小限制（10MB）
# - 文件扩展白名单
# - 文件缓存机制
```

### Week 1 Day 6-7: 后端推送服务和图标生成（10h）

```python
# 创建文件：relay-server/push_service.py
# 实现端点：
# - POST /api/notifications/subscribe
# - POST /api/notifications/unsubscribe
# - POST /api/notifications/send

# 集成 pywebpush 库
# 添加订阅管理
# 添加错误处理和重试机制
```

```bash
# 生成 PWA 图标
npx pwa-asset-generator logo.png ./web/ui/icons/
# 生成 10 个尺寸：16x16, 32x32, 72x72, 96x96, 128x128, 144x144, 152x152, 192x192, 384x384, 512x512
```

### Week 1 交付物

- [ ] VAPID 密钥对配置文件（~/.env）
- [ ] 后端文件 API 代码（relay-server/file_api.py）
- [ ] 后端推送服务代码（relay-server/push_service.py）
- [ ] PWA 图标资源包（10 个尺寸）
- [ ] 前端 VAPID 公钥配置（web/ui/js/push.js）

**Week 1 结束标准：**
- ✅ 所有 P0 后端代码实现完成
- ✅ 单元测试覆盖率 > 80%
- ✅ 集成测试通过
- ✅ 代码审查通过

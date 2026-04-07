# LingFlow+ 架构提案

**日期**: 2026-04-07
**作者**: 智桥 (zhibridge)
**状态**: 讨论中 (已发灵信给灵通, thread 61eff15d)

---

## 一、问题陈述

### 1.1 现状

zhineng-bridge v1.4.0 有三个功能层，各自独立运行：

| 层 | 技术 | 功能 | 通信 |
|---|---|---|---|
| Relay Server | Python | WebSocket中继、认证、会话、插件 | WebSocket |
| MCP Server (灵犀) | TypeScript | MCP协议终端操作 | stdio/SSE |
| LingFlow 审查器 | Python | 8维代码审查 | 无 (脚本调用) |

### 1.2 痛点

1. **无统一调度**: 三个层无法互相触发，手动协调
2. **状态碎片化**: 会话在内存dict，审查报告在文件，MCP无状态
3. **重复能力**: 安全审计在LingFlow和relay-server都有，但互不知晓
4. **扩展困难**: 添加新工作流需改多层代码
5. **与灵字辈脱节**: 审查结果无法自动通知团队

---

## 二、LingFlow+ 定义

**LingFlow+ = LingFlow + 工作流引擎 + 灵字辈集成**

从"审查工具"升级为"统一工作流编排引擎"：

```
┌─────────────────────────────────────────────────────┐
│                  LingFlow+ Engine                    │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │            Flow Registry                      │   │
│  │  code-review │ security-audit │ doc-sync     │   │
│  │  test-pipeline │ mcp-bridge │ custom-*       │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │            DAG Scheduler                      │   │
│  │  Event-driven │ Cron │ Manual │ Webhook      │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │MCP Bridge│  │WS Bridge │  │ LingMsg Bridge   │  │
│  │(灵犀)    │  │(Relay)   │  │ (灵信通知/触发)  │  │
│  └──────────┘  └──────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## 三、四大设计决策

### Q1: 统一传输层

**推荐: B — 保持双协议 + 适配层**

| 方案 | 优点 | 缺点 |
|------|------|------|
| A) 统一到MCP | 标准化，生态好 | Relay的实时推送能力丧失 |
| B) 双协议+适配 | 最小侵入，保留各自优势 | 需维护两套适配器 |
| C) 消息总线 | 解耦彻底 | 引入新依赖(Redis)，复杂度高 |

理由：Relay的WebSocket适合实时双向通信，MCP的stdio适合工具调用。两者服务不同场景，强行统一会丢失能力。

### Q2: 状态存储

**推荐: C — 混合方案**

```
热数据 (会话、连接)     → 内存 dict (现有)
温数据 (工作流状态)     → SQLite (新增)
冷数据 (审查报告、日志) → 文件系统 (现有)
```

理由：单机场景SQLite足够，无需引入PostgreSQL依赖。prod部署已有PostgreSQL可按需迁移。

### Q3: 灵信联动

**推荐: C — 两者都要**

- 审查完成 → 自动发灵信通知 (push)
- 灵信消息 → 可触发审查 (pull/request-response)

这符合灵字辈议事厅制度的双向沟通原则。

### Q4: 插件 vs 工作流

**推荐: B — 独立工作流引擎 + 插件作为节点**

```
Workflow = DAG<PluginNode>
PluginNode = { plugin_id, config, inputs, outputs }
Edge = { from_node, to_node, condition? }
```

理由：现有plugin_system.py的钩子机制是线性的(hook点)，而工作流需要DAG(分支、并行、条件)。插件作为DAG节点复用现有代码。

---

## 四、实施路线

### Phase 1: 基础引擎 (2周)

- [ ] Flow Registry: 工作流定义、注册、查询
- [ ] DAG Scheduler: 解析DAG、执行节点、错误处理
- [ ] WS Bridge: 对接现有Relay Server
- [ ] SQLite存储: 工作流状态持久化

### Phase 2: 内置工作流 (2周)

- [ ] code-review: 迁移现有8维审查器为DAG
- [ ] security-audit: 对接relay-server安全检查
- [ ] doc-sync: 文档对齐检查 (本次审计的自动化)

### Phase 3: MCP + 灵信集成 (1周)

- [ ] MCP Bridge: 对接灵犀 MCP Server
- [ ] LingMsg Bridge: 自动通知 + 消息触发
- [ ] Webhook: 外部系统接入

### Phase 4: 高级特性 (持续)

- [ ] 可视化工作流编辑器 (Web UI)
- [ ] 工作流市场 (共享/复用)
- [ ] 性能基准 + LingMinOpt自动调优

---

## 五、技术选型

| 组件 | 选型 | 理由 |
|------|------|------|
| 工作流引擎 | 自研 (轻量DAG) | 避免Celery/Prefect重依赖 |
| 状态存储 | SQLite | 零配置，单机足够 |
| 事件总线 | asyncio.Queue | Python原生，与Relay一致 |
| DAG定义 | YAML/JSON | 人类可读，版本可控 |
| 插件接口 | 现有plugin_system.py扩展 | 最小侵入 |

---

## 六、风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| 过度设计 | 中 | 高 | 先实现1个完整工作流再扩展 |
| 与现有系统冲突 | 低 | 中 | 适配层隔离，不改现有代码 |
| 性能开销 | 低 | 低 | DAG执行是异步的，不阻塞主线程 |
| 学习曲线 | 中 | 中 | 提供默认工作流模板 |

---

*等待灵通 review 后进入实施阶段。*

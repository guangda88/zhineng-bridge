# 智桥测试审计报告

> **日期**: 2026-04-05  
> **提交**: `5d22023` (审计修复) → 当前工作目录  
> **报告人**: AI 工程审计  
> **提请**: 议事厅讨论  

---

## 一、审计背景

广大老师在代码审查中发现测试套件存在 **42 个跳过测试**，指出"42 skipped 这么多？"并要求修复。

经过逐项排查，发现根本原因是：大量测试**连接外部生产服务器**（`ws://localhost:8765`）而非自托管测试服务器。生产服务器启用 WSS（SSL），测试代码使用 `ws://` 明文协议，永远无法握手成功。

更深层次的问题是 `test_websocket.py` 和 `test_benchmark.py` 测试的是**不存在的协议消息**（`start_session`、`stop_session`、`list_sessions`、`delete_session`），而真实服务器只支持 `ping`、`register_backend`、`chat`、`reply`、`push`、`switch_backend`、`list_backends`。

---

## 二、已完成的修复

### 2.1 重写 `test_websocket.py`（17 → 22 个测试）

| 项目 | 修复前 | 修复后 |
|------|--------|--------|
| 服务器 | 连接 `ws://localhost:8765`（生产 WSS） | 自托管 `AIRelayServer`（随机端口） |
| 协议 | 假协议：`start_session`/`session_started` 等 | 真实协议：`ping`/`chat`/`reply`/`push` 等 |
| 测试数 | 17 个（全部跳过） | 22 个（全部通过） |

新增测试覆盖：
- `test_register_backend_missing_id` — 缺少 backend_id 的错误处理
- `test_list_backends_empty` — 空后端列表
- `test_chat_empty_text_ignored` — 空文本消息被忽略
- `test_push_broadcast` — 广播推送
- `test_push_targeted` — 定向推送
- `test_backend_disconnect_cleanup` — 断开后自动清理
- `test_concurrent_connections` — 10 个并发客户端
- `test_concurrent_chat_flood` — 20 个并发聊天消息

### 2.2 重写 `test_benchmark.py`（14 → 12 个测试）

| 项目 | 修复前 | 修复后 |
|------|--------|--------|
| 服务器 | 连接 `ws://localhost:8765`（生产 WSS） | 自托管 `AIRelayServer`（随机端口） |
| 协议 | 假协议：`start_session`/`list_sessions` | 真实协议：`ping`/`chat`/`register_backend` |
| 依赖 | `memory_profiler`（未安装）、`pytest-benchmark` | 无外部依赖，纯 `time.monotonic()` 计时 |
| 测试数 | 14 个（全部跳过） | 12 个（全部通过） |

性能基准分组：

| 分组 | 测试 | 指标 |
|------|------|------|
| 连接性能 | 连接+ping 耗时、纯连接耗时 | < 500ms / < 200ms |
| Ping 延迟 | 50 次 RTT、100 次吞吐量 | < 50ms avg / > 100 msg/s |
| 路由延迟 | chat→reply 20 次往返 | < 200ms avg |
| 注册速度 | 10 次后端注册 | < 200ms avg |
| 并发性能 | 20 并发 ping、10 并发 chat | < 5s 总耗时 |
| 压力测试 | 200 高频 ping、20 次快速注册/断开 | > 50 msg/s |

### 2.3 清理 lingflow 测试

移除了 `test_zhineng_bridge_lingflow.py` 和 `test_zhineng_bridge_scenarios.py` 中的 `requires_ws` 装饰器（该装饰器在模块加载时同步连接 WS 服务器，会拖慢整个测试启动）。

改为显式 `@pytest.mark.skip(reason="...")`，因为这两组测试存在更深层的协议不匹配问题（详见第三节）。

---

## 三、剩余 12 个跳过测试详情

### 3.1 Chrome DevTools MCP — 4 个跳过

**跳过原因**: Node.js 版本不满足（当前 v18.19.1，需 v20.19.0+）

| 测试 | 实际内容 |
|------|----------|
| `test_setup_instructions` | 打印环境搭建说明字符串 |
| `test_mcp_tool_instructions` | 打印 MCP 工具使用指令 |
| `test_manual_test_checklist` | 打印手动测试检查清单 |
| `test_playwright_setup_instructions` | 打印 Playwright 安装说明 |

**评估**: 这 4 个测试**没有实际断言**，只是 `print()` 或 `pass`。即使升级 Node.js，它们也不会检测到任何 bug。同文件中的 `TestWebUIBasic`（5 个测试）正常通过。

### 3.2 lingflow E2E — 5 个跳过 (`test_zhineng_bridge_lingflow.py`)

**跳过原因**: 生产 WS 服务器使用 WSS（SSL），`ws://` 客户端无法握手；且测试代码使用假协议

| 测试 | 实际行为 |
|------|----------|
| `test_websocket_connection_scenario` | 连接 `ws://localhost:8765` → 失败 |
| `test_session_creation_scenario` | 发送 `start_session` → 服务器不识别 |
| `test_session_listing_scenario` | 发送 `list_sessions` → 服务器不识别 |
| `test_message_exchange_scenario` | 发送 `ping` → 连接失败 |
| `test_comprehensive_e2e_scenario` | 串联以上 4 步 → 全部失败 |

**双重问题**:
1. **连接层**: `websockets.connect("ws://localhost:8765")` 连接 WSS 服务器，握手失败
2. **协议层**: `ZhinengBridgeTestTool` 使用 `start_session`/`list_sessions` 等不存在的消息类型

### 3.3 lingflow 场景测试 — 3 个跳过 (`test_zhineng_bridge_scenarios.py`)

**跳过原因**: lingflow 场景运行器工具注册不匹配

| 测试 | 实际行为 |
|------|----------|
| `test_full_workflow_scenario` | `AIScenarioRunner` 报 "缺少必需工具: websocket_connect" |
| `test_performance_scenario` | 类似问题 |
| `test_batch_scenarios` | 批量运行，1 个失败导致断言失败 |

**注意**: 这 3 个测试能成功导入 lingflow 框架（`HAS_LINGFLOW=True`），但运行时 `AIScenarioRunner` 无法匹配场景定义与工具注册表。需要深入理解 lingflow 的场景运行机制才能修复。

---

## 四、修复方案对比

### 方案 A：保持现状（推荐）

**做法**: 12 个跳过测试维持现状，73 个通过的测试已覆盖核心功能。

**理由**:
- 73 个通过的测试完整覆盖了 `AIRelayServer` 的全部消息类型和 `SessionManager` 的完整生命周期
- 12 个跳过测试中，4 个无实际断言，8 个依赖 lingflow 框架的深层集成
- 修复 lingflow 测试需要深入框架内部，投入产出比不高

**跳过分类**:

| 类别 | 数量 | 性质 | 影响 |
|------|------|------|------|
| Chrome DevTools MCP | 4 | 无断言的文档输出 | 零影响 |
| lingflow E2E | 5 | 假协议 + WSS 不兼容 | 协议已由其他测试覆盖 |
| lingflow 场景 | 3 | 场景运行器不匹配 | 需研究 lingflow 内部机制 |

### 方案 B：重写 lingflow 测试

**做法**: 将 8 个 lingflow 测试重写为自托管服务器 + 真实协议，与 `test_websocket.py` 同模式。

**工作量**: 中等（约 2-3 小时），需要：
1. 为 lingflow 测试类添加 `relay_server` fixture
2. 重写 `ZhinengBridgeTestTool` 使用真实协议
3. 重写 `test_zhineng_bridge_scenarios.py` 的工具注册逻辑
4. 需要理解 `CodeTestScenario`、`AIScenarioRunner` 的工具发现机制

**风险**: lingflow 框架的 `AIScenarioRunner` 可能有自己的工具发现和调用机制，与直接 WebSocket 测试不同。强行改造可能引入脆弱的测试。

### 方案 C：删除无效测试文件

**做法**: 删除 4 个 Chrome DevTools 无断言测试方法，对 8 个 lingflow 测试标记 `@pytest.mark.xfail` 并添加注释说明。

**效果**: 跳过数从 12 减少到 8（或 0，取决于处理方式）。

### 方案 D：升级环境

**做法**: 升级 Node.js 到 v20+，使 Chrome DevTools 测试可以运行（但它们仍然没有断言）。

**效果**: 减少约 4 个跳过，但投入较大且无实际质量提升。

---

## 五、当前测试覆盖总览

```
================= 73 passed, 12 skipped, 0 failed ==================

通过的 73 个测试:
├── 单元测试 (15) — AIRelayServer._dispatch 全路径
│   ├── init、register_backend (正常/缺 ID)
│   ├── list_backends、chat_routes_to_backend
│   ├── chat_no_backend_returns_error
│   ├── reply_forwards_to_user、switch_backend
│   ├── ping、unknown_message_type_returns_error
│   ├── cleanup_on_user_disconnect、stop
│
├── 集成测试 (17) — SessionManager 完整生命周期
│   ├── init、list_tools、get_tool_info
│   ├── create_session (正常/无效工具/多个)
│   ├── get_session (正常/不存在)
│   ├── list_sessions、get/set_active_session
│   ├── Session 类 (init/to_dict)
│   └── full_workflow、multiple_managers_isolation
│
├── E2E 协议测试 (22) — test_websocket.py
│   ├── ping/pong、invalid_json、unknown_type
│   ├── register_backend (正常/缺 ID)
│   ├── list_backends (有后端/空)
│   ├── chat 路由、chat→reply 往返
│   ├── chat 无后端错误、chat 空文本忽略
│   ├── switch_backend、push 广播、push 定向
│   ├── backend 断开清理、多消息序列
│   └── 并发连接 (10)、压力测试 (50 msg + 20 并发 chat)
│
├── E2E 中继测试 (9) — test_relay_e2e.py
│   └── ping_pong、register+list、chat 路由
│       reply 往返、switch、unknown、invalid_json
│       chat 无后端、backend 断开、多并发 chat
│
├── 性能基准 (10) — test_benchmark.py
│   └── 连接耗时 (10+20次)、ping 延迟 (50次)
│       批量吞吐 (100次)、chat 往返 (20次)
│       注册速度 (10次)、并发 ping (20)
│       并发 chat (10)、高频 ping (200)
│       快速注册断开 (20次)
│
└── Web UI 基础 (5) — test_chrome_devtools_mcp.py::TestWebUIBasic
    └── 文件存在、必需元素、WS 配置
        server.py 存在、config.py 存在

跳过的 12 个测试:
├── Chrome DevTools MCP (4) — Node.js v18 < v20 要求
├── lingflow E2E (5) — 假协议 + WSS 不兼容
└── lingflow 场景 (3) — 场景运行器工具注册不匹配
```

---

## 六、待议事厅决议

1. **是否采用方案 A（保持 12 个跳过）？** 这是最务实的方案，73 个通过的测试已充分覆盖核心功能。

2. **是否重写 lingflow 测试（方案 B）？** 需要投入约 2-3 小时，且 lingflow 场景测试的核心价值是框架集成而非协议测试——后者已被完整覆盖。

3. **是否删除 4 个无断言的 Chrome DevTools 测试方法？** 它们本质上只是文档字符串，没有测试价值。

4. **是否需要为 lingflow 测试添加自托管服务器？** 当前 lingflow 测试连接生产服务器，即使修复协议也无法在没有生产环境的情况下运行。

---

*报告完毕，请议事厅审议。*

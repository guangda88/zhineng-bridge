# 智桥 (Zhineng-Bridge) 系统审计报告

**审计日期:** 2026-04-05  
**审计范围:** 全栈代码、架构、安全、测试、配置、部署  
**代码规模:** ~22,838行 Python, ~8,501行 JS, ~7,575行 HTML, ~1,872行 CSS  
**审计人:** 智桥 (zhineng-bridge)

---

## 一、审计总结

| 类别 | 评级 | 说明 |
|------|------|------|
| 代码质量 | ⭐⭐⭐☆☆ | 核心模块结构清晰，但存在命名不一致、死代码、重复实现 |
| 安全性 | ⭐⭐☆☆☆ | 认证系统有多个严重缺陷，敏感信息保护不足 |
| 架构设计 | ⭐⭐⭐☆☆ | 整体合理，但服务器实现重复、职责划分不清 |
| 测试覆盖 | ⭐⭐☆☆☆ | 64个测试无法运行（ImportError），E2E/性能测试依赖在线服务 |
| 部署配置 | ⭐⭐⭐☆☆ | Docker配置完善，但存在生产安全隐患 |
| 文档 | ⭐⭐☆☆☆ | 60+根目录Markdown文件，大量过时/重复内容 |

---

## 二、严重问题 (P0 - 必须立即修复)

### P0-1: 启动入口 ImportError — 服务器无法启动

**文件:** `relay-server/start_server.py`  
**影响:** 生产阻塞 — 服务器启动即失败

```python
# start_server.py 实际代码:
from server import CrushRelayServer  # ❌ 不存在

# server.py 实际定义:
class AIRelayServer:                  # ✅ 正确的类名
```

**原因:** 类名从 `CrushRelayServer` 重命名为 `AIRelayServer`，但入口文件未同步更新。

**同样影响测试:** `tests/unit/test_relay_server.py:16` 也导入 `CrushRelayServer`，导致 **全部64个测试无法收集**。

**修复方案:**
```python
# start_server.py
from server import AIRelayServer
# 同时更新所有引用处
```

---

### P0-2: JWT Token 实际为一次性使用 — 严重认证缺陷

**文件:** `relay-server/auth_jwt.py`  
**影响:** 用户登录后发送第二个请求即被拒绝（token被视为重放攻击）

**根因:** `validate_token()` 将每个已验证的 JTI 记入 `_used_tokens` 集合。第二次使用同一 JWT 时，即使未过期，也会被判定为重放攻击而拒绝。

```python
# auth_jwt.py validate_token() 逻辑：
jti = payload.get("jti")
if jti in self._used_tokens:    # 第二次使用时必然命中
    raise SecurityError("Token replay detected")  # ❌ 错误拒绝
self._used_tokens[jti] = now    # 每次验证都记录
```

**应改为:** `_used_tokens` 应仅记录已主动撤销的 JTI，而非所有已见过的 JTI。

---

### P0-3: 服务器重启丢失所有会话

**文件:** `relay-server/auth_manager.py`  
**影响:** 服务器重启后，所有未过期 JWT 均被拒绝

**根因:** `AuthenticationManager.validate_token()` 检查内存中的 `_sessions` 字典。重启后字典为空，所有合法 token 失效。

```python
# auth_manager.py
self._sessions: Dict[str, SessionInfo] = {}  # 纯内存，无持久化
```

尽管数据库中有 `sessions` 表，但代码从未从 DB 加载会话。

---

### P0-4: OAuth2 回调缺少 CSRF 保护

**文件:** `relay-server/oauth2.py`  
**影响:** 攻击者可伪造 OAuth2 回调，绑定受害者账号到攻击者的外部身份

**根因:** `get_authorization_url()` 生成 `state` 参数但它是可选的。`handle_oauth2_callback()` 从不验证 `state`。

```python
def handle_oauth2_callback(self, provider, code, state=None):
    # state 参数被忽略，不验证 ❌
    user_info = await provider.get_user_info(token_data["access_token"])
```

---

### P0-5: Web UI 硬编码 WebSocket 地址

**文件:** `web/ui/js/app.js`  
**影响:** 生产环境无法连接

```javascript
const wsUrl = 'ws://localhost:8765';  // ❌ 硬编码
```

应从配置或当前页面 URL 动态生成。

---

## 三、高危问题 (P1 - 尽快修复)

### P1-1: 双服务器实现并存，职责不清

| 文件 | 类名 | 用途 | 行数 |
|------|------|------|------|
| `server.py` | `AIRelayServer` | WebSocket中继（生产用） | ~580 |
| `chat_server.py` | `ChatRelayServer` | 关键词匹配聊天（非LLM） | 296 |
| `health_check.py` | `HealthCheckHandler` | 健康检查+文件API+推送 | 1069 |

- `chat_server.py` 使用硬编码关键词回复，不连接任何 LLM
- `health_check.py` 1069行，承担了健康检查、文件API、推送服务、OpenAPI文档四种职责
- 三个HTTP服务端口：8000(aiohttp)、8080(stdlib http)、8765(WebSocket)

**建议:** 明确弃用 `chat_server.py`，拆分 `health_check.py` 职责。

### P1-2: Session Manager 仅为原型实现

**文件:** `phase1/session_manager/session_manager.py`  
**现状:**
- 会话是纯内存字典，无子进程管理
- `start_session()` 不启动任何进程，仅创建元数据
- `stop_session()` 不终止任何进程
- 8个AI工具（crush/claude/cursor等）均无实际执行路径

```python
def create_session(self, tool_name, args=None):
    session_id = str(uuid.uuid4())
    session = {"session_id": session_id, "tool_name": tool_name, ...}
    self.sessions[session_id] = session  # 仅存字典
    return session_id
```

### P1-3: OAuth2 用户查询始终返回 None

**文件:** `relay-server/oauth2.py:390`

```python
def get_user(self, user_id=None, username=None):
    return None  # ❌ 永远返回None，每次OAuth登录都创建新用户
```

**影响:** 同一 GitHub/Google 账号每次登录都会创建重复用户记录。

### P1-4: 配置硬编码IP地址

**文件:** `relay-server/config.py`

```python
ws_host: str = "100.66.1.8"     # ❌ 内网IP
ws_hosts: List[str] = ["100.66.1.8", "100.66.1.9"]  # ❌ 多IP硬编码
```

### P1-5: 请求签名默认密钥

**文件:** `relay-server/request_signing.py:66`

```python
signing_key = settings.security.secret_key or "default-request-signing-key"
```

若未配置 `secret_key`，所有实例共享同一签名密钥。

---

## 四、中等问题 (P2 - 计划修复)

### P2-1: 认证子系统缺陷汇总

| 问题 | 文件 | 说明 |
|------|------|------|
| Token缓存未使用 | `auth_jwt.py:62` | `_token_cache` 定义后从未读写 |
| 缓存键碰撞风险 | `auth_manager.py:260` | 缓存键仅用token前16字符 |
| OAuth2类型错误 | `oauth2.py:302` | `picture_url` vs `avatar_url` 属性名不一致 |
| SQLite绕过连接池 | `auth_manager.py:162,189` | 直接 `sqlite3.connect()` 绕过连接池 |
| 会话token明文存储 | `auth_db.py` | OAuth token和session token数据库明文 |
| 数据序列化注入 | `request_signing.py:98` | 值未URL编码，可注入额外参数 |

### P2-2: 代码质量问题

| 问题 | 文件 | 说明 |
|------|------|------|
| 裸except吞异常 | `auth_db.py:63,118-123` | 连接池中 `except:` 吞掉所有异常 |
| ShardedLock进程不一致 | `sharded_lock.py` | `hash()` 在不同进程返回不同值 |
| OAuth2 httpx连接不复用 | `oauth2.py` | 每次调用创建新 `AsyncClient` |
| imports在函数体内 | `auth_jwt.py` | `base64`, `secrets` 在方法内导入 |

### P2-3: Docker/部署问题

| 问题 | 文件 | 说明 |
|------|------|------|
| 容器以root运行 | `Dockerfile` | 无 `USER` 指令 |
| gcc残留 | `Dockerfile` | 构建后未移除，增加攻击面 |
| 数据库端口暴露 | `docker-compose.prod.yml` | PostgreSQL(5439)、Redis(6379)暴露到宿主机 |
| Prometheus/Grafana无认证 | `docker-compose.prod.yml` | 端口9090/3000直接暴露 |
| Grafana默认admin | `docker-compose.prod.yml` | 未强制修改默认密码 |

### P2-4: CI/CD 管道问题

| 问题 | 文件 | 说明 |
|------|------|------|
| Lint失败被静默忽略 | `ci.yml` | `\|\| echo "..."` 导致lint永不阻塞 |
| Coverage配置位置错误 | `pytest.ini` | coverage配置段放在pytest.ini中无效 |
| 过时的Action版本 | `.github/workflows/ci.yml` | upload-artifact@v3 应升级到v4 |

### P2-5: 文档膨胀

根目录包含 **60+ Markdown文件**，大量为自动生成的审计/分析报告。包括但不限于：
- `AUTO_FIX_PROGRESS_REPORT.md`
- `CHROME_DEVTOOLS_MCP_README.md`
- `CI_CD_README.md`
- `CODE_COVERAGE_ANALYSIS.md`
- 等等...

**建议:** 归档到 `docs/reports/` 目录，根目录仅保留 `README.md` 和 `CHANGELOG.md`。

---

## 五、低优先级 (P3 - 可选优化)

### P3-1: 前端代码
- `client.js` 和 `app.js` 全局状态通过 `window` 对象管理，无模块化
- 无前端构建工具（无 package.json），所有JS直接引入
- CSS文件拆分合理但缺乏CSS Modules或CSS-in-JS

### P3-2: 测试改进
- 单元测试 (17个) 质量尚可，但因 ImportError 全部无法运行
- 集成测试 (18个) 可独立运行，但只测 SessionManager
- E2E测试 (17个) 和性能测试 (12个) 需要在线服务器才能运行
- 测试覆盖率：无法测量（pytest 收集阶段就失败了）

### P3-3: 依赖管理
- 无 `requirements.txt` 或 `pyproject.toml`
- 依赖仅在 Dockerfile 中通过 `pip install` 列出
- 前端无 `package.json`

---

## 六、架构评估

### 整体架构

```
浏览器 ──WebSocket──> 智桥(AIRelayServer:8765) ──WebSocket──> AI后端
    │                        │
    │                        ├── 健康检查(:8080, stdlib http)
    │                        ├── HTTP API(:8000, aiohttp)
    │                        └── Session Manager(内存字典)
    │
    └── 静态文件(:8000/web/ui/)
```

### 架构优势
1. **消息模型规范** — Pydantic模型定义完整，WebSocket协议清晰
2. **配置分层** — Pydantic Settings + 环境变量 + .env 支持
3. **可观测性基础好** — structlog + Prometheus metrics + health checks
4. **安全模块齐全** — 限流、签名、SSL、JWT、OAuth2（虽然实现有bug）
5. **Docker化完备** — 开发/生产两套 compose 配置

### 架构劣势
1. **三套HTTP服务** — 职责重叠，端口管理混乱
2. **认证系统复杂但破损** — JWT一次性使用、OAuth2用户查不到、会话不持久
3. **Session Manager空壳** — 核心功能（AI工具进程管理）未实现
4. **无依赖管理** — 缺少 requirements.txt/pyproject.toml

---

## 七、修复优先级路线图

### 第一阶段：紧急修复 (1-2天)
1. **修复 `CrushRelayServer` → `AIRelayServer` 导入**（start_server.py + tests）
2. **修复 JWT 重放检测逻辑**（仅记录已撤销的JTI，不记录所有已验证的）
3. **添加会话持久化**（从DB加载会话到内存，或在validate_token中跳过内存检查）
4. **动态生成 WebSocket URL**（从当前页面URL推导，不硬编码localhost）

### 第二阶段：高优先级修复 (1周)
5. **添加 OAuth2 state 验证**
6. **修复 OAuth2 用户查询**（实现 `get_user()` 或使用 `auth_db.py`）
7. **移除硬编码IP**（改为环境变量或配置文件）
8. **清理默认签名密钥**（配置缺失时抛异常而非使用默认值）

### 第三阶段：架构优化 (2-4周)
9. **弃用 `chat_server.py`**，明确 `server.py` 为唯一服务实现
10. **拆分 `health_check.py`**（健康检查、文件API、推送服务分离）
11. **实现 Session Manager 真实进程管理**（subprocess + 输出捕获）
12. **添加 `pyproject.toml`** 依赖管理
13. **归档根目录 Markdown 文件**到 `docs/reports/`

### 第四阶段：持续改进
14. **修复CI管道**（lint失败应阻塞、coverage配置迁移）
15. **Docker安全加固**（非root用户、移除gcc、限制端口暴露）
16. **前端模块化**（引入构建工具或ES Modules）

---

## 八、测试结果

```
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.0.2
collected 64 items / 1 error

ERROR tests/unit/test_relay_server.py — ImportError: cannot import name 'CrushRelayServer'
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
```

**64个测试全部无法运行。** ImportError 导致 pytest 收集阶段中断。

若修复导入后，预计：
- 单元测试 (17个) ✅ 应通过（基于AsyncMock，无外部依赖）
- 集成测试 (18个) ✅ 应通过（仅测SessionManager）
- E2E测试 (17个) ⚠️ 需要在线服务器（否则skip）
- 性能测试 (12个) ⚠️ 需要在线服务器 + memory_profiler

---

## 九、文件统计

| 模块 | 文件数 | 代码行 | 关键发现 |
|------|--------|--------|----------|
| relay-server/ | 20+ | ~8,000 | 核心服务，5个P0/P1问题 |
| phase1/ | 4 | ~400 | Session Manager仅为原型 |
| phase3/ | 4 | ~1,200 | 加密/存储，未集成到主流程 |
| phase4/ | 6 | ~1,500 | 性能优化/监控，独立运行 |
| web/ui/ | 12+ | ~10,000 | 前端，硬编码WS地址 |
| tests/ | 8 | ~1,500 | 因导入错误全部无法运行 |
| 配置/部署 | 10+ | ~800 | Docker完善但有安全隐患 |
| 根目录文档 | 60+ | ~30,000 | 大量过时报告需归档 |

---

**审计完成时间:** 2026-04-05  
**下一步:** 提交至议事厅讨论修复方案

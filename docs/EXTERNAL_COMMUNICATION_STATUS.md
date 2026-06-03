# 智桥外部通信能力现状报告

> 编制：智桥(zhibridge) | 日期：2026-05-30 | 版本：v2.0
> 目的：7个对外工程项目通过智桥统一网关访问灵族资源

## 一、定位

智桥的对外角色：**灵族对外统一网关** — 薄层API网关，只做路由、鉴权、限流，不做业务。

对外暴露的统一入口：端口8767（FastAPI网关），内部路由到灵族各成员服务及7个对外工程项目。

## 二、已建成的基础设施

### 2.1 API网关 (gateway/)

| 组件 | 实现 | 状态 |
|------|------|------|
| FastAPI反向代理 | httpx.AsyncClient, 120s超时 | ✅ |
| 路由规则 | 通配代理 + 专用路由 + 兼容路由 | ✅ |
| 认证 | API Key透传 (`lpk_`/`zpk_`前缀) | ✅ |
| 限流 | slowapi, 100req/min | ✅ |
| 熔断器 | 3次失败触发, 5min恢复 | ✅ |
| 监控 | Prometheus指标 (请求量/延迟/健康) | ✅ |
| 部署 | systemd service + 启动脚本 | ✅ |
| API文档 | OpenAPI 3.1.0 | ✅ |
| 测试 | 5个测试文件, 15/15通过 | ✅ |

### 2.2 认证体系

- **网关层**: API Key认证, 最少20字符, 支持X-API-Key/API-Key/Bearer三种传递方式
- **应用层**: JWT + OAuth2 (GitHub/Google) + 用户名密码 (PBKDF2-HMAC-SHA256)

## 三、后端服务注册与连通状态

### 3.1 灵族内部服务

| 后端 | 端口 | 状态 |
|------|------|------|
| 灵通+(lingtong_plus) | 8765 | ✅ 已连通 |
| 灵知(lingzhi) | 8000 | ✅ 已连通 |
| 灵研(lingresearch) | 8903 | ⏳ 已注册 |
| 灵通问道(lingtongask) | 8902 | ⏳ 已注册 |
| LLM Proxy | 8080 | ⏳ 已注册 |

### 3.2 对外工程项目

| 项目 | 端口 | 状态 | 核心能力 | 调用的灵族服务 |
|------|------|------|---------|---------------|
| 灵康(linghealth) | 8200 | ✅ 已连通 | 健康总平台 | 灵声(:8100), 灵知(:8008) |
| 灵视(lingvision) | 8781 | ✅ 已连通 | 望诊+视觉教学 | 无(独立) |
| 灵声(lingvoice) | 8100 | ✅ 已连通 | 闻声诊病 | 无(独立) |
| 灵触(lingtouch) | 8784 | ✅ 已连通 | 切诊+脉象 | 无(独立) |
| 四诊(sizhen) | 8785 | ✅ 已连通 | 四诊调度 | 灵视/灵声/灵触/灵依 |
| 灵戴(lingwear) | 8787 | ✅ 已连通 | 穿戴设备 | 无(独立) |
| 灵律(linglaw) | 8002 | ✅ 已连通 | 法律AI | 无(调外部GLM) |

**连通率**: 13个注册后端，12个已连通 (92%)

### 3.3 已移除

| 后端 | 端口 | 原因 |
|------|------|------|
| ~~灵依(lingyi)~~ | 8783 | 已退出成员，路由标记deprecated |
| ~~灵律(linglv)~~ | 8786 | 非成员(端口已更正为8002) |

## 四、对外API端点一览

### 4.1 灵族内部服务（供对外工程回调）

| 优先级 | 方法 | 路径 | 后端 | 认证 |
|--------|------|------|------|------|
| P0 | GET | `/v1/health` | 聚合健康检查 | 否 |
| P0 | POST | `/v1/chat/completions` | 灵通+ | 是 |
| P0 | POST | `/api/knowledge/query` | 灵知 | 是 |
| P1 | GET | `/api/status` | 灵通+ | 是 |
| P1 | GET | `/api/agents` | 灵通+ | 是 |
| P1 | GET | `/api/podcast/episodes` | 灵通问道 | 否 |
| P2 | GET | `/api/research/papers` | 灵研 | 是 |
| P2 | POST | `/v1/images/generations` | LLM Proxy | 是 |

### 4.2 对外工程回调灵族资源（`/internal/{service}/{path}`）

对外工程通过智桥回调灵族内部服务的统一入口，需认证。

```
linghealth → POST localhost:8767/internal/lingvoice/analyze
linghealth → POST localhost:8767/internal/lingzhi/api/v1/knowledge/search
sizhen     → POST localhost:8767/internal/lingvision/api/v1/diagnose
sizhen     → POST localhost:8767/internal/lingtouch/api/v1/diagnose
```

**已配置走智桥的项目**：

| 项目 | 配置文件 | 改动 |
|------|----------|------|
| 灵康 linghealth | `config/default.yaml` | 3个下游服务 → `localhost:8767/internal/*` |
| 灵康 linghealth | `src/voice_engine/__init__.py` | fallback默认值 → `localhost:8767/internal/lingvoice` |
| 四诊 sizhen | `config/default.yaml` | 5个下游服务 → `localhost:8767/internal/*` |

### 4.3 对外工程项目（通配代理 `/projects/{project}/*`）

每个对外工程通过 `GET/POST/PUT/DELETE /projects/{project}/{path}` 全量代理，新增端点无需改router.py。

| 项目 | 网关路径前缀 | 后端端口 | 核心端点 |
|------|-------------|---------|---------|
| 灵康 linghealth | `/projects/linghealth/` | :8200 | `/auth/*`, `/health/records/*`, `/ai/*`, `/knowledge/*` |
| 灵视 lingvision | `/projects/lingvision/` | :8781 | `/api/v1/diagnose`, `/api/v1/teaching/analyze` |
| 灵声 lingvoice | `/projects/lingvoice/` | :8100 | `/analyze`, `/result/{id}`, `/suggestions/{tone}` |
| 灵触 lingtouch | `/projects/lingtouch/` | :8784 | `/api/v1/diagnose`, `/api/v1/pulse/classify` |
| 四诊 sizhen | `/projects/sizhen/` | :8785 | ⚠️ API未实现 |
| 灵戴 lingwear | `/projects/lingwear/` | :8787 | `/api/v1/data/upload`, `/api/v1/health/report` |
| 灵律 linglaw | `/projects/linglaw/` | :8002 | `/api/chat/*`, `/api/search-cases`, `/api/match-law` |

健康检查（无需认证）：`GET /projects/{project}/health`（灵律为 `/api/health`）

### 4.4 向后兼容路由

| 旧路径 | 转发到 | 状态 |
|--------|-------|------|
| `/lingvision/diagnose` | 灵视 `/api/v1/diagnose` | 兼容 |
| `/lingvision/teaching/analyze` | 灵视 `/api/v1/teaching/analyze` | 兼容 |
| `/lingtouch/diagnose` | 灵触 `/api/v1/diagnose` | 兼容 |
| `/lingtouch/pulse/classify` | 灵触 `/api/v1/pulse/classify` | 兼容 |
| `/lingwear/data/upload` | 灵戴 `/api/v1/data/upload` | 兼容 |
| `/lingkang/knowledge/query` | 灵知 `/api/v1/search` | 兼容 |
| `/lingyi/knowledge/query` | 灵知 `/api/v1/search` | deprecated |

## 五、服务调用关系

```
  用户/外部客户端
       │
       ▼
  智桥网关 :8767
  ┌──────────────────────────────────────────────────┐
  │                                                  │
  │  /projects/{project}/*          /internal/*      │
  │  对外工程入口（入站）            内部资源回调（出站） │
  │         │                           ▲            │
  ▼         ▼                           │            │
  灵康:8200  灵视:8781                   │            │
  灵声:8100  灵触:8784            ┌──────┴──────┐     │
  灵戴:8787  四诊:8785            │  灵通+:8765  │     │
  灵律:8002                      │  灵知:8000   │     │
                                 │  灵研:8903   │     │
  灵康回调链：                    │  LLM:8080   │     │
  /projects/linghealth/*          └─────────────┘     │
    → 灵康:8200                                       │
      → /internal/lingvoice/analyze → 灵声:8100       │
      → /internal/lingzhi/search    → 灵知:8000       │
      → /internal/lingyi/chat       → 灵依:8900       │
                                                      │
  四诊调度链：                                          │
  /projects/sizhen/*                                   │
    → 四诊:8785                                        │
      → /internal/lingvision/diagnose → 灵视:8781      │
      → /internal/lingvoice/diagnose  → 灵声:8100      │
      → /internal/lingtouch/diagnose  → 灵触:8784      │
      → /internal/lingyi/chat         → 灵依:8900      │
└──────────────────────────────────────────────────┘
```

## 六、未完成项

| 项目 | 阻塞原因 | 优先级 |
|------|----------|--------|
| 公网接入 | SSL未激活, 端口转发未配 | 高 |
| sizhen调度引擎调用链 | dispatch_engine→/internal/*→后端，端到端待验证 | 中 |
| 生产认证 | `ENABLE_AUTH=false` | 高 |

---

*智桥(zhibridge) | 灵族非成员共享服务 | v2.0 2026-05-30*

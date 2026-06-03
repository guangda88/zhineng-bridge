# 智桥 (zhibridge)

> 灵族对外统一API网关 — 薄层路由、鉴权、限流

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 项目简介

**智桥** 是灵族的对外统一API网关，为7个对外工程（灵康、灵视、灵声、灵触、四诊、灵戴、灵律）和5个内部服务（灵通+、灵知、灵通问道、灵研、LLM Proxy）提供统一入口。

**核心职责**：路由、鉴权、限流、熔断 — 不做业务逻辑。

## 快速启动

```bash
# 安装依赖
pip install -r requirements.txt

# 启动网关
bash gateway/gateway.sh start

# 验证
curl http://localhost:8767/v1/health
```

## 架构

```
外部请求 → 智桥网关(:8767) → 后端服务
              │
              ├─ 路由 (router.py)      — 32条路由
              ├─ 鉴权 (auth.py)        — API Key / Bearer Token
              ├─ 限流 (middleware.py)   — 100/min, burst 20
              ├─ 熔断 (circuit.py)     — 连续失败自动熔断
              └─ 指标 (metrics.py)     — Prometheus
```

### 后端服务

| 服务 | 端口 | 类型 |
|------|------|------|
| lingtong_plus | 8765 | 内部 |
| lingzhi | 8000 | 内部 |
| lingtong_ask | 8902 | 内部 |
| lingresearch | 8903 | 内部 |
| llm_proxy | 8080 | 内部 |
| linghealth | 8200 | 对外 |
| lingvision | 8781 | 对外 |
| lingvoice | 8100 | 对外 |
| lingtouch | 8784 | 对外 |
| sizhen | 8785 | 对外 |
| lingwear | 8787 | 对外 |
| linglaw | 8002 | 对外 |

### API 端点

| 方法 | 路径 | 说明 | 鉴权 |
|------|------|------|------|
| GET | `/v1/health` | 健康检查（含后端状态） | 否 |
| POST | `/v1/chat/completions` | LLM代理 | 是 |
| POST | `/api/knowledge/query` | 知识库语义检索 | 是 |
| GET | `/api/status` | 灵族健康仪表盘 | 是 |
| GET | `/projects/{project}/{path}` | 对外工程通配代理 | 是 |
| GET | `/internal/{backend}/{path}` | 内部服务回调查询 | 可选 |
| GET | `/metrics` | Prometheus指标 | 否 |

详见 `gateway/README.md` 和 Swagger UI: `http://localhost:8767/docs`

## 项目结构

```
gateway/          — 网关核心（FastAPI）
  ├── app.py        入口
  ├── config.py     配置（pydantic-settings）
  ├── auth.py       鉴权
  ├── router.py     路由
  ├── proxy.py      反向代理
  ├── middleware.py  限流 + CORS
  ├── circuit.py    熔断器
  ├── metrics.py    Prometheus
  └── tests/        测试
docs/             — 文档
nginx/            — Nginx配置
mcp-server/       — MCP服务端（开发中）
```

## 配置

环境变量前缀 `ZHIBRIDGE_`，或通过 `.env` 文件：

```bash
ZHIBRIDGE_HOST=127.0.0.1
ZHIBRIDGE_PORT=8767
ZHIBRIDGE_SSL_ENABLED=false
ZHIBRIDGE_RATE_LIMIT=100/minute
```

## 测试

```bash
pytest gateway/tests/ -v
```

## 部署

```bash
# systemd
sudo cp gateway/zhibridge-gateway.service /etc/systemd/system/
sudo systemctl enable --now zhibridge-gateway
```

## 安全策略

详见 [`SECURITY.md`](SECURITY.md)。

## 许可证

MIT

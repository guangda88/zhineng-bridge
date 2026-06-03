# 智桥网关 - 灵族对外统一接口

薄层API网关，只做路由、鉴权、限流，不做业务逻辑。

## 快速启动

```bash
# 启动
bash gateway/gateway.sh start

# 停止
bash gateway/gateway.sh stop

# 状态
bash gateway/gateway.sh status

# 测试
bash gateway/gateway.sh test
```

## 访问地址

- 网关地址: http://localhost:8767
- Swagger UI: http://localhost:8767/docs
- ReDoc: http://localhost:8767/redoc
- OpenAPI JSON: http://localhost:8767/openapi.json

## API 端点

| 优先级 | 方法 | 路径 | 说明 | 鉴权 |
|--------|------|------|------|------|
| P0 | GET | `/v1/health` | 健康检查（含后端状态） | 否 |
| P0 | POST | `/v1/chat/completions` | LLM代理（转发灵通+） | 是 |
| P0 | POST | `/api/knowledge/query` | 知识库语义检索（转发灵知） | 是 |
| P1 | GET | `/api/status` | 灵族健康仪表盘（转发灵通+） | 是 |
| P1 | GET | `/api/agents` | 成员状态列表（转发灵通+） | 是 |
| P1 | GET | `/api/podcast/episodes` | 播客元数据（灵通问道） | 否 |
| P2 | GET | `/api/research/papers` | 论文检索（转发灵研） | 是 |
| P2 | POST | `/v1/images/generations` | 图片生成（转发LLM Proxy） | 是 |
| - | GET | `/metrics` | Prometheus指标 | 否 |

## 鉴权方式

支持三种API Key传递方式：

```bash
# 方式1: X-API-Key header（推荐）
curl -H "X-API-Key: lpk_your_key" http://localhost:8767/api/status

# 方式2: API-Key header
curl -H "API-Key: lpk_your_key" http://localhost:8767/api/status

# 方式3: Bearer Token
curl -H "Authorization: Bearer lpk_your_key" http://localhost:8767/api/status
```

## 后端服务配置

| 服务 | 默认地址 | 状态 |
|------|----------|------|
| lingtong_plus | http://localhost:8765 | ✅ |
| lingzhi | http://localhost:8000 | ✅ |
| lingtong_ask | http://localhost:8902 | ❌ |
| lingresearch | http://localhost:8903 | ❌ |
| llm_proxy | http://localhost:8080 | ❌ |

## 架构说明

### 薄层网关设计原则：
1. **无状态** - 网关本身不存状态，全部透传后端
2. **鉴权透传** - API Key直接传递给后端验证，网关只做格式校验
3. **无业务逻辑** - 网关只转发，不处理业务
4. **熔断器** - 后端连续失败自动熔断，5分钟后自动恢复
5. **限流** - 100请求/分钟，突发20

### 文件结构

```
gateway/
├── app.py          # FastAPI入口
├── config.py       # 配置（pydantic-settings）
├── auth.py         # API Key鉴权
├── router.py       # 路由注册
├── proxy.py        # 反向代理核心
├── middleware.py   # 限流 + CORS + 请求日志
├── circuit.py      # 熔断器 + 后端健康检查
├── metrics.py      # Prometheus指标
├── gateway.sh      # 启停脚本
├── openapi.json   # OpenAPI规范
├── zhibridge-gateway.service  # systemd服务
└── tests/          # 测试
```

## 部署

### systemd 安装（需sudo）

```bash
sudo cp gateway/zhibridge-gateway.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable zhibridge-gateway
sudo systemctl start zhibridge-gateway
sudo systemctl status zhibridge-gateway
```

## 测试示例

```bash
# 健康检查
curl http://localhost:8767/v1/health

# LLM代理
curl -X POST http://localhost:8767/v1/chat/completions \
  -H "X-API-Key: lpk_your_key" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4", "messages": [{"role": "user", "content": "你好"}]}'

# 知识库搜索
curl -X POST http://localhost:8767/api/knowledge/query \
  -H "X-API-Key: lpk_your_key" \
  -H "Content-Type: application/json" \
  -d '{"query": "气功", "limit": 10}'
```

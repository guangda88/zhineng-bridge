# 架构概览

## 系统架构

```
浏览器/客户端 ←──ws/wss──→ 智桥 (:8765) ←──ws──→ AI 后端
                                  |
                            HTTP API (:8080)
                                  |
                            ┌─────┼─────┐
                          认证   团队   插件
                          系统   系统   系统
```

## 核心模块

### 1. WebSocket 中继服务器 (`relay-server/`)

| 文件 | 职责 |
|------|------|
| `server.py` | WebSocket 主服务器，处理连接和消息路由 |
| `http_server.py` | HTTP API 服务器，认证/团队/插件/健康检查 |
| `plugin_system.py` | 插件框架核心，生命周期/钩子/命令管理 |
| `auth_manager.py` | 认证管理，注册/登录/JWT/OAuth2/2FA |
| `auth_db.py` | SQLite 数据库连接池和用户表 |
| `auth_totp.py` | TOTP 双因素认证 (RFC 6238) |
| `team_manager.py` | 团队协作业务逻辑 |
| `team_db.py` | 团队数据库 CRUD |
| `team_models.py` | 团队数据模型 |
| `auth_models.py` | 用户数据模型 |

### 2. 会话管理 (`phase1/session_manager/`)

| 文件 | 职责 |
|------|------|
| `session_manager.py` | AI 工具会话管理，工具注册表（15个工具） |
| `start_manager.py` | 启动入口 |

### 3. 插件系统 (`plugins/`)

| 文件 | 职责 |
|------|------|
| `message_stats.py` | 消息统计插件示例 |
| `auto_reply.py` | 关键词自动回复示例 |
| `msg_transform.py` | 消息格式转换示例 |

### 4. Web UI (`web/ui/`)

| 文件 | 职责 |
|------|------|
| `index.html` | 主页面 |
| `js/client.js` | WebSocket 客户端 |
| `js/app.js` | 应用逻辑 |
| `css/base.css` | CSS 变量和基础样式 |

## 数据流

### WebSocket 消息流
1. 客户端连接 `ws://localhost:8765`
2. 发送 JSON 消息 `{"type": "...", "data": {...}}`
3. 服务器路由到对应处理器
4. 触发插件钩子（如 `on_message_received`）
5. 处理完成后响应

### HTTP API 请求流
1. 客户端发送 HTTP 请求到 `:8080`
2. 中间件验证 JWT Token
3. 路由到对应处理器
4. 业务逻辑处理
5. 返回 JSON 响应

## 数据库

使用 SQLite，表结构：

- `users` — 用户信息（含 2FA 字段）
- `oauth_tokens` — OAuth2 令牌
- `sessions` — 登录会话
- `password_reset_tokens` — 密码重置令牌
- `teams` — 团队
- `team_members` — 团队成员（含角色）
- `team_invites` — 邀请链接
- `shared_sessions` — 共享会话

## 配置

配置通过 `relay-server/config.py` 的 `settings` 对象管理，支持的环境变量：

- `WS_PORT` — WebSocket 端口（默认 8765）
- `HTTP_PORT` — HTTP API 端口（默认 8080）
- `DB_PATH` — 数据库路径
- `SECRET_KEY` — JWT 签名密钥

# API 参考

## 基础信息

- **Base URL**: `http://localhost:8080`
- **认证方式**: Bearer Token（`Authorization: Bearer <token>`）
- **内容类型**: `application/json`

---

## 认证 API

### POST /api/users/register

注册新用户。

**请求体**:
```json
{"username": "user", "password": "password123", "email": "user@example.com"}
```

**响应** `201`:
```json
{"type": "user_registered", "user_id": "...", "username": "user", "email": "user@example.com"}
```

### POST /api/users/login

用户登录。

**请求体**:
```json
{"username": "user", "password": "password123"}
```

**响应** `200`:
```json
{"type": "user_logged_in", "token": "eyJ...", "user_id": "...", "username": "user", "expires_at": "...", "scopes": ["read", "write"]}
```

### POST /api/users/logout

登出。

**Headers**: `Authorization: Bearer <token>`

**响应** `200`:
```json
{"type": "user_logged_out", "message": "Successfully logged out"}
```

### GET /api/users/me

获取当前用户信息。

**Headers**: `Authorization: Bearer <token>`

### PUT /api/users/{user_id}

更新用户信息（管理员或本人）。

### DELETE /api/users/{user_id}

删除用户（管理员或本人）。

### GET /api/users

列出所有用户（仅管理员）。

---

## 密码重置 API

### POST /api/users/password-reset/request

请求密码重置。

**请求体**: `{"email": "user@example.com"}`

### POST /api/users/password-reset/confirm

确认密码重置。

**请求体**: `{"token": "reset-token", "new_password": "newpass123"}`

### POST /api/users/password/change

修改密码（需登录）。

**请求体**: `{"current_password": "old", "new_password": "new12345"}`

---

## 双因素认证 API

### POST /api/users/2fa/setup

初始化 2FA（返回密钥和 QR 码 URL）。

### POST /api/users/2fa/enable

启用 2FA。**请求体**: `{"code": "123456"}`

### POST /api/users/2fa/verify

验证 TOTP 码。**请求体**: `{"code": "123456"}`

### POST /api/users/2fa/disable

禁用 2FA。**请求体**: `{"code": "123456"}`

### POST /api/users/2fa/backup-codes

重新生成备用码。**请求体**: `{"code": "123456"}`

---

## 团队协作 API

### POST /api/teams

创建团队。**请求体**: `{"name": "团队名", "description": "描述"}`

### GET /api/teams

列出我的团队。

### GET /api/teams/{team_id}

获取团队详情和成员。

### PUT /api/teams/{team_id}

更新团队信息（Owner/Admin）。**请求体**: `{"name": "新名称"}`

### DELETE /api/teams/{team_id}

删除团队（仅 Owner）。

### GET /api/teams/{team_id}/members

列出团队成员。

### PUT /api/teams/{team_id}/members/{target_id}

修改成员角色。**请求体**: `{"role": "admin"}`

### DELETE /api/teams/{team_id}/members/{target_id}

移除成员。

### POST /api/teams/{team_id}/leave

离开团队。

### POST /api/teams/{team_id}/invites

创建邀请。**请求体**: `{"email": "user@example.com", "expires_hours": 72}`

### GET /api/teams/{team_id}/invites

列出邀请。

### POST /api/teams/invites/{token}/accept

接受邀请。

### POST /api/teams/{team_id}/sessions/share

共享会话。**请求体**: `{"session_id": "...", "title": "标题"}`

### DELETE /api/teams/sessions/{share_id}

取消共享。

### GET /api/teams/{team_id}/sessions

查看团队共享的会话。

---

## 插件管理 API

### GET /api/plugins

列出已加载的插件。

### GET /api/plugins/{plugin_id}

获取插件详情。

### POST /api/plugins/{plugin_id}/enable

启用插件。

### POST /api/plugins/{plugin_id}/disable

禁用插件。

### POST /api/plugins/{plugin_id}/reload

重载插件（卸载 + 重新加载）。

### POST /api/plugins/{plugin_id}/config

设置插件配置。**请求体**: `{"key": "value"}`

### GET /api/plugins/{plugin_id}/commands

列出插件注册的命令。

### POST /api/plugins/discover

扫描发现可用插件。

---

## 健康检查

### GET /health

返回服务状态。

```json
{"status": "healthy", "timestamp": "...", "service": "zhineng-bridge", "version": "1.4.0"}
```

---

## WebSocket 消息

### 客户端 → 服务器

| type | 说明 |
|------|------|
| `ping` | 心跳 |
| `list_sessions` | 列出会话 |
| `start_session` | 创建会话（`tool_name`, `args`） |
| `stop_session` | 停止会话（`session_id`） |
| `delete_session` | 删除会话（`session_id`） |

### 服务器 → 客户端

| type | 说明 |
|------|------|
| `pong` | 心跳响应 |
| `sessions_list` | 会话列表 |
| `session_started` | 会话已创建 |
| `session_stopped` | 会话已停止 |
| `session_deleted` | 会话已删除 |
| `output` | 会话输出 |
| `error` | 错误信息 |

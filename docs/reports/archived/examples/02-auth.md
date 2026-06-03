# 用户认证

## 注册

```bash
curl -X POST http://localhost:8080/api/users/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "mypassword123", "email": "test@example.com"}'
```

```json
{
  "type": "user_registered",
  "user_id": "xxx-xxx-xxx",
  "username": "testuser",
  "email": "test@example.com"
}
```

## 登录

```bash
curl -X POST http://localhost:8080/api/users/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "mypassword123"}'
```

```json
{
  "type": "user_logged_in",
  "token": "eyJ...",
  "user_id": "xxx-xxx-xxx",
  "username": "testuser",
  "expires_at": "2026-04-08T12:00:00",
  "scopes": ["read", "write"]
}
```

## 使用 Token 访问受保护资源

```bash
curl http://localhost:8080/api/users/me \
  -H "Authorization: Bearer eyJ..."
```

## 密码重置

```bash
# 请求重置
curl -X POST http://localhost:8080/api/users/password-reset/request \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

# 确认重置
curl -X POST http://localhost:8080/api/users/password-reset/confirm \
  -H "Content-Type: application/json" \
  -d '{"token": "reset-token", "new_password": "newpassword123"}'
```

## 双因素认证 (TOTP)

```bash
# 初始化 2FA（返回 QR 码 URL）
curl -X POST http://localhost:8080/api/users/2fa/setup \
  -H "Authorization: Bearer eyJ..."

# 启用 2FA
curl -X POST http://localhost:8080/api/users/2fa/enable \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{"code": "123456"}'

# 验证
curl -X POST http://localhost:8080/api/users/2fa/verify \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{"code": "123456"}'
```

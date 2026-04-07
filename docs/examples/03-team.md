# 团队协作

## 创建团队

```bash
curl -X POST http://localhost:8080/api/teams \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{"name": "开发组", "description": "项目开发团队"}'
```

```json
{
  "type": "team_created",
  "team": {
    "team_id": "team-xxx",
    "name": "开发组",
    "description": "项目开发团队",
    "owner_id": "user-xxx",
    "created_at": "2026-04-07T12:00:00"
  }
}
```

## 查看我的团队

```bash
curl http://localhost:8080/api/teams \
  -H "Authorization: Bearer eyJ..."
```

## 邀请成员

```bash
curl -X POST http://localhost:8080/api/teams/team-xxx/invites \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{"email": "newuser@example.com", "expires_hours": 72}'
```

## 接受邀请

```bash
curl -X POST http://localhost:8080/api/teams/invites/TOKEN/accept \
  -H "Authorization: Bearer eyJ..."
```

## 管理角色

```bash
# 修改成员角色（需要 Owner 或 Admin 权限）
curl -X PUT http://localhost:8080/api/teams/team-xxx/members/target-user-id \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{"role": "admin"}'
```

角色层级：`owner > admin > member > viewer`

## 共享会话

```bash
# 共享会话给团队
curl -X POST http://localhost:8080/api/teams/team-xxx/sessions/share \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{"session_id": "session-xxx", "title": "调试会话"}'

# 查看团队共享的会话
curl http://localhost:8080/api/teams/team-xxx/sessions \
  -H "Authorization: Bearer eyJ..."
```

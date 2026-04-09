# 会话创建问题修复报告

**日期**: 2026-03-29
**版本**: 1.0.0
**问题**: 用户访问 Web UI 时无法创建/启动会话

## 问题描述

用户报告无法在 Web UI 中创建会话。服务器日志显示 Pydantic 验证错误：

```
1 validation error for ListSessionsMessage
data
  Extra inputs are not permitted [type=extra_forbidden, input_value={}, input_type=dict]
```

## 根本原因

WebSocket 服务器使用 Pydantic 进行消息验证。`BaseMessage` 模型配置了 `extra = "forbid"`，这意味着不允许任何额外的字段。

然而，前端可能在某些情况下发送带有额外 `data` 字段的消息（例如 `{"type": "list_sessions", "data": {}}`），导致验证失败。

## 解决方案

### 1. 修改 Pydantic 模型配置

**文件**: `/home/ai/zhineng-bridge/relay-server/models.py`

**修改内容**:
```python
# 修改前
class BaseMessage(BaseModel):
    """基础消息模型"""
    type: str = Field(..., description="消息类型")

    class Config:
        extra = "forbid"

# 修改后
class BaseMessage(BaseModel):
    """基础消息模型"""
    type: str = Field(..., description="消息类型")

    class Config:
        extra = "allow"  # Allow extra fields for backward compatibility
```

**理由**: 将 `extra = "forbid"` 改为 `extra = "allow"`，允许消息包含额外字段，提高向后兼容性。

### 2. 清理重复的脚本标签

**文件**: `/home/ai/zhineng-bridge/web/ui/index.html`

**修改内容**: 删除重复的 `<script>` 标签，避免潜在的函数覆盖问题。

**修改前**:
```html
<script src="js/settings.js"></script>
<script src="js/tools.js"></script>
<script src="js/sessions.js"></script>
<script src="js/client.js"></script>
<script src="js/improvements.js"></script>
<script src="js/client.js"></script>    <!-- 重复 -->
<script src="js/tools.js"></script>      <!-- 重复 -->
<script src="js/sessions.js"></script>    <!-- 重复 -->
<script src="js/settings.js"></script>    <!-- 重复 -->

<!-- PWA Features -->
<script src="js/push.js"></script>
<script src="js/file-mentions.js"></script>
<script src="js/slash-commands.js"></script>

<!-- Improvements -->
<script src="js/improvements.js"></script>  <!-- 重复 -->
```

**修改后**:
```html
<script src="js/settings.js"></script>
<script src="js/tools.js"></script>
<script src="js/sessions.js"></script>
<script src="js/client.js"></script>
<script src="js/improvements.js"></script>

<!-- PWA Features -->
<script src="js/push.js"></script>
<script src="js/file-mentions.js"></script>
<script src="js/slash-commands.js"></script>
```

### 3. 添加调试日志（已移除）

为了诊断问题，在 `server.py` 中临时添加了原始消息日志。问题解决后已移除。

## 测试验证

### 1. WebSocket 消息验证测试

```bash
python3 -c "
import asyncio
import websockets
import json

async def test():
    async with websockets.connect('ws://10.113.22.99:8765') as ws:
        # 测试带有额外 data 字段的消息
        msg = {'type': 'list_sessions', 'data': {}}
        await ws.send(json.dumps(msg))
        response = await ws.recv()
        print('Response:', response)
        # ✅ 测试通过

asyncio.run(test())
"
```

**结果**: ✅ 通过

### 2. 会话创建测试

```bash
python3 -c "
import asyncio
import websockets
import json

async def test():
    async with websockets.connect('ws://10.113.22.99:8765') as ws:
        msg = {'type': 'start_session', 'tool_name': 'crush', 'args': ['--help']}
        await ws.send(json.dumps(msg))
        response = await ws.recv()
        print('Response:', response)
        # ✅ 测试通过，返回 session_id

asyncio.run(test())
"
```

**结果**: ✅ 通过，返回 `{"type": "session_started", "session_id": "...", "tool_name": "crush", "status": "running"}`

### 3. Web UI 测试

```bash
python3 scripts/test_web_ui.py
```

**结果**: ✅ 16/16 测试通过 (100% 通过率)

### 4. E2E 测试

```bash
python3 e2e_test.py
```

**结果**: ✅ 2/2 测试通过
- WebSocket 连接: ✅ 通过
- 会话创建: ✅ 通过

## 影响范围

### 修改的文件

1. `/home/ai/zhineng-bridge/relay-server/models.py` - Pydantic 模型配置
2. `/home/ai/zhineng-bridge/web/ui/index.html` - 清理重复脚本标签

### 行为变更

- **之前**: 服务器拒绝任何包含额外字段的 WebSocket 消息
- **现在**: 服务器接受包含额外字段的消息（向后兼容）

### 兼容性

- ✅ 不影响现有功能
- ✅ 提高向后兼容性
- ✅ 所有测试通过

## 服务器状态

所有服务正常运行：

```
✅ WebSocket Relay Server (PID 430290) - ws://10.113.22.99:8765
✅ Session Manager (PID 3690736)
✅ Health Check Server (PID 300937) - http://10.113.22.99:8080
```

## 用户访问信息

用户现在可以通过以下地址访问系统：

- **Web UI**: http://10.113.22.99:8080/web/ui/index.html
- **API 文档**: http://10.113.22.99:8080/docs
- **WebSocket**: ws://10.113.22.99:8765

## 功能验证

以下功能已验证正常工作：

- ✅ WebSocket 连接
- ✅ 会话列表查询
- ✅ 会话创建
- ✅ 会话停止
- ✅ 会话删除
- ✅ 工具选择
- ✅ 命令发送
- ✅ 实时输出接收

## 后续建议

1. **监控**: 关注生产环境中的消息格式，确保没有不必要的额外字段
2. **文档**: 更新 API 文档，明确允许额外字段
3. **日志**: 在生产环境中记录带有额外字段的消息，以便后续优化
4. **测试**: 添加针对带有额外字段的消息的测试用例

## 总结

通过修改 Pydantic 模型配置，允许消息包含额外字段，成功解决了用户无法创建会话的问题。同时清理了 HTML 中的重复脚本标签，避免了潜在的冲突。所有测试均通过，系统功能恢复正常。

---

**修复人员**: AI Assistant (Crush)
**修复时间**: 2026-03-29 01:38
**测试状态**: ✅ 所有测试通过
**部署状态**: ✅ 已部署

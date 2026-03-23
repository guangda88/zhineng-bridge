# 智桥 API 文档

## 目录

- [WebSocket API](#websocket-api)
- [Session Manager API](#session-manager-api)
- [Encryption API](#encryption-api)
- [Storage API](#storage-api)

## WebSocket API

### 连接

```
ws://localhost:8765
```

### 消息类型

#### list_sessions

列出所有会话

**请求：**
```json
{
  "type": "list_sessions",
  "data": {}
}
```

**响应：**
```json
{
  "type": "sessions_list",
  "sessions": [
    {
      "session_id": "xxx-xxx-xxx",
      "tool_name": "crush",
      "status": "running",
      "created_at": "2026-03-24T02:00:00Z"
    }
  ],
  "count": 1
}
```

#### start_session

启动会话

**请求：**
```json
{
  "type": "start_session",
  "tool_name": "crush",
  "args": ["--help"]
}
```

**响应：**
```json
{
  "type": "session_started",
  "session_id": "xxx-xxx-xxx",
  "tool_name": "crush",
  "status": "running"
}
```

#### stop_session

停止会话

**请求：**
```json
{
  "type": "stop_session",
  "session_id": "xxx-xxx-xxx"
}
```

**响应：**
```json
{
  "type": "session_stopped",
  "session_id": "xxx-xxx-xxx",
  "status": "stopped"
}
```

#### send_command

发送命令

**请求：**
```json
{
  "type": "send_command",
  "session_id": "xxx-xxx-xxx",
  "command": "help"
}
```

**响应：**
```json
{
  "type": "command_sent",
  "session_id": "xxx-xxx-xxx",
  "command": "help",
  "status": "sent"
}
```

#### output

输出消息

**消息：**
```json
{
  "type": "output",
  "session_id": "xxx-xxx-xxx",
  "output": "Output text...",
  "timestamp": "2026-03-24T02:00:00Z"
}
```

#### ping

心跳

**请求：**
```json
{
  "type": "ping"
}
```

**响应：**
```json
{
  "type": "pong",
  "timestamp": "2026-03-24T02:00:00Z"
}
```

## Session Manager API

### SessionManager 类

#### 初始化

```python
from session_manager import SessionManager

manager = SessionManager(base_dir="/tmp")
```

#### 方法

##### list_tools()

列出所有工具

**返回：**
```python
{
  'crush': {
    'name': 'Crush',
    'description': 'Charmbracelet Crush - AI 编码助手',
    'executable': '/usr/local/bin/crush',
    'icon': '💎',
    'color': '#FFE66D'
  },
  ...
}
```

##### create_session(tool_name, args)

创建会话

**参数：**
- `tool_name`: 工具名称
- `args`: 参数列表

**返回：** 会话 ID

##### get_session(session_id)

获取会话

**参数：**
- `session_id`: 会话 ID

**返回：** 会话信息

##### list_sessions()

列出所有会话

**返回：** 会话列表

## Encryption API

### EncryptionManager 类

#### 初始化

```javascript
const encryptionManager = new EncryptionManager();
await encryptionManager.init();
```

#### 方法

##### generateKeyPair()

生成 RSA 密钥对

**返回：** 密钥对

##### exportPublicKey()

导出公钥

**返回：** Base64 编码的公钥

##### importPublicKey(publicKeyBase64)

导入公钥

**参数：**
- `publicKeyBase64`: Base64 编码的公钥

**返回：** 公钥对象

##### encryptMessage(message, publicKey)

加密消息

**参数：**
- `message`: 消息
- `publicKey`: 公钥

**返回：** Base64 编码的加密消息

##### decryptMessage(encryptedBase64)

解密消息

**参数：**
- `encryptedBase64`: Base64 编码的加密消息

**返回：** 解密后的消息

## Storage API

### StorageManager 类

#### 初始化

```javascript
const storageManager = new StorageManager();
await storageManager.init();
```

#### 方法

##### saveSession(session)

保存会话

**参数：**
- `session`: 会话对象

**返回：** 会话对象

##### getSession(sessionId)

获取会话

**参数：**
- `sessionId`: 会话 ID

**返回：** 会话对象

##### getAllSessions()

获取所有会话

**返回：** 会话列表

##### saveOutput(output)

保存输出

**参数：**
- `output`: 输出对象

**返回：** 输出对象

##### getSessionOutputs(sessionId, limit)

获取会话输出

**参数：**
- `sessionId`: 会话 ID
- `limit`: 最大输出数

**返回：** 输出列表

---

**API 文档版本: 1.0.0**
**最后更新: 2026-03-24 02:00**

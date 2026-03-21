# 🌀 智桥 - Zhineng Bridge

跨平台实时同步和通信SDK，支持CLI与移动端之间的实时双向通信。

## 功能特性

### 1. 实时CLI同步
- 桌面CLI与移动端App之间的**双向实时同步**
- 通过**加密中继服务器**传输
- **终端状态同步**：命令历史、输入状态、光标位置
- **双向启动**：任何设备都可以发起对话、发送消息

### 2. 多会话管理
- 支持多个并发的会话
- 每个会话独立维护项目上下文、对话历史、终端状态
- 会话可以**暂停、恢复、无缝切换**

### 3. 端到端加密
- **AES-256-GCM** 加密算法
- 共享密钥加密（通过二维码或手动输入）
- 中继服务器只处理**加密数据**，无法访问明文
- **零信任架构**

### 4. 离线优先架构
- 异步通信通过加密中继服务器
- 离线消息队列
- 网络恢复后自动同步

## 快速开始

### 安装

```bash
cd zhineng-bridge
npm install
```

### 启动中继服务器

```bash
npm start
# 或
node relay-server/server.js
```

服务器默认运行在 `ws://localhost:8001`

### 启动CLI

```bash
npm run cli
# 或
node cli/index.js
```

### 使用测试客户端

在浏览器中打开 `test-client.html`

## 命令列表

CLI支持以下命令：

```
/join <channel>     加入频道
/leave              离开当前频道
/sessions           列出所有会话
/create <name>     创建新会话
/switch <id>       切换到指定会话
/pause             暂停当前会话
/resume            恢复当前会话
/sync              强制同步终端状态
/offline           获取离线消息
/quit              退出CLI
```

## API参考

### WebSocket消息类型

#### 客户端 → 服务器

| 类型 | 描述 |
|------|------|
| `join` | 加入频道 |
| `leave` | 离开频道 |
| `message` | 发送消息 |
| `direct` | 发送私信 |
| `terminal_state` | 同步终端状态 |
| `command` | 执行命令 |
| `create_session` | 创建会话 |
| `get_sessions` | 获取会话列表 |
| `switch_session` | 切换会话 |
| `pause_session` | 暂停会话 |
| `resume_session` | 恢复会话 |
| `offline_message` | 发送离线消息 |
| `get_offline_messages` | 获取离线消息 |

#### 服务器 → 客户端

| 类型 | 描述 |
|------|------|
| `connected` | 连接成功 |
| `joined` | 加入频道成功 |
| `message` | 收到消息 |
| `terminal_state` | 终端状态更新 |
| `command` | 收到命令 |
| `command_result` | 命令执行结果 |
| `session_created` | 会话创建成功 |
| `sessions_list` | 会话列表 |
| `session_state` | 会话状态 |
| `session_paused` | 会话已暂停 |
| `session_resumed` | 会话已恢复 |
| `offline_messages` | 离线消息 |

## 加密说明

### 生成密钥

```javascript
const { Encryption } = require('./packages/core-sdk/src/utils/Encryption');
const encryption = new Encryption();

const { key, salt } = encryption.generateKey('password');
// 或
const sharedSecret = encryption.generateSharedSecret();
```

### 加密/解密

```javascript
const encrypted = encryption.encrypt('Hello World', key);
const decrypted = encryption.decrypt(encrypted, key);
```

## 项目结构

```
zhineng-bridge/
├── relay-server/        # 中继服务器
│   └── server.js       # WebSocket服务器
├── cli/                # CLI客户端
│   └── index.js        # CLI主程序
├── packages/           # SDK包
│   └── core-sdk/       # 核心SDK
│       └── src/utils/  # 工具类
│           ├── Encryption.js   # 加密模块
│           └── SessionManager.js # 会话管理
├── test-client.html    # Web测试客户端
└── package.json        # 项目配置
```

## 技术栈

- **WebSocket**: 实时双向通信
- **AES-256-GCM**: 端到端加密
- **Node.js**: 服务器运行时
- **HTML/CSS/JS**: Web客户端

## 许可证

MIT License

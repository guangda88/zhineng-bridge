# 智桥 (Zhineng Bridge) SDK

智桥 (Zhineng Bridge) 是一个跨平台的实时同步和通信 SDK，支持移动端、桌面端和CLI的无缝集成。

## 🌟 核心特性

- **实时双向通信**: 基于WebSocket的实时消息同步
- **跨平台支持**: 移动端、桌面端、CLI工具
- **端到端加密**: AES-256-GCM加密保护
- **终端状态同步**: CLI工具支持终端状态实时同步
- **多会话管理**: 支持多个独立会话
- **离线优先**: 消息队列支持离线操作

## 🏗️ 架构概述

### 分层架构

```
应用层 (App)
    ↓
SDK 层 (TraeBridgeSDK)
    ↓
服务层 (SyncService, MessageService, SessionService)
    ↓
数据层 (StorageAdapter, State)
    ↓
工具层 (CryptoService, EventBus, Logger)
```

### 核心组件

- **Core SDK**: 平台无关的核心功能实现
- **Mobile SDK**: 移动端特定功能（语音输入、二维码扫描、推送通知）
- **Desktop SDK**: 桌面端特定功能（终端集成、文件监控、VS Code 集成）
- **CLI Tool**: 命令行工具，支持终端状态同步
- **Relay Server**: WebSocket中继服务器

## 🚀 快速开始

### 安装

```bash
# Core SDK
npm install @zhineng-bridge/core-sdk

# Mobile SDK
npm install @zhineng-bridge/mobile-sdk

# Desktop SDK
npm install @zhineng-bridge/desktop-sdk

# CLI Tool
cd cli && npm install
```

### 启动服务

#### 1. 启动Relay Server

```bash
cd relay-server
npm install
node server.js
```

服务将在 `ws://localhost:8001` 启动。

#### 2. 启动CLI工具

```bash
cd cli
npm install
node index.js
```

#### 3. 使用测试客户端

在浏览器中打开 `test-client.html`，连接到 `ws://localhost:8001`。

## 📦 核心功能

### 连接管理

```typescript
// 连接
await sdk.connect();

// 断开连接
await sdk.disconnect();

// 检查连接状态
const connected = sdk.isConnected();

// 监听连接变化
sdk.onConnectionChange((connected) => {
  console.log('Connection:', connected);
});
```

### 会话管理

```typescript
// 创建会话
const session = await sdk.createSession('Project Name', 'Description');

// 切换会话
await sdk.switchSession(sessionId);

// 关闭会话
await sdk.closeSession(sessionId);

// 获取所有会话
const sessions = sdk.getSessions();

// 获取当前会话
const currentSession = sdk.getCurrentSession();
```

### 消息发送

```typescript
// 发送文本消息
await sdk.sendMessage('Hello', 'chat');

// 发送命令
await sdk.sendCommand('npm run dev');

// 发送状态
await sdk.sendState({ type: 'status', data: 'running' });

// 监听消息
sdk.onMessage((message) => {
  console.log('Received:', message.content);
});
```

### 终端状态同步

```typescript
// CLI工具自动同步终端状态
// 包括：命令历史、当前输入、光标位置、输出历史

// 手动同步终端状态
sdk.sendTerminalState({
  commandHistory: ['ls', 'cd project'],
  currentInput: 'npm run',
  cursorPosition: 7,
  outputHistory: ['output line 1', 'output line 2']
});
```

## 🔧 CLI工具

### 安装和启动

```bash
cd cli
npm install
node index.js
```

### 可用命令

- `help` - 显示帮助信息
- `status` - 显示连接状态
- `exit` - 断开连接并退出
- 任何其他文本 - 作为消息发送

### 配置

CLI工具会在用户主目录下创建 `.zhineng-bridge.json` 配置文件：

```json
{
  "serverUrl": "ws://100.66.1.8:8001",
  "defaultChannel": "default"
}
```

## 🌐 Relay Server

### 启动服务器

```bash
cd relay-server
npm install
node server.js
```

### 配置

服务器默认监听端口 8001，支持以下环境变量：

- `PORT` - 服务器端口（默认：8001）

### 功能特性

- WebSocket连接管理
- 频道管理
- 消息广播
- 终端状态同步
- 心跳检测

## 📡 事件系统

```typescript
// 监听所有事件
sdk.on('connection:changed', (state) => {
  console.log('Connection:', state.connected);
});

sdk.on('message:received', (message) => {
  console.log('Message:', message.content);
});

sdk.on('session:changed', (session) => {
  console.log('Session:', session?.projectName);
});

sdk.on('terminal_state', (state) => {
  console.log('Terminal State:', state);
});

// 取消监听
const unsubscribe = sdk.on('message:received', (message) => {
  console.log(message);
});

unsubscribe();
```

## 🔒 安全性

### 端到端加密

- 使用 AES-256-GCM 加密算法
- 支持密钥交换和配对
- 零信任架构设计

### 最佳实践

1. 在生产环境中启用加密
2. 定期更新加密密钥
3. 使用安全的WebSocket连接（WSS）
4. 验证客户端身份

## 📖 最佳实践

1. **初始化**: 总是先调用 `initialize()` 再调用 `connect()`
2. **错误处理**: 使用 try-catch 包装异步操作
3. **资源清理**: 在应用退出时调用 `destroy()`
4. **事件监听**: 记得取消不再需要的事件监听器
5. **会话管理**: 适当关闭不再使用的会话
6. **加密**: 在生产环境中启用加密
7. **日志**: 在开发环境使用debug级别，生产环境使用error级别

## 🤝 贡献

欢迎贡献代码！请查看 CONTRIBUTING.md 了解详情。

## 📄 许可证

MIT

## 🔗 相关链接

- [项目仓库](http://zhinenggitea.iepose.cn/guangda/zhineng-bridge)
- [问题反馈](http://zhinenggitea.iepose.cn/guangda/zhineng-bridge/issues)

## 📞 联系方式

- 项目维护者：Zhineng Bridge Team
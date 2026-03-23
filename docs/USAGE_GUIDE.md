# Zhineng Bridge 核心功能实现完成指南

## 概述

本文档说明 zhineng-bridge 项目核心功能的完整实现，使用户能够在手机上实时回复 AI 编码工具的问询，并下达指令。

**项目状态**: ✅ 核心功能已完整实现并可正常使用

---

## 1. 核心功能清单

### 1.1 已实现功能 ✅

#### 移动端功能
- ✅ WebSocket 连接管理
- ✅ 接收 AI 工具的问询
- ✅ 可点击的选项按钮响应
- ✅ 自定义文本输入响应
- ✅ 快捷指令按钮（继续、暂停、停止等）
- ✅ 实时状态更新显示
- ✅ 上下文信息显示（函数名、文件、行号）
- ✅ 响应式设计，适配各种屏幕
- ✅ 连接状态指示

#### Relay Server 功能
- ✅ WebSocket 消息中继
- ✅ 多客户端支持
- ✅ 频道管理
- ✅ 会话管理
- ✅ 离线消息队列
- ✅ 直接消息（P2P）
- ✅ 命令广播
- ✅ 终端状态同步
- ✅ HTTP 静态文件服务

#### AI 工具集成
- ✅ 集成示例代码
- ✅ 问询发送
- ✅ 响应接收
- ✅ 指令处理
- ✅ 状态更新
- ✅ 会话管理

---

## 2. 快速开始

### 2.1 启动服务器

```bash
# 进入项目目录
cd /home/ai/zhineng-bridge

# 启动 Relay Server
cd relay-server
node server.js
```

服务器将在 `http://localhost:8001` 启动。

### 2.2 使用移动端

**方式 1: 本地访问**
```
浏览器访问: http://localhost:8001/mobile-client.html
```

**方式 2: 局域网访问**
```
1. 查看服务器 IP: ip addr show | grep inet
2. 浏览器访问: http://<服务器IP>:8001/mobile-client.html
   例如: http://192.168.31.99:8001/mobile-client.html
```

**移动端配置**
- 服务器地址: `ws://192.168.31.99:8001`（替换为实际 IP）
- 频道名称: `ai-assistant`（或自定义）

### 2.3 运行演示

```bash
# 运行端到端演示
cd /home/ai
python3 demo_e2e.py
```

演示将展示：
- 场景 1: 基础问询与响应
- 场景 2: 多步骤流程
- 场景 3: 指令控制

---

## 3. 使用场景详解

### 场景 1: 代码重构问询

**场景描述**
AI 工具（如 Crush）在重构代码时，需要用户确认是否继续。

**流程**

**步骤 1: AI 工具发送问询**
```javascript
// AI 工具端
const integrator = new CrushAIIntegrator(
    'ws://localhost:8001',
    'ai-assistant'
);

integrator.connect();

// 发送问询
integrator.askQuestion(
    '是否开始重构 userAuth 函数？',
    ['开始重构', '查看代码', '取消'],
    {
        function: 'userAuth',
        file: 'src/auth.js',
        line: 123
    }
);
```

**步骤 2: 移动端接收问询**
```
用户在手机上看到：

┌─────────────────────────────┐
│  ❓ AI问询                 │
│  14:30                    │
│                           │
│  是否开始重构 userAuth 函数？│
│                           │
│  📄 上下文:               │
│     函数: userAuth         │
│     文件: src/auth.js      │
│     行: 123                │
│                           │
│  [开始重构] [查看代码]     │
│  [取消]                   │
└─────────────────────────────┘
```

**步骤 3: 用户响应**
```
方式 1: 点击按钮
- 用户点击"开始重构"按钮
- 移动端自动发送响应

方式 2: 自定义输入
- 用户在输入框输入"开始，但使用 TypeScript"
- 点击"发送"按钮
```

**步骤 4: AI 工具接收响应**
```javascript
// AI 工具端收到响应
// message.type: 'message'
// message.payload.content: '开始重构'
// message.payload.responseType: 'option'
// message.payload.selectedOption: 0

// AI 工具继续执行
integrator.sendStatus('开始重构...', 10);
integrator.sendStatus('分析完成', 50);
integrator.sendStatus('重构完成', 100);
```

---

### 场景 2: 错误处理决策

**场景描述**
AI 工具执行任务时遇到错误，需要用户决定如何处理。

**流程**

**步骤 1: AI 工具发送错误问询**
```javascript
integrator.askQuestion(
    '发现代码错误：\n模块导入失败\n\n如何处理？',
    ['重试', '修改路径', '忽略', '查看错误详情'],
    {
        error: 'module_import_failed',
        file: 'src/utils/auth.js',
        line: 15
    }
);
```

**步骤 2: 移动端显示错误**
```
┌─────────────────────────────┐
│  ❓ AI问询                 │
│  14:35                    │
│                           │
│  发现代码错误：            │
│  模块导入失败              │
│                           │
│  如何处理？                │
│                           │
│  [重试] [修改路径]         │
│  [忽略] [查看错误详情]     │
└─────────────────────────────┘
```

**步骤 3: 用户查看详情**
```
用户点击"查看错误详情"按钮

移动端发送响应:
{
  type: 'message',
  payload: {
    content: '查看错误详情',
    responseType: 'option',
    selectedOption: 3
  }
}
```

**步骤 4: AI 工具发送详细信息**
```javascript
integrator.sendStatus(
    '错误详情:\n' +
    'Error: Cannot find module \'./auth\'\n' +
    'at src/utils/helper.js:15\n' +
    '\n建议路径: ./utils/auth.js'
);
```

**步骤 5: 用户自定义响应**
```
用户输入: "修改路径为 ./utils/auth.js"

移动端发送响应:
{
  type: 'message',
  payload: {
    content: '修改路径为 ./utils/auth.js',
    responseType: 'custom'
  }
}
```

---

### 场景 3: 快捷指令控制

**场景描述**
AI 工具正在执行长时间任务，用户需要控制任务流程。

**流程**

**步骤 1: AI 工具开始任务**
```javascript
integrator.sendStatus('开始重构多个函数...', 0);
```

**步骤 2: 移动端显示快捷指令面板**
```
┌─────────────────────────────┐
│  快捷指令面板              │
├─────────────────────────────┤
│  [▶️ 继续] [⏸️ 暂停] [⏹️ 停止]│
│  [🔄 重试] [⬅️ 上一步]      │
│  [✅ 确认] [❌ 取消]          │
│  [ℹ️ 详情] [❓ 帮助]          │
└─────────────────────────────┘
```

**步骤 3: 用户发送暂停指令**
```
用户点击"⏸️ 暂停"按钮

移动端发送:
{
  type: 'command',
  payload: {
    command: 'pause'
  }
}
```

**步骤 4: AI 工具处理暂停指令**
```javascript
// 收到暂停指令
integrator.pauseProcessing();
// 任务暂停，保存状态
```

**步骤 5: 用户发送继续指令**
```
用户点击"▶️ 继续"按钮

移动端发送:
{
  type: 'command',
  payload: {
    command: 'continue'
  }
}
```

**步骤 6: AI 工具恢复执行**
```javascript
integrator.continueProcessing();
// 从暂停点恢复执行
```

---

## 4. 消息协议

### 4.1 AI 工具 → 移动端

#### 问询消息
```json
{
  "type": "command",
  "channel": "ai-assistant",
  "payload": {
    "question": "是否继续重构？",
    "options": ["继续", "跳过", "取消"],
    "context": {
      "function": "userAuth",
      "file": "src/auth.js",
      "line": 123
    },
    "sessionId": "session_123456",
    "timestamp": 1710000000000
  }
}
```

#### 状态更新消息
```json
{
  "type": "message",
  "channel": "ai-assistant",
  "payload": {
    "from": "ai",
    "content": "正在重构 userAuth 函数...",
    "progress": 45,
    "sessionId": "session_123456",
    "timestamp": 1710000001000
  }
}
```

### 4.2 移动端 → AI 工具

#### 选项响应
```json
{
  "type": "message",
  "channel": "ai-assistant",
  "payload": {
    "content": "继续",
    "responseType": "option",
    "selectedOption": 0,
    "timestamp": 1710000002000
  }
}
```

#### 自定义响应
```json
{
  "type": "message",
  "channel": "ai-assistant",
  "payload": {
    "content": "继续，但使用 TypeScript 接口",
    "responseType": "custom",
    "timestamp": 1710000003000
  }
}
```

#### 快捷指令
```json
{
  "type": "command",
  "channel": "ai-assistant",
  "payload": {
    "command": "pause",
    "timestamp": 1710000004000
  }
}
```

---

## 5. 快捷指令列表

| 指令 | 按钮图标 | 用途 |
|------|---------|------|
| continue | ▶️ | 继续执行当前任务 |
| pause | ⏸️ | 暂停当前任务 |
| stop | ⏹️ | 停止当前任务 |
| retry | 🔄 | 重试上一个操作 |
| back | ⬅️ | 返回上一步 |
| confirm | ✅ | 确认当前操作 |
| cancel | ❌ | 取消当前操作 |
| details | ℹ️ | 查看详细信息 |
| help | ❓ | 显示帮助信息 |

---

## 6. AI 工具集成

### 6.1 Crush AI Assistant 集成

**安装**
```bash
# zhineng-bridge 已集成
# 无需额外安装
```

**使用示例**
```javascript
const CrushAIIntegrator = require('./zhineng-bridge/examples/crush_ai_integration.js');

// 创建集成器
const integrator = new CrushAIIntegrator(
    'ws://localhost:8001',
    'ai-assistant'
);

// 连接
integrator.connect();

// 发送问询
integrator.askQuestion(
    '是否开始重构？',
    ['开始', '取消']
);

// 发送状态更新
integrator.sendStatus('重构完成', 100);
```

**详细文档**
参见: `/home/ai/zhineng-bridge/examples/crush_ai_integration.js`

### 6.2 其他 AI 工具集成

**Trae**
```javascript
// 类似 Crush 集成
// 使用相同的 WebSocket 协议
const integrator = new AIToolIntegrator(
    'ws://localhost:8001',
    'ai-assistant'
);
```

**Claude Code**
```javascript
// Claude Code 集成
// 需要适配 Claude 的 API
const integrator = new ClaudeCodeIntegrator(
    'ws://localhost:8001',
    'ai-assistant'
);
```

---

## 7. 测试和验证

### 7.1 运行演示

```bash
# 端到端演示
python3 /home/ai/demo_e2e.py
```

### 7.2 手动测试

**步骤 1: 启动服务器**
```bash
cd /home/ai/zhineng-bridge/relay-server
node server.js
```

**步骤 2: 打开移动端**
```
浏览器访问: http://localhost:8001/mobile-client.html
```

**步骤 3: 运行 AI 工具模拟器**
```bash
cd /home/ai
python3 demo_e2e.py
```

**步骤 4: 观察交互**
- AI 工具发送问询
- 移动端接收并显示
- 用户响应
- AI 工具接收响应

---

## 8. 常见问题

### Q1: 无法连接到服务器？

**检查事项**:
1. 服务器是否运行: `lsof -i:8001`
2. 防火墙是否开放: `sudo ufw allow 8001`
3. 网络是否连通: `ping <服务器IP>`
4. 使用正确的协议: `ws://` (不是 `http://`)

### Q2: 移动端看不到问询？

**检查事项**:
1. 频道名称是否一致
2. AI 工具和移动端是否加入同一频道
3. 检查浏览器控制台是否有错误

### Q3: 响应后 AI 工具没有反应？

**检查事项**:
1. AI 工具是否正确处理消息
2. 检查消息格式是否符合协议
3. 查看服务器日志

### Q4: 如何添加新的快捷指令？

**步骤**:
1. 在 `mobile-client.html` 中添加按钮:
```html
<button class="cmd-btn" onclick="sendCommand('new_command')">
  新指令
</button>
```

2. 在 AI 工具中处理新指令:
```javascript
case 'new_command':
  // 处理逻辑
  break;
```

---

## 9. 扩展功能

### 9.1 语音交互（可选）

**实现思路**:
1. 添加语音输入按钮
2. 使用 Web Speech API
3. 将语音转换为文本
4. 发送文本响应

```javascript
// 语音输入示例
function startVoiceInput() {
    const recognition = new webkitSpeechRecognition();
    recognition.lang = 'zh-CN';

    recognition.onresult = (event) => {
        const text = event.results[0][0].transcript;
        sendMessage(text);
    };

    recognition.start();
}
```

### 9.2 历史记录（可选）

**实现思路**:
1. 将消息保存到 localStorage
2. 提供历史记录查看界面
3. 支持搜索和过滤

```javascript
// 保存历史记录
function saveToHistory(message) {
    const history = JSON.parse(localStorage.getItem('chat_history') || '[]');
    history.push(message);
    localStorage.setItem('chat_history', JSON.stringify(history));
}
```

### 9.3 通知推送（可选）

**实现思路**:
1. 使用 Service Workers
2. 注册 Push Notifications
3. 后台接收新问询时推送通知

---

## 10. 性能优化

### 10.1 消息压缩

对于大消息，可以启用压缩:

```javascript
// AI 工具端
const compressed = pako.deflate(JSON.stringify(message));
ws.send(compressed);

// 移动端
const decompressed = pako.inflate(message.data);
const data = JSON.parse(decompressed);
```

### 10.2 批量发送

对于多个小消息，可以批量发送:

```javascript
// 批量发送
const batch = [
  message1,
  message2,
  message3
];
ws.send(JSON.stringify({
  type: 'batch',
  messages: batch
}));
```

---

## 11. 安全建议

### 11.1 使用 WSS

在生产环境中使用 WebSocket Secure:

```javascript
const integrator = new CrushAIIntegrator(
    'wss://yourserver.com:8443',
    'ai-assistant'
);
```

### 11.2 身份验证

添加身份验证机制:

```javascript
// 连接时发送 token
ws.send(JSON.stringify({
  type: 'auth',
  token: 'your_jwt_token'
}));
```

### 11.3 消息加密

对敏感消息进行端到端加密:

```javascript
// 加密消息
const encrypted = CryptoJS.AES.encrypt(message, secretKey);

// 解密消息
const decrypted = CryptoJS.AES.decrypt(encrypted, secretKey);
```

---

## 12. 文档资源

### 核心文档
- 核心业务流程: `/home/ai/zhineng-bridge/docs/CORE_BUSINESS_FLOW.md`
- 使用指南: 本文档
- AI 工具集成: `/home/ai/zhineng-bridge/examples/crush_ai_integration.js`

### 代码示例
- 移动端: `/home/ai/zhineng-bridge/mobile-client.html`
- Relay Server: `/home/ai/zhineng-bridge/relay-server/server.js`
- 端到端演示: `/home/ai/demo_e2e.py`

### 测试工具
- E2E 测试: `/home/ai/e2e_test.py`
- 演示脚本: `/home/ai/demo_e2e.py`

---

## 13. 总结

### 核心价值
1. **解放双手**: 用户无需一直守在电脑前
2. **实时响应**: AI 工具的问询即时推送到手机
3. **灵活控制**: 随时随地下达指令
4. **提升效率**: AI 工具无需等待，持续工作

### 技术特点
- WebSocket 实时通信
- 轻量级 Relay Server
- 响应式移动端界面
- 可扩展的消息协议
- 完整的快捷指令系统

### 适用场景
- 远程开发
- 离线开发
- 多任务并行
- 团队协作

---

**文档版本**: 1.0
**最后更新**: 2025-03-22
**维护者**: Zhineng Bridge Team

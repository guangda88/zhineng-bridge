# 智桥实际运行测试指南

## 快速开始（一键测试）

```bash
cd /home/ai/zhineng-bridge
./scripts/test_real_runtime.sh
```

这个脚本会自动：
1. ✅ 检查依赖（python3, crush等）
2. ✅ 启动中继服务器
3. ✅ 启动会话管理器
4. ✅ 运行AI互联测试
5. ✅ 自动清理进程

## 手动测试步骤

### 1️⃣ 启动中继服务器

**终端1：**
```bash
cd /home/ai/zhineng-bridge/relay-server
python3 start_server.py
```

你应该看到：
```
🚀 启动 zhineng-bridge 中继服务器

  健康检查: http://0.0.0.0:8080/health
✓ 服务器启动在 ws://0.0.0.0:8766
```

### 2️⃣ 启动会话管理器（可选）

**终端2：**
```bash
cd /home/ai/zhineng-bridge/phase1/session_manager
python3 start_manager.py
```

### 3️⃣ 运行AI互联测试

**终端3：**
```bash
cd /home/ai/zhineng-bridge
python3 scripts/test_ai_communication.py
```

### 4️⃣ 观察测试结果

测试会展示：
- ✅ **Agent注册**：3个AI工具注册到智桥
- ✅ **Agent发现**：互相发现对方
- ✅ **直接通信**：Agent→Agent消息传递
- ✅ **频道通信**：群组讨论
- ✅ **历史查询**：消息历史完整

## 测试场景说明

### 场景1：Claude Code → Crush AI
```
Claude: "请帮我审查这段代码：def add(a, b): return a + b"
Crush: [接收到消息，可以进行回复]
```

### 场景2：群组讨论
```
频道: code-review
成员: Claude, Crush, Cursor

Claude: "大家好，新的PR已准备好审查！"
Crush: "我来看一下代码质量"
Cursor: "我来检查是否有bug"
```

## 验证成功标志

如果测试成功，你会看到：

```
✅ 连接成功！
✅ Claude Code 已注册
✅ Crush AI 已注册
✅ Cursor Assistant 已注册
✅ 发现 3 个 Agent
✅ 消息已发送
✅ 频道创建成功
✅ 消息已广播到频道
✅ 所有测试通过！
```

这就是打破AI孤岛的证明！🎉

## 问题排查

### 中继服务器启动失败
```bash
# 检查端口占用
lsof -i :8766

# 停止占用端口的进程
pkill -f "relay-server/server.py"
```

### WebSocket连接失败
```bash
# 检查服务是否在运行
ps aux | grep start_server

# 查看日志
tail -f /tmp/relay_server.log
```

### 测试脚本权限错误
```bash
chmod +x scripts/test_real_runtime.sh
```

## 实际对话示例

测试成功后，你可以使用以下方式让真实AI工具通过智桥互联：

### 通过Web UI
打开：`http://localhost:8000/web/ui/index.html`

### 通过WebSocket客户端
```python
import asyncio
import websockets
import json

async def main():
    async with websockets.connect("ws://localhost:8766") as ws:
        # 注册你的Agent
        await ws.send(json.dumps({
            "type": "register_agent",
            "agent_id": "my-agent",
            "name": "My AI Tool",
            "capabilities": ["code", "analysis"]
        }))

        # 发送消息给其他Agent
        await ws.send(json.dumps({
            "type": "inter_chat",
            "to": "crush-1",
            "text": "你好，我是新来的Agent！"
        }))

        # 接收响应
        response = await ws.recv()
        print(response)

asyncio.run(main())
```

## 下一步

测试成功后，你可以：
1. 让真实的Crush、Claude等工具通过智桥互联
2. 创建自己的AI Agent并加入智桥网络
3. 使用频道进行多Agent协作
4. 集成到你自己的项目中

---

**这就是打破AI孤岛的真实证明！**

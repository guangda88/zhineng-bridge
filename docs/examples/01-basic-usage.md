# 基础用法 — WebSocket 连接与消息

## 连接到智桥服务器

```javascript
// web/ui/js/client.js 中的连接方式
const ws = new WebSocket('ws://localhost:8765');

ws.onopen = () => {
    console.log('✅ 已连接到智桥服务器');
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('收到消息:', data);
};

ws.onerror = (error) => {
    console.error('❌ 连接错误:', error);
};

ws.onclose = () => {
    console.log('连接已关闭');
};
```

## 发送心跳

```javascript
// 每 10 秒发送一次心跳
setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }));
    }
}, 10000);
```

## 管理会话

```javascript
// 列出所有会话
ws.send(JSON.stringify({ type: 'list_sessions', data: {} }));

// 创建新会话
ws.send(JSON.stringify({
    type: 'start_session',
    tool_name: 'crush',
    args: ['--help']
}));

// 停止会话
ws.send(JSON.stringify({
    type: 'stop_session',
    session_id: 'your-session-id'
}));

// 删除会话
ws.send(JSON.stringify({
    type: 'delete_session',
    session_id: 'your-session-id'
}));
```

## Python 客户端

```python
import asyncio
import json
import websockets

async def connect():
    async with websockets.connect('ws://localhost:8765') as ws:
        # 列出会话
        await ws.send(json.dumps({'type': 'list_sessions', 'data': {}}))
        response = await ws.recv()
        print(json.loads(response))

        # 创建会话
        await ws.send(json.dumps({
            'type': 'start_session',
            'tool_name': 'crush',
            'args': []
        }))
        response = await ws.recv()
        data = json.loads(response)
        print(f'会话已创建: {data.get("session_id")}')

asyncio.run(connect())
```

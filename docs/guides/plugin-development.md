# 插件开发指南

## 概述

智桥插件系统允许开发者扩展服务器功能，通过钩子（Hook）监听事件、通过命令（Command）暴露功能。

## 快速开始

### 1. 创建插件文件

在 `plugins/` 目录创建 `.py` 文件：

```
plugins/
├── my_plugin.py       ← 单文件插件
└── my_complex_plugin/  ← 包形式插件
    └── __init__.py
```

### 2. 实现插件类

```python
from plugin_system import PluginInterface

class MyPlugin(PluginInterface):
    # 必填：插件元信息（类属性）
    plugin_id = "my_plugin"       # 唯一标识符
    name = "我的插件"              # 显示名称

    # 可选元信息
    version = "1.0.0"
    description = "插件描述"
    author = "作者名"
    category = "general"          # general/monitoring/automation/messaging
    dependencies = []             # 依赖的其他插件 ID
    config_schema = {}            # 配置 JSON Schema

    def on_load(self, ctx):
        """加载时调用 — 在此注册钩子和命令"""
        pass

    def on_enable(self):
        """启用时调用"""
        pass

    def on_disable(self):
        """禁用时调用"""
        pass

    def on_unload(self):
        """卸载时调用 — 清理资源"""
        pass
```

### 3. 注册钩子

```python
def on_load(self, ctx):
    self.register_hook("on_message_received", self.handle_message)

def handle_message(self, message: dict):
    # 处理消息，返回值会收集到 trigger_hook 的结果列表
    msg_type = message.get("type")
    if msg_type == "output":
        message["output"] = "[处理后] " + message.get("output", "")
    return message
```

### 4. 注册命令

```python
def on_load(self, ctx):
    self.register_command("my_cmd", self.run_command)

def run_command(self, arg1: str = "default"):
    return {"result": arg1}
```

## 生命周期

```
发现 → 加载(on_load) → 启用(on_enable) ↔ 禁用(on_disable) → 卸载(on_unload)
                         ↑                        ↓
                         └──── 可多次切换 ──────────┘
```

- **LOADED**: 文件加载完成，钩子和命令已注册
- **ENABLED**: 插件活跃，钩子处理器会被触发
- **DISABLED**: 插件暂停，钩子处理器被跳过
- **ERROR**: 加载失败

## 可用事件钩子

| 事件 | 触发时机 | 处理器签名 |
|------|----------|------------|
| `on_message_received` | 收到客户端消息 | `(message: dict) -> Any` |
| `on_message_sent` | 向客户端发送消息 | `(message: dict) -> Any` |
| `on_session_created` | AI 会话创建 | `(session_id: str) -> None` |
| `on_session_destroyed` | AI 会话销毁 | `(session_id: str) -> None` |
| `on_user_connected` | WebSocket 连接建立 | `(user_id: str) -> None` |
| `on_user_disconnected` | WebSocket 连接断开 | `(user_id: str) -> None` |

## 插件配置

通过 API 设置配置，插件内通过 `self.get_config()` 读取：

```python
class MyPlugin(PluginInterface):
    def on_load(self, ctx):
        config = self.get_config()
        self._threshold = config.get("threshold", 100)
```

```bash
# 设置配置
curl -X POST http://localhost:8080/api/plugins/my_plugin/config \
  -H "Authorization: Bearer TOKEN" \
  -d '{"threshold": 200}'
```

## 最佳实践

1. **插件 ID 唯一** — 使用下划线命名，避免与标准库冲突（如不要用 `dis`、`os`）
2. **幂等的 on_load** — 重复加载不应出错
3. **异常处理** — 钩子处理器中的异常不会影响其他插件，但应自行处理
4. **资源清理** — `on_unload` 中释放所有资源（文件句柄、定时器等）
5. **无阻塞** — 钩子处理器应快速返回，耗时操作使用异步或线程

## 示例：消息过滤插件

```python
from plugin_system import PluginInterface

class FilterPlugin(PluginInterface):
    plugin_id = "msg_filter"
    name = "消息过滤器"
    version = "1.0.0"
    description = "过滤敏感词"

    def on_load(self, ctx):
        self._blocked = {"password", "secret", "token"}
        self.register_hook("on_message_sent", self._filter)

    def _filter(self, message: dict):
        output = message.get("output", "")
        for word in self._blocked:
            if word in output.lower():
                message["output"] = "[已过滤]"
                break
        return message
```

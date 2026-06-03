# 插件开发

## 最简插件

在 `plugins/` 目录下创建 Python 文件，继承 `PluginInterface`：

```python
# plugins/hello_world.py
from plugin_system import PluginInterface

class HelloWorldPlugin(PluginInterface):
    plugin_id = "hello_world"     # 全局唯一 ID
    name = "Hello World"          # 显示名称
    version = "1.0.0"            # 版本号
    description = "示例插件"      # 描述
    author = "me"                # 作者
    category = "general"         # 分类

    def on_load(self, ctx):
        """插件加载时调用 — 注册钩子和命令"""
        self.register_hook("on_message_received", self._on_message)
        self.register_command("hello", self._hello)

    def on_enable(self):
        """插件启用"""
        pass

    def on_disable(self):
        """插件禁用"""
        pass

    def on_unload(self):
        """插件卸载"""
        pass

    def _on_message(self, message: dict):
        """处理消息钩子"""
        print(f"收到消息: {message.get('type')}")
        return message

    def _hello(self, name: str = "world"):
        """自定义命令"""
        return f"Hello, {name}!"
```

## 支持的事件钩子

| 钩子 | 触发时机 | 参数 |
|------|----------|------|
| `on_message_received` | 收到 WebSocket 消息 | `message: dict` |
| `on_message_sent` | 发送 WebSocket 消息 | `message: dict` |
| `on_session_created` | 创建会话 | `session_id: str` |
| `on_session_destroyed` | 销毁会话 | `session_id: str` |
| `on_user_connected` | 用户连接 | `user_id: str` |
| `on_user_disconnected` | 用户断开 | `user_id: str` |

## 插件配置

```python
class MyPlugin(PluginInterface):
    def on_load(self, ctx):
        config = self.get_config()
        self._prefix = config.get("prefix", "[默认]")

    def on_enable(self):
        # 通过 API 设置配置后可读取
        config = self.get_config()
        self._prefix = config.get("prefix", self._prefix)
```

## 管理插件（API）

```bash
# 发现可用插件
curl -X POST http://localhost:8080/api/plugins/discover \
  -H "Authorization: Bearer eyJ..."

# 列出已加载插件
curl http://localhost:8080/api/plugins \
  -H "Authorization: Bearer eyJ..."

# 启用插件
curl -X POST http://localhost:8080/api/plugins/hello_world/enable \
  -H "Authorization: Bearer eyJ..."

# 查看插件命令
curl http://localhost:8080/api/plugins/hello_world/commands \
  -H "Authorization: Bearer eyJ..."

# 配置插件
curl -X POST http://localhost:8080/api/plugins/hello_world/config \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{"prefix": "[智桥]"}'

# 重载插件
curl -X POST http://localhost:8080/api/plugins/hello_world/reload \
  -H "Authorization: Bearer eyJ..."

# 禁用插件
curl -X POST http://localhost:8080/api/plugins/hello_world/disable \
  -H "Authorization: Bearer eyJ..."
```

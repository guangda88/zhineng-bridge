#!/usr/bin/env python3
"""
示例插件 — 消息转换

在消息发送前对其进行转换处理（如添加前缀、格式化）。
"""

from plugin_system import PluginInterface


class MessageTransformPlugin(PluginInterface):
    plugin_id = "msg_transform"
    name = "消息转换"
    version = "1.0.0"
    description = "消息格式转换和预处理"
    author = "zhineng-bridge"
    category = "messaging"

    def on_load(self, ctx):
        self._prefix = "[智桥] "
        self._transforms_enabled = True
        self.register_hook("on_message_sent", self._transform_message)
        self.register_command("set_prefix", self._set_prefix)

    def on_enable(self):
        self._transforms_enabled = True

    def on_disable(self):
        self._transforms_enabled = False

    def on_unload(self):
        pass

    def _transform_message(self, message: dict):
        if not self._transforms_enabled:
            return message
        if message.get("type") == "output" and "output" in message:
            message["output"] = self._prefix + message["output"]
        return message

    def _set_prefix(self, prefix: str = ""):
        self._prefix = prefix
        return {"prefix_set": prefix}

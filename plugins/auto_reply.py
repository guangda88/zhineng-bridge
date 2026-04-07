#!/usr/bin/env python3
"""
示例插件 — 自动回复

当消息匹配关键词时自动回复。
"""

from plugin_system import PluginInterface


class AutoReplyPlugin(PluginInterface):
    plugin_id = "auto_reply"
    name = "自动回复"
    version = "1.0.0"
    description = "根据关键词自动回复消息"
    author = "zhineng-bridge"
    category = "automation"

    def on_load(self, ctx):
        self._replies = {
            "hello": "你好！我是智桥助手 🌉",
            "help": "可用命令: stats, ping, tools",
            "ping": "pong 🏓",
            "version": "zhineng-bridge v1.3.0",
        }
        self.register_hook("on_message_received", self._check_auto_reply)

    def on_enable(self):
        pass

    def on_disable(self):
        pass

    def on_unload(self):
        self._replies.clear()

    def _check_auto_reply(self, message: dict):
        text = message.get("data", {}).get("text", "") or message.get("data", {}).get("message", "")
        if not text:
            return None
        text_lower = text.lower().strip()
        for keyword, reply in self._replies.items():
            if keyword in text_lower:
                return {"auto_reply": reply, "triggered_by": keyword}
        return None

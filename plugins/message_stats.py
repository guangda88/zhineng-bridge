#!/usr/bin/env python3
"""
示例插件 — 消息统计

统计所有经过服务器的消息类型和数量。
"""

import time
from collections import defaultdict
from plugin_system import PluginInterface, PluginState


class MessageStatsPlugin(PluginInterface):
    plugin_id = "message_stats"
    name = "消息统计"
    version = "1.0.0"
    description = "统计 WebSocket 消息的类型和数量"
    author = "zhineng-bridge"
    category = "monitoring"

    def on_load(self, ctx):
        self._stats = defaultdict(int)
        self._start_time = time.time()
        self.register_hook("on_message_received", self._count_message)
        self.register_command("stats", self._get_stats)

    def on_enable(self):
        self._stats.clear()
        self._start_time = time.time()

    def on_disable(self):
        pass

    def on_unload(self):
        self._stats.clear()

    def _count_message(self, message: dict):
        msg_type = message.get("type", "unknown")
        self._stats[msg_type] += 1

    def _get_stats(self):
        uptime = time.time() - self._start_time
        return {
            "uptime_seconds": round(uptime, 1),
            "total_messages": sum(self._stats.values()),
            "by_type": dict(self._stats),
        }

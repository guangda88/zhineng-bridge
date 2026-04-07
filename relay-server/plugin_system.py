#!/usr/bin/env python3
"""
插件系统

支持动态加载、生命周期管理、钩子机制。
"""

import os
import sys
import json
import importlib
import inspect
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from logger import get_logger


class PluginState(Enum):
    """插件状态"""
    LOADED = "loaded"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


@dataclass
class PluginInfo:
    """插件元信息"""
    plugin_id: str
    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    homepage: str = ""
    category: str = "general"
    dependencies: List[str] = field(default_factory=list)
    config_schema: dict = field(default_factory=dict)
    state: PluginState = PluginState.LOADED
    error_message: Optional[str] = None
    loaded_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "plugin_id": self.plugin_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "category": self.category,
            "dependencies": self.dependencies,
            "state": self.state.value,
            "error_message": self.error_message,
            "loaded_at": self.loaded_at.isoformat(),
        }


class PluginInterface:
    """
    插件基类 — 所有插件必须继承此类。

    生命周期:
        on_load()      → 插件加载时调用（注册钩子、初始化状态）
        on_enable()    → 插件启用时调用（启动服务、监听）
        on_disable()   → 插件禁用时调用（暂停服务、清理）
        on_unload()    → 插件卸载时调用（释放资源）

    钩子:
        register_hook(event_name, handler)  → 注册事件处理器
        register_command(name, handler)     → 注册自定义命令

    支持的事件钩子:
        - on_message_received  → WebSocket 消息到达前
        - on_message_sent      → WebSocket 消息发送后
        - on_session_created   → 会话创建后
        - on_session_destroyed → 会话销毁后
        - on_user_connected    → 用户连接后
        - on_user_disconnected → 用户断开后
    """

    plugin_id: str = ""
    name: str = ""
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    category: str = "general"
    dependencies: list = []
    config_schema: dict = {}

    def __init__(self):
        self._hooks: Dict[str, List[Callable]] = {}
        self._commands: Dict[str, Callable] = {}
        self._config: dict = {}
        self._context: dict = {}

    def on_load(self, context: dict) -> None:
        """插件加载时调用"""
        pass

    def on_enable(self) -> None:
        """插件启用时调用"""
        pass

    def on_disable(self) -> None:
        """插件禁用时调用"""
        pass

    def on_unload(self) -> None:
        """插件卸载时调用"""
        pass

    def register_hook(self, event: str, handler: Callable) -> None:
        """注册事件钩子"""
        if event not in self._hooks:
            self._hooks[event] = []
        self._hooks[event].append(handler)

    def register_command(self, name: str, handler: Callable) -> None:
        """注册自定义命令"""
        self._commands[name] = handler

    def get_hooks(self) -> Dict[str, List[Callable]]:
        return self._hooks

    def get_commands(self) -> Dict[str, Callable]:
        return self._commands

    def set_config(self, config: dict) -> None:
        self._config = config

    def get_config(self) -> dict:
        return self._config


class PluginManager:
    """插件管理器"""

    PLUGIN_DIR = "plugins"

    def __init__(self, base_dir: str = None):
        self.logger = get_logger(__name__)
        self.base_dir = base_dir or os.path.dirname(os.path.abspath(__file__))
        self.plugin_dir = os.path.join(self.base_dir, self.PLUGIN_DIR)
        self._plugins: Dict[str, PluginInterface] = {}
        self._plugin_info: Dict[str, PluginInfo] = {}
        self._hooks: Dict[str, List[tuple]] = {}  # event -> [(plugin_id, handler)]
        self._commands: Dict[str, tuple] = {}  # command -> (plugin_id, handler)
        self._context: dict = {}

        os.makedirs(self.plugin_dir, exist_ok=True)
        sys.path.insert(0, self.plugin_dir)

    def set_context(self, **kwargs) -> None:
        """设置全局上下文（服务器实例、session_manager 等）"""
        self._context.update(kwargs)

    # ========================================================================
    # 加载/卸载
    # ========================================================================

    def discover_plugins(self) -> List[str]:
        """扫描插件目录，返回可加载的插件ID列表"""
        discovered = []
        if not os.path.isdir(self.plugin_dir):
            return discovered

        for entry in os.listdir(self.plugin_dir):
            plugin_path = os.path.join(self.plugin_dir, entry)
            if os.path.isdir(plugin_path):
                init_file = os.path.join(plugin_path, "__init__.py")
                if os.path.exists(init_file):
                    discovered.append(entry)
            elif entry.endswith(".py") and not entry.startswith("_"):
                discovered.append(entry[:-3])

        return discovered

    def load_plugin(self, plugin_id: str) -> Optional[PluginInfo]:
        """加载单个插件"""
        if plugin_id in self._plugins:
            return self._plugin_info[plugin_id]

        try:
            module = importlib.import_module(plugin_id)
            plugin_class = None

            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (inspect.isclass(attr) and
                        issubclass(attr, PluginInterface) and
                        attr is not PluginInterface):
                    plugin_class = attr
                    break

            if not plugin_class:
                raise ValueError(f"No PluginInterface subclass found in plugin '{plugin_id}'")

            plugin_instance = plugin_class()

            info = PluginInfo(
                plugin_id=plugin_id,
                name=getattr(plugin_instance, 'name', plugin_id),
                version=getattr(plugin_instance, 'version', '1.0.0'),
                description=getattr(plugin_instance, 'description', ''),
                author=getattr(plugin_instance, 'author', ''),
                category=getattr(plugin_instance, 'category', 'general'),
                dependencies=getattr(plugin_instance, 'dependencies', []),
            )

            self._plugins[plugin_id] = plugin_instance
            self._plugin_info[plugin_id] = info

            plugin_instance.on_load(self._context)

            for event, handlers in plugin_instance.get_hooks().items():
                if event not in self._hooks:
                    self._hooks[event] = []
                for handler in handlers:
                    self._hooks[event].append((plugin_id, handler))

            for cmd_name, handler in plugin_instance.get_commands().items():
                self._commands[cmd_name] = (plugin_id, handler)

            info.state = PluginState.LOADED
            self.logger.info("Plugin loaded", plugin_id=plugin_id, name=info.name)
            return info

        except Exception as e:
            self.logger.error("Failed to load plugin", plugin_id=plugin_id, error=str(e))
            info = PluginInfo(plugin_id=plugin_id, name=plugin_id, state=PluginState.ERROR, error_message=str(e))
            self._plugin_info[plugin_id] = info
            return info

    def load_all(self) -> Dict[str, PluginInfo]:
        """加载所有发现的插件"""
        for plugin_id in self.discover_plugins():
            self.load_plugin(plugin_id)
        return dict(self._plugin_info)

    def unload_plugin(self, plugin_id: str) -> bool:
        """卸载插件"""
        if plugin_id not in self._plugins:
            return False

        plugin = self._plugins[plugin_id]
        info = self._plugin_info[plugin_id]

        if info.state == PluginState.ENABLED:
            plugin.on_disable()
        plugin.on_unload()

        self._hooks = {e: [(pid, h) for pid, h in hs if pid != plugin_id]
                       for e, hs in self._hooks.items()}
        self._commands = {c: (pid, h) for c, (pid, h) in self._commands.items()
                          if pid != plugin_id}

        del self._plugins[plugin_id]
        del self._plugin_info[plugin_id]

        if plugin_id in sys.modules:
            del sys.modules[plugin_id]

        self.logger.info("Plugin unloaded", plugin_id=plugin_id)
        return True

    # ========================================================================
    # 启用/禁用
    # ========================================================================

    def enable_plugin(self, plugin_id: str) -> bool:
        if plugin_id not in self._plugins:
            return False
        plugin = self._plugins[plugin_id]
        info = self._plugin_info[plugin_id]
        plugin.on_enable()
        info.state = PluginState.ENABLED
        self.logger.info("Plugin enabled", plugin_id=plugin_id)
        return True

    def disable_plugin(self, plugin_id: str) -> bool:
        if plugin_id not in self._plugins:
            return False
        plugin = self._plugins[plugin_id]
        info = self._plugin_info[plugin_id]
        plugin.on_disable()
        info.state = PluginState.DISABLED
        self.logger.info("Plugin disabled", plugin_id=plugin_id)
        return True

    # ========================================================================
    # 钩子触发
    # ========================================================================

    def trigger_hook(self, event: str, *args, **kwargs) -> List[Any]:
        """触发事件钩子，返回所有处理器的返回值"""
        results = []
        for plugin_id, handler in self._hooks.get(event, []):
            info = self._plugin_info.get(plugin_id)
            if info and info.state != PluginState.ENABLED:
                continue
            try:
                result = handler(*args, **kwargs)
                results.append(result)
            except Exception as e:
                self.logger.error("Hook handler error", plugin_id=plugin_id,
                                  hook_event=event, error=str(e))
        return results

    def execute_command(self, command: str, *args, **kwargs) -> Any:
        """执行插件注册的命令"""
        if command not in self._commands:
            raise ValueError(f"Unknown command: {command}")
        plugin_id, handler = self._commands[command]
        info = self._plugin_info.get(plugin_id)
        if info and info.state != PluginState.ENABLED:
            raise RuntimeError(f"Plugin {plugin_id} is not enabled")
        return handler(*args, **kwargs)

    # ========================================================================
    # 查询
    # ========================================================================

    def list_plugins(self) -> List[PluginInfo]:
        return list(self._plugin_info.values())

    def get_plugin_info(self, plugin_id: str) -> Optional[PluginInfo]:
        return self._plugin_info.get(plugin_id)

    def get_plugin(self, plugin_id: str) -> Optional[PluginInterface]:
        return self._plugins.get(plugin_id)

    def list_commands(self) -> Dict[str, str]:
        """返回命令名 → 插件ID 映射"""
        return {cmd: pid for cmd, (pid, _) in self._commands.items()}

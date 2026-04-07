"""
插件系统单元测试
"""

import os
import sys
import json
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'relay-server'))

from plugin_system import PluginManager, PluginInterface, PluginState, PluginInfo


class _DummyPlugin(PluginInterface):
    plugin_id = "dummy"
    name = "Dummy Plugin"
    version = "0.1.0"
    description = "test plugin"

    def __init__(self):
        super().__init__()
        self.loaded = False
        self.enabled = False
        self.unloaded = False

    def on_load(self, ctx):
        self.loaded = True
        self.register_hook("on_message_received", self._on_msg)
        self.register_command("ping", self._ping)

    def on_enable(self):
        self.enabled = True

    def on_disable(self):
        self.enabled = False

    def on_unload(self):
        self.unloaded = True

    def _on_msg(self, msg):
        return msg

    def _ping(self):
        return "pong"


def _write_plugin_file(plugin_dir, filename, content):
    os.makedirs(plugin_dir, exist_ok=True)
    path = os.path.join(plugin_dir, filename)
    with open(path, 'w') as f:
        f.write(content)
    return path


class TestPluginInterface:
    def test_register_hook(self):
        p = _DummyPlugin()
        p.on_load({})
        hooks = p.get_hooks()
        assert "on_message_received" in hooks
        assert len(hooks["on_message_received"]) == 1

    def test_register_command(self):
        p = _DummyPlugin()
        p.on_load({})
        cmds = p.get_commands()
        assert "ping" in cmds

    def test_set_get_config(self):
        p = _DummyPlugin()
        p.set_config({"key": "value"})
        assert p.get_config() == {"key": "value"}


class TestPluginManagerInit:
    def test_creates_plugin_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = PluginManager(base_dir=tmpdir)
            assert os.path.isdir(os.path.join(tmpdir, "plugins"))

    def test_default_plugin_dir(self):
        pm = PluginManager()
        assert os.path.isdir(pm.plugin_dir)


class TestPluginManagerDiscover:
    def test_discover_py_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = PluginManager(base_dir=tmpdir)
            _write_plugin_file(pm.plugin_dir, "hello.py", "# test")
            _write_plugin_file(pm.plugin_dir, "_hidden.py", "# skip")
            discovered = pm.discover_plugins()
            assert "hello" in discovered
            assert "_hidden" not in discovered

    def test_discover_package(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = PluginManager(base_dir=tmpdir)
            pkg_dir = os.path.join(pm.plugin_dir, "mypkg")
            _write_plugin_file(pkg_dir, "__init__.py", "# pkg")
            discovered = pm.discover_plugins()
            assert "mypkg" in discovered

    def test_discover_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = PluginManager(base_dir=tmpdir)
            assert pm.discover_plugins() == []


class TestPluginManagerLifecycle:
    def test_load_plugin(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = PluginManager(base_dir=tmpdir)
            code = '''
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'relay-server'))
from plugin_system import PluginInterface

class TestPlug(PluginInterface):
    plugin_id = "test_plug"
    name = "Test"
    version = "1.0.0"
    def on_load(self, ctx):
        self.register_hook("on_message_received", lambda m: m)
        self.register_command("hello", lambda: "world")
'''
            _write_plugin_file(pm.plugin_dir, "test_plug.py", code)
            info = pm.load_plugin("test_plug")
            assert info is not None
            assert info.plugin_id == "test_plug"
            assert info.state == PluginState.LOADED

    def test_load_all(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = PluginManager(base_dir=tmpdir)
            code = '''
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'relay-server'))
from plugin_system import PluginInterface

class PlugA(PluginInterface):
    plugin_id = "plug_a"
    name = "A"
'''
            _write_plugin_file(pm.plugin_dir, "plug_a.py", code)
            code_b = '''
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'relay-server'))
from plugin_system import PluginInterface

class PlugB(PluginInterface):
    plugin_id = "plug_b"
    name = "B"
'''
            _write_plugin_file(pm.plugin_dir, "plug_b.py", code_b)
            result = pm.load_all()
            assert len(result) == 2

    def test_load_duplicate_returns_existing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = PluginManager(base_dir=tmpdir)
            code = '''
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'relay-server'))
from plugin_system import PluginInterface

class DupPlug(PluginInterface):
    plugin_id = "dup"
    name = "Dup"
'''
            _write_plugin_file(pm.plugin_dir, "dup.py", code)
            info1 = pm.load_plugin("dup")
            info2 = pm.load_plugin("dup")
            assert info1 is info2

    def test_load_bad_plugin_marks_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = PluginManager(base_dir=tmpdir)
            _write_plugin_file(pm.plugin_dir, "bad.py", "raise RuntimeError('broken')")
            info = pm.load_plugin("bad")
            assert info.state == PluginState.ERROR
            assert info.error_message is not None

    def test_load_no_subclass(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = PluginManager(base_dir=tmpdir)
            _write_plugin_file(pm.plugin_dir, "noplugin.py", "x = 42")
            info = pm.load_plugin("noplugin")
            assert info.state == PluginState.ERROR

    def test_unload_plugin(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = PluginManager(base_dir=tmpdir)
            code = '''
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'relay-server'))
from plugin_system import PluginInterface

class UnloadPlug(PluginInterface):
    plugin_id = "unload_me"
    name = "Unload"
'''
            _write_plugin_file(pm.plugin_dir, "unload_me.py", code)
            pm.load_plugin("unload_me")
            assert pm.unload_plugin("unload_me") is True
            assert pm.get_plugin_info("unload_me") is None

    def test_unload_nonexistent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = PluginManager(base_dir=tmpdir)
            assert pm.unload_plugin("nope") is False


class TestPluginManagerEnableDisable:
    def test_enable_plugin(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = PluginManager(base_dir=tmpdir)
            code = '''
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'relay-server'))
from plugin_system import PluginInterface

class EnPlug(PluginInterface):
    plugin_id = "en"
    name = "En"
'''
            _write_plugin_file(pm.plugin_dir, "en.py", code)
            pm.load_plugin("en")
            assert pm.enable_plugin("en") is True
            info = pm.get_plugin_info("en")
            assert info.state == PluginState.ENABLED

    def test_disable_plugin(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = PluginManager(base_dir=tmpdir)
            code = '''
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'relay-server'))
from plugin_system import PluginInterface

class DisPlug(PluginInterface):
    plugin_id = "dis_plug"
    name = "Dis"
'''
            _write_plugin_file(pm.plugin_dir, "dis_plug.py", code)
            pm.load_plugin("dis_plug")
            pm.enable_plugin("dis_plug")
            assert pm.disable_plugin("dis_plug") is True
            info = pm.get_plugin_info("dis_plug")
            assert info.state == PluginState.DISABLED

    def test_enable_nonexistent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = PluginManager(base_dir=tmpdir)
            assert pm.enable_plugin("nope") is False

    def test_disable_nonexistent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = PluginManager(base_dir=tmpdir)
            assert pm.disable_plugin("nope") is False


class TestPluginManagerHooks:
    def test_trigger_hook(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = PluginManager(base_dir=tmpdir)
            code = '''
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'relay-server'))
from plugin_system import PluginInterface

class HookPlug(PluginInterface):
    plugin_id = "hooker"
    name = "Hooker"
    def on_load(self, ctx):
        self.register_hook("on_message_received", self._h)
    def _h(self, msg):
        return msg.get("type")
'''
            _write_plugin_file(pm.plugin_dir, "hooker.py", code)
            pm.load_plugin("hooker")
            pm.enable_plugin("hooker")
            results = pm.trigger_hook("on_message_received", {"type": "chat"})
            assert results == ["chat"]

    def test_trigger_hook_disabled_skips(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = PluginManager(base_dir=tmpdir)
            code = '''
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'relay-server'))
from plugin_system import PluginInterface

class SkipPlug(PluginInterface):
    plugin_id = "skipper"
    name = "Skipper"
    def on_load(self, ctx):
        self.register_hook("on_message_received", lambda m: "should_not_appear")
'''
            _write_plugin_file(pm.plugin_dir, "skipper.py", code)
            pm.load_plugin("skipper")
            # not enabled — should be skipped
            results = pm.trigger_hook("on_message_received", {})
            assert results == []

    def test_trigger_hook_error_handled(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = PluginManager(base_dir=tmpdir)
            code = '''
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'relay-server'))
from plugin_system import PluginInterface

class ErrPlug(PluginInterface):
    plugin_id = "errplug"
    name = "Err"
    def on_load(self, ctx):
        self.register_hook("on_message_received", self._boom)
    def _boom(self, m):
        raise RuntimeError("boom")
'''
            _write_plugin_file(pm.plugin_dir, "errplug.py", code)
            pm.load_plugin("errplug")
            pm.enable_plugin("errplug")
            results = pm.trigger_hook("on_message_received", {})
            assert results == []

    def test_trigger_no_hooks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = PluginManager(base_dir=tmpdir)
            assert pm.trigger_hook("nonexistent_event") == []


class TestPluginManagerCommands:
    def test_execute_command(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = PluginManager(base_dir=tmpdir)
            code = '''
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'relay-server'))
from plugin_system import PluginInterface

class CmdPlug(PluginInterface):
    plugin_id = "cmdplug"
    name = "Cmd"
    def on_load(self, ctx):
        self.register_command("greet", self._greet)
    def _greet(self, name="world"):
        return f"hello {name}"
'''
            _write_plugin_file(pm.plugin_dir, "cmdplug.py", code)
            pm.load_plugin("cmdplug")
            pm.enable_plugin("cmdplug")
            result = pm.execute_command("greet", name="test")
            assert result == "hello test"

    def test_execute_unknown_command(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = PluginManager(base_dir=tmpdir)
            with pytest.raises(ValueError, match="Unknown command"):
                pm.execute_command("nonexistent")

    def test_execute_command_disabled(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = PluginManager(base_dir=tmpdir)
            code = '''
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'relay-server'))
from plugin_system import PluginInterface

class DisCmdPlug(PluginInterface):
    plugin_id = "discmd"
    name = "DisCmd"
    def on_load(self, ctx):
        self.register_command("foo", lambda: "bar")
'''
            _write_plugin_file(pm.plugin_dir, "discmd.py", code)
            pm.load_plugin("discmd")
            # not enabled
            with pytest.raises(RuntimeError, match="not enabled"):
                pm.execute_command("foo")

    def test_list_commands(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = PluginManager(base_dir=tmpdir)
            code = '''
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'relay-server'))
from plugin_system import PluginInterface

class LcPlug(PluginInterface):
    plugin_id = "lcplug"
    name = "Lc"
    def on_load(self, ctx):
        self.register_command("a", lambda: 1)
        self.register_command("b", lambda: 2)
'''
            _write_plugin_file(pm.plugin_dir, "lcplug.py", code)
            pm.load_plugin("lcplug")
            cmds = pm.list_commands()
            assert "a" in cmds
            assert "b" in cmds


class TestPluginManagerQuery:
    def test_list_plugins(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = PluginManager(base_dir=tmpdir)
            assert pm.list_plugins() == []
            code = '''
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'relay-server'))
from plugin_system import PluginInterface

class QPlug(PluginInterface):
    plugin_id = "qplug"
    name = "Q"
'''
            _write_plugin_file(pm.plugin_dir, "qplug.py", code)
            pm.load_plugin("qplug")
            assert len(pm.list_plugins()) == 1

    def test_get_plugin_info(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = PluginManager(base_dir=tmpdir)
            code = '''
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'relay-server'))
from plugin_system import PluginInterface

class GIPlug(PluginInterface):
    plugin_id = "giplug"
    name = "GI"
    version = "2.0.0"
    description = "test desc"
    author = "tester"
    category = "testing"
'''
            _write_plugin_file(pm.plugin_dir, "giplug.py", code)
            pm.load_plugin("giplug")
            info = pm.get_plugin_info("giplug")
            assert info is not None
            assert info.name == "GI"
            assert info.version == "2.0.0"
            d = info.to_dict()
            assert d["plugin_id"] == "giplug"
            assert "loaded_at" in d

    def test_get_plugin_info_nonexistent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = PluginManager(base_dir=tmpdir)
            assert pm.get_plugin_info("nope") is None

    def test_get_plugin_instance(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = PluginManager(base_dir=tmpdir)
            code = '''
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'relay-server'))
from plugin_system import PluginInterface

class InstPlug(PluginInterface):
    plugin_id = "instplug"
    name = "Inst"
'''
            _write_plugin_file(pm.plugin_dir, "instplug.py", code)
            pm.load_plugin("instplug")
            plugin = pm.get_plugin("instplug")
            assert plugin is not None
            assert isinstance(plugin, PluginInterface)


class TestPluginManagerContext:
    def test_set_context(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = PluginManager(base_dir=tmpdir)
            pm.set_context(server="test", port=1234)
            assert pm._context["server"] == "test"
            assert pm._context["port"] == 1234


class TestPluginInfoToDict:
    def test_to_dict(self):
        info = PluginInfo(
            plugin_id="test",
            name="Test",
            version="1.0.0",
            description="desc",
            author="me",
            category="general",
        )
        d = info.to_dict()
        assert d["plugin_id"] == "test"
        assert d["state"] == "loaded"
        assert d["error_message"] is None

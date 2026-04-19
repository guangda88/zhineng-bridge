#!/usr/bin/env python3
"""Agent 消息总线单元测试 — 测试 AgentRegistry、MessageBus、频道系统"""

import json
import os
import sys
from unittest.mock import AsyncMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../relay-server"))

from agent_bus import AgentRegistry, MessageBus, Channel


class TestAgentRegistry:

    @pytest.fixture
    def registry(self):
        return AgentRegistry()

    def test_register_new_agent(self, registry):
        ws = AsyncMock()
        agent = registry.register("claude-1", ws, name="Claude", capabilities=["code", "chat"])

        assert agent.agent_id == "claude-1"
        assert agent.name == "Claude"
        assert agent.capabilities == ["code", "chat"]
        assert agent.is_online()

    def test_register_reconnect(self, registry):
        ws1 = AsyncMock()
        ws2 = AsyncMock()

        registry.register("claude-1", ws1)
        agent = registry.register("claude-1", ws2, name="Claude v2")

        assert agent._websocket is ws2
        assert agent.name == "Claude v2"
        assert len(registry._agents) == 1

    def test_unregister(self, registry):
        ws = AsyncMock()
        registry.register("claude-1", ws)

        registry.unregister("claude-1")
        agent = registry.get("claude-1")

        assert agent is not None
        assert not agent.is_online()

    def test_get_online(self, registry):
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        registry.register("claude-1", ws1)
        registry.register("crush-1", ws2)
        registry.unregister("crush-1")

        online = registry.get_online()
        assert len(online) == 1
        assert online[0].agent_id == "claude-1"

    def test_find_by_capability(self, registry):
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        registry.register("claude-1", ws1, capabilities=["code", "review"])
        registry.register("crush-1", ws2, capabilities=["code"])

        code_agents = registry.find_by_capability("code")
        assert len(code_agents) == 2

        review_agents = registry.find_by_capability("review")
        assert len(review_agents) == 1

    def test_list_all(self, registry):
        ws = AsyncMock()
        registry.register("claude-1", ws, name="Claude")

        result = registry.list_all()
        assert len(result) == 1
        assert result[0]["agent_id"] == "claude-1"
        assert result[0]["name"] == "Claude"
        assert result[0]["online"] is True

    def test_remove(self, registry):
        ws = AsyncMock()
        registry.register("claude-1", ws)
        registry.remove("claude-1")

        assert registry.get("claude-1") is None


class TestChannel:

    def test_join_leave(self):
        ch = Channel("test-ch", "creator-1")
        ch.join("agent-1")
        ch.join("agent-2")

        assert "agent-1" in ch.members
        assert "agent-2" in ch.members
        assert len(ch.members) == 3  # creator + 2

        ch.leave("agent-1")
        assert "agent-1" not in ch.members

    def test_history(self):
        ch = Channel("test-ch", "creator-1", max_history=3)
        for i in range(5):
            ch.add_message({"text": f"msg-{i}"})

        history = ch.get_history(limit=3)
        assert len(history) == 3
        assert history[0]["text"] == "msg-2"
        assert history[2]["text"] == "msg-4"

    def test_to_dict(self):
        ch = Channel("test-ch", "creator-1", name="Test Channel")
        d = ch.to_dict()

        assert d["channel_id"] == "test-ch"
        assert d["name"] == "Test Channel"
        assert d["member_count"] == 1


class TestMessageBus:

    @pytest.fixture
    def bus(self):
        registry = AgentRegistry()
        return MessageBus(registry)

    @pytest.fixture
    def registered_bus(self):
        registry = AgentRegistry()
        bus = MessageBus(registry)

        ws_a = AsyncMock()
        ws_b = AsyncMock()
        registry.register("claude-1", ws_a, name="Claude")
        registry.register("crush-1", ws_b, name="Crush")

        return bus, registry, ws_a, ws_b

    @pytest.mark.asyncio
    async def test_send_direct(self, registered_bus):
        bus, registry, ws_a, ws_b = registered_bus

        result = await bus.send_direct("claude-1", "crush-1", "Hello Crush!")

        assert result["type"] == "inter_chat_sent"
        assert result["to"] == "crush-1"
        assert "conversation_id" in result
        assert "message_id" in result

        ws_b.send.assert_called_once()
        sent = json.loads(ws_b.send.call_args[0][0])
        assert sent["type"] == "inter_chat"
        assert sent["from"] == "claude-1"
        assert sent["to"] == "crush-1"
        assert sent["text"] == "Hello Crush!"

    @pytest.mark.asyncio
    async def test_send_direct_unknown_target(self, registered_bus):
        bus, registry, ws_a, ws_b = registered_bus

        result = await bus.send_direct("claude-1", "unknown-agent", "Hello")

        assert result["type"] == "error"
        assert "不存在" in result["message"]

    @pytest.mark.asyncio
    async def test_send_direct_offline_target(self, registered_bus):
        bus, registry, ws_a, ws_b = registered_bus
        registry.unregister("crush-1")

        result = await bus.send_direct("claude-1", "crush-1", "Hello")

        assert result["type"] == "error"
        assert "不在线" in result["message"]

    @pytest.mark.asyncio
    async def test_conversation_threading(self, registered_bus):
        bus, registry, ws_a, ws_b = registered_bus

        r1 = await bus.send_direct("claude-1", "crush-1", "msg 1")
        r2 = await bus.send_direct("claude-1", "crush-1", "msg 2")
        r3 = await bus.send_direct("crush-1", "claude-1", "reply")

        assert r1["conversation_id"] == r2["conversation_id"]
        convs = bus.list_conversations("claude-1")
        assert len(convs) == 1
        assert convs[0]["message_count"] == 3

    @pytest.mark.asyncio
    async def test_channel_create(self, bus):
        result = bus.create_channel("review", "claude-1", name="Code Review")

        assert result["type"] == "channel_created"
        assert result["channel_id"] == "review"
        assert result["name"] == "Code Review"

    @pytest.mark.asyncio
    async def test_channel_duplicate(self, bus):
        bus.create_channel("review", "claude-1")
        result = bus.create_channel("review", "claude-1")

        assert result["type"] == "error"

    @pytest.mark.asyncio
    async def test_channel_join_leave(self, bus):
        registry = bus.registry
        ws = AsyncMock()
        registry.register("agent-1", ws)

        bus.create_channel("test", "creator")
        result = bus.join_channel("test", "agent-1")
        assert result["type"] == "channel_joined"

        result = bus.leave_channel("test", "agent-1")
        assert result["type"] == "channel_left"

    @pytest.mark.asyncio
    async def test_channel_post(self, bus):
        registry = bus.registry
        ws_creator = AsyncMock()
        ws_member = AsyncMock()
        registry.register("creator", ws_creator, name="Creator")
        registry.register("member-1", ws_member, name="Member")

        bus.create_channel("test", "creator")
        bus.join_channel("test", "member-1")

        result = await bus.post_to_channel("test", "creator", "Hello channel!")

        assert result["type"] == "channel_post_sent"
        assert result["delivered_to"] == 1

        ws_member.send.assert_called_once()
        sent = json.loads(ws_member.send.call_args[0][0])
        assert sent["type"] == "channel_message"
        assert sent["from"] == "creator"
        assert sent["text"] == "Hello channel!"

    @pytest.mark.asyncio
    async def test_channel_post_non_member(self, bus):
        registry = bus.registry
        ws = AsyncMock()
        registry.register("creator", ws)
        registry.register("outsider", AsyncMock())

        bus.create_channel("test", "creator")
        result = await bus.post_to_channel("test", "outsider", "Hello")

        assert result["type"] == "error"
        assert "未加入" in result["message"]

    def test_list_channels(self, bus):
        bus.create_channel("ch1", "a")
        bus.create_channel("ch2", "b")

        channels = bus.list_channels()
        assert len(channels) == 2

    def test_channel_history(self, bus):
        bus.create_channel("test", "creator")
        bus._channels["test"].add_message({"text": "msg1"})
        bus._channels["test"].add_message({"text": "msg2"})

        result = bus.get_channel_history("test")
        assert result["type"] == "channel_history"
        assert result["count"] == 2


class TestServerBusIntegration:

    @pytest.fixture
    def server(self):
        from server import AIRelayServer
        srv = AIRelayServer(host="localhost", port=8765)
        from agent_bus import AgentRegistry, MessageBus
        srv.agent_registry = AgentRegistry()
        srv.message_bus = MessageBus(srv.agent_registry)
        return srv

    @pytest.mark.asyncio
    async def test_register_agent(self, server):
        ws = AsyncMock()
        msg = {
            "type": "register_agent",
            "agent_id": "claude-1",
            "name": "Claude",
            "capabilities": ["code"],
        }
        await server._dispatch("conn-1", ws, msg)

        assert "conn-1" in server._agent_connections
        assert server._agent_connections["conn-1"] == "claude-1"
        assert server.agent_registry.get("claude-1") is not None

        sent = json.loads(ws.send.call_args[0][0])
        assert sent["type"] == "agent_registered"
        assert sent["agent_id"] == "claude-1"

    @pytest.mark.asyncio
    async def test_inter_chat_between_agents(self, server):
        ws_a = AsyncMock()
        ws_b = AsyncMock()

        await server._dispatch("conn-a", ws_a, {
            "type": "register_agent",
            "agent_id": "claude-1",
            "name": "Claude",
        })
        await server._dispatch("conn-b", ws_b, {
            "type": "register_agent",
            "agent_id": "crush-1",
            "name": "Crush",
        })

        ws_a.send.reset_mock()
        await server._dispatch("conn-a", ws_a, {
            "type": "inter_chat",
            "to": "crush-1",
            "text": "Hello from Claude!",
        })

        sent_to_caller = json.loads(ws_a.send.call_args[0][0])
        assert sent_to_caller["type"] == "inter_chat_sent"

        sent_to_target = json.loads(ws_b.send.call_args[0][0])
        assert sent_to_target["type"] == "inter_chat"
        assert sent_to_target["from"] == "claude-1"
        assert sent_to_target["text"] == "Hello from Claude!"

    @pytest.mark.asyncio
    async def test_inter_chat_without_register(self, server):
        ws = AsyncMock()
        await server._dispatch("conn-1", ws, {
            "type": "inter_chat",
            "to": "crush-1",
            "text": "Hello",
        })

        sent = json.loads(ws.send.call_args[0][0])
        assert sent["type"] == "error"
        assert "register_agent" in sent["message"]

    @pytest.mark.asyncio
    async def test_list_agents(self, server):
        ws = AsyncMock()
        await server._dispatch("conn-a", AsyncMock(), {
            "type": "register_agent",
            "agent_id": "claude-1",
            "name": "Claude",
        })

        await server._dispatch("conn-b", ws, {"type": "list_agents"})

        sent = json.loads(ws.send.call_args[0][0])
        assert sent["type"] == "agents_list"
        assert sent["count"] >= 1

    @pytest.mark.asyncio
    async def test_channel_workflow(self, server):
        ws_a = AsyncMock()
        ws_b = AsyncMock()

        await server._dispatch("conn-a", ws_a, {
            "type": "register_agent",
            "agent_id": "claude-1",
            "name": "Claude",
        })
        await server._dispatch("conn-b", ws_b, {
            "type": "register_agent",
            "agent_id": "crush-1",
            "name": "Crush",
        })

        await server._dispatch("conn-a", ws_a, {
            "type": "channel_create",
            "channel_id": "review",
            "name": "Code Review",
        })
        await server._dispatch("conn-b", ws_b, {
            "type": "channel_join",
            "channel_id": "review",
        })

        ws_a.send.reset_mock()
        ws_b.send.reset_mock()
        await server._dispatch("conn-a", ws_a, {
            "type": "channel_post",
            "channel_id": "review",
            "text": "Please review this code",
        })

        sent_to_caller = json.loads(ws_a.send.call_args[0][0])
        assert sent_to_caller["type"] == "channel_post_sent"

        sent_to_member = json.loads(ws_b.send.call_args[0][0])
        assert sent_to_member["type"] == "channel_message"
        assert sent_to_member["from"] == "claude-1"

    @pytest.mark.asyncio
    async def test_agent_cleanup_on_disconnect(self, server):
        ws = AsyncMock()

        await server._dispatch("conn-1", ws, {
            "type": "register_agent",
            "agent_id": "claude-1",
            "name": "Claude",
        })
        assert "conn-1" in server._agent_connections

        server._agent_connections.pop("conn-1", None)
        server.agent_registry.unregister("claude-1")

        agent = server.agent_registry.get("claude-1")
        assert agent is not None
        assert not agent.is_online()

    @pytest.mark.asyncio
    async def test_list_conversations(self, server):
        ws_a = AsyncMock()
        ws_b = AsyncMock()

        await server._dispatch("conn-a", ws_a, {
            "type": "register_agent",
            "agent_id": "claude-1",
            "name": "Claude",
        })
        await server._dispatch("conn-b", ws_b, {
            "type": "register_agent",
            "agent_id": "crush-1",
            "name": "Crush",
        })

        await server._dispatch("conn-a", ws_a, {
            "type": "inter_chat",
            "to": "crush-1",
            "text": "Hello!",
        })

        ws_a.send.reset_mock()
        await server._dispatch("conn-a", ws_a, {
            "type": "list_conversations",
        })

        sent = json.loads(ws_a.send.call_args[0][0])
        assert sent["type"] == "conversations_list"
        assert sent["count"] == 1
        assert sent["conversations"][0]["peer"] == "crush-1"

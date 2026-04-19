#!/usr/bin/env python3
"""智桥 Agent 消息总线 — AI后端之间的跨会话通信。

架构:
  Backend A ←ws→ 智桥(:8766) ←ws→ Backend B
                     ↑
  支持: 直接消息、频道广播、会话线程、共享上下文

核心组件:
  - AgentRegistry: AI后端代理注册、发现、能力查询
  - MessageBus: 跨后端消息路由、线程管理
  - Channel: 发布/订阅频道，多后端组通信
"""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger("zhineng-bridge.bus")


@dataclass
class Agent:
    """AI代理身份"""
    agent_id: str
    name: str
    description: str = ""
    capabilities: List[str] = field(default_factory=list)
    connected_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    _websocket: Any = field(default=None, repr=False)

    def is_online(self) -> bool:
        return self._websocket is not None


@dataclass
class Conversation:
    """对话线程 — 两个或多个 Agent 之间的持续对话"""
    conversation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    participants: Set[str] = field(default_factory=set)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    message_count: int = 0
    context: Dict[str, Any] = field(default_factory=dict)


class AgentRegistry:
    """AI代理注册表 — 管理 agent 的注册、发现、查询"""

    def __init__(self):
        self._agents: Dict[str, Agent] = {}

    def register(self, agent_id: str, websocket, **kwargs) -> Agent:
        if agent_id in self._agents:
            agent = self._agents[agent_id]
            agent._websocket = websocket
            agent.connected_at = datetime.now().isoformat()
            for k, v in kwargs.items():
                if hasattr(agent, k):
                    setattr(agent, k, v)
            logger.info(f"[AgentRegistry] 重新连接: {agent_id}")
            return agent

        agent = Agent(
            agent_id=agent_id,
            name=kwargs.get("name", agent_id),
            description=kwargs.get("description", ""),
            capabilities=kwargs.get("capabilities", []),
            metadata=kwargs.get("metadata", {}),
            _websocket=websocket,
        )
        self._agents[agent_id] = agent
        logger.info(f"[AgentRegistry] 注册: {agent_id} (能力: {agent.capabilities})")
        return agent

    def unregister(self, agent_id: str):
        agent = self._agents.get(agent_id)
        if agent:
            agent._websocket = None
            logger.info(f"[AgentRegistry] 离线: {agent_id}")

    def get(self, agent_id: str) -> Optional[Agent]:
        return self._agents.get(agent_id)

    def get_online(self) -> List[Agent]:
        return [a for a in self._agents.values() if a.is_online()]

    def find_by_capability(self, capability: str) -> List[Agent]:
        return [
            a for a in self._agents.values()
            if a.is_online() and capability in a.capabilities
        ]

    def list_all(self) -> List[Dict[str, Any]]:
        return [
            {
                "agent_id": a.agent_id,
                "name": a.name,
                "description": a.description,
                "capabilities": a.capabilities,
                "online": a.is_online(),
                "connected_at": a.connected_at,
            }
            for a in self._agents.values()
        ]

    def remove(self, agent_id: str):
        self._agents.pop(agent_id, None)


class Channel:
    """发布/订阅频道 — 多个 Agent 之间的组通信"""

    def __init__(self, channel_id: str, creator: str, **kwargs):
        self.channel_id = channel_id
        self.creator = creator
        self.members: Set[str] = {creator}
        self.name = kwargs.get("name", channel_id)
        self.description = kwargs.get("description", "")
        self.created_at = datetime.now().isoformat()
        self.history: List[Dict[str, Any]] = []
        self.max_history = kwargs.get("max_history", 200)

    def join(self, agent_id: str):
        self.members.add(agent_id)

    def leave(self, agent_id: str):
        self.members.discard(agent_id)

    def add_message(self, message: Dict[str, Any]):
        self.history.append(message)
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self.history[-limit:]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "channel_id": self.channel_id,
            "name": self.name,
            "description": self.description,
            "creator": self.creator,
            "members": list(self.members),
            "member_count": len(self.members),
            "created_at": self.created_at,
        }


class MessageBus:
    """跨后端消息总线 — 直接消息、频道通信、对话线程"""

    def __init__(self, registry: AgentRegistry):
        self.registry = registry
        self._channels: Dict[str, Channel] = {}
        self._conversations: Dict[str, Conversation] = {}
        self._pending_inter: Dict[str, tuple[str, float]] = {}
        self._inter_ttl = 300
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start(self):
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("[MessageBus] 启动")

    async def stop(self):
        if self._cleanup_task:
            self._cleanup_task.cancel()
        self._channels.clear()
        self._conversations.clear()
        self._pending_inter.clear()
        logger.info("[MessageBus] 停止")

    # ---- 直接消息 (Agent → Agent) ----

    async def send_direct(
        self, from_id: str, to_id: str, text: str,
        conversation_id: Optional[str] = None, **extra
    ) -> Dict[str, Any]:
        """Agent A 直接发消息给 Agent B"""
        from_agent = self.registry.get(from_id)
        to_agent = self.registry.get(to_id)

        if not from_agent:
            return {"type": "error", "message": f"发送方 {from_id} 不存在"}
        if not to_agent:
            return {"type": "error", "message": f"接收方 {to_id} 不存在"}
        if not to_agent.is_online():
            return {"type": "error", "message": f"接收方 {to_id} 不在线"}

        conv_id = conversation_id
        if not conv_id:
            conv = self._find_or_create_conversation(from_id, to_id)
            conv_id = conv.conversation_id
        else:
            conv = self._conversations.get(conv_id)
            if conv:
                if from_id not in conv.participants or to_id not in conv.participants:
                    return {"type": "error", "message": "不在该对话线程中"}

        message_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        payload = {
            "type": "inter_chat",
            "message_id": message_id,
            "from": from_id,
            "from_name": from_agent.name,
            "to": to_id,
            "text": text,
            "conversation_id": conv_id,
            "timestamp": timestamp,
            **extra,
        }

        if conv:
            conv.message_count += 1

        self._pending_inter[message_id] = (from_id, time.monotonic())

        try:
            await to_agent._websocket.send(json.dumps(payload))
            logger.info(f"[MessageBus] 直接消息: {from_id} → {to_id} (conv={conv_id[:8]})")

            ack = {
                "type": "inter_chat_sent",
                "message_id": message_id,
                "to": to_id,
                "conversation_id": conv_id,
                "timestamp": timestamp,
            }
            return ack
        except Exception as e:
            self._pending_inter.pop(message_id, None)
            logger.error(f"[MessageBus] 发送失败: {e}")
            return {"type": "error", "message": f"消息发送失败: {e}"}

    # ---- 频道通信 ----

    def create_channel(self, channel_id: str, creator: str, **kwargs) -> Dict[str, Any]:
        if channel_id in self._channels:
            return {"type": "error", "message": f"频道 {channel_id} 已存在"}

        ch = Channel(channel_id, creator, **kwargs)
        self._channels[channel_id] = ch
        logger.info(f"[MessageBus] 频道创建: {channel_id} by {creator}")
        return {"type": "channel_created", "channel_id": channel_id, **ch.to_dict()}

    def join_channel(self, channel_id: str, agent_id: str) -> Dict[str, Any]:
        ch = self._channels.get(channel_id)
        if not ch:
            return {"type": "error", "message": f"频道 {channel_id} 不存在"}

        agent = self.registry.get(agent_id)
        if not agent:
            return {"type": "error", "message": f"Agent {agent_id} 不存在"}

        ch.join(agent_id)
        logger.info(f"[MessageBus] {agent_id} 加入频道 {channel_id}")
        return {
            "type": "channel_joined",
            "channel_id": channel_id,
            "agent_id": agent_id,
            "members": list(ch.members),
        }

    def leave_channel(self, channel_id: str, agent_id: str) -> Dict[str, Any]:
        ch = self._channels.get(channel_id)
        if not ch:
            return {"type": "error", "message": f"频道 {channel_id} 不存在"}

        ch.leave(agent_id)
        logger.info(f"[MessageBus] {agent_id} 离开频道 {channel_id}")
        return {
            "type": "channel_left",
            "channel_id": channel_id,
            "agent_id": agent_id,
        }

    async def post_to_channel(
        self, channel_id: str, from_id: str, text: str, **extra
    ) -> Dict[str, Any]:
        ch = self._channels.get(channel_id)
        if not ch:
            return {"type": "error", "message": f"频道 {channel_id} 不存在"}

        from_agent = self.registry.get(from_id)
        if not from_agent:
            return {"type": "error", "message": f"Agent {from_id} 不存在"}

        if from_id not in ch.members:
            return {"type": "error", "message": f"未加入频道 {channel_id}，请先 join"}

        message_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        payload = {
            "type": "channel_message",
            "message_id": message_id,
            "channel_id": channel_id,
            "from": from_id,
            "from_name": from_agent.name,
            "text": text,
            "timestamp": timestamp,
            **extra,
        }

        ch.add_message(payload)

        sent_count = 0
        for member_id in ch.members:
            if member_id == from_id:
                continue
            member = self.registry.get(member_id)
            if member and member.is_online():
                try:
                    await member._websocket.send(json.dumps(payload))
                    sent_count += 1
                except Exception as e:
                    logger.warning(f"[MessageBus] 频道发送给 {member_id} 失败: {e}")

        logger.info(
            f"[MessageBus] 频道消息: {from_id}@{channel_id} → {sent_count} 人"
        )

        return {
            "type": "channel_post_sent",
            "message_id": message_id,
            "channel_id": channel_id,
            "delivered_to": sent_count,
            "timestamp": timestamp,
        }

    # ---- 对话管理 ----

    def _find_or_create_conversation(self, agent_a: str, agent_b: str) -> Conversation:
        pair = tuple(sorted([agent_a, agent_b]))
        for conv in self._conversations.values():
            if set(conv.participants) == set(pair):
                return conv

        conv = Conversation(participants=set(pair))
        self._conversations[conv.conversation_id] = conv
        logger.info(
            f"[MessageBus] 新对话线程: {conv.conversation_id[:8]} ({agent_a} ↔ {agent_b})"
        )
        return conv

    def list_conversations(self, agent_id: str) -> List[Dict[str, Any]]:
        results = []
        for conv in self._conversations.values():
            if agent_id in conv.participants:
                other = conv.participants - {agent_id}
                results.append({
                    "conversation_id": conv.conversation_id,
                    "participants": list(conv.participants),
                    "peer": list(other)[0] if other else None,
                    "message_count": conv.message_count,
                    "created_at": conv.created_at,
                })
        return results

    # ---- 查询 ----

    def list_channels(self) -> List[Dict[str, Any]]:
        return [ch.to_dict() for ch in self._channels.values()]

    def get_channel_history(self, channel_id: str, limit: int = 50) -> Dict[str, Any]:
        ch = self._channels.get(channel_id)
        if not ch:
            return {"type": "error", "message": f"频道 {channel_id} 不存在"}
        return {
            "type": "channel_history",
            "channel_id": channel_id,
            "messages": ch.get_history(limit),
            "count": len(ch.get_history(limit)),
        }

    # ---- 清理 ----

    async def _cleanup_loop(self):
        while True:
            await asyncio.sleep(60)
            now = time.monotonic()
            expired = [
                k for k, (_, ts) in self._pending_inter.items()
                if now - ts > self._inter_ttl
            ]
            for k in expired:
                del self._pending_inter[k]
            if expired:
                logger.info(f"[MessageBus] 清理 {len(expired)} 个过期消息")

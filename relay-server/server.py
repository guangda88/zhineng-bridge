#!/usr/bin/env python3
"""智桥 AI Relay Server — 用户与AI后端之间的WebSocket中继。

架构:
  用户(浏览器) ←ws→ 智桥(:8765) ←ws→ AI后端(灵克/灵知...)

协议:
  用户 → 智桥: {"type":"chat","target":"lingke","text":"..."}
  智桥 → AI:   {"type":"chat","from":"user_xxx","text":"..."}
  AI → 智桥:   {"type":"reply","text":"...","audio":"base64..."}
  智桥 → 用户: {"type":"reply","text":"...","audio":"base64..."}

  用户 → 智桥: {"type":"register_backend","backend_id":"lingke"}
  智桥确认:    {"type":"backend_registered","backend_id":"lingke"}
"""

import asyncio
import hmac
import json
import logging
import ssl
import time
import uuid
from datetime import datetime
from pathlib import Path

import websockets

try:
    from auth import ws_auth as _ws_auth
except Exception:
    _ws_auth = None

try:
    from agent_bus import AgentRegistry, MessageBus
except Exception:
    _bus_available = False
else:
    _bus_available = True

try:
    from session_protocol.manager import FamilySessionManager
except Exception:
    _session_mgr_available = False
else:
    _session_mgr_available = True

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("zhineng-bridge")


class AIRelayServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 8766, backend_secret: str = None):
        self.host = host
        self.port = port
        self.server = None
        self._ws_auth = _ws_auth
        self._backend_secret = backend_secret

        # 用户连接: client_id → websocket
        self.users: dict[str, websockets.WebSocketServerProtocol] = {}
        # AI后端连接: backend_id → websocket
        self.backends: dict[str, websockets.WebSocketServerProtocol] = {}
        # 用户当前对话的AI: client_id → backend_id
        self.routing: dict[str, str] = {}
        # AI后端元数据: backend_id → {name, description, ...}
        self.backend_meta: dict[str, dict] = {}
        # 待回复的请求: request_id → (client_id, timestamp)
        self.pending: dict[str, tuple[str, float]] = {}
        # pending 条目 TTL（秒）
        self._pending_ttl = 300  # 5 分钟
        self._cleanup_task: asyncio.Task | None = None

        # AI代理消息总线
        self.agent_registry: AgentRegistry | None = None
        self.message_bus: MessageBus | None = None
        # 已注册的代理: conn_id → agent_id
        self._agent_connections: dict[str, str] = {}

        # 全族会话管理
        self.session_manager: FamilySessionManager | None = None
        self._session_map: dict[str, str] = {}  # conn_id → session_id

    async def start(self):
        ssl_kwargs = {}
        cert_dir = Path.home() / ".zhibridge"
        cert_pem = cert_dir / "cert.pem"
        cert_key = cert_dir / "cert.key"
        if cert_pem.exists() and cert_key.exists():
            ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_ctx.load_cert_chain(str(cert_pem), str(cert_key))
            ssl_kwargs["ssl"] = ssl_ctx
            proto = "wss"
        else:
            proto = "ws"

        logger.info(f"智桥 AI Relay 启动: {proto}://{self.host}:{self.port}")
        self._cleanup_task = asyncio.create_task(self._pending_cleanup_loop())

        # 初始化消息总线
        if _bus_available:
            self.agent_registry = AgentRegistry()
            self.message_bus = MessageBus(self.agent_registry)
            await self.message_bus.start()
            logger.info("智桥 Agent 消息总线已启用")

        # 初始化全族会话管理
        if _session_mgr_available:
            self.session_manager = FamilySessionManager()
            self.session_manager.update_heartbeat("ZhiBridge")
            logger.info("智桥 全族会话管理器已启用")

        self.server = await websockets.serve(
            self._handle_connection,
            self.host,
            self.port,
            ping_interval=30,
            ping_timeout=60,
            **ssl_kwargs,
        )
        logger.info("智桥就绪 — 等待用户和AI后端连接")
        await self.server.wait_closed()

    async def _handle_connection(self, websocket: websockets.WebSocketServerProtocol):
        conn_id = str(uuid.uuid4())[:8]
        logger.info(f"[连接] 新连接 {conn_id}")

        try:
            authenticated = False
            async for raw in websocket:
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({"type": "error", "message": "Invalid JSON"}))
                    continue

                if not authenticated and self._ws_auth:
                    token = msg.get("token", "")
                    ok, err = self._ws_auth.authenticate_connection(conn_id, token)
                    if not ok:
                        await websocket.send(
                            json.dumps({"type": "error", "message": f"认证失败: {err}"})
                        )
                        await websocket.close(4001, "Authentication required")
                        return
                    authenticated = True

                await self._dispatch(conn_id, websocket, msg)

        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            logger.error(f"[连接] {conn_id} 异常: {e}")
        finally:
            if self._ws_auth:
                self._ws_auth.disconnect(conn_id)

            # 清理代理注册
            agent_id = self._agent_connections.pop(conn_id, None)
            if agent_id and self.agent_registry:
                self.agent_registry.unregister(agent_id)
                logger.info(f"[断开] 代理 {agent_id} 从消息总线注销")

            # 清理会话
            session_id = self._session_map.pop(conn_id, None)
            if session_id and self.session_manager:
                self.session_manager.update_session_status(session_id, "archived")
                logger.info(f"[断开] 会话 {session_id[:8]} 已归档")

            if conn_id in self.users:
                del self.users[conn_id]
                if conn_id in self.routing:
                    del self.routing[conn_id]
                logger.info(f"[断开] 用户 {conn_id}")
            for bid, bws in list(self.backends.items()):
                if bws is websocket:
                    del self.backends[bid]
                    self.backend_meta.pop(bid, None)
                    logger.info(f"[断开] 后端 {bid}")
            self.pending = {k: (cid, ts) for k, (cid, ts) in self.pending.items() if cid != conn_id}

    async def _dispatch(self, conn_id: str, websocket, msg: dict):
        mtype = msg.get("type", "")

        # AI后端注册
        if mtype == "register_backend":
            backend_id = msg.get("backend_id", "")
            if not backend_id:
                await websocket.send(
                    json.dumps({"type": "error", "message": "backend_id required"})
                )
                return
            if self._backend_secret:
                secret = msg.get("secret", "")
                if not hmac.compare_digest(secret, self._backend_secret):
                    await websocket.send(
                        json.dumps({"type": "error", "message": "后端注册需要有效密钥"})
                    )
                    return
            self.backends[backend_id] = websocket
            self.backend_meta[backend_id] = {
                "name": msg.get("name", backend_id),
                "description": msg.get("description", ""),
                "capabilities": msg.get("capabilities", []),
                "connected_at": datetime.now().isoformat(),
            }
            # 如果这个后端之前有用户在等，恢复路由
            for cid, bid in list(self.routing.items()):
                if bid == backend_id:
                    logger.info(f"[路由] 恢复 用户 {cid} → {backend_id}")
            await websocket.send(
                json.dumps(
                    {
                        "type": "backend_registered",
                        "backend_id": backend_id,
                        "message": f"智桥已注册 {backend_id}",
                    }
                )
            )
            logger.info(f"[注册] AI后端 {backend_id} 已注册")

            # 创建后端会话记录
            if self.session_manager:
                sess = self.session_manager.create_session(
                    member_id=backend_id,
                    metadata={"role": "backend", "conn_id": conn_id},
                )
                self._session_map[conn_id] = sess["session_id"]
            return

        # AI后端回复（转发给用户）
        if mtype == "reply":
            request_id = msg.get("request_id", "")
            entry = self.pending.pop(request_id, None)
            client_id = entry[0] if entry else None
            if client_id and client_id in self.users:
                await self.users[client_id].send(
                    json.dumps(
                        {
                            "type": "reply",
                            "text": msg.get("text", ""),
                            "audio": msg.get("audio"),
                            "backend": msg.get("backend", ""),
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                )
                logger.info(f"[回复] {request_id[:8]} → 用户 {client_id}")
            else:
                logger.warning(f"[回复] 找不到请求 {request_id} 对应的用户")
            return

        # AI后端主动推送
        if mtype == "push":
            if websocket not in self.backends.values():
                await websocket.send(
                    json.dumps(
                        {"type": "error", "message": "未授权: 只有已注册的AI后端可以推送消息"}
                    )
                )
                return
            target_client = msg.get("target_client")
            payload = {
                "type": "push",
                "category": msg.get("category", "info"),
                "text": msg.get("text", ""),
                "backend": msg.get("backend", ""),
                "timestamp": datetime.now().isoformat(),
            }
            if target_client and target_client in self.users:
                await self.users[target_client].send(json.dumps(payload))
            else:
                # 广播给所有用户
                for cid, cws in list(self.users.items()):
                    try:
                        await cws.send(json.dumps(payload))
                    except Exception:
                        pass
            return

        # 用户聊天消息（转发给AI后端）
        if mtype == "chat":
            target = msg.get("target", "lingke")
            text = msg.get("text", "").strip()
            if not text:
                await websocket.send(json.dumps({"type": "error", "message": "消息不能为空"}))
                return

            # 自动注册用户
            if conn_id not in self.users:
                self.users[conn_id] = websocket
                if conn_id not in self.routing:
                    self.routing[conn_id] = target
                logger.info(f"[用户] 新用户 {conn_id} 默认路由 → {target}")

                # 创建会话记录
                if self.session_manager and conn_id not in self._session_map:
                    sess = self.session_manager.create_session(
                        member_id="ZhiBridge",
                        metadata={"conn_id": conn_id, "target": target},
                    )
                    self._session_map[conn_id] = sess["session_id"]

            backend_id = self.routing.get(conn_id, target)
            backend_ws = self.backends.get(backend_id)

            if not backend_ws:
                if self.backends:
                    original_target = backend_id
                    backend_id = next(iter(self.backends))
                    backend_ws = self.backends[backend_id]
                    self.routing[conn_id] = backend_id
                    logger.info(f"[路由] {original_target} 不可用，回退到 {backend_id}")
                else:
                    await websocket.send(
                        json.dumps(
                            {
                                "type": "error",
                                "message": "没有可用的AI后端，请稍后再试",
                            }
                        )
                    )
                    return

            request_id = str(uuid.uuid4())
            self.pending[request_id] = (conn_id, time.monotonic())

            await backend_ws.send(
                json.dumps(
                    {
                        "type": "chat",
                        "request_id": request_id,
                        "from": conn_id,
                        "text": text,
                        "audio": msg.get("audio"),
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            )
            logger.info(f"[转发] 用户 {conn_id} → {backend_id}: {text[:50]}")
            return

        # 用户切换AI后端
        if mtype == "switch_backend":
            target = msg.get("target", "lingke")
            self.routing[conn_id] = target
            await websocket.send(
                json.dumps(
                    {
                        "type": "backend_switched",
                        "backend_id": target,
                    }
                )
            )
            logger.info(f"[切换] 用户 {conn_id} → {target}")
            return

        # 列出可用AI后端
        if mtype == "list_backends":
            backends = []
            for bid, meta in self.backend_meta.items():
                backends.append(
                    {
                        "id": bid,
                        "name": meta.get("name", bid),
                        "description": meta.get("description", ""),
                        "online": bid in self.backends,
                    }
                )
            await websocket.send(
                json.dumps(
                    {
                        "type": "backends_list",
                        "backends": backends,
                        "current": self.routing.get(conn_id, ""),
                    }
                )
            )
            return

        # 心跳
        if mtype == "ping":
            await websocket.send(
                json.dumps(
                    {
                        "type": "pong",
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            )
            return

        # ===================== Agent 消息总线 =====================
        result = await self._dispatch_bus(conn_id, websocket, mtype, msg)
        if result is not None:
            await websocket.send(json.dumps(result))
            return

        # 未知类型
        await websocket.send(
            json.dumps(
                {
                    "type": "error",
                    "message": f"Unknown message type: {mtype}",
                }
            )
        )

    async def _dispatch_bus(
        self, conn_id: str, websocket, mtype: str, msg: dict
    ) -> dict | None:
        """处理 Agent 消息总线相关的消息类型。

        Returns:
            dict: 响应消息（发送给调用方）
            None: 非总线消息，交给后续处理
        """
        if not self.agent_registry or not self.message_bus:
            bus_types = {
                "register_agent", "inter_chat", "inter_reply",
                "list_agents", "list_conversations",
                "channel_create", "channel_join", "channel_leave",
                "channel_post", "list_channels", "channel_history",
            }
            if mtype in bus_types:
                return {"type": "error", "message": "消息总线未启用"}
            return None

        # Agent 注册
        if mtype == "register_agent":
            agent_id = msg.get("agent_id", "")
            if not agent_id:
                return {"type": "error", "message": "agent_id 必填"}
            self.agent_registry.register(
                agent_id, websocket,
                name=msg.get("name", agent_id),
                description=msg.get("description", ""),
                capabilities=msg.get("capabilities", []),
            )
            self._agent_connections[conn_id] = agent_id
            return {
                "type": "agent_registered",
                "agent_id": agent_id,
                "message": "代理已注册到消息总线",
            }

        # 获取当前代理ID（后续操作需要）
        agent_id = self._agent_connections.get(conn_id)

        # Agent 间直接消息
        if mtype == "inter_chat":
            if not agent_id:
                return {"type": "error", "message": "请先 register_agent"}
            return await self.message_bus.send_direct(
                from_id=agent_id,
                to_id=msg.get("to", ""),
                text=msg.get("text", ""),
                conversation_id=msg.get("conversation_id"),
            )

        # Agent 间回复
        if mtype == "inter_reply":
            if not agent_id:
                return {"type": "error", "message": "请先 register_agent"}
            return await self.message_bus.send_direct(
                from_id=agent_id,
                to_id=msg.get("to", ""),
                text=msg.get("text", ""),
                conversation_id=msg.get("conversation_id"),
            )

        # 列出代理
        if mtype == "list_agents":
            agents = self.agent_registry.list_all()
            return {
                "type": "agents_list",
                "agents": agents,
                "count": len(agents),
            }

        # 列出对话
        if mtype == "list_conversations":
            if not agent_id:
                return {"type": "error", "message": "请先 register_agent"}
            convs = self.message_bus.list_conversations(agent_id)
            return {
                "type": "conversations_list",
                "conversations": convs,
                "count": len(convs),
            }

        # 频道创建
        if mtype == "channel_create":
            if not agent_id:
                return {"type": "error", "message": "请先 register_agent"}
            return self.message_bus.create_channel(
                channel_id=msg.get("channel_id", ""),
                creator=agent_id,
                name=msg.get("name"),
                description=msg.get("description"),
            )

        # 频道加入
        if mtype == "channel_join":
            if not agent_id:
                return {"type": "error", "message": "请先 register_agent"}
            return self.message_bus.join_channel(
                channel_id=msg.get("channel_id", ""),
                agent_id=agent_id,
            )

        # 频道离开
        if mtype == "channel_leave":
            if not agent_id:
                return {"type": "error", "message": "请先 register_agent"}
            return self.message_bus.leave_channel(
                channel_id=msg.get("channel_id", ""),
                agent_id=agent_id,
            )

        # 频道消息
        if mtype == "channel_post":
            if not agent_id:
                return {"type": "error", "message": "请先 register_agent"}
            return await self.message_bus.post_to_channel(
                channel_id=msg.get("channel_id", ""),
                from_id=agent_id,
                text=msg.get("text", ""),
            )

        # 列出频道
        if mtype == "list_channels":
            channels = self.message_bus.list_channels()
            return {
                "type": "channels_list",
                "channels": channels,
                "count": len(channels),
            }

        # 频道历史
        if mtype == "channel_history":
            return self.message_bus.get_channel_history(
                channel_id=msg.get("channel_id", ""),
                limit=msg.get("limit", 50),
            )

        return None

    async def _pending_cleanup_loop(self):
        """定期清理过期的 pending 条目，防止内存泄漏。"""
        while True:
            await asyncio.sleep(60)
            now = time.monotonic()
            expired = [k for k, (_, ts) in self.pending.items() if now - ts > self._pending_ttl]
            for k in expired:
                del self.pending[k]
            if expired:
                logger.info(f"[清理] 清理 {len(expired)} 个过期 pending 条目")

    async def stop(self):
        logger.info("智桥停止中...")
        if self._cleanup_task:
            self._cleanup_task.cancel()
        for ws in list(self.users.values()) + list(self.backends.values()):
            try:
                await ws.close()
            except Exception:
                pass
        self.users.clear()
        self.backends.clear()
        self.routing.clear()
        self.pending.clear()
        self._agent_connections.clear()
        if self.message_bus:
            await self.message_bus.stop()
        if self.session_manager:
            for sid in self._session_map.values():
                try:
                    self.session_manager.update_session_status(sid, "archived")
                except Exception:
                    pass
            self._session_map.clear()
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        logger.info("智桥已停止")


async def main():
    backend_secret = None
    try:
        from config import settings

        if settings.security.enable_auth:
            backend_secret = settings.security.secret_key
    except Exception:
        pass
    server = AIRelayServer(host="0.0.0.0", port=8766, backend_secret=backend_secret)
    await server.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n智桥已停止")

#!/usr/bin/env python3
"""智桥 AI Relay Server — 用户与AI后端之间的WebSocket中继。

架构:
  用户(浏览器) ←ws→ 智桥(:8765) ←ws→ AI后端(灵依/灵克/灵知...)
  用户(浏览器) ←ws→ 智桥(:8765) ←ws→ AI后端(灵依/灵克/灵知...)

协议:
  用户 → 智桥: {"type":"chat","target":"lingyi","text":"..."}
  智桥 → AI:   {"type":"chat","from":"user_xxx","text":"..."}
  AI → 智桥:   {"type":"reply","text":"...","audio":"base64..."}
  智桥 → 用户: {"type":"reply","text":"...","audio":"base64..."}

  用户 → 智桥: {"type":"register_backend","backend_id":"lingyi"}
  智桥确认:    {"type":"backend_registered","backend_id":"lingyi"}
"""

import asyncio
import json
import logging
import ssl
import uuid
from datetime import datetime
from pathlib import Path

import websockets

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("zhineng-bridge")


class AIRelayServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 8765):
        self.host = host
        self.port = port
        self.server = None

        # 用户连接: client_id → websocket
        self.users: dict[str, websockets.WebSocketServerProtocol] = {}
        # AI后端连接: backend_id → websocket
        self.backends: dict[str, websockets.WebSocketServerProtocol] = {}
        # 用户当前对话的AI: client_id → backend_id
        self.routing: dict[str, str] = {}
        # AI后端元数据: backend_id → {name, description, ...}
        self.backend_meta: dict[str, dict] = {}
        # 待回复的请求: request_id → client_id
        self.pending: dict[str, str] = {}

    async def start(self):
        ssl_kwargs = {}
        cert_dir = Path.home() / ".lingyi"
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
        self.server = await websockets.serve(
            self._handle_connection,
            self.host,
            self.port,
            ping_interval=30,
            ping_timeout=60,
            **ssl_kwargs,
        )
        logger.info(f"智桥就绪 — 等待用户和AI后端连接")
        await self.server.wait_closed()

    async def _handle_connection(self, websocket: websockets.WebSocketServerProtocol):
        conn_id = str(uuid.uuid4())[:8]
        logger.info(f"[连接] 新连接 {conn_id}")

        try:
            async for raw in websocket:
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({"type": "error", "message": "Invalid JSON"}))
                    continue

                await self._dispatch(conn_id, websocket, msg)

        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            logger.error(f"[连接] {conn_id} 异常: {e}")
        finally:
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
            self.pending = {k: v for k, v in self.pending.items() if v != conn_id}

    async def _dispatch(self, conn_id: str, websocket, msg: dict):
        mtype = msg.get("type", "")

        # AI后端注册
        if mtype == "register_backend":
            backend_id = msg.get("backend_id", "")
            if not backend_id:
                await websocket.send(json.dumps({"type": "error", "message": "backend_id required"}))
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
            await websocket.send(json.dumps({
                "type": "backend_registered",
                "backend_id": backend_id,
                "message": f"智桥已注册 {backend_id}",
            }))
            logger.info(f"[注册] AI后端 {backend_id} 已注册")
            return

        # AI后端回复（转发给用户）
        if mtype == "reply":
            request_id = msg.get("request_id", "")
            client_id = self.pending.pop(request_id, None)
            if client_id and client_id in self.users:
                await self.users[client_id].send(json.dumps({
                    "type": "reply",
                    "text": msg.get("text", ""),
                    "audio": msg.get("audio"),
                    "backend": msg.get("backend", ""),
                    "timestamp": datetime.now().isoformat(),
                }))
                logger.info(f"[回复] {request_id[:8]} → 用户 {client_id}")
            else:
                logger.warning(f"[回复] 找不到请求 {request_id} 对应的用户")
            return

        # AI后端主动推送
        if mtype == "push":
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
            target = msg.get("target", "lingyi")
            text = msg.get("text", "").strip()
            if not text:
                return

            # 自动注册用户
            if conn_id not in self.users:
                self.users[conn_id] = websocket
                if conn_id not in self.routing:
                    self.routing[conn_id] = target
                logger.info(f"[用户] 新用户 {conn_id} 默认路由 → {target}")

            backend_id = self.routing.get(conn_id, target)
            backend_ws = self.backends.get(backend_id)

            if not backend_ws:
                # 尝试任意可用后端
                if self.backends:
                    backend_id = next(iter(self.backends))
                    backend_ws = self.backends[backend_id]
                    self.routing[conn_id] = backend_id
                    logger.info(f"[路由] {backend_id} 不可用，回退到 {backend_id}")
                else:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "没有可用的AI后端，请稍后再试",
                    }))
                    return

            request_id = str(uuid.uuid4())
            self.pending[request_id] = conn_id

            await backend_ws.send(json.dumps({
                "type": "chat",
                "request_id": request_id,
                "from": conn_id,
                "text": text,
                "audio": msg.get("audio"),
                "timestamp": datetime.now().isoformat(),
            }))
            logger.info(f"[转发] 用户 {conn_id} → {backend_id}: {text[:50]}")
            return

        # 用户切换AI后端
        if mtype == "switch_backend":
            target = msg.get("target", "lingyi")
            self.routing[conn_id] = target
            await websocket.send(json.dumps({
                "type": "backend_switched",
                "backend_id": target,
            }))
            logger.info(f"[切换] 用户 {conn_id} → {target}")
            return

        # 列出可用AI后端
        if mtype == "list_backends":
            backends = []
            for bid, meta in self.backend_meta.items():
                backends.append({
                    "id": bid,
                    "name": meta.get("name", bid),
                    "description": meta.get("description", ""),
                    "online": bid in self.backends,
                })
            await websocket.send(json.dumps({
                "type": "backends_list",
                "backends": backends,
                "current": self.routing.get(conn_id, ""),
            }))
            return

        # 心跳
        if mtype == "ping":
            await websocket.send(json.dumps({
                "type": "pong",
                "timestamp": datetime.now().isoformat(),
            }))
            return

        # 未知类型
        await websocket.send(json.dumps({
            "type": "error",
            "message": f"Unknown message type: {mtype}",
        }))

    async def stop(self):
        logger.info("智桥停止中...")
        for ws in list(self.users.values()) + list(self.backends.values()):
            try:
                await ws.close()
            except Exception:
                pass
        self.users.clear()
        self.backends.clear()
        self.routing.clear()
        self.pending.clear()
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        logger.info("智桥已停止")


async def main():
    server = AIRelayServer(host="0.0.0.0", port=8765)
    await server.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n智桥已停止")

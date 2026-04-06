#!/usr/bin/env python3
"""
zhineng-bridge Session Manager — 真实子进程管理

管理 AI 工具的子进程生命周期：启动、停止、输入/输出、超时清理。
"""

import asyncio
import os
import shutil
import signal
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any


class SessionManager:
    """Session Manager — 会话管理器，支持真实子进程管理"""

    def __init__(self, base_dir: str = "/tmp"):
        self.base_dir = base_dir
        self.sessions: Dict[str, Session] = {}
        self.active_session_id: Optional[str] = None

        self.tools = {
            "crush": {
                "name": "Crush",
                "description": "Charmbracelet Crush - AI 编码助手",
                "executable": "crush",
                "icon": "💎",
                "color": "#FFE66D",
            },
            "claude": {
                "name": "Claude Code",
                "description": "Anthropic Claude Code - AI 编码助手",
                "executable": "claude",
                "icon": "🤖",
                "color": "#FF6B6B",
            },
            "iflow": {
                "name": "iFlow CLI",
                "description": "阿里巴巴心流 iFlow CLI - AI 编码助手",
                "executable": "iflow",
                "icon": "🌊",
                "color": "#4ECDC4",
            },
            "cursor": {
                "name": "Cursor",
                "description": "Anysphere Cursor - AI IDE",
                "executable": "cursor",
                "icon": "👆",
                "color": "#45B7D1",
            },
            "trae": {
                "name": "Trae",
                "description": "字节跳动 Trae - AI IDE",
                "executable": "trae",
                "icon": "🌊",
                "color": "#96CEB4",
            },
            "factroydroid": {
                "name": "Droid",
                "description": "Factory Droid - AI Agent",
                "executable": "droid",
                "icon": "🤖",
                "color": "#FFEEAD",
            },
            "openclaw": {
                "name": "OpenClaw",
                "description": "OpenClaw - AI 助手",
                "executable": "openclaw",
                "icon": "🦞",
                "color": "#D4A5A5",
            },
            "copilot": {
                "name": "GitHub Copilot",
                "description": "GitHub Copilot - AI 助手",
                "executable": "copilot",
                "icon": "🤖",
                "color": "#F0F0F0",
            },
            "aider": {
                "name": "Aider",
                "description": "Aider - AI 结对编程 (GPT-4/Claude)",
                "executable": "aider",
                "icon": "🦸",
                "color": "#7C3AED",
            },
            "continue": {
                "name": "Continue",
                "description": "Continue.dev - 开源 AI 代码助手",
                "executable": "continue",
                "icon": "▶️",
                "color": "#06B6D4",
            },
            "tabnine": {
                "name": "Tabnine",
                "description": "Tabnine - AI 代码补全",
                "executable": "tabnine",
                "icon": "⌨️",
                "color": "#6366F1",
            },
            "codium": {
                "name": "CodiumAI",
                "description": "CodiumAI - AI 测试与代码完整性",
                "executable": "codium",
                "icon": "🧪",
                "color": "#F59E0B",
            },
            "windsurf": {
                "name": "Windsurf",
                "description": "Codeium Windsurf - AI IDE",
                "executable": "windsurf",
                "icon": "🏄",
                "color": "#10B981",
            },
            "cody": {
                "name": "Sourcegraph Cody",
                "description": "Sourcegraph Cody - AI 代码助手",
                "executable": "cody",
                "icon": "🔍",
                "color": "#8B5CF6",
            },
            "augment": {
                "name": "Augment",
                "description": "Augment Code - AI 编程助手",
                "executable": "augment",
                "icon": "⚡",
                "color": "#EF4444",
            },
        }

    def list_tools(self) -> Dict[str, Dict[str, Any]]:
        return self.tools

    def get_tool_info(self, tool_key: str) -> Optional[Dict[str, Any]]:
        return self.tools.get(tool_key)

    def is_tool_available(self, tool_key: str) -> bool:
        info = self.tools.get(tool_key)
        if not info:
            return False
        return shutil.which(info["executable"]) is not None

    def create_session(self, tool_name: str, args: List[str] = None) -> str:
        if tool_name not in self.tools:
            raise ValueError(f"工具不存在: {tool_name}")

        session_id = str(uuid.uuid4())
        session = Session(
            session_id=session_id,
            tool_name=tool_name,
            args=args or [],
            base_dir=self.base_dir,
        )
        self.sessions[session_id] = session
        self.active_session_id = session_id
        return session_id

    async def start_session(self, session_id: str) -> Dict[str, Any]:
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"会话不存在: {session_id}")
        if session.status == "running":
            return {"session_id": session_id, "status": "running", "message": "already running"}

        tool_info = self.tools.get(session.tool_name)
        if not tool_info:
            raise ValueError(f"工具不存在: {session.tool_name}")

        executable = tool_info["executable"]
        if not shutil.which(executable):
            session.status = "error"
            return {"session_id": session_id, "status": "error", "message": f"executable not found: {executable}"}

        try:
            proc = await asyncio.create_subprocess_exec(
                executable,
                *session.args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=session.base_dir if os.path.isdir(session.base_dir) else None,
            )
            session.process = proc
            session.status = "running"
            session.started_at = datetime.now().isoformat()
            return {"session_id": session_id, "status": "running", "pid": proc.pid}
        except Exception as e:
            session.status = "error"
            return {"session_id": session_id, "status": "error", "message": str(e)}

    async def stop_session(self, session_id: str) -> Dict[str, Any]:
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"会话不存在: {session_id}")

        proc = session.process
        if proc and proc.returncode is None:
            try:
                proc.terminate()
                try:
                    await asyncio.wait_for(proc.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    proc.kill()
                    await proc.wait()
            except ProcessLookupError:
                pass

        session.status = "stopped"
        session.process = None
        return {"session_id": session_id, "status": "stopped"}

    def delete_session(self, session_id: str) -> Dict[str, Any]:
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"会话不存在: {session_id}")

        proc = session.process
        if proc and proc.returncode is None:
            raise RuntimeError(f"会话 {session_id} 仍在运行，请先停止")

        del self.sessions[session_id]
        if self.active_session_id == session_id:
            self.active_session_id = None
        return {"session_id": session_id, "status": "deleted"}

    async def send_input(self, session_id: str, text: str) -> Dict[str, Any]:
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"会话不存在: {session_id}")
        if session.status != "running" or not session.process:
            raise RuntimeError(f"会话 {session_id} 未在运行")

        proc = session.process
        if proc.stdin.is_closing():
            raise RuntimeError("stdin closed")

        proc.stdin.write(text.encode())
        await proc.stdin.drain()
        return {"session_id": session_id, "status": "sent", "bytes": len(text)}

    async def read_output(self, session_id: str, timeout: float = 1.0) -> Dict[str, Any]:
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"会话不存在: {session_id}")
        if session.status != "running" or not session.process:
            raise RuntimeError(f"会话 {session_id} 未在运行")

        proc = session.process
        output_lines = []

        try:
            while True:
                line = await asyncio.wait_for(proc.stdout.readline(), timeout=timeout)
                if not line:
                    break
                output_lines.append(line.decode(errors="replace"))
        except asyncio.TimeoutError:
            pass

        return {"session_id": session_id, "output": "".join(output_lines)}

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        session = self.sessions.get(session_id)
        if session:
            return session.to_dict()
        return None

    def list_sessions(self) -> List[Dict[str, Any]]:
        return [s.to_dict() for s in self.sessions.values()]

    def get_active_session(self) -> Optional[Dict[str, Any]]:
        if self.active_session_id:
            return self.get_session(self.active_session_id)
        return None

    def set_active_session(self, session_id: str) -> None:
        if session_id not in self.sessions:
            raise ValueError(f"会话不存在: {session_id}")
        self.active_session_id = session_id

    async def cleanup_all(self) -> int:
        count = 0
        for sid in list(self.sessions.keys()):
            session = self.sessions[sid]
            if session.process and session.process.returncode is None:
                await self.stop_session(sid)
                count += 1
        return count


class Session:
    """Session — 单个 AI 工具子进程会话"""

    def __init__(self, session_id: str, tool_name: str, args: List[str], base_dir: str = "/tmp"):
        self.session_id = session_id
        self.tool_name = tool_name
        self.args = args
        self.base_dir = base_dir
        self.status = "created"
        self.created_at = datetime.now().isoformat()
        self.started_at: Optional[str] = None
        self.process: Optional[asyncio.subprocess.Process] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "session_id": self.session_id,
            "tool_name": self.tool_name,
            "status": self.status,
            "created_at": self.created_at,
            "args": self.args,
        }
        if self.started_at:
            d["started_at"] = self.started_at
        if self.process and self.process.returncode is not None:
            d["exit_code"] = self.process.returncode
        return d


if __name__ == "__main__":
    manager = SessionManager()

    print("\n📋 可用工具:")
    for tool_key, tool_info in manager.list_tools().items():
        available = "✅" if manager.is_tool_available(tool_key) else "❌"
        print(f"  {available} {tool_key}: {tool_info['name']}")

    print("\n📋 会话列表:")
    for session in manager.list_sessions():
        print(f"  - {session['session_id'][:8]}: {session['tool_name']} ({session['status']})")

"""智桥 MCP Server — 12个核心HTTP API封装为MCP工具。

智桥是灵字辈生态的中继服务，提供用户认证、文件访问、团队协作、插件管理。
本服务器通过HTTP调用智桥API，保持松耦合。

工具清单:
  认证: login, get_current_user
  文件: file_read, file_list, file_search, file_stats
  团队: list_teams, create_team, team_get_sessions, share_session
  插件: list_plugins, health_check
"""

from __future__ import annotations

import json
import os
from typing import Any

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    name="ZhinengBridge",
    instructions="智桥（Zhineng-Bridge）MCP Server — 灵字辈中继服务核心API",
)

BASE_URL = os.environ.get("ZHINENG_BRIDGE_URL", "http://localhost:8000")
_auth_token: str = ""


def _headers() -> dict[str, str]:
    h = {"Content-Type": "application/json"}
    if _auth_token:
        h["Authorization"] = f"Bearer {_auth_token}"
    return h


def _request(method: str, path: str, data: dict | None = None, params: dict | None = None) -> Any:
    import urllib.parse
    import urllib.request

    url = BASE_URL + path
    if params:
        url += "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=_headers(), method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return json.loads(raw)
        except Exception:
            return {"error": e.reason, "status": e.code}
    except Exception as e:
        return {"error": str(e)}


# ── 认证（2个工具） ──


@mcp.tool(name="login", description="用户登录（灵登）")
def tool_login(username: str, password: str) -> dict:
    """登录智桥获取认证令牌。成功后自动缓存token供后续调用使用。"""
    global _auth_token
    result = _request("POST", "/api/users/login", {"username": username, "password": password})
    if "token" in result:
        _auth_token = result["token"]
    return result


@mcp.tool(name="get_current_user", description="当前用户（灵我）")
def tool_get_current_user() -> dict:
    """获取当前已认证用户信息。"""
    return _request("GET", "/api/users/me")


# ── 文件（4个工具） ──


@mcp.tool(name="file_read", description="读取文件（灵读）")
def tool_file_read(path: str) -> dict:
    """读取服务器上指定文件内容。"""
    return _request("GET", "/api/files/read", params={"path": path})


@mcp.tool(name="file_list", description="列出文件（灵列）")
def tool_file_list(path: str = ".", recursive: bool = False) -> dict:
    """列出目录内容。"""
    return _request(
        "GET", "/api/files/list", params={"path": path, "recursive": str(recursive).lower()}
    )


@mcp.tool(name="file_search", description="搜索文件（灵搜）")
def tool_file_search(query: str, path: str = "") -> dict:
    """按文件名搜索文件。"""
    return _request("GET", "/api/files/search", params={"query": query, "path": path or None})


@mcp.tool(name="file_stats", description="文件信息（灵态）")
def tool_file_stats(path: str) -> dict:
    """获取文件或目录的元数据。"""
    return _request("GET", "/api/files/stats", params={"path": path})


# ── 团队（4个工具） ──


@mcp.tool(name="list_teams", description="列出团队（灵队）")
def tool_list_teams() -> dict:
    """列出当前用户所属的团队。"""
    return _request("GET", "/api/teams")


@mcp.tool(name="create_team", description="创建团队（灵创队）")
def tool_create_team(name: str, description: str = "") -> dict:
    """创建新团队。"""
    return _request("POST", "/api/teams", {"name": name, "description": description})


@mcp.tool(name="team_get_sessions", description="团队会话（灵享）")
def tool_team_get_sessions(team_id: str) -> dict:
    """获取团队共享的会话列表。"""
    return _request("GET", f"/api/teams/{team_id}/sessions")


@mcp.tool(name="share_session", description="共享会话（灵传）")
def tool_share_session(team_id: str, session_id: str, title: str = "") -> dict:
    """将会话共享到团队。"""
    return _request(
        "POST",
        f"/api/teams/{team_id}/sessions/share",
        {
            "session_id": session_id,
            "title": title,
        },
    )


# ── 插件+健康（2个工具） ──


@mcp.tool(name="list_plugins", description="插件列表（灵件）")
def tool_list_plugins() -> dict:
    """列出所有插件及其状态。"""
    return _request("GET", "/api/plugins")


@mcp.tool(name="health_check", description="健康检查（灵康）")
def tool_health_check(verbose: bool = False) -> dict:
    """检查智桥服务健康状态（数据库、插件、磁盘、认证）。"""
    return _request("GET", "/health", params={"verbose": "1" if verbose else None})


def main():
    try:
        from lingmessage.registry import register_fastmcp_server
        register_fastmcp_server("zhibridge", "智桥", mcp, "跨平台桥接")
    except Exception:
        pass
    mcp.run()


if __name__ == "__main__":
    main()

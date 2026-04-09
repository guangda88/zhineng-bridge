#!/usr/bin/env python3
"""
HTTP 服务器

处理:
- OAuth2 回调
- 健康检查
- 用户管理 API
"""

import html
import secrets
from datetime import datetime

from aiohttp import web
from exceptions import (
    AuthenticationError,
    ValidationError,
    exception_to_dict,
)
from file_api import FileAPI, setup_file_routes
from logger import get_logger
from oauth2 import oauth2_manager
from plugin_system import PluginManager
from push_service import PushService, setup_push_routes
from team_manager import TeamManager
from team_models import TeamRole
from user_auth import AuthenticationManager

from config import settings


class HTTPServer:
    """HTTP 服务器"""

    def __init__(self, auth_manager: AuthenticationManager):
        """
        初始化 HTTP 服务器

        Args:
            auth_manager: 认证管理器
        """
        self.logger = get_logger(__name__)
        self.auth_manager = auth_manager
        self.port = settings.monitoring.http_port
        self.app = web.Application()

        # 初始化文件 API
        self.file_api = FileAPI(base_dir="/home/ai/zhineng-bridge")

        # 初始化推送服务
        self.push_service = PushService()

        # 初始化团队管理器
        self.team_manager = TeamManager(auth_manager.db)

        # 初始化插件管理器
        self.plugin_manager = PluginManager()
        self.plugin_manager.load_all()

        self._setup_routes()

    def _setup_routes(self):
        """设置路由"""
        # OAuth2 路由
        self.app.router.add_get("/auth/{provider}", self.auth_provider)
        self.app.router.add_get("/auth/{provider}/callback", self.auth_callback)

        # 用户管理 API
        self.app.router.add_post("/api/users/register", self.register_user)
        self.app.router.add_post("/api/users/login", self.login_user)
        self.app.router.add_post("/api/users/logout", self.logout_user)
        self.app.router.add_get("/api/users/me", self.get_current_user)
        self.app.router.add_put("/api/users/{user_id}", self.update_user)
        self.app.router.add_delete("/api/users/{user_id}", self.delete_user)
        self.app.router.add_get("/api/users", self.list_users)

        # 密码重置 API
        self.app.router.add_post("/api/users/password-reset/request", self.request_password_reset)
        self.app.router.add_post("/api/users/password-reset/confirm", self.confirm_password_reset)
        self.app.router.add_post("/api/users/password/change", self.change_password)

        # 双因素认证 API
        self.app.router.add_post("/api/users/2fa/setup", self.setup_2fa)
        self.app.router.add_post("/api/users/2fa/enable", self.enable_2fa)
        self.app.router.add_post("/api/users/2fa/verify", self.verify_2fa)
        self.app.router.add_post("/api/users/2fa/disable", self.disable_2fa)
        self.app.router.add_post("/api/users/2fa/backup-codes", self.regenerate_backup_codes)

        # 文件 API
        setup_file_routes(self.app, self.file_api)

        # 推送服务 API
        setup_push_routes(self.app, self.push_service)

        # 团队协作 API
        self.app.router.add_post("/api/teams", self.create_team)
        self.app.router.add_get("/api/teams", self.list_teams)
        self.app.router.add_get("/api/teams/{team_id}", self.get_team)
        self.app.router.add_put("/api/teams/{team_id}", self.update_team)
        self.app.router.add_delete("/api/teams/{team_id}", self.delete_team)
        self.app.router.add_get("/api/teams/{team_id}/members", self.get_team_members)
        self.app.router.add_put("/api/teams/{team_id}/members/{target_id}", self.update_member_role)
        self.app.router.add_delete("/api/teams/{team_id}/members/{target_id}", self.remove_member)
        self.app.router.add_post("/api/teams/{team_id}/leave", self.leave_team)
        self.app.router.add_post("/api/teams/{team_id}/invites", self.create_invite)
        self.app.router.add_get("/api/teams/{team_id}/invites", self.list_invites)
        self.app.router.add_post("/api/teams/invites/{token}/accept", self.accept_invite)
        self.app.router.add_post("/api/teams/{team_id}/sessions/share", self.share_session)
        self.app.router.add_delete("/api/teams/sessions/{share_id}", self.unshare_session)
        self.app.router.add_get("/api/teams/{team_id}/sessions", self.get_team_sessions)

        # 插件管理 API
        self.app.router.add_get("/api/plugins", self.list_plugins)
        self.app.router.add_get("/api/plugins/{plugin_id}", self.get_plugin)
        self.app.router.add_post("/api/plugins/{plugin_id}/enable", self.enable_plugin)
        self.app.router.add_post("/api/plugins/{plugin_id}/disable", self.disable_plugin)
        self.app.router.add_post("/api/plugins/{plugin_id}/reload", self.reload_plugin)
        self.app.router.add_post("/api/plugins/{plugin_id}/config", self.configure_plugin)
        self.app.router.add_get("/api/plugins/{plugin_id}/commands", self.get_plugin_commands)
        self.app.router.add_post("/api/plugins/discover", self.discover_plugins)

        # 健康检查
        self.app.router.add_get("/health", self.health_check)

    async def start(self):
        """启动 HTTP 服务器"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", self.port)
        await site.start()

        self.logger.info(
            "HTTP server started",
            port=self.port,
            oauth2_providers=oauth2_manager.list_providers(),
        )

    async def stop(self):
        """停止 HTTP 服务器"""
        self.logger.info("HTTP server stopped")

    # ========================================================================
    # OAuth2 端点
    # ========================================================================

    async def auth_provider(self, request: web.Request) -> web.Response:
        """
        OAuth2 授权端点

        重定向到 OAuth2 提供商的授权页面
        """
        provider_name = request.match_info["provider"]

        # 生成 state 参数（CSRF 保护）
        state = secrets.token_urlsafe(32)

        # F-021: 存储 state 用于回调验证
        if not hasattr(self, "_oauth_states"):
            self._oauth_states = {}
        self._oauth_states[state] = datetime.now().isoformat()

        provider = oauth2_manager.get_provider(provider_name)
        if not provider:
            return web.json_response(
                {
                    "type": "error",
                    "message": f"OAuth2 provider '{provider_name}' not found",
                    "code": 400,
                },
                status=400,
            )

        # Validate Host header to prevent injection
        host = request.host
        allowed_hosts = ["localhost", "127.0.0.1"]
        server_ws_host = settings.server.ws_host
        if server_ws_host:
            allowed_hosts.append(server_ws_host)
        host_without_port = host.split(":")[0]
        if host_without_port not in allowed_hosts:
            return web.json_response(
                {"type": "error", "message": "Invalid host header"},
                status=400,
            )

        # 构建回调 URL
        redirect_uri = f"http://{host}/auth/{provider_name}/callback"

        # 获取授权 URL
        auth_url = provider.get_authorization_url(redirect_uri, state)

        self.logger.info(
            "OAuth2 authorization initiated",
            provider=provider_name,
            state=state,
        )

        return web.Response(status=302, headers={"Location": auth_url})

    async def auth_callback(self, request: web.Request) -> web.Response:
        """
        OAuth2 回调端点

        处理 OAuth2 提供商的回调
        """
        provider_name = request.match_info["provider"]
        code = request.query.get("code")
        state = request.query.get("state")
        error = request.query.get("error")

        if error:
            self.logger.error(
                "OAuth2 callback error",
                provider=provider_name,
                error=error,
                error_description=request.query.get("error_description"),
            )
            return web.Response(
                text=f"OAuth2 authentication failed: {error}",
                status=400,
            )

        if not code:
            return web.Response(
                text="Missing authorization code",
                status=400,
            )

        # F-021: 验证 state 参数
        if hasattr(self, "_oauth_states"):
            if state not in self._oauth_states:
                return web.Response(
                    text="Invalid or expired state parameter",
                    status=400,
                )
            del self._oauth_states[state]
        elif state:
            self.logger.warning("OAuth2 state received but no state store initialized")

        try:
            # 构建回调 URL
            redirect_uri = f"http://{request.host}/auth/{provider_name}/callback"

            # 处理 OAuth2 回调
            user = await oauth2_manager.handle_oauth2_callback(
                provider_name=provider_name,
                code=code,
                redirect_uri=redirect_uri,
                auth_manager=self.auth_manager,
            )

            # 登录用户
            token, token_info = self.auth_manager.login_user_oauth(user)

            self.logger.info(
                "User authenticated via OAuth2",
                provider=provider_name,
                user_id=user.user_id,
                username=user.username,
            )

            # F-020: 设置 HTTP-only cookie 而非在 HTML 中显示 token
            response = web.Response(
                text=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Authentication Successful</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    }}
                    .container {{
                        background: white;
                        padding: 2rem;
                        border-radius: 10px;
                        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
                        text-align: center;
                    }}
                    .success {{
                        color: #48bb78;
                        font-size: 1.5rem;
                        margin-bottom: 1rem;
                    }}
                    button {{
                        background: #667eea;
                        color: white;
                        border: none;
                        padding: 0.75rem 1.5rem;
                        border-radius: 5px;
                        cursor: pointer;
                        font-size: 1rem;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="success">✅ Authentication Successful!</div>
                    <p>Welcome, {html.escape(user.username)}!</p>
                    <p>Your authentication token has been saved.</p>
                    <button onclick="window.close()">Close</button>
                </div>
            </body>
            </html>
            """,
                content_type="text/html",
            )
            response.set_cookie(
                "auth_token",
                token,
                httponly=True,
                secure=request.scheme == "https",
                max_age=86400,
                samesite="Lax",
            )
            return response

        except Exception as e:
            self.logger.error(
                "OAuth2 callback failed",
                provider=provider_name,
                error=str(e),
                exc_info=True,
            )
            return web.Response(
                text=f"Authentication failed: {str(e)}",
                status=500,
            )

    # ========================================================================
    # 用户管理 API
    # ========================================================================

    async def register_user(self, request: web.Request) -> web.Response:
        """
        用户注册端点

        POST /api/users/register
        {
            "username": "user",
            "password": "password",
            "email": "user@example.com"
        }
        """
        try:
            data = await request.json()

            username = data.get("username")
            password = data.get("password")
            email = data.get("email")

            if not username or not password:
                raise ValidationError("Username and password are required")

            # 验证密码强度
            if len(password) < 8:
                raise ValidationError("Password must be at least 8 characters")

            # 注册用户
            user = self.auth_manager.register_user(
                username=username,
                password=password,
                email=email,
            )

            self.logger.info("User registered", user_id=user.user_id, username=username)

            return web.json_response(
                {
                    "type": "user_registered",
                    "user_id": user.user_id,
                    "username": user.username,
                    "email": user.email,
                },
                status=201,
            )

        except ValidationError as e:
            return web.json_response(e.to_dict(), status=400)
        except ValueError as e:
            return web.json_response(
                {
                    "type": "error",
                    "message": str(e),
                    "code": 409,
                },
                status=409,
            )
        except Exception as e:
            self.logger.error("Registration failed", error=str(e), exc_info=True)
            return web.json_response(
                exception_to_dict(e),
                status=500,
            )

    async def login_user(self, request: web.Request) -> web.Response:
        """
        用户登录端点

        POST /api/users/login
        {
            "username": "user",
            "password": "password"
        }
        """
        try:
            data = await request.json()

            username = data.get("username")
            password = data.get("password")

            if not username or not password:
                raise ValidationError("Username and password are required")

            # 登录用户
            token, token_info = self.auth_manager.login_user(username, password)

            self.logger.info("User logged in", username=username)

            return web.json_response(
                {
                    "type": "user_logged_in",
                    "token": token,
                    "user_id": token_info.user_id,
                    "username": token_info.username,
                    "expires_at": (
                        token_info.expires_at.isoformat() if token_info.expires_at else None
                    ),
                    "scopes": token_info.scopes,
                },
                status=200,
            )

        except ValidationError as e:
            return web.json_response(e.to_dict(), status=400)
        except AuthenticationError as e:
            return web.json_response(e.to_dict(), status=401)
        except Exception as e:
            self.logger.error("Login failed", error=str(e), exc_info=True)
            return web.json_response(
                exception_to_dict(e),
                status=500,
            )

    async def logout_user(self, request: web.Request) -> web.Response:
        """
        用户登出端点

        POST /api/users/logout
        Headers: Authorization: Bearer <token>
        """
        try:
            token = request.headers.get("Authorization", "").replace("Bearer ", "")

            if not token:
                raise ValidationError("Authorization header required")

            # 登出用户
            success = self.auth_manager.logout_user(token)

            if success:
                self.logger.info("User logged out")
                return web.json_response(
                    {
                        "type": "user_logged_out",
                        "message": "Successfully logged out",
                    },
                    status=200,
                )
            else:
                return web.json_response(
                    {
                        "type": "error",
                        "message": "Invalid token",
                        "code": 401,
                    },
                    status=401,
                )

        except ValidationError as e:
            return web.json_response(e.to_dict(), status=400)
        except Exception as e:
            self.logger.error("Logout failed", error=str(e), exc_info=True)
            return web.json_response(
                exception_to_dict(e),
                status=500,
            )

    async def get_current_user(self, request: web.Request) -> web.Response:
        """
        获取当前用户信息

        GET /api/users/me
        Headers: Authorization: Bearer <token>
        """
        try:
            token = request.headers.get("Authorization", "").replace("Bearer ", "")

            if not token:
                raise ValidationError("Authorization header required")

            # 验证 token
            user = self.auth_manager.get_user_from_token(token)

            if not user:
                raise AuthenticationError("Invalid or expired token")

            return web.json_response(
                {
                    "type": "user_info",
                    "user": user.to_dict(),
                },
                status=200,
            )

        except ValidationError as e:
            return web.json_response(e.to_dict(), status=400)
        except AuthenticationError as e:
            return web.json_response(e.to_dict(), status=401)
        except Exception as e:
            self.logger.error("Get user info failed", error=str(e), exc_info=True)
            return web.json_response(
                exception_to_dict(e),
                status=500,
            )

    async def update_user(self, request: web.Request) -> web.Response:
        """
        更新用户信息

        PUT /api/users/{user_id}
        Headers: Authorization: Bearer <token>
        {
            "email": "newemail@example.com",
            "role": "admin"
        }
        """
        try:
            user_id = request.match_info["user_id"]
            token = request.headers.get("Authorization", "").replace("Bearer ", "")

            if not token:
                raise ValidationError("Authorization header required")

            # 验证 token
            current_user = self.auth_manager.get_user_from_token(token)
            if not current_user:
                raise AuthenticationError("Invalid or expired token")

            # 检查权限（只能更新自己或管理员可以更新任何人）
            if current_user.user_id != user_id and "admin" not in current_user.permissions:
                raise AuthenticationError("Insufficient permissions")

            data = await request.json()

            # F-022: 白名单过滤允许更新的字段
            allowed_fields = {"username", "email", "display_name"}
            filtered_data = {k: v for k, v in data.items() if k in allowed_fields}
            if not filtered_data:
                return web.json_response(
                    {"type": "error", "message": "No valid fields to update", "code": 400},
                    status=400,
                )

            # 更新用户
            success = self.auth_manager.db.update_user(user_id, **filtered_data)

            if success:
                self.logger.info("User updated", user_id=user_id)
                updated_user = self.auth_manager.db.get_user(user_id=user_id)
                return web.json_response(
                    {
                        "type": "user_updated",
                        "user": updated_user.to_dict(),
                    },
                    status=200,
                )
            else:
                return web.json_response(
                    {
                        "type": "error",
                        "message": "User not found",
                        "code": 404,
                    },
                    status=404,
                )

        except ValidationError as e:
            return web.json_response(e.to_dict(), status=400)
        except AuthenticationError as e:
            return web.json_response(e.to_dict(), status=401)
        except Exception as e:
            self.logger.error("Update user failed", error=str(e), exc_info=True)
            return web.json_response(
                exception_to_dict(e),
                status=500,
            )

    async def delete_user(self, request: web.Request) -> web.Response:
        """
        删除用户

        DELETE /api/users/{user_id}
        Headers: Authorization: Bearer <token>
        """
        try:
            user_id = request.match_info["user_id"]
            token = request.headers.get("Authorization", "").replace("Bearer ", "")

            if not token:
                raise ValidationError("Authorization header required")

            # 验证 token
            current_user = self.auth_manager.get_user_from_token(token)
            if not current_user:
                raise AuthenticationError("Invalid or expired token")

            # 检查权限（只能删除自己或管理员可以删除任何人）
            if current_user.user_id != user_id and "admin" not in current_user.permissions:
                raise AuthenticationError("Insufficient permissions")

            # 删除用户
            success = self.auth_manager.db.delete_user(user_id)

            if success:
                self.logger.info("User deleted", user_id=user_id)
                return web.json_response(
                    {
                        "type": "user_deleted",
                        "user_id": user_id,
                    },
                    status=200,
                )
            else:
                return web.json_response(
                    {
                        "type": "error",
                        "message": "User not found",
                        "code": 404,
                    },
                    status=404,
                )

        except ValidationError as e:
            return web.json_response(e.to_dict(), status=400)
        except AuthenticationError as e:
            return web.json_response(e.to_dict(), status=401)
        except Exception as e:
            self.logger.error("Delete user failed", error=str(e), exc_info=True)
            return web.json_response(
                exception_to_dict(e),
                status=500,
            )

    async def list_users(self, request: web.Request) -> web.Response:
        """
        列出用户

        GET /api/users
        Headers: Authorization: Bearer <token>
        Query: ?limit=100&offset=0
        """
        try:
            token = request.headers.get("Authorization", "").replace("Bearer ", "")

            if not token:
                raise ValidationError("Authorization header required")

            # 验证 token
            current_user = self.auth_manager.get_user_from_token(token)
            if not current_user:
                raise AuthenticationError("Invalid or expired token")

            # 检查权限（只有管理员可以列出所有用户）
            if "admin" not in current_user.permissions:
                raise AuthenticationError("Insufficient permissions")

            # 获取查询参数
            limit = int(request.query.get("limit", 100))
            offset = int(request.query.get("offset", 0))

            # 列出用户
            users = self.auth_manager.db.list_users(limit=limit, offset=offset)

            return web.json_response(
                {
                    "type": "users_list",
                    "users": [user.to_dict() for user in users],
                    "count": len(users),
                },
                status=200,
            )

        except ValidationError as e:
            return web.json_response(e.to_dict(), status=400)
        except AuthenticationError as e:
            return web.json_response(e.to_dict(), status=401)
        except Exception as e:
            self.logger.error("List users failed", error=str(e), exc_info=True)
            return web.json_response(
                exception_to_dict(e),
                status=500,
            )

    # ========================================================================
    # 密码重置
    # ========================================================================

    async def request_password_reset(self, request: web.Request) -> web.Response:
        """POST /api/users/password-reset/request  {"email": "..."}"""
        try:
            data = await request.json()
            email = data.get("email")
            if not email:
                raise ValidationError("Email is required")
            self.auth_manager.request_password_reset(email)
            # 无论邮箱是否存在都返回成功（防止枚举攻击）
            return web.json_response(
                {
                    "type": "password_reset_requested",
                    "message": "If the email exists, a reset link has been sent",
                },
                status=200,
            )
        except ValidationError as e:
            return web.json_response(e.to_dict(), status=400)
        except Exception as e:
            self.logger.error("Password reset request failed", error=str(e), exc_info=True)
            # 仍然返回成功（防止枚举）
            return web.json_response(
                {
                    "type": "password_reset_requested",
                    "message": "If the email exists, a reset link has been sent",
                },
                status=200,
            )

    async def confirm_password_reset(self, request: web.Request) -> web.Response:
        """POST /api/users/password-reset/confirm  {"token": "...", "new_password": "..."}"""
        try:
            data = await request.json()
            token = data.get("token")
            new_password = data.get("new_password")
            if not token or not new_password:
                raise ValidationError("Token and new_password are required")
            if len(new_password) < 8:
                raise ValidationError("Password must be at least 8 characters")
            success = self.auth_manager.confirm_password_reset(token, new_password)
            if success:
                return web.json_response(
                    {"type": "password_reset_confirmed", "message": "Password has been reset"},
                    status=200,
                )
            return web.json_response(
                {"type": "error", "message": "Invalid or expired reset token", "code": 400},
                status=400,
            )
        except ValidationError as e:
            return web.json_response(e.to_dict(), status=400)
        except Exception as e:
            self.logger.error("Password reset confirm failed", error=str(e), exc_info=True)
            return web.json_response(exception_to_dict(e), status=500)

    async def change_password(self, request: web.Request) -> web.Response:
        """POST /api/users/password/change  {"current_password": "...", "new_password": "..."}"""
        try:
            token = request.headers.get("Authorization", "").replace("Bearer ", "")
            if not token:
                raise ValidationError("Authorization header required")
            user = self.auth_manager.get_user_from_token(token)
            if not user:
                raise AuthenticationError("Invalid or expired token")
            data = await request.json()
            current_password = data.get("current_password")
            new_password = data.get("new_password")
            if not current_password or not new_password:
                raise ValidationError("current_password and new_password are required")
            if len(new_password) < 8:
                raise ValidationError("Password must be at least 8 characters")
            success = self.auth_manager.change_password(
                user.user_id, current_password, new_password
            )
            if success:
                return web.json_response(
                    {"type": "password_changed", "message": "Password changed successfully"},
                    status=200,
                )
            return web.json_response(
                {"type": "error", "message": "Current password is incorrect", "code": 401},
                status=401,
            )
        except ValidationError as e:
            return web.json_response(e.to_dict(), status=400)
        except AuthenticationError as e:
            return web.json_response(e.to_dict(), status=401)
        except Exception as e:
            self.logger.error("Password change failed", error=str(e), exc_info=True)
            return web.json_response(exception_to_dict(e), status=500)

    # ========================================================================
    # 双因素认证 (2FA)
    # ========================================================================

    async def setup_2fa(self, request: web.Request) -> web.Response:
        """POST /api/users/2fa/setup — 初始化 2FA"""
        try:
            token = request.headers.get("Authorization", "").replace("Bearer ", "")
            if not token:
                raise ValidationError("Authorization header required")
            user = self.auth_manager.get_user_from_token(token)
            if not user:
                raise AuthenticationError("Invalid or expired token")
            result = self.auth_manager.setup_2fa(user.user_id)
            return web.json_response({"type": "2fa_setup", **result}, status=200)
        except ValidationError as e:
            return web.json_response(e.to_dict(), status=400)
        except AuthenticationError as e:
            return web.json_response(e.to_dict(), status=401)
        except Exception as e:
            self.logger.error("2FA setup failed", error=str(e), exc_info=True)
            return web.json_response(exception_to_dict(e), status=500)

    async def enable_2fa(self, request: web.Request) -> web.Response:
        """POST /api/users/2fa/enable  {"code": "123456"}"""
        try:
            token = request.headers.get("Authorization", "").replace("Bearer ", "")
            if not token:
                raise ValidationError("Authorization header required")
            user = self.auth_manager.get_user_from_token(token)
            if not user:
                raise AuthenticationError("Invalid or expired token")
            data = await request.json()
            code = data.get("code")
            if not code:
                raise ValidationError("TOTP code is required")
            success = self.auth_manager.enable_2fa(user.user_id, code)
            if success:
                return web.json_response(
                    {"type": "2fa_enabled", "message": "2FA has been enabled"}, status=200
                )
            return web.json_response(
                {"type": "error", "message": "Invalid TOTP code", "code": 400}, status=400
            )
        except ValidationError as e:
            return web.json_response(e.to_dict(), status=400)
        except AuthenticationError as e:
            return web.json_response(e.to_dict(), status=401)
        except Exception as e:
            self.logger.error("2FA enable failed", error=str(e), exc_info=True)
            return web.json_response(exception_to_dict(e), status=500)

    async def verify_2fa(self, request: web.Request) -> web.Response:
        """POST /api/users/2fa/verify  {"code": "123456"}"""
        try:
            token = request.headers.get("Authorization", "").replace("Bearer ", "")
            if not token:
                raise ValidationError("Authorization header required")
            user = self.auth_manager.get_user_from_token(token)
            if not user:
                raise AuthenticationError("Invalid or expired token")
            data = await request.json()
            code = data.get("code")
            if not code:
                raise ValidationError("TOTP code is required")
            success = self.auth_manager.verify_2fa(user.user_id, code)
            if success:
                return web.json_response(
                    {"type": "2fa_verified", "message": "2FA verification successful"}, status=200
                )
            return web.json_response(
                {"type": "error", "message": "Invalid TOTP code", "code": 401}, status=401
            )
        except ValidationError as e:
            return web.json_response(e.to_dict(), status=400)
        except AuthenticationError as e:
            return web.json_response(e.to_dict(), status=401)
        except Exception as e:
            self.logger.error("2FA verify failed", error=str(e), exc_info=True)
            return web.json_response(exception_to_dict(e), status=500)

    async def disable_2fa(self, request: web.Request) -> web.Response:
        """POST /api/users/2fa/disable  {"code": "123456"}"""
        try:
            token = request.headers.get("Authorization", "").replace("Bearer ", "")
            if not token:
                raise ValidationError("Authorization header required")
            user = self.auth_manager.get_user_from_token(token)
            if not user:
                raise AuthenticationError("Invalid or expired token")
            data = await request.json()
            code = data.get("code")
            if not code:
                raise ValidationError("TOTP code or backup code is required")
            success = self.auth_manager.disable_2fa(user.user_id, code)
            if success:
                return web.json_response(
                    {"type": "2fa_disabled", "message": "2FA has been disabled"}, status=200
                )
            return web.json_response(
                {"type": "error", "message": "Invalid code", "code": 401}, status=401
            )
        except ValidationError as e:
            return web.json_response(e.to_dict(), status=400)
        except AuthenticationError as e:
            return web.json_response(e.to_dict(), status=401)
        except Exception as e:
            self.logger.error("2FA disable failed", error=str(e), exc_info=True)
            return web.json_response(exception_to_dict(e), status=500)

    async def regenerate_backup_codes(self, request: web.Request) -> web.Response:
        """POST /api/users/2fa/backup-codes  {"code": "123456"}"""
        try:
            token = request.headers.get("Authorization", "").replace("Bearer ", "")
            if not token:
                raise ValidationError("Authorization header required")
            user = self.auth_manager.get_user_from_token(token)
            if not user:
                raise AuthenticationError("Invalid or expired token")
            data = await request.json()
            code = data.get("code")
            if not code:
                raise ValidationError("TOTP code is required")
            new_codes = self.auth_manager.regenerate_backup_codes(user.user_id, code)
            if new_codes is not None:
                return web.json_response(
                    {"type": "backup_codes_regenerated", "backup_codes": new_codes}, status=200
                )
            return web.json_response(
                {"type": "error", "message": "Invalid code", "code": 401}, status=401
            )
        except ValidationError as e:
            return web.json_response(e.to_dict(), status=400)
        except AuthenticationError as e:
            return web.json_response(e.to_dict(), status=401)
        except Exception as e:
            self.logger.error("Backup code regeneration failed", error=str(e), exc_info=True)
            return web.json_response(exception_to_dict(e), status=500)

    # ========================================================================
    # 团队协作端点
    # ========================================================================

    async def _get_auth_user_id(self, request: web.Request) -> str:
        """从请求中提取并验证用户ID"""
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            raise ValidationError("Authorization header required")
        user = self.auth_manager.get_user_from_token(token)
        if not user:
            raise AuthenticationError("Invalid or expired token")
        return user.user_id

    async def create_team(self, request: web.Request) -> web.Response:
        """POST /api/teams"""
        try:
            user_id = await self._get_auth_user_id(request)
            data = await request.json()
            name = data.get("name", "").strip()
            description = data.get("description")
            if not name:
                raise ValidationError("团队名称不能为空")
            team = self.team_manager.create_team(name, user_id, description)
            return web.json_response({"type": "team_created", "team": team.to_dict()}, status=201)
        except (ValidationError, ValueError) as e:
            return web.json_response(exception_to_dict(e), status=400)
        except AuthenticationError as e:
            return web.json_response(exception_to_dict(e), status=401)
        except Exception as e:
            self.logger.error("Create team failed", error=str(e), exc_info=True)
            return web.json_response(exception_to_dict(e), status=500)

    async def list_teams(self, request: web.Request) -> web.Response:
        """GET /api/teams"""
        try:
            user_id = await self._get_auth_user_id(request)
            teams = self.team_manager.list_user_teams(user_id)
            return web.json_response(
                {"type": "teams_list", "teams": [t.to_dict() for t in teams], "count": len(teams)}
            )
        except AuthenticationError as e:
            return web.json_response(exception_to_dict(e), status=401)
        except Exception as e:
            self.logger.error("List teams failed", error=str(e), exc_info=True)
            return web.json_response(exception_to_dict(e), status=500)

    async def get_team(self, request: web.Request) -> web.Response:
        """GET /api/teams/{team_id}"""
        try:
            user_id = await self._get_auth_user_id(request)
            team_id = request.match_info["team_id"]
            team = self.team_manager.get_team(team_id, user_id)
            if not team:
                return web.json_response(
                    {"type": "error", "message": "团队不存在或无权访问"}, status=404
                )
            members = self.team_manager.get_team_members(team_id, user_id)
            return web.json_response(
                {
                    "type": "team_info",
                    "team": team.to_dict(),
                    "members": [m.to_dict() for m in members],
                }
            )
        except (AuthenticationError,) as e:
            return web.json_response(exception_to_dict(e), status=401)
        except PermissionError as e:
            return web.json_response({"type": "error", "message": str(e)}, status=403)
        except Exception as e:
            self.logger.error("Get team failed", error=str(e), exc_info=True)
            return web.json_response(exception_to_dict(e), status=500)

    async def update_team(self, request: web.Request) -> web.Response:
        """PUT /api/teams/{team_id}"""
        try:
            user_id = await self._get_auth_user_id(request)
            team_id = request.match_info["team_id"]
            data = await request.json()
            # Whitelist allowed fields to prevent mass assignment
            allowed_fields = {"name", "description"}
            safe_data = {k: v for k, v in data.items() if k in allowed_fields}
            team = self.team_manager.update_team(team_id, user_id, **safe_data)
            return web.json_response({"type": "team_updated", "team": team.to_dict()})
        except PermissionError as e:
            return web.json_response({"type": "error", "message": str(e)}, status=403)
        except (ValidationError, ValueError) as e:
            return web.json_response(exception_to_dict(e), status=400)
        except AuthenticationError as e:
            return web.json_response(exception_to_dict(e), status=401)
        except Exception as e:
            self.logger.error("Update team failed", error=str(e), exc_info=True)
            return web.json_response(exception_to_dict(e), status=500)

    async def delete_team(self, request: web.Request) -> web.Response:
        """DELETE /api/teams/{team_id}"""
        try:
            user_id = await self._get_auth_user_id(request)
            team_id = request.match_info["team_id"]
            self.team_manager.delete_team(team_id, user_id)
            return web.json_response({"type": "team_deleted", "team_id": team_id})
        except PermissionError as e:
            return web.json_response({"type": "error", "message": str(e)}, status=403)
        except AuthenticationError as e:
            return web.json_response(exception_to_dict(e), status=401)
        except Exception as e:
            self.logger.error("Delete team failed", error=str(e), exc_info=True)
            return web.json_response(exception_to_dict(e), status=500)

    async def get_team_members(self, request: web.Request) -> web.Response:
        """GET /api/teams/{team_id}/members"""
        try:
            user_id = await self._get_auth_user_id(request)
            team_id = request.match_info["team_id"]
            members = self.team_manager.get_team_members(team_id, user_id)
            return web.json_response(
                {
                    "type": "team_members",
                    "members": [m.to_dict() for m in members],
                    "count": len(members),
                }
            )
        except PermissionError as e:
            return web.json_response({"type": "error", "message": str(e)}, status=403)
        except AuthenticationError as e:
            return web.json_response(exception_to_dict(e), status=401)
        except Exception as e:
            self.logger.error("Get team members failed", error=str(e), exc_info=True)
            return web.json_response(exception_to_dict(e), status=500)

    async def update_member_role(self, request: web.Request) -> web.Response:
        """PUT /api/teams/{team_id}/members/{target_id}"""
        try:
            user_id = await self._get_auth_user_id(request)
            team_id = request.match_info["team_id"]
            target_id = request.match_info["target_id"]
            data = await request.json()
            role_str = data.get("role", "")
            try:
                new_role = TeamRole(role_str)
            except ValueError:
                raise ValidationError(f"无效的角色: {role_str}")
            self.team_manager.update_member_role(team_id, user_id, target_id, new_role)
            return web.json_response(
                {
                    "type": "member_role_updated",
                    "team_id": team_id,
                    "user_id": target_id,
                    "role": role_str,
                }
            )
        except PermissionError as e:
            return web.json_response({"type": "error", "message": str(e)}, status=403)
        except (ValidationError, ValueError) as e:
            return web.json_response(exception_to_dict(e), status=400)
        except AuthenticationError as e:
            return web.json_response(exception_to_dict(e), status=401)
        except Exception as e:
            self.logger.error("Update member role failed", error=str(e), exc_info=True)
            return web.json_response(exception_to_dict(e), status=500)

    async def remove_member(self, request: web.Request) -> web.Response:
        """DELETE /api/teams/{team_id}/members/{target_id}"""
        try:
            user_id = await self._get_auth_user_id(request)
            team_id = request.match_info["team_id"]
            target_id = request.match_info["target_id"]
            self.team_manager.remove_member(team_id, user_id, target_id)
            return web.json_response(
                {"type": "member_removed", "team_id": team_id, "user_id": target_id}
            )
        except PermissionError as e:
            return web.json_response({"type": "error", "message": str(e)}, status=403)
        except (ValidationError, ValueError) as e:
            return web.json_response({"type": "error", "message": str(e)}, status=400)
        except AuthenticationError as e:
            return web.json_response(exception_to_dict(e), status=401)
        except Exception as e:
            self.logger.error("Remove member failed", error=str(e), exc_info=True)
            return web.json_response(exception_to_dict(e), status=500)

    async def leave_team(self, request: web.Request) -> web.Response:
        """POST /api/teams/{team_id}/leave"""
        try:
            user_id = await self._get_auth_user_id(request)
            team_id = request.match_info["team_id"]
            self.team_manager.leave_team(team_id, user_id)
            return web.json_response({"type": "left_team", "team_id": team_id})
        except (ValidationError, ValueError) as e:
            return web.json_response({"type": "error", "message": str(e)}, status=400)
        except AuthenticationError as e:
            return web.json_response(exception_to_dict(e), status=401)
        except Exception as e:
            self.logger.error("Leave team failed", error=str(e), exc_info=True)
            return web.json_response(exception_to_dict(e), status=500)

    async def create_invite(self, request: web.Request) -> web.Response:
        """POST /api/teams/{team_id}/invites"""
        try:
            user_id = await self._get_auth_user_id(request)
            team_id = request.match_info["team_id"]
            data = await request.json()
            email = data.get("email", "").strip()
            if not email:
                raise ValidationError("邮箱不能为空")
            hours = data.get("expires_hours", 72)
            invite = self.team_manager.create_invite(team_id, user_id, email, hours)
            return web.json_response(
                {"type": "invite_created", "invite": invite.to_dict()}, status=201
            )
        except PermissionError as e:
            return web.json_response({"type": "error", "message": str(e)}, status=403)
        except (ValidationError, ValueError) as e:
            return web.json_response(exception_to_dict(e), status=400)
        except AuthenticationError as e:
            return web.json_response(exception_to_dict(e), status=401)
        except Exception as e:
            self.logger.error("Create invite failed", error=str(e), exc_info=True)
            return web.json_response(exception_to_dict(e), status=500)

    async def list_invites(self, request: web.Request) -> web.Response:
        """GET /api/teams/{team_id}/invites"""
        try:
            user_id = await self._get_auth_user_id(request)
            team_id = request.match_info["team_id"]
            invites = self.team_manager.list_team_invites(team_id, user_id)
            return web.json_response(
                {
                    "type": "invites_list",
                    "invites": [i.to_dict() for i in invites],
                    "count": len(invites),
                }
            )
        except PermissionError as e:
            return web.json_response({"type": "error", "message": str(e)}, status=403)
        except AuthenticationError as e:
            return web.json_response(exception_to_dict(e), status=401)
        except Exception as e:
            self.logger.error("List invites failed", error=str(e), exc_info=True)
            return web.json_response(exception_to_dict(e), status=500)

    async def accept_invite(self, request: web.Request) -> web.Response:
        """POST /api/teams/invites/{token}/accept"""
        try:
            user_id = await self._get_auth_user_id(request)
            token = request.match_info["token"]
            invite = self.team_manager.accept_invite(token, user_id)
            return web.json_response({"type": "invite_accepted", "team_id": invite.team_id})
        except (ValidationError, ValueError) as e:
            return web.json_response({"type": "error", "message": str(e)}, status=400)
        except AuthenticationError as e:
            return web.json_response(exception_to_dict(e), status=401)
        except Exception as e:
            self.logger.error("Accept invite failed", error=str(e), exc_info=True)
            return web.json_response(exception_to_dict(e), status=500)

    async def share_session(self, request: web.Request) -> web.Response:
        """POST /api/teams/{team_id}/sessions/share"""
        try:
            user_id = await self._get_auth_user_id(request)
            team_id = request.match_info["team_id"]
            data = await request.json()
            session_id = data.get("session_id", "").strip()
            if not session_id:
                raise ValidationError("session_id 不能为空")
            title = data.get("title")
            shared = self.team_manager.share_session(session_id, team_id, user_id, title)
            return web.json_response(
                {"type": "session_shared", "share": shared.to_dict()}, status=201
            )
        except PermissionError as e:
            return web.json_response({"type": "error", "message": str(e)}, status=403)
        except (ValidationError, ValueError) as e:
            return web.json_response(exception_to_dict(e), status=400)
        except AuthenticationError as e:
            return web.json_response(exception_to_dict(e), status=401)
        except Exception as e:
            self.logger.error("Share session failed", error=str(e), exc_info=True)
            return web.json_response(exception_to_dict(e), status=500)

    async def unshare_session(self, request: web.Request) -> web.Response:
        """DELETE /api/teams/sessions/{share_id}"""
        try:
            user_id = await self._get_auth_user_id(request)
            share_id = request.match_info["share_id"]
            data = await request.json()
            team_id = data.get("team_id", "")
            if not team_id:
                raise ValidationError("team_id required")
            self.team_manager.unshare_session(share_id, team_id, user_id)
            return web.json_response({"type": "session_unshared", "share_id": share_id})
        except PermissionError as e:
            return web.json_response({"type": "error", "message": str(e)}, status=403)
        except (ValidationError, ValueError) as e:
            return web.json_response(exception_to_dict(e), status=400)
        except AuthenticationError as e:
            return web.json_response(exception_to_dict(e), status=401)
        except Exception as e:
            self.logger.error("Unshare session failed", error=str(e), exc_info=True)
            return web.json_response(exception_to_dict(e), status=500)

    async def get_team_sessions(self, request: web.Request) -> web.Response:
        """GET /api/teams/{team_id}/sessions"""
        try:
            user_id = await self._get_auth_user_id(request)
            team_id = request.match_info["team_id"]
            sessions = self.team_manager.get_team_sessions(team_id, user_id)
            return web.json_response(
                {
                    "type": "team_sessions",
                    "sessions": [s.to_dict() for s in sessions],
                    "count": len(sessions),
                }
            )
        except PermissionError as e:
            return web.json_response({"type": "error", "message": str(e)}, status=403)
        except AuthenticationError as e:
            return web.json_response(exception_to_dict(e), status=401)
        except Exception as e:
            self.logger.error("Get team sessions failed", error=str(e), exc_info=True)
            return web.json_response(exception_to_dict(e), status=500)

    # ========================================================================
    # 插件管理端点
    # ========================================================================

    async def list_plugins(self, request: web.Request) -> web.Response:
        """GET /api/plugins"""
        try:
            await self._get_auth_user_id(request)
            plugins = self.plugin_manager.list_plugins()
            return web.json_response(
                {
                    "type": "plugins_list",
                    "plugins": [p.to_dict() for p in plugins],
                    "count": len(plugins),
                }
            )
        except AuthenticationError as e:
            return web.json_response(exception_to_dict(e), status=401)
        except Exception as e:
            self.logger.error("List plugins failed", error=str(e), exc_info=True)
            return web.json_response(exception_to_dict(e), status=500)

    async def get_plugin(self, request: web.Request) -> web.Response:
        """GET /api/plugins/{plugin_id}"""
        try:
            await self._get_auth_user_id(request)
            plugin_id = request.match_info["plugin_id"]
            info = self.plugin_manager.get_plugin_info(plugin_id)
            if not info:
                return web.json_response(
                    {"type": "error", "message": "Plugin not found"}, status=404
                )
            return web.json_response({"type": "plugin_info", "plugin": info.to_dict()})
        except AuthenticationError as e:
            return web.json_response(exception_to_dict(e), status=401)
        except Exception as e:
            self.logger.error("Get plugin failed", error=str(e), exc_info=True)
            return web.json_response(exception_to_dict(e), status=500)

    async def enable_plugin(self, request: web.Request) -> web.Response:
        """POST /api/plugins/{plugin_id}/enable"""
        try:
            await self._get_auth_user_id(request)
            plugin_id = request.match_info["plugin_id"]
            success = self.plugin_manager.enable_plugin(plugin_id)
            if success:
                return web.json_response({"type": "plugin_enabled", "plugin_id": plugin_id})
            return web.json_response({"type": "error", "message": "Plugin not found"}, status=404)
        except AuthenticationError as e:
            return web.json_response(exception_to_dict(e), status=401)
        except Exception as e:
            self.logger.error("Enable plugin failed", error=str(e), exc_info=True)
            return web.json_response(exception_to_dict(e), status=500)

    async def disable_plugin(self, request: web.Request) -> web.Response:
        """POST /api/plugins/{plugin_id}/disable"""
        try:
            await self._get_auth_user_id(request)
            plugin_id = request.match_info["plugin_id"]
            success = self.plugin_manager.disable_plugin(plugin_id)
            if success:
                return web.json_response({"type": "plugin_disabled", "plugin_id": plugin_id})
            return web.json_response({"type": "error", "message": "Plugin not found"}, status=404)
        except AuthenticationError as e:
            return web.json_response(exception_to_dict(e), status=401)
        except Exception as e:
            self.logger.error("Disable plugin failed", error=str(e), exc_info=True)
            return web.json_response(exception_to_dict(e), status=500)

    async def reload_plugin(self, request: web.Request) -> web.Response:
        """POST /api/plugins/{plugin_id}/reload"""
        try:
            await self._get_auth_user_id(request)
            plugin_id = request.match_info["plugin_id"]
            self.plugin_manager.unload_plugin(plugin_id)
            info = self.plugin_manager.load_plugin(plugin_id)
            if info:
                return web.json_response({"type": "plugin_reloaded", "plugin": info.to_dict()})
            return web.json_response(
                {"type": "error", "message": "Failed to reload plugin"}, status=500
            )
        except AuthenticationError as e:
            return web.json_response(exception_to_dict(e), status=401)
        except Exception as e:
            self.logger.error("Reload plugin failed", error=str(e), exc_info=True)
            return web.json_response(exception_to_dict(e), status=500)

    async def configure_plugin(self, request: web.Request) -> web.Response:
        """POST /api/plugins/{plugin_id}/config"""
        try:
            await self._get_auth_user_id(request)
            plugin_id = request.match_info["plugin_id"]
            data = await request.json()
            plugin = self.plugin_manager.get_plugin(plugin_id)
            if not plugin:
                return web.json_response(
                    {"type": "error", "message": "Plugin not found"}, status=404
                )
            plugin.set_config(data)
            return web.json_response({"type": "plugin_configured", "plugin_id": plugin_id})
        except AuthenticationError as e:
            return web.json_response(exception_to_dict(e), status=401)
        except Exception as e:
            self.logger.error("Configure plugin failed", error=str(e), exc_info=True)
            return web.json_response(exception_to_dict(e), status=500)

    async def get_plugin_commands(self, request: web.Request) -> web.Response:
        """GET /api/plugins/{plugin_id}/commands"""
        try:
            await self._get_auth_user_id(request)
            plugin_id = request.match_info["plugin_id"]
            plugin = self.plugin_manager.get_plugin(plugin_id)
            if not plugin:
                return web.json_response(
                    {"type": "error", "message": "Plugin not found"}, status=404
                )
            commands = plugin.get_commands()
            return web.json_response(
                {
                    "type": "plugin_commands",
                    "plugin_id": plugin_id,
                    "commands": list(commands.keys()),
                    "count": len(commands),
                }
            )
        except AuthenticationError as e:
            return web.json_response(exception_to_dict(e), status=401)
        except Exception as e:
            self.logger.error("Get plugin commands failed", error=str(e), exc_info=True)
            return web.json_response(exception_to_dict(e), status=500)

    async def discover_plugins(self, request: web.Request) -> web.Response:
        """POST /api/plugins/discover"""
        try:
            await self._get_auth_user_id(request)
            discovered = self.plugin_manager.discover_plugins()
            return web.json_response(
                {
                    "type": "plugins_discovered",
                    "plugin_ids": discovered,
                    "count": len(discovered),
                }
            )
        except AuthenticationError as e:
            return web.json_response(exception_to_dict(e), status=401)
        except Exception as e:
            self.logger.error("Discover plugins failed", error=str(e), exc_info=True)
            return web.json_response(exception_to_dict(e), status=500)

    # ========================================================================
    # 健康检查
    # ========================================================================

    async def health_check(self, request: web.Request) -> web.Response:
        """
        增强版健康检查端点

        GET /health
        GET /health?verbose=1  (含提示信息)
        """
        import os as _os
        import shutil as _shutil

        checks = {}
        hints = {}

        # 数据库
        try:
            db_result = self.auth_manager.db.health_check()
            checks["database"] = db_result
            if not db_result.get("ok"):
                hints["database"] = "数据库连接失败，请检查文件权限和磁盘空间"
        except Exception as e:
            checks["database"] = {"ok": False, "error": str(e)}
            hints["database"] = "数据库异常，请查看日志"

        # 插件
        try:
            plugins = self.plugin_manager.list_plugins()
            enabled = [p for p in plugins if p.state.value == "enabled"]
            errored = [p for p in plugins if p.state.value == "error"]
            checks["plugins"] = {
                "ok": len(errored) == 0,
                "total": len(plugins),
                "enabled": len(enabled),
                "errors": len(errored),
                "error_ids": [p.plugin_id for p in errored],
            }
            if errored:
                hints["plugins"] = (
                    f"插件加载失败: {', '.join(p.plugin_id for p in errored)}。"
                    "查看日志了解详情，或调用 POST /api/plugins/{id}/reload 重试"
                )
        except Exception as e:
            checks["plugins"] = {"ok": False, "error": str(e)}

        # 磁盘空间
        try:
            disk_usage = _shutil.disk_usage("/")
            free_pct = disk_usage.free / disk_usage.total * 100
            checks["disk"] = {
                "ok": free_pct > 10,
                "free_gb": round(disk_usage.free / (1024**3), 1),
                "total_gb": round(disk_usage.total / (1024**3), 1),
                "free_percent": round(free_pct, 1),
            }
            if free_pct <= 10:
                hints["disk"] = f"磁盘空间不足 ({free_pct:.0f}% 可用)，" "可能导致数据库写入失败"
        except Exception:
            pass

        # 认证系统
        try:
            checks["auth"] = {
                "ok": True,
                "enabled": self.auth_manager is not None,
            }
        except Exception as e:
            checks["auth"] = {"ok": False, "error": str(e)}

        # OAuth2
        try:
            providers = oauth2_manager.list_providers()
            checks["oauth2"] = {
                "ok": True,
                "providers": providers,
                "configured": len(providers) > 0,
            }
        except Exception:
            checks["oauth2"] = {"ok": True, "configured": False}

        # 判断整体状态
        all_ok = all(v.get("ok", True) for v in checks.values())
        overall = "healthy" if all_ok else "degraded"

        # 读取版本
        version = "unknown"
        try:
            version_path = _os.path.join(
                _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                "VERSION",
            )
            with open(version_path) as f:
                version = f.read().strip()
        except Exception:
            pass

        body = {
            "status": overall,
            "timestamp": datetime.now().isoformat(),
            "service": "zhineng-bridge",
            "version": version,
            "checks": checks,
        }

        verbose = request.query.get("verbose", "")
        if verbose or not all_ok:
            body["hints"] = hints

        status = 200 if all_ok else 503
        return web.json_response(body, status=status)


# ============================================================================
# 导出
# ============================================================================

__all__ = ["HTTPServer"]

#!/usr/bin/env python3
"""
OAuth2 认证提供商集成

支持:
- GitHub OAuth2
- Google OAuth2
"""

import secrets
from dataclasses import dataclass
from typing import Dict, List, Optional

import httpx
from logger import get_logger
from user_auth import User, UserRole

from config import settings


@dataclass
class OAuth2Provider:
    """OAuth2 提供商配置"""

    name: str
    auth_url: str
    token_url: str
    user_info_url: str
    client_id: str
    client_secret: str
    scopes: List[str]


@dataclass
class OAuth2UserInfo:
    """OAuth2 用户信息"""

    provider: str
    user_id: str
    username: str
    email: Optional[str] = None
    name: Optional[str] = None
    avatar_url: Optional[str] = None


class GitHubOAuth2:
    """GitHub OAuth2 提供商"""

    def __init__(self, client_id: str, client_secret: str):
        """
        初始化 GitHub OAuth2

        Args:
            client_id: GitHub OAuth App Client ID
            client_secret: GitHub OAuth App Client Secret
        """
        self.logger = get_logger(__name__)
        self.provider = OAuth2Provider(
            name="github",
            auth_url="https://github.com/login/oauth/authorize",
            token_url="https://github.com/login/oauth/access_token",
            user_info_url="https://api.github.com/user",
            client_id=client_id,
            client_secret=client_secret,
            scopes=["read:user", "user:email"],
        )

    def get_authorization_url(self, redirect_uri: str, state: str = None) -> str:
        """
        获取授权 URL

        Args:
            redirect_uri: 回调 URL
            state: 状态参数（CSRF 保护）

        Returns:
            授权 URL
        """
        import urllib.parse

        params = {
            "client_id": self.provider.client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(self.provider.scopes),
            "response_type": "code",
        }

        if state:
            params["state"] = state

        return f"{self.provider.auth_url}?{urllib.parse.urlencode(params)}"

    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> Dict:
        """
        用授权码换取 access token

        Args:
            code: 授权码
            redirect_uri: 回调 URL

        Returns:
            Token 信息

        Raises:
            Exception: 如果交换失败
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.provider.token_url,
                data={
                    "client_id": self.provider.client_id,
                    "client_secret": self.provider.client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
                headers={"Accept": "application/json"},
            )

            if response.status_code != 200:
                self.logger.error(
                    "Failed to exchange code for token",
                    status=response.status_code,
                    error=response.text,
                )
                raise Exception(f"Failed to exchange code for token: {response.status_code}")

            token_data = response.json()
            self.logger.info("Token exchanged successfully")

            return token_data

    async def get_user_info(self, access_token: str) -> OAuth2UserInfo:
        """
        获取用户信息

        Args:
            access_token: Access token

        Returns:
            用户信息

        Raises:
            Exception: 如果获取失败
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.provider.user_info_url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
            )

            if response.status_code != 200:
                self.logger.error(
                    "Failed to get user info",
                    status=response.status_code,
                    error=response.text,
                )
                raise Exception(f"Failed to get user info: {response.status_code}")

            user_data = response.json()

            return OAuth2UserInfo(
                provider="github",
                user_id=str(user_data["id"]),
                username=user_data["login"],
                email=user_data.get("email"),
                name=user_data.get("name"),
                avatar_url=user_data.get("avatar_url"),
            )


class GoogleOAuth2:
    """Google OAuth2 提供商"""

    def __init__(self, client_id: str, client_secret: str):
        """
        初始化 Google OAuth2

        Args:
            client_id: Google OAuth Client ID
            client_secret: Google OAuth Client Secret
        """
        self.logger = get_logger(__name__)
        self.provider = OAuth2Provider(
            name="google",
            auth_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            user_info_url="https://www.googleapis.com/oauth2/v2/userinfo",
            client_id=client_id,
            client_secret=client_secret,
            scopes=["openid", "email", "profile"],
        )

    def get_authorization_url(self, redirect_uri: str, state: str = None) -> str:
        """
        获取授权 URL

        Args:
            redirect_uri: 回调 URL
            state: 状态参数（CSRF 保护）

        Returns:
            授权 URL
        """
        import urllib.parse

        params = {
            "client_id": self.provider.client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(self.provider.scopes),
            "response_type": "code",
            "access_type": "offline",
        }

        if state:
            params["state"] = state

        return f"{self.provider.auth_url}?{urllib.parse.urlencode(params)}"

    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> Dict:
        """
        用授权码换取 access token

        Args:
            code: 授权码
            redirect_uri: 回调 URL

        Returns:
            Token 信息

        Raises:
            Exception: 如果交换失败
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.provider.token_url,
                data={
                    "client_id": self.provider.client_id,
                    "client_secret": self.provider.client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
                headers={"Accept": "application/json"},
            )

            if response.status_code != 200:
                self.logger.error(
                    "Failed to exchange code for token",
                    status=response.status_code,
                    error=response.text,
                )
                raise Exception(f"Failed to exchange code for token: {response.status_code}")

            token_data = response.json()
            self.logger.info("Token exchanged successfully")

            return token_data

    async def get_user_info(self, access_token: str) -> OAuth2UserInfo:
        """
        获取用户信息

        Args:
            access_token: Access token

        Returns:
            用户信息

        Raises:
            Exception: 如果获取失败
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.provider.user_info_url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
            )

            if response.status_code != 200:
                self.logger.error(
                    "Failed to get user info",
                    status=response.status_code,
                    error=response.text,
                )
                raise Exception(f"Failed to get user info: {response.status_code}")

            user_data = response.json()

            return OAuth2UserInfo(
                provider="google",
                user_id=user_data["id"],
                email=user_data["email"],
                name=user_data.get("name"),
                username=user_data["email"].split("@")[0] if user_data.get("email") else None,
                avatar_url=user_data.get("picture"),
            )


class OAuth2Manager:
    """OAuth2 管理器"""

    def __init__(self):
        """初始化 OAuth2 管理器"""
        self.logger = get_logger(__name__)
        self.providers: Dict[str, object] = {}
        self._pending_states: Dict[str, float] = {}
        self._init_providers()

    def _init_providers(self):
        """初始化 OAuth2 提供商"""
        # GitHub OAuth2
        github_client_id = getattr(settings, "GITHUB_OAUTH_CLIENT_ID", None)
        github_client_secret = getattr(settings, "GITHUB_OAUTH_CLIENT_SECRET", None)

        if github_client_id and github_client_secret:
            self.providers["github"] = GitHubOAuth2(github_client_id, github_client_secret)
            self.logger.info("GitHub OAuth2 provider initialized")

        # Google OAuth2
        google_client_id = getattr(settings, "GOOGLE_OAUTH_CLIENT_ID", None)
        google_client_secret = getattr(settings, "GOOGLE_OAUTH_CLIENT_SECRET", None)

        if google_client_id and google_client_secret:
            self.providers["google"] = GoogleOAuth2(google_client_id, google_client_secret)
            self.logger.info("Google OAuth2 provider initialized")

        if not self.providers:
            self.logger.warning("No OAuth2 providers configured")

    def get_provider(self, provider_name: str) -> Optional[object]:
        """
        获取 OAuth2 提供商

        Args:
            provider_name: 提供商名称 (github, google)

        Returns:
            OAuth2 提供商实例或 None
        """
        return self.providers.get(provider_name)

    def list_providers(self) -> List[str]:
        """
        列出可用的 OAuth2 提供商

        Returns:
            提供商名称列表
        """
        return list(self.providers.keys())

    def generate_state(self, provider_name: str) -> str:
        """
        生成 OAuth2 state 参数并记录

        Args:
            provider_name: 提供商名称

        Returns:
            state 字符串
        """
        import time

        state = secrets.token_urlsafe(32)
        self._pending_states[state] = time.time()
        # 清理超过10分钟的pending states
        now = time.time()
        expired = [s for s, t in self._pending_states.items() if now - t > 600]
        for s in expired:
            del self._pending_states[s]
        return state

    async def handle_oauth2_callback(
        self,
        provider_name: str,
        code: str,
        redirect_uri: str,
        auth_manager,
        state: str = None,
    ) -> User:
        """
        处理 OAuth2 回调

        Args:
            provider_name: 提供商名称
            code: 授权码
            redirect_uri: 回调 URL
            auth_manager: 认证管理器
            state: CSRF state 参数

        Returns:
            用户对象

        Raises:
            Exception: 如果处理失败
        """
        provider = self.get_provider(provider_name)
        if not provider:
            raise Exception(f"OAuth2 provider '{provider_name}' not found")

        # 验证 state 参数（CSRF 保护）
        if state:
            if state not in self._pending_states:
                raise Exception("Invalid OAuth2 state parameter - possible CSRF attack")
            del self._pending_states[state]
        else:
            raise Exception("Missing OAuth2 state parameter")

        # 交换授权码换取 access token
        token_data = await provider.exchange_code_for_token(code, redirect_uri)

        # 获取用户信息
        user_info = await provider.get_user_info(token_data["access_token"])

        # 检查用户是否已存在（通过 OAuth provider + ID）
        existing_user = auth_manager.db.get_user_by_oauth(
            provider=user_info.provider,
            oauth_id=user_info.user_id,
        )

        if existing_user:
            return existing_user

        # 创建新用户
        try:
            new_user = auth_manager.db.create_user(
                username=user_info.username,
                email=user_info.email,
                role=UserRole.USER,
                permissions=["read", "write"],
            )

            # 更新 OAuth 信息
            auth_manager.db.update_user(
                new_user.user_id,
                oauth_provider=user_info.provider,
                oauth_id=user_info.user_id,
            )

            self.logger.info(
                "User created via OAuth2",
                user_id=new_user.user_id,
                provider=user_info.provider,
            )

            return new_user

        except ValueError:
            # 用户名已存在，生成唯一用户名
            unique_username = f"{user_info.username}_{user_info.user_id[:8]}"
            new_user = auth_manager.db.create_user(
                username=unique_username,
                email=user_info.email,
                role=UserRole.USER,
                permissions=["read", "write"],
            )

            auth_manager.db.update_user(
                new_user.user_id,
                oauth_provider=user_info.provider,
                oauth_id=user_info.user_id,
            )

            self.logger.info(
                "User created via OAuth2 (with unique username)",
                user_id=new_user.user_id,
                provider=user_info.provider,
            )

            return new_user


# ============================================================================
# 全局 OAuth2 管理器实例
# ============================================================================

oauth2_manager = OAuth2Manager()


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    "OAuth2Provider",
    "OAuth2UserInfo",
    "GitHubOAuth2",
    "GoogleOAuth2",
    "OAuth2Manager",
    "oauth2_manager",
]

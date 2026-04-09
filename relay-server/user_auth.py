#!/usr/bin/env python3
"""
用户认证和授权系统

支持:
- 用户注册和登录
- JWT Token 认证
- OAuth2 (GitHub, Google)
- 权限管理
- 密码重置
- 双因素认证 (TOTP)

此模块现在作为统一入口点，从拆分后的模块导入所有组件。
"""

# ============================================================================
# 从数据模型模块导入
# ============================================================================

from auth_db import (
    USER_CACHE_MAXSIZE,
    USER_CACHE_TTL,
    SQLiteConnectionPool,
    UserDatabase,
)
from auth_hash import (
    PBKDF2_ITERATIONS,
    PasswordHasher,
)
from auth_jwt import (
    JWTAuth,
)
from auth_manager import (
    TOKEN_CACHE_MAXSIZE,
    TOKEN_CACHE_TTL,
    AuthenticationManager,
)
from auth_models import (
    AuthType,
    OAuth2Token,
    Permission,
    TokenInfo,
    User,
    UserRole,
)

# ============================================================================
# 从密码哈希模块导入
# ============================================================================


# ============================================================================
# 从 JWT 认证模块导入
# ============================================================================


# ============================================================================
# 从数据库模块导入
# ============================================================================


# ============================================================================
# 从认证管理器模块导入
# ============================================================================


# ============================================================================
# 从密码重置模块导入
# ============================================================================

# Password reset is handled by AuthenticationManager in auth_manager
PasswordResetManager = AuthenticationManager

# ============================================================================
# 从 TOTP 双因素认证模块导入
# ============================================================================

from auth_totp import (
    TOTPAuth,
    TOTPManager,
)

# ============================================================================
# 全局认证管理器实例
# ============================================================================

auth_manager = AuthenticationManager()


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    # 数据模型
    "AuthType",
    "UserRole",
    "Permission",
    "User",
    "TokenInfo",
    "OAuth2Token",
    # 密码哈希
    "PasswordHasher",
    "PBKDF2_ITERATIONS",
    # JWT 认证
    "JWTAuth",
    # 数据库
    "SQLiteConnectionPool",
    "UserDatabase",
    "USER_CACHE_TTL",
    "USER_CACHE_MAXSIZE",
    # 认证管理器
    "AuthenticationManager",
    "TOKEN_CACHE_TTL",
    "TOKEN_CACHE_MAXSIZE",
    # 密码重置
    "PasswordResetManager",
    # 双因素认证
    "TOTPAuth",
    "TOTPManager",
    # 全局实例
    "auth_manager",
]

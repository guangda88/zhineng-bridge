#!/usr/bin/env python3
"""
用户数据库模块

提供数据库连接池和用户数据库操作。
"""

import sqlite3
import uuid
import threading
import json
from typing import Optional, List
from datetime import datetime
from contextlib import contextmanager
from queue import Queue, Empty

from cachetools import TTLCache

from logger import get_logger
from config import settings
from auth_models import User, UserRole
from auth_hash import PasswordHasher

# ============================================================================
# 缓存配置
# ============================================================================

# 用户信息缓存: TTL 5分钟, 最大1000条
USER_CACHE_TTL = 300  # 5分钟
USER_CACHE_MAXSIZE = 1000


class SQLiteConnectionPool:
    """SQLite 连接池

    线程安全的数据库连接池实现，支持连接复用和最大连接数限制。
    使用 Queue 实现连接的获取和释放。
    """

    def __init__(self, db_path: str, max_connections: int = 5):
        """
        初始化连接池

        Args:
            db_path: 数据库文件路径
            max_connections: 最大连接数（默认5）
        """
        self.db_path = db_path
        self.max_connections = max_connections
        self._pool: Queue[sqlite3.Connection] = Queue(maxsize=max_connections)
        self._created_connections = 0
        self._lock = threading.Lock()
        self._local = threading.local()

        # 预创建部分连接
        self._initialize_pool()

    def _initialize_pool(self):
        """初始化连接池，预创建部分连接"""
        for _ in range(min(2, self.max_connections)):
            try:
                self._pool.put(self._create_connection(), block=False)
            except Exception:
                pass

    def _create_connection(self) -> sqlite3.Connection:
        """创建新的数据库连接"""
        conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
        )
        conn.row_factory = sqlite3.Row
        return conn

    @contextmanager
    def get_connection(self):
        """
        获取连接（上下文管理器）

        自动处理连接的获取和释放。

        Returns:
            数据库连接

        Example:
            with pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users")
        """
        conn = None

        try:
            # 尝试从线程本地存储获取连接
            if hasattr(self._local, 'connection') and self._local.connection is not None:
                yield self._local.connection
                return

            # 尝试从池中获取连接
            try:
                conn = self._pool.get(timeout=5.0)
            except Empty:
                # 池中没有可用连接，创建新连接
                with self._lock:
                    if self._created_connections < self.max_connections:
                        conn = self._create_connection()
                        self._created_connections += 1
                    else:
                        # 等待可用连接
                        conn = self._pool.get(timeout=30.0)

            yield conn

        finally:
            # 将连接放回池中（如果不是线程本地连接）
            if conn is not None and not hasattr(self._local, 'connection'):
                try:
                    self._pool.put_nowait(conn)
                except Exception:
                    # 池已满，直接关闭连接
                    try:
                        conn.close()
                    except Exception:
                        pass

    @contextmanager
    def get_transaction(self):
        """
        获取事务连接（上下文管理器）

        自动提交或回滚事务。

        Returns:
            数据库连接

        Example:
            with pool.get_transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users ...")
                # 自动提交
        """
        conn = None

        try:
            conn = self._pool.get(timeout=5.0)
            yield conn
            conn.commit()
        except Exception:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                try:
                    self._pool.put_nowait(conn)
                except Exception:
                    try:
                        conn.close()
                    except Exception:
                        pass

    def close_all(self):
        """关闭所有连接"""
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                conn.close()
            except (Empty, Exception):
                break

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_all()


class UserDatabase:
    """用户数据库"""

    # 用户信息缓存 (TTL: 5分钟, 最大1000条)
    _user_cache: TTLCache = TTLCache(maxsize=USER_CACHE_MAXSIZE, ttl=USER_CACHE_TTL)
    _user_cache_lock = threading.Lock()

    @classmethod
    def invalidate_user_cache(cls, user_id: str = None, username: str = None):
        """
        使缓存失效

        Args:
            user_id: 用户 ID
            username: 用户名
        """
        with cls._user_cache_lock:
            if user_id:
                key = f"user_id:{user_id}"
                if key in cls._user_cache:
                    del cls._user_cache[key]
            if username:
                key = f"username:{username}"
                if key in cls._user_cache:
                    del cls._user_cache[key]

    def __init__(self, db_path: str = None, max_connections: int = 5):
        """
        初始化用户数据库

        Args:
            db_path: 数据库文件路径
            max_connections: 连接池最大连接数（默认5）
        """
        self.logger = get_logger(__name__)
        self.db_path = db_path or settings.database.db_path
        self._pool = SQLiteConnectionPool(self.db_path, max_connections)
        self._init_database()

    def _init_database(self):
        """初始化数据库表"""
        with self._pool.get_connection() as conn:
            cursor = conn.cursor()

            # 用户表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE,
                    password_hash TEXT,
                    role TEXT NOT NULL DEFAULT 'user',
                    permissions TEXT DEFAULT '[]',
                    is_active BOOLEAN DEFAULT TRUE,
                    oauth_provider TEXT,
                    oauth_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # OAuth2 令牌表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS oauth_tokens (
                    token_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    access_token TEXT NOT NULL,
                    refresh_token TEXT,
                    expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
                )
            """)

            # 会话表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    token TEXT NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
                )
            """)

            # 创建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_oauth_tokens_user ON oauth_tokens(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)")

            conn.commit()
            self.logger.info("User database initialized", db_path=self.db_path)

    def create_user(
        self,
        username: str,
        password: str = None,
        email: str = None,
        role: UserRole = UserRole.USER,
        permissions: List[str] = None,
    ) -> User:
        """
        创建新用户

        Args:
            username: 用户名
            password: 密码（可选，用于OAuth用户）
            email: 邮箱（可选）
            role: 用户角色
            permissions: 权限列表

        Returns:
            创建的用户

        Raises:
            ValueError: 如果用户名或邮箱已存在
        """
        if permissions is None:
            permissions = ["read", "write"]

        password_hash = PasswordHasher.hash_password(password) if password else None

        with self._pool.get_connection() as conn:
            cursor = conn.cursor()

            try:
                user_id = str(uuid.uuid4())
                now = datetime.now().isoformat()

                cursor.execute("""
                    INSERT INTO users (
                        user_id, username, email, password_hash,
                        role, permissions, is_active, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    username,
                    email,
                    password_hash,
                    role.value,
                    json.dumps(permissions),
                    True,
                    now,
                    now,
                ))

                conn.commit()
                self.logger.info("User created", user_id=user_id, username=username)

                return User(
                    user_id=user_id,
                    username=username,
                    email=email,
                    password_hash=password_hash,
                    role=role,
                    permissions=permissions,
                    is_active=True,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )

            except sqlite3.IntegrityError as e:
                if "username" in str(e):
                    raise ValueError(f"Username '{username}' already exists")
                elif "email" in str(e):
                    raise ValueError(f"Email '{email}' already exists")
                else:
                    raise ValueError(f"Failed to create user: {e}")

    def get_user(self, user_id: str = None, username: str = None) -> Optional[User]:
        """
        获取用户（带缓存，TTL 5分钟）

        Args:
            user_id: 用户 ID
            username: 用户名

        Returns:
            用户对象或 None
        """
        if not user_id and not username:
            return None

        # 构建缓存键
        cache_key = f"user_id:{user_id}" if user_id else f"username:{username}"

        # 尝试从缓存获取
        with self._user_cache_lock:
            if cache_key in self._user_cache:
                self.logger.debug("User cache hit", cache_key=cache_key)
                return self._user_cache[cache_key]

        # 缓存未命中，从数据库查询
        with self._pool.get_connection() as conn:
            cursor = conn.cursor()

            if user_id:
                cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            elif username:
                cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            else:
                return None

            row = cursor.fetchone()
            if not row:
                return None

            user = self._row_to_user(row)

            # 写入缓存
            with self._user_cache_lock:
                self._user_cache[cache_key] = user

            return user

    def verify_user(self, username: str, password: str) -> Optional[User]:
        """
        验证用户凭据

        Args:
            username: 用户名
            password: 密码

        Returns:
            用户对象或 None
        """
        with self._pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM users WHERE username = ? AND is_active = TRUE",
                (username,)
            )
            row = cursor.fetchone()

            if not row:
                return None

            user = self._row_to_user(row)

            if user.password_hash and PasswordHasher.verify_password(password, user.password_hash):
                self.logger.info("User verified", user_id=user.user_id, username=username)
                return user

            return None

    def update_user(self, user_id: str, **kwargs) -> bool:
        """
        更新用户信息（更新后使缓存失效）

        Args:
            user_id: 用户 ID
            **kwargs: 要更新的字段

        Returns:
            是否成功
        """
        allowed_fields = {"username", "email", "role", "permissions", "is_active", "oauth_provider", "oauth_id"}
        update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not update_fields:
            return False

        with self._pool.get_connection() as conn:
            cursor = conn.cursor()

            # 处理 permissions 字段（需要 JSON 序列化）
            if "permissions" in update_fields:
                update_fields["permissions"] = json.dumps(update_fields["permissions"])

            # 处理 role 字段（需要枚举值）
            if "role" in update_fields and isinstance(update_fields["role"], UserRole):
                update_fields["role"] = update_fields["role"].value

            # 构建 SQL
            set_clause = ", ".join([f"{k} = ?" for k in update_fields.keys()])
            values = list(update_fields.values()) + [user_id]

            cursor.execute(
                f"UPDATE users SET {set_clause}, updated_at = ? WHERE user_id = ?",
                values + [datetime.now().isoformat()]
            )
            conn.commit()

            self.logger.info("User updated", user_id=user_id)

            # 使缓存失效
            self.invalidate_user_cache(user_id=user_id)

            return True

    def delete_user(self, user_id: str) -> bool:
        """
        删除用户（删除后使缓存失效）

        Args:
            user_id: 用户 ID

        Returns:
            是否成功
        """
        with self._pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            username = row[0] if row else None

            cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
            conn.commit()

            self.logger.info("User deleted", user_id=user_id)

            # 使缓存失效
            self.invalidate_user_cache(user_id=user_id, username=username)

            return cursor.rowcount > 0

    def list_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        """
        列出用户

        Args:
            limit: 限制数量
            offset: 偏移量

        Returns:
            用户列表
        """
        with self._pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset)
            )
            rows = cursor.fetchall()
            return [self._row_to_user(row) for row in rows]

    def store_token(
        self,
        session_id: str,
        user_id: str,
        token: str,
        expires_at: datetime,
    ) -> bool:
        """
        存储令牌到会话表

        Args:
            session_id: 会话 ID
            user_id: 用户 ID
            token: 令牌
            expires_at: 过期时间

        Returns:
            是否成功存储
        """
        try:
            with self._pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO sessions (session_id, user_id, token, expires_at, created_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (session_id, user_id, token, expires_at.isoformat()))
                conn.commit()
                self.logger.debug("Token stored", session_id=session_id, user_id=user_id)
                return True
        except sqlite3.IntegrityError as e:
            self.logger.warning("Failed to store token", error=str(e))
            return False

    def get_token(self, token: str) -> Optional[dict]:
        """
        获取令牌信息

        Args:
            token: 令牌

        Returns:
            令牌信息字典或 None
        """
        with self._pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT session_id, user_id, token, expires_at, created_at
                FROM sessions WHERE token = ?
            """, (token,))
            row = cursor.fetchone()
            if row:
                return {
                    "session_id": row[0],
                    "user_id": row[1],
                    "token": row[2],
                    "expires_at": datetime.fromisoformat(row[3]),
                    "created_at": datetime.fromisoformat(row[4]),
                }
            return None

    def revoke_token(self, token: str) -> bool:
        """
        撤销令牌

        Args:
            token: 令牌

        Returns:
            是否成功撤销
        """
        with self._pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()
            deleted = cursor.rowcount > 0
            if deleted:
                self.logger.info("Token revoked", token=token[:10] + "...")
            return deleted

    def revoke_all_user_tokens(self, user_id: str) -> int:
        """
        撤销用户的所有令牌

        Args:
            user_id: 用户 ID

        Returns:
            撤销的令牌数量
        """
        with self._pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
            conn.commit()
            count = cursor.rowcount
            self.logger.info("All user tokens revoked", user_id=user_id, count=count)
            return count

    def cleanup_expired_tokens(self) -> int:
        """
        清理过期的令牌

        Returns:
            清理的令牌数量
        """
        with self._pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM sessions WHERE expires_at < CURRENT_TIMESTAMP
            """)
            conn.commit()
            count = cursor.rowcount
            if count > 0:
                self.logger.info("Expired tokens cleaned up", count=count)
            return count

    def get_user_tokens(self, user_id: str) -> List[dict]:
        """
        获取用户的所有令牌

        Args:
            user_id: 用户 ID

        Returns:
            令牌信息列表
        """
        with self._pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT session_id, user_id, token, expires_at, created_at
                FROM sessions WHERE user_id = ? AND expires_at > CURRENT_TIMESTAMP
            """, (user_id,))
            rows = cursor.fetchall()
            return [
                {
                    "session_id": row[0],
                    "user_id": row[1],
                    "token": row[2],
                    "expires_at": datetime.fromisoformat(row[3]),
                    "created_at": datetime.fromisoformat(row[4]),
                }
                for row in rows
            ]

    def _row_to_user(self, row) -> User:
        """将数据库行转换为 User 对象"""
        return User(
            user_id=row[0],
            username=row[1],
            email=row[2],
            password_hash=row[3],
            role=UserRole(row[4]),
            permissions=json.loads(row[5]),
            is_active=row[6],
            oauth_provider=row[7],
            oauth_id=row[8],
            created_at=datetime.fromisoformat(row[9]),
            updated_at=datetime.fromisoformat(row[10]),
        )

    def get_user_by_oauth(self, provider: str, oauth_id: str) -> Optional[User]:
        """
        通过 OAuth 提供商和 ID 获取用户

        Args:
            provider: OAuth 提供商名称
            oauth_id: OAuth 用户 ID

        Returns:
            用户对象或 None
        """
        with self._pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM users WHERE oauth_provider = ? AND oauth_id = ?",
                (provider, oauth_id),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_user(row)

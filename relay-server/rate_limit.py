#!/usr/bin/env python3
"""
智桥速率限制中间件

使用 Token Bucket 算法实现速率限制
"""

import time
import threading
from typing import Dict, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from logger import get_logger
from config import settings


@dataclass
class TokenBucket:
    """令牌桶算法实现"""

    capacity: int  # 桶容量
    refill_rate: int  # 每秒补充的令牌数
    tokens: float = field(default_factory=lambda: 0.0)
    last_refill: float = field(default_factory=time.time)

    def __post_init__(self):
        """初始化后创建锁"""
        self._lock = threading.Lock()

    def consume(self, tokens_requested: int = 1) -> bool:
        """
        消费令牌

        Args:
            tokens_requested: 请求的令牌数

        Returns:
            是否成功消费令牌
        """
        with self._lock:
            now = time.time()

            # 补充令牌
            time_passed = now - self.last_refill
            self.tokens += time_passed * self.refill_rate

            # 限制最大容量
            if self.tokens > self.capacity:
                self.tokens = float(self.capacity)

            # 更新最后补充时间
            self.last_refill = now

            # 检查是否有足够令牌
            if self.tokens >= tokens_requested:
                self.tokens -= tokens_requested
                return True
            return False

    def wait_time(self, tokens_requested: int = 1) -> float:
        """
        计算需要等待的时间（秒）

        Args:
            tokens_requested: 请求的令牌数

        Returns:
            等待时间（秒）
        """
        with self._lock:
            if self.tokens >= tokens_requested:
                return 0.0

            tokens_needed = tokens_requested - self.tokens
            return tokens_needed / self.refill_rate


@dataclass
class SlidingWindow:
    """滑动窗口算法实现"""

    window_size: int  # 窗口大小（秒）
    max_requests: int  # 最大请求数
    requests: deque = field(default_factory=deque)

    def __post_init__(self):
        """初始化后创建锁"""
        self._lock = threading.Lock()

    def allow_request(self) -> bool:
        """
        检查是否允许请求

        Returns:
            是否允许请求
        """
        with self._lock:
            now = time.time()

            # 移除窗口外的请求
            while self.requests and now - self.requests[0] >= self.window_size:
                self.requests.popleft()

            # 检查请求数是否超过限制
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True
            return False

    def get_count(self) -> int:
        """获取当前窗口内的请求数"""
        with self._lock:
            now = time.time()

            # 移除窗口外的请求
            while self.requests and now - self.requests[0] >= self.window_size:
                self.requests.popleft()

            return len(self.requests)

    def reset_time(self) -> float:
        """计算窗口重置时间（秒）"""
        with self._lock:
            if not self.requests:
                return 0.0

            oldest_request = self.requests[0]
            window_start = oldest_request + self.window_size
            return max(0.0, window_start - time.time())


class RateLimiter:
    """速率限制器"""

    def __init__(
        self,
        requests_per_minute: int = None,
        requests_per_hour: int = None,
        algorithm: str = "token_bucket",  # token_bucket 或 sliding_window
    ):
        """
        初始化速率限制器

        Args:
            requests_per_minute: 每分钟请求数限制
            requests_per_hour: 每小时请求数限制
            algorithm: 使用的算法 (token_bucket 或 sliding_window)
        """
        self.logger = get_logger(__name__)
        self.algorithm = algorithm

        # 使用配置文件中的值，如果没有则使用默认值
        self.requests_per_minute = (
            requests_per_minute or settings.security.rate_limit_per_minute
        )
        self.requests_per_hour = (
            requests_per_hour or settings.security.rate_limit_per_hour
        )

        # 根据算法选择不同的限制器
        if algorithm == "token_bucket":
            # 令牌桶算法
            self.minute_bucket = TokenBucket(
                capacity=self.requests_per_minute,
                refill_rate=self.requests_per_minute / 60.0,
            )
            self.hour_bucket = TokenBucket(
                capacity=self.requests_per_hour,
                refill_rate=self.requests_per_hour / 3600.0,
            )
        else:
            # 滑动窗口算法
            self.minute_window = SlidingWindow(
                window_size=60, max_requests=self.requests_per_minute
            )
            self.hour_window = SlidingWindow(
                window_size=3600, max_requests=self.requests_per_hour
            )

        # 为每个客户端维护独立的限制器
        self.client_limiters: Dict[str, Dict[str, object]] = defaultdict(
            lambda: {
                "minute": (
                    TokenBucket(
                        capacity=self.requests_per_minute,
                        refill_rate=self.requests_per_minute / 60.0,
                    )
                    if algorithm == "token_bucket"
                    else SlidingWindow(
                        window_size=60, max_requests=self.requests_per_minute
                    )
                ),
                "hour": (
                    TokenBucket(
                        capacity=self.requests_per_hour,
                        refill_rate=self.requests_per_hour / 3600.0,
                    )
                    if algorithm == "token_bucket"
                    else SlidingWindow(
                        window_size=3600, max_requests=self.requests_per_hour
                    )
                ),
                "blocked_until": None,
                "last_activity": datetime.now(),  # 跟踪客户端最后活动时间
            }
        )

        # 全局限制器（所有客户端共享）
        self.global_limiters = {
            "minute": (
                TokenBucket(
                    capacity=self.requests_per_minute * 10,  # 全局限制更大
                    refill_rate=self.requests_per_minute * 10 / 60.0,
                )
                if algorithm == "token_bucket"
                else SlidingWindow(
                    window_size=60, max_requests=self.requests_per_minute * 10
                )
            ),
            "hour": (
                TokenBucket(
                    capacity=self.requests_per_hour * 10,
                    refill_rate=self.requests_per_hour * 10 / 3600.0,
                )
                if algorithm == "token_bucket"
                else SlidingWindow(
                    window_size=3600, max_requests=self.requests_per_hour * 10
                )
            ),
        }

        self.logger.info(
            "Rate limiter initialized",
            algorithm=algorithm,
            requests_per_minute=self.requests_per_minute,
            requests_per_hour=self.requests_per_hour,
        )

    def is_allowed(self, client_id: str, tokens: int = 1) -> Tuple[bool, str]:
        """
        检查客户端是否允许请求

        Args:
            client_id: 客户端 ID
            tokens: 请求的令牌数（默认为 1）

        Returns:
            (是否允许, 拒绝原因)
        """
        # 如果速率限制未启用，直接允许
        if not settings.security.enable_rate_limit:
            return True, ""

        # 检查客户端是否被暂时阻止
        client_limiter = self.client_limiters[client_id]

        # 更新客户端最后活动时间
        client_limiter["last_activity"] = datetime.now()

        if client_limiter["blocked_until"]:
            if datetime.now() < client_limiter["blocked_until"]:
                retry_after = int(
                    (client_limiter["blocked_until"] - datetime.now()).total_seconds()
                )
                return False, f"Rate limit exceeded. Retry after {retry_after} seconds"
            else:
                # 解除阻止
                client_limiter["blocked_until"] = None

        # 检查全局限制
        if self.algorithm == "token_bucket":
            if not self.global_limiters["minute"].consume(tokens):
                wait_time = self.global_limiters["minute"].wait_time(tokens)
                return False, f"Global rate limit exceeded. Wait {wait_time:.1f} seconds"
            if not self.global_limiters["hour"].consume(tokens):
                wait_time = self.global_limiters["hour"].wait_time(tokens)
                return False, f"Global hourly rate limit exceeded. Wait {wait_time:.1f} seconds"
        else:
            if not self.global_limiters["minute"].allow_request():
                reset_time = self.global_limiters["minute"].reset_time()
                return False, f"Global rate limit exceeded. Reset after {reset_time:.1f} seconds"
            if not self.global_limiters["hour"].allow_request():
                reset_time = self.global_limiters["hour"].reset_time()
                return False, f"Global hourly rate limit exceeded. Reset after {reset_time:.1f} seconds"

        # 检查客户端限制
        minute_limiter = client_limiter["minute"]
        hour_limiter = client_limiter["hour"]

        if self.algorithm == "token_bucket":
            if not minute_limiter.consume(tokens):
                wait_time = minute_limiter.wait_time(tokens)
                self.logger.warning(
                    "Client minute rate limit exceeded",
                    client_id=client_id,
                    wait_time=wait_time,
                )
                return False, f"Rate limit exceeded. Wait {wait_time:.1f} seconds"

            if not hour_limiter.consume(tokens):
                wait_time = hour_limiter.wait_time(tokens)
                self.logger.warning(
                    "Client hourly rate limit exceeded",
                    client_id=client_id,
                    wait_time=wait_time,
                )
                return False, f"Hourly rate limit exceeded. Wait {wait_time:.1f} seconds"
        else:
            if not minute_limiter.allow_request():
                reset_time = minute_limiter.reset_time()
                self.logger.warning(
                    "Client minute rate limit exceeded",
                    client_id=client_id,
                    reset_time=reset_time,
                )
                return False, f"Rate limit exceeded. Reset after {reset_time:.1f} seconds"

            if not hour_limiter.allow_request():
                reset_time = hour_limiter.reset_time()
                self.logger.warning(
                    "Client hourly rate limit exceeded",
                    client_id=client_id,
                    reset_time=reset_time,
                )
                return False, f"Hourly rate limit exceeded. Reset after {reset_time:.1f} seconds"

        return True, ""

    def block_client(self, client_id: str, duration: int = 300):
        """
        阻止客户端

        Args:
            client_id: 客户端 ID
            duration: 阻止时长（秒）
        """
        client_limiter = self.client_limiters[client_id]
        client_limiter["blocked_until"] = datetime.now() + timedelta(seconds=duration)
        self.logger.warning(
            "Client blocked", client_id=client_id, duration=duration
        )

    def unblock_client(self, client_id: str):
        """
        解除阻止客户端

        Args:
            client_id: 客户端 ID
        """
        client_limiter = self.client_limiters[client_id]
        client_limiter["blocked_until"] = None
        self.logger.info("Client unblocked", client_id=client_id)

    def get_client_stats(self, client_id: str) -> dict:
        """
        获取客户端统计信息

        Args:
            client_id: 客户端 ID

        Returns:
            统计信息字典
        """
        client_limiter = self.client_limiters[client_id]
        minute_limiter = client_limiter["minute"]
        hour_limiter = client_limiter["hour"]

        stats = {
            "client_id": client_id,
            "blocked": client_limiter["blocked_until"] is not None,
            "blocked_until": (
                client_limiter["blocked_until"].isoformat()
                if client_limiter["blocked_until"]
                else None
            ),
        }

        if self.algorithm == "token_bucket":
            stats["minute_tokens"] = minute_limiter.tokens
            stats["hour_tokens"] = hour_limiter.tokens
            stats["minute_capacity"] = minute_limiter.capacity
            stats["hour_capacity"] = hour_limiter.capacity
        else:
            stats["minute_requests"] = minute_limiter.get_count()
            stats["hour_requests"] = hour_limiter.get_count()
            stats["minute_max"] = minute_limiter.max_requests
            stats["hour_max"] = hour_limiter.max_requests

        return stats

    def get_global_stats(self) -> dict:
        """
        获取全局统计信息

        Returns:
            统计信息字典
        """
        stats = {
            "algorithm": self.algorithm,
            "requests_per_minute": self.requests_per_minute,
            "requests_per_hour": self.requests_per_hour,
            "active_clients": len(self.client_limiters),
        }

        if self.algorithm == "token_bucket":
            stats["global_minute_tokens"] = self.global_limiters["minute"].tokens
            stats["global_hour_tokens"] = self.global_limiters["hour"].tokens
        else:
            stats["global_minute_requests"] = (
                self.global_limiters["minute"].get_count()
            )
            stats["global_hour_requests"] = self.global_limiters["hour"].get_count()

        return stats

    def reset_client(self, client_id: str):
        """
        重置客户端限制器

        Args:
            client_id: 客户端 ID
        """
        if client_id in self.client_limiters:
            del self.client_limiters[client_id]
            self.logger.info("Client rate limiter reset", client_id=client_id)

    def cleanup_inactive_clients(self, max_age: int = 3600):
        """
        清理不活跃的客户端

        Args:
            max_age: 最大不活跃时间（秒），默认 1 小时
        """
        now = datetime.now()
        clients_to_remove = []

        # 查找所有不活跃的客户端
        for client_id, client_data in self.client_limiters.items():
            last_activity = client_data.get("last_activity")
            if last_activity:
                inactive_time = (now - last_activity).total_seconds()
                if inactive_time > max_age:
                    clients_to_remove.append(client_id)
            else:
                # 如果没有活动时间记录，视为不活跃
                clients_to_remove.append(client_id)

        # 清理不活跃的客户端
        for client_id in clients_to_remove:
            del self.client_limiters[client_id]
            self.logger.info("Client rate limiter removed (inactive)", client_id=client_id)

        if clients_to_remove:
            self.logger.info("Cleanup inactive clients completed", count=len(clients_to_remove))
        else:
            self.logger.debug("No inactive clients to clean up")


# ============================================================================
# 全局速率限制器实例
# ============================================================================

rate_limiter = RateLimiter()


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    "TokenBucket",
    "SlidingWindow",
    "RateLimiter",
    "rate_limiter",
]

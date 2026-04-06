#!/usr/bin/env python3
"""
分片锁管理器 - 使用分片锁策略减少并发竞争

该模块提供了一个分片锁机制，通过将数据分散到多个锁分片上，
从而减少并发竞争，提高高并发场景下的性能。
"""

import asyncio
from typing import Dict, Optional, Callable, TypeVar
from functools import wraps
from logger import get_logger

T = TypeVar('T')

logger = get_logger(__name__)


class ShardedLockManager:
    """分片锁管理器

    使用一致性哈希将键映射到固定数量的锁分片上，
    不同分片的操作可以并发执行，从而减少锁竞争。

    示例:
        # 创建16个分片的锁管理器
        lock_manager = ShardedLockManager(shard_count=16)

        # 使用客户端ID作为分片键
        async with lock_manager.lock(client_id):
            # 操作该客户端对应的数据
            data[client_id] = value
    """

    def __init__(self, shard_count: int = 16) -> None:
        """初始化分片锁管理器

        Args:
            shard_count: 分片数量，默认16个分片
        """
        self._shard_count = shard_count
        self._locks: tuple[asyncio.Lock, ...] = tuple(
            asyncio.Lock() for _ in range(shard_count)
        )
        self.logger = get_logger(__name__)
        self.logger.info(
            "ShardedLockManager initialized",
            shard_count=shard_count
        )

    def _get_shard_index(self, key: str) -> int:
        """根据键获取分片索引

        使用内置哈希函数确保相同键总是映射到同一分片。

        Args:
            key: 分片键（通常是client_id, session_id, user_id等）

        Returns:
            分片索引 (0 到 shard_count-1)
        """
        return hash(key) % self._shard_count

    def get_lock(self, key: str) -> asyncio.Lock:
        """获取指定键对应的锁

        Args:
            key: 分片键

        Returns:
            对应的异步锁
        """
        shard_index = self._get_shard_index(key)
        return self._locks[shard_index]

    def lock(self, key: str):
        """获取指定键的锁上下文管理器

        Args:
            key: 分片键

        Returns:
            异步锁上下文管理器

        Example:
            async with lock_manager.lock(client_id):
                # 临界区代码
                pass
        """
        return self.get_lock(key)

    async def acquire(self, key: str) -> None:
        """获取指定键的锁

        Args:
            key: 分片键
        """
        await self.get_lock(key).acquire()

    def release(self, key: str) -> None:
        """释放指定键的锁

        Args:
            key: 分片键
        """
        lock = self.get_lock(key)
        if lock.locked():
            lock.release()

    def is_locked(self, key: str) -> bool:
        """检查指定键的锁是否被持有

        Args:
            key: 分片键

        Returns:
            锁是否被持有
        """
        return self.get_lock(key).locked()

    def get_stats(self) -> Dict[str, int]:
        """获取各分片的锁状态统计

        Returns:
            包含各分片锁定状态的字典
        """
        return {
            f"shard_{i}": int(lock.locked())
            for i, lock in enumerate(self._locks)
        }

    @property
    def shard_count(self) -> int:
        """获取分片数量"""
        return self._shard_count

    async def acquire_all(self) -> None:
        """获取所有分片锁

        用于需要全局一致性的操作，如遍历所有数据。
        按顺序获取所有锁以避免死锁。

        注意：此操作会阻塞所有分片，应谨慎使用。
        """
        for lock in self._locks:
            await lock.acquire()

    def release_all(self) -> None:
        """释放所有分片锁

        必须在 acquire_all 后调用。
        按相反顺序释放锁。
        """
        for lock in reversed(self._locks):
            if lock.locked():
                lock.release()


def with_sharded_lock(
    lock_manager: ShardedLockManager,
    key_param: str = "key"
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """装饰器：为函数添加分片锁

    Args:
        lock_manager: 分片锁管理器实例
        key_param: 用作分片键的参数名

    Returns:
        装饰后的函数

    Example:
        lock_manager = ShardedLockManager()

        @with_sharded_lock(lock_manager, "client_id")
        async def process_request(client_id: str, data: dict):
            # 函数执行时会自动获取client_id对应的锁
            return await _do_process(client_id, data)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # 获取分片键
            key = kwargs.get(key_param)
            if key is None:
                # 尝试从位置参数获取（简化处理）
                raise ValueError(f"Parameter '{key_param}' not found for sharded lock")

            async with lock_manager.lock(str(key)):
                return await func(*args, **kwargs)
        return wrapper
    return decorator


class ShardedDataStore:
    """带分片锁的数据存储

    一个简单的线程安全字典，使用分片锁来保护访问。

    示例:
        store = ShardedDataStore(shard_count=16)
        await store.set("client_1", websocket)
        ws = await store.get("client_1")
        await store.delete("client_1")
    """

    def __init__(self, shard_count: int = 16) -> None:
        """初始化分片数据存储

        Args:
            shard_count: 分片数量
        """
        self._lock_manager = ShardedLockManager(shard_count)
        self._shard_count = shard_count
        self._data: tuple[Dict[str, object], ...] = tuple(
            {} for _ in range(shard_count)
        )
        self.logger = get_logger(__name__)

    async def get(self, key: str, default: Optional[T] = None) -> Optional[T]:
        """获取值

        Args:
            key: 键
            default: 默认值

        Returns:
            对应的值或默认值
        """
        async with self._lock_manager.lock(key):
            shard = self._data[self._lock_manager._get_shard_index(key)]
            return shard.get(key, default)

    async def set(self, key: str, value: object) -> None:
        """设置值

        Args:
            key: 键
            value: 值
        """
        async with self._lock_manager.lock(key):
            self._data[self._lock_manager._get_shard_index(key)][key] = value

    async def delete(self, key: str) -> bool:
        """删除键

        Args:
            key: 键

        Returns:
            是否成功删除
        """
        async with self._lock_manager.lock(key):
            shard = self._data[self._lock_manager._get_shard_index(key)]
            if key in shard:
                del shard[key]
                return True
            return False

    async def contains(self, key: str) -> bool:
        """检查键是否存在

        Args:
            key: 键

        Returns:
            键是否存在
        """
        async with self._lock_manager.lock(key):
            return key in self._data[self._lock_manager._get_shard_index(key)]

    async def keys(self) -> list[str]:
        """获取所有键

        注意：此操作需要获取所有分片锁，开销较大。

        Returns:
            所有键的列表
        """
        # 获取所有锁以确保一致性
        acquired_locks = []
        for lock in self._lock_manager._locks:
            await lock.acquire()
            acquired_locks.append(lock)

        try:
            result = []
            for shard in self._data:
                result.extend(shard.keys())
            return result
        finally:
            # 释放所有锁
            for lock in reversed(acquired_locks):
                lock.release()

    async def items(self) -> list[tuple[str, object]]:
        """获取所有键值对

        注意：此操作需要获取所有分片锁，开销较大。

        Returns:
            所有键值对的列表
        """
        acquired_locks = []
        for lock in self._lock_manager._locks:
            await lock.acquire()
            acquired_locks.append(lock)

        try:
            result = []
            for shard in self._data:
                result.extend(shard.items())
            return result
        finally:
            for lock in reversed(acquired_locks):
                lock.release()

    async def clear(self) -> None:
        """清空所有数据

        注意：此操作需要获取所有分片锁。
        """
        acquired_locks = []
        for lock in self._lock_manager._locks:
            await lock.acquire()
            acquired_locks.append(lock)

        try:
            for shard in self._data:
                shard.clear()
        finally:
            for lock in reversed(acquired_locks):
                lock.release()

    def __len__(self) -> int:
        """获取数据项数量

        注意：此方法为近似值，不持有锁。如需精确计数请使用 async len_async()。
        """
        return sum(len(shard) for shard in self._data)

from __future__ import annotations

from redis.asyncio import Redis

from app.core.config import get_settings
from app.core.utils import new_id


class AgentLockManager:
    def __init__(self, redis: Redis) -> None:
        self.redis = redis
        self.settings = get_settings()

    def _key(self, agent_id: str) -> str:
        return f"agent-lock:{agent_id}"

    async def acquire(self, agent_id: str) -> str | None:
        lock_value = new_id("lock")
        acquired = await self.redis.set(
            self._key(agent_id),
            lock_value,
            ex=self.settings.redis_lock_ttl_seconds,
            nx=True,
        )
        return lock_value if acquired else None

    async def release(self, agent_id: str, lock_value: str) -> None:
        key = self._key(agent_id)
        existing = await self.redis.get(key)
        if existing == lock_value:
            await self.redis.delete(key)

    async def is_locked(self, agent_id: str) -> bool:
        return bool(await self.redis.exists(self._key(agent_id)))

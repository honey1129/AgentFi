from __future__ import annotations

import asyncio

from redis.asyncio import Redis, from_url

from app.core.config import get_settings


_redis: Redis | None = None
_redis_loop_id: int | None = None


async def init_redis() -> Redis:
    global _redis, _redis_loop_id
    current_loop_id = id(asyncio.get_running_loop())
    if _redis is None or _redis_loop_id != current_loop_id:
        settings = get_settings()
        _redis = from_url(settings.redis_url, decode_responses=True)
        await _redis.ping()
        _redis_loop_id = current_loop_id
    return _redis


async def get_redis() -> Redis:
    if _redis is None or _redis_loop_id != id(asyncio.get_running_loop()):
        return await init_redis()
    return _redis


async def close_redis() -> None:
    global _redis, _redis_loop_id
    if _redis is not None:
        await _redis.aclose()
        _redis = None
        _redis_loop_id = None

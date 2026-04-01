from __future__ import annotations

from fastapi import HTTPException, status
from redis.asyncio import Redis


def _rate_limit_key(namespace: str, subject: str) -> str:
    normalized_namespace = namespace.strip().replace(" ", "-") or "default"
    normalized_subject = subject.strip().replace(" ", "-") or "anonymous"
    return f"ratelimit:{normalized_namespace}:{normalized_subject}"


async def enforce_rate_limit(
    redis: Redis,
    *,
    namespace: str,
    subject: str,
    limit: int,
    window_seconds: int,
) -> None:
    if limit <= 0 or window_seconds <= 0:
        return

    key = _rate_limit_key(namespace, subject)
    current = await redis.incr(key)
    if current == 1:
        await redis.expire(key, window_seconds)

    if current <= limit:
        return

    ttl = await redis.ttl(key)
    retry_after = max(int(ttl or window_seconds), 1)
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=f"Rate limit exceeded. Retry in {retry_after} seconds.",
    )

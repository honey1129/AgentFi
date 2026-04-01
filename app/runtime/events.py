from __future__ import annotations

from typing import Any

from redis.asyncio import Redis


async def emit_runtime_event(redis: Redis, event_type: str, payload: dict[str, Any]) -> None:
    fields = {"event_type": event_type}
    for key, value in payload.items():
        fields[key] = "" if value is None else str(value)
    await redis.xadd("agent_runtime_events", fields=fields)

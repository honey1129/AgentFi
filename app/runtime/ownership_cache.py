from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.core.config import get_settings
from app.db.models import AgentNFT


class OwnershipCache:
    def __init__(self, redis: Redis) -> None:
        self.redis = redis
        self.settings = get_settings()

    def _agent_key(self, agent_id: str) -> str:
        return f"agent-owner:{agent_id}"

    def _token_key(self, token_id: str) -> str:
        return f"token-owner:{token_id}"

    async def get_owner_wallet_id(
        self,
        session: AsyncSession,
        *,
        agent_id: str,
        token_id: str,
    ) -> str:
        cached = await self.redis.get(self._agent_key(agent_id))
        if cached:
            return cached

        nft = await session.scalar(select(AgentNFT).where(AgentNFT.token_id == token_id))
        if nft is None:
            raise ValueError("NFT not found.")

        await self.set_owner_wallet_id(agent_id=agent_id, token_id=token_id, owner_wallet_id=nft.owner_wallet_id)
        return nft.owner_wallet_id

    async def set_owner_wallet_id(self, *, agent_id: str, token_id: str, owner_wallet_id: str) -> None:
        ttl = self.settings.owner_cache_ttl_seconds
        await self.redis.set(self._agent_key(agent_id), owner_wallet_id, ex=ttl)
        await self.redis.set(self._token_key(token_id), owner_wallet_id, ex=ttl)

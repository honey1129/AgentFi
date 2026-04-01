from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.core.utils import new_id, utcnow
from app.db.models import (
    AgentNFT,
    MarketListing,
    MarketListingChainState,
    MarketOrderEvent,
    RuntimeCheckpoint,
    TransactionRecord,
)
from app.runtime.events import emit_runtime_event
from app.runtime.ownership_cache import OwnershipCache
from app.services.onchain_market import wei_to_display_price
from app.services.runtime import WalletService, normalize_chain_address


class ChainSyncService:
    @staticmethod
    def checkpoint_key(contract_address: str, *, namespace: str = "nft-listener") -> str:
        return f"{namespace}:{normalize_chain_address(contract_address) or contract_address}"

    @staticmethod
    async def get_last_synced_block(
        session: AsyncSession,
        contract_address: str,
        *,
        namespace: str = "nft-listener",
    ) -> int | None:
        checkpoint = await session.get(RuntimeCheckpoint, ChainSyncService.checkpoint_key(contract_address, namespace=namespace))
        return int(checkpoint.value) if checkpoint is not None else None

    @staticmethod
    async def save_last_synced_block(
        session: AsyncSession,
        contract_address: str,
        block_number: int,
        *,
        namespace: str = "nft-listener",
    ) -> None:
        key = ChainSyncService.checkpoint_key(contract_address, namespace=namespace)
        checkpoint = await session.get(RuntimeCheckpoint, key)
        if checkpoint is None:
            checkpoint = RuntimeCheckpoint(key=key, value=str(block_number))
            session.add(checkpoint)
        else:
            checkpoint.value = str(block_number)
            checkpoint.updated_at = utcnow()
        await session.commit()

    @staticmethod
    async def apply_transfer(
        session: AsyncSession,
        redis: Redis,
        *,
        contract_address: str,
        chain_token_id: str,
        to_address: str,
        tx_hash: str,
        block_number: int,
    ) -> bool:
        normalized_contract = normalize_chain_address(contract_address)
        normalized_to = normalize_chain_address(to_address)
        nft = await session.scalar(
            select(AgentNFT)
            .where(
                AgentNFT.contract_address == normalized_contract,
                AgentNFT.chain_token_id == str(chain_token_id),
            )
            .with_for_update()
        )
        if nft is None or normalized_to is None:
            return False

        wallet = await WalletService.get_or_create_chain_wallet(session, normalized_to)
        open_listing = await session.scalar(
            select(MarketListing).where(MarketListing.token_id == nft.token_id, MarketListing.status == "OPEN").with_for_update()
        )
        if open_listing:
            chain_state = await session.scalar(
                select(MarketListingChainState)
                .where(MarketListingChainState.listing_id == open_listing.id)
                .with_for_update()
            )
            is_listing_open_transfer = chain_state is not None and chain_state.open_tx_hash == tx_hash
            is_historical_transfer_before_listing = (
                chain_state is not None
                and chain_state.last_synced_block is not None
                and block_number <= chain_state.last_synced_block
            )
            if not is_listing_open_transfer and not is_historical_transfer_before_listing:
                open_listing.status = "CANCELLED"
                open_listing.closed_at = utcnow()

        nft.owner_wallet_id = wallet.id
        nft.last_transfer_at = utcnow()
        nft.last_synced_tx_hash = tx_hash
        nft.last_synced_block = block_number
        await session.commit()

        ownership_cache = OwnershipCache(redis)
        await ownership_cache.set_owner_wallet_id(agent_id=nft.agent_id, token_id=nft.token_id, owner_wallet_id=wallet.id)
        await emit_runtime_event(
            redis,
            "chain_transfer_synced",
            {
                "token_id": nft.token_id,
                "chain_token_id": chain_token_id,
                "to_wallet_id": wallet.id,
                "tx_hash": tx_hash,
                "block_number": block_number,
            },
        )
        return True

    @staticmethod
    async def _record_listing_event(
        session: AsyncSession,
        *,
        listing_id: str | None,
        chain_listing_id: str | None,
        event_type: str,
        tx_hash: str,
        block_number: int,
        payload: dict,
    ) -> None:
        session.add(
            MarketOrderEvent(
                id=new_id("order_event"),
                listing_id=listing_id,
                chain_listing_id=chain_listing_id,
                event_type=event_type,
                tx_hash=tx_hash,
                block_number=block_number,
                payload_json=payload,
            )
        )

    @staticmethod
    async def _record_transaction(
        session: AsyncSession,
        *,
        listing_id: str,
        tx_hash: str,
        tx_kind: str,
        from_address: str | None,
        to_address: str | None,
        payload: dict,
    ) -> None:
        existing = await session.scalar(select(TransactionRecord).where(TransactionRecord.tx_hash == tx_hash))
        if existing is not None:
            existing.entity_type = "LISTING"
            existing.entity_id = listing_id
            existing.tx_kind = tx_kind
            existing.status = "CONFIRMED"
            existing.from_address = from_address
            existing.to_address = to_address
            existing.payload_json = payload
            existing.updated_at = utcnow()
            return

        session.add(
            TransactionRecord(
                id=new_id("tx"),
                entity_type="LISTING",
                entity_id=listing_id,
                tx_hash=tx_hash,
                tx_kind=tx_kind,
                status="CONFIRMED",
                from_address=from_address,
                to_address=to_address,
                payload_json=payload,
            )
        )

    @staticmethod
    async def apply_listing_opened(
        session: AsyncSession,
        redis: Redis,
        *,
        market_contract_address: str,
        nft_contract_address: str,
        chain_listing_id: str,
        seller_address: str,
        chain_token_id: str,
        price_wei: str,
        tx_hash: str,
        block_number: int,
    ) -> bool:
        normalized_market = normalize_chain_address(market_contract_address)
        normalized_nft = normalize_chain_address(nft_contract_address)
        normalized_seller = normalize_chain_address(seller_address)
        nft = await session.scalar(
            select(AgentNFT)
            .where(
                AgentNFT.contract_address == normalized_nft,
                AgentNFT.chain_token_id == str(chain_token_id),
            )
            .with_for_update()
        )
        if nft is None or normalized_market is None or normalized_seller is None:
            return False

        seller_wallet = await WalletService.get_or_create_chain_wallet(session, normalized_seller)
        chain_state = await session.scalar(
            select(MarketListingChainState)
            .where(
                MarketListingChainState.market_contract_address == normalized_market,
                MarketListingChainState.chain_listing_id == str(chain_listing_id),
            )
            .with_for_update()
        )
        listing = None
        if chain_state is not None:
            listing = await session.scalar(
                select(MarketListing).where(MarketListing.id == chain_state.listing_id).with_for_update()
            )

        if listing is None:
            listing = MarketListing(
                id=new_id("listing"),
                token_id=nft.token_id,
                agent_id=nft.agent_id,
                seller_wallet_id=seller_wallet.id,
                price=Decimal(wei_to_display_price(price_wei)),
                status="OPEN",
            )
            session.add(listing)
            await session.flush()
        else:
            listing.seller_wallet_id = seller_wallet.id
            listing.price = Decimal(wei_to_display_price(price_wei))
            listing.status = "OPEN"
            listing.buyer_wallet_id = None
            listing.closed_at = None

        if chain_state is None:
            chain_state = MarketListingChainState(
                listing_id=listing.id,
                market_contract_address=normalized_market,
                chain_listing_id=str(chain_listing_id),
                price_wei=str(price_wei),
                seller_chain_address=normalized_seller,
                open_tx_hash=tx_hash,
                last_synced_block=block_number,
            )
            session.add(chain_state)
        else:
            chain_state.seller_chain_address = normalized_seller
            chain_state.price_wei = str(price_wei)
            chain_state.open_tx_hash = tx_hash
            chain_state.last_synced_block = block_number
            chain_state.close_tx_hash = None
            chain_state.buyer_chain_address = None

        payload = {
            "listing_id": listing.id,
            "chain_listing_id": str(chain_listing_id),
            "token_id": nft.token_id,
            "chain_token_id": str(chain_token_id),
            "seller_chain_address": normalized_seller,
            "price_wei": str(price_wei),
        }
        await ChainSyncService._record_listing_event(
            session,
            listing_id=listing.id,
            chain_listing_id=str(chain_listing_id),
            event_type="LISTING_CREATED",
            tx_hash=tx_hash,
            block_number=block_number,
            payload=payload,
        )
        await ChainSyncService._record_transaction(
            session,
            listing_id=listing.id,
            tx_hash=tx_hash,
            tx_kind="OPEN_LISTING",
            from_address=normalized_seller,
            to_address=normalized_market,
            payload=payload,
        )
        await session.commit()

        await emit_runtime_event(
            redis,
            "chain_listing_opened",
            {
                "listing_id": listing.id,
                "chain_listing_id": chain_listing_id,
                "token_id": nft.token_id,
                "tx_hash": tx_hash,
            },
        )
        return True

    @staticmethod
    async def apply_listing_cancelled(
        session: AsyncSession,
        redis: Redis,
        *,
        market_contract_address: str,
        chain_listing_id: str,
        seller_address: str,
        chain_token_id: str,
        tx_hash: str,
        block_number: int,
    ) -> bool:
        normalized_market = normalize_chain_address(market_contract_address)
        normalized_seller = normalize_chain_address(seller_address)
        chain_state = await session.scalar(
            select(MarketListingChainState)
            .where(
                MarketListingChainState.market_contract_address == normalized_market,
                MarketListingChainState.chain_listing_id == str(chain_listing_id),
            )
            .with_for_update()
        )
        if chain_state is None:
            return False

        listing = await session.scalar(select(MarketListing).where(MarketListing.id == chain_state.listing_id).with_for_update())
        if listing is None:
            return False

        listing.status = "CANCELLED"
        listing.closed_at = utcnow()
        chain_state.close_tx_hash = tx_hash
        chain_state.last_synced_block = block_number
        payload = {
            "listing_id": listing.id,
            "chain_listing_id": str(chain_listing_id),
            "seller_chain_address": normalized_seller,
            "chain_token_id": str(chain_token_id),
        }
        await ChainSyncService._record_listing_event(
            session,
            listing_id=listing.id,
            chain_listing_id=str(chain_listing_id),
            event_type="LISTING_CANCELLED",
            tx_hash=tx_hash,
            block_number=block_number,
            payload=payload,
        )
        await ChainSyncService._record_transaction(
            session,
            listing_id=listing.id,
            tx_hash=tx_hash,
            tx_kind="CANCEL_LISTING",
            from_address=normalized_market,
            to_address=normalized_seller,
            payload=payload,
        )
        await session.commit()
        await emit_runtime_event(
            redis,
            "chain_listing_cancelled",
            {
                "listing_id": listing.id,
                "chain_listing_id": chain_listing_id,
                "tx_hash": tx_hash,
            },
        )
        return True

    @staticmethod
    async def apply_listing_purchased(
        session: AsyncSession,
        redis: Redis,
        *,
        market_contract_address: str,
        chain_listing_id: str,
        buyer_address: str,
        seller_address: str,
        chain_token_id: str,
        price_wei: str,
        tx_hash: str,
        block_number: int,
    ) -> bool:
        normalized_market = normalize_chain_address(market_contract_address)
        normalized_buyer = normalize_chain_address(buyer_address)
        normalized_seller = normalize_chain_address(seller_address)
        chain_state = await session.scalar(
            select(MarketListingChainState)
            .where(
                MarketListingChainState.market_contract_address == normalized_market,
                MarketListingChainState.chain_listing_id == str(chain_listing_id),
            )
            .with_for_update()
        )
        if chain_state is None or normalized_buyer is None:
            return False

        listing = await session.scalar(select(MarketListing).where(MarketListing.id == chain_state.listing_id).with_for_update())
        if listing is None:
            return False

        buyer_wallet = await WalletService.get_or_create_chain_wallet(session, normalized_buyer)
        listing.buyer_wallet_id = buyer_wallet.id
        listing.status = "SOLD"
        listing.closed_at = utcnow()
        chain_state.buyer_chain_address = normalized_buyer
        chain_state.close_tx_hash = tx_hash
        chain_state.last_synced_block = block_number
        payload = {
            "listing_id": listing.id,
            "chain_listing_id": str(chain_listing_id),
            "buyer_chain_address": normalized_buyer,
            "seller_chain_address": normalized_seller,
            "chain_token_id": str(chain_token_id),
            "price_wei": str(price_wei),
        }
        await ChainSyncService._record_listing_event(
            session,
            listing_id=listing.id,
            chain_listing_id=str(chain_listing_id),
            event_type="LISTING_PURCHASED",
            tx_hash=tx_hash,
            block_number=block_number,
            payload=payload,
        )
        await ChainSyncService._record_transaction(
            session,
            listing_id=listing.id,
            tx_hash=tx_hash,
            tx_kind="BUY_LISTING",
            from_address=normalized_buyer,
            to_address=normalized_seller,
            payload=payload,
        )
        await session.commit()
        await emit_runtime_event(
            redis,
            "chain_listing_purchased",
            {
                "listing_id": listing.id,
                "chain_listing_id": chain_listing_id,
                "tx_hash": tx_hash,
            },
        )
        return True

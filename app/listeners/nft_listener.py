from __future__ import annotations

import asyncio

from web3 import Web3

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.runtime.redis_client import init_redis
from app.services.chain_sync import ChainSyncService
from app.services.onchain_market import AGENT_MARKETPLACE_ABI
from app.services.web3_client import build_web3


TRANSFER_EVENT_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "from", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "to", "type": "address"},
            {"indexed": True, "internalType": "uint256", "name": "tokenId", "type": "uint256"},
        ],
        "name": "Transfer",
        "type": "event",
    }
]


async def run_listener() -> None:
    settings = get_settings()
    redis = await init_redis()

    if not settings.web3_provider_url or not settings.nft_contract_address:
        print("NFT listener is idle: WEB3_PROVIDER_URL or NFT_CONTRACT_ADDRESS is not configured.")
        while True:
            await asyncio.sleep(60)

    web3 = build_web3(settings.web3_provider_url)
    contract = web3.eth.contract(
        address=Web3.to_checksum_address(settings.nft_contract_address),
        abi=TRANSFER_EVENT_ABI,
    )
    market_contract = None
    if settings.marketplace_contract_address:
        market_contract = web3.eth.contract(
            address=Web3.to_checksum_address(settings.marketplace_contract_address),
            abi=AGENT_MARKETPLACE_ABI,
        )

    while True:
        try:
            latest_block = web3.eth.block_number
            async with SessionLocal() as session:
                nft_checkpoint = await ChainSyncService.get_last_synced_block(
                    session,
                    settings.nft_contract_address,
                    namespace="nft-listener",
                )
                market_checkpoint = None
                if market_contract is not None:
                    market_checkpoint = await ChainSyncService.get_last_synced_block(
                        session,
                        settings.marketplace_contract_address,
                        namespace="market-listener",
                    )

            nft_from_block = int(settings.web3_start_block) if nft_checkpoint is None and settings.web3_start_block.strip() else (nft_checkpoint + 1 if nft_checkpoint is not None else latest_block)

            market_from_block = None
            if market_contract is not None:
                market_from_block = (
                    int(settings.web3_start_block)
                    if market_checkpoint is None and settings.web3_start_block.strip()
                    else (market_checkpoint + 1 if market_checkpoint is not None else latest_block)
                )

            candidate_blocks = [value for value in [nft_from_block, market_from_block] if value is not None]
            if candidate_blocks:
                from_block = min(candidate_blocks)
                if from_block <= latest_block:
                    to_block = min(latest_block, from_block + settings.web3_block_batch_size - 1)
                    async with SessionLocal() as session:
                        if market_contract is not None and market_from_block is not None and market_from_block <= to_block:
                            market_events = market_contract.events.ListingCreated().get_logs(
                                from_block=market_from_block,
                                to_block=to_block,
                            )
                            for event in market_events:
                                await ChainSyncService.apply_listing_opened(
                                    session,
                                    redis,
                                    market_contract_address=settings.marketplace_contract_address,
                                    nft_contract_address=settings.nft_contract_address,
                                    chain_listing_id=str(event["args"]["listingId"]),
                                    seller_address=event["args"]["seller"],
                                    chain_token_id=str(event["args"]["tokenId"]),
                                    price_wei=str(event["args"]["price"]),
                                    tx_hash=event["transactionHash"].hex(),
                                    block_number=event["blockNumber"],
                                )

                            cancelled_events = market_contract.events.ListingCancelled().get_logs(
                                from_block=market_from_block,
                                to_block=to_block,
                            )
                            for event in cancelled_events:
                                await ChainSyncService.apply_listing_cancelled(
                                    session,
                                    redis,
                                    market_contract_address=settings.marketplace_contract_address,
                                    chain_listing_id=str(event["args"]["listingId"]),
                                    seller_address=event["args"]["seller"],
                                    chain_token_id=str(event["args"]["tokenId"]),
                                    tx_hash=event["transactionHash"].hex(),
                                    block_number=event["blockNumber"],
                                )

                            purchased_events = market_contract.events.ListingPurchased().get_logs(
                                from_block=market_from_block,
                                to_block=to_block,
                            )
                            for event in purchased_events:
                                await ChainSyncService.apply_listing_purchased(
                                    session,
                                    redis,
                                    market_contract_address=settings.marketplace_contract_address,
                                    chain_listing_id=str(event["args"]["listingId"]),
                                    buyer_address=event["args"]["buyer"],
                                    seller_address=event["args"]["seller"],
                                    chain_token_id=str(event["args"]["tokenId"]),
                                    price_wei=str(event["args"]["price"]),
                                    tx_hash=event["transactionHash"].hex(),
                                    block_number=event["blockNumber"],
                                )

                            await ChainSyncService.save_last_synced_block(
                                session,
                                settings.marketplace_contract_address,
                                to_block,
                                namespace="market-listener",
                            )

                        if nft_from_block <= to_block:
                            events = contract.events.Transfer().get_logs(from_block=nft_from_block, to_block=to_block)
                            for event in events:
                                await ChainSyncService.apply_transfer(
                                    session,
                                    redis,
                                    contract_address=settings.nft_contract_address,
                                    chain_token_id=str(event["args"]["tokenId"]),
                                    to_address=event["args"]["to"],
                                    tx_hash=event["transactionHash"].hex(),
                                    block_number=event["blockNumber"],
                                )
                            await ChainSyncService.save_last_synced_block(
                                session,
                                settings.nft_contract_address,
                                to_block,
                                namespace="nft-listener",
                            )
            await asyncio.sleep(settings.web3_poll_interval_seconds)
        except Exception as exc:
            print(f"NFT listener error: {exc}")
            await asyncio.sleep(settings.web3_poll_interval_seconds)


if __name__ == "__main__":
    asyncio.run(run_listener())

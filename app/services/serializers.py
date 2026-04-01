from __future__ import annotations

from app.db.models import (
    Agent,
    AgentNFT,
    AgentRun,
    AgentSchedule,
    MarketListing,
    MarketListingChainState,
    MarketOrderEvent,
    TransactionRecord,
    Wallet,
)
from app.services.nft_modes import get_nft_sync_mode
from app.services.onchain_market import wei_to_display_price


def wallet_to_dict(wallet: Wallet) -> dict:
    return {
        "id": wallet.id,
        "name": wallet.name,
        "chain_address": wallet.chain_address,
        "balance": str(wallet.balance),
        "created_at": wallet.created_at,
    }


def nft_to_dict(nft: AgentNFT) -> dict:
    sync_mode = get_nft_sync_mode(nft)
    return {
        "token_id": nft.token_id,
        "agent_id": nft.agent_id,
        "owner_wallet_id": nft.owner_wallet_id,
        "contract_address": nft.contract_address,
        "chain_token_id": nft.chain_token_id,
        "sync_mode": sync_mode,
        "local_market_enabled": sync_mode != "CHAIN_SYNCED",
        "onchain_transfer_enabled": sync_mode == "CHAIN_SYNCED",
        "metadata_uri": nft.metadata_uri,
        "last_synced_tx_hash": nft.last_synced_tx_hash,
        "last_synced_block": nft.last_synced_block,
        "created_at": nft.created_at,
        "last_transfer_at": nft.last_transfer_at,
    }


def agent_to_dict(
    agent: Agent,
    nft: AgentNFT,
    active_listing: MarketListing | None = None,
    active_listing_chain_state: MarketListingChainState | None = None,
) -> dict:
    return {
        "id": agent.id,
        "name": agent.name,
        "description": agent.description,
        "system_prompt": agent.system_prompt,
        "status": agent.status,
        "memory": agent.memory_json,
        "created_at": agent.created_at,
        "updated_at": agent.updated_at,
        "nft": nft_to_dict(nft),
        "active_listing": listing_to_dict(active_listing, active_listing_chain_state) if active_listing else None,
    }


def listing_chain_state_to_dict(chain_state: MarketListingChainState | None) -> dict | None:
    if chain_state is None:
        return None

    return {
        "mode": chain_state.mode,
        "market_contract_address": chain_state.market_contract_address,
        "chain_listing_id": chain_state.chain_listing_id,
        "currency_symbol": chain_state.currency_symbol,
        "price_wei": chain_state.price_wei,
        "seller_chain_address": chain_state.seller_chain_address,
        "buyer_chain_address": chain_state.buyer_chain_address,
        "open_tx_hash": chain_state.open_tx_hash,
        "close_tx_hash": chain_state.close_tx_hash,
        "last_synced_block": chain_state.last_synced_block,
        "created_at": chain_state.created_at,
        "updated_at": chain_state.updated_at,
    }


def listing_to_dict(listing: MarketListing | None, chain_state: MarketListingChainState | None = None) -> dict | None:
    if listing is None:
        return None

    display_price = wei_to_display_price(chain_state.price_wei) if chain_state is not None else str(listing.price)
    return {
        "id": listing.id,
        "token_id": listing.token_id,
        "agent_id": listing.agent_id,
        "seller_wallet_id": listing.seller_wallet_id,
        "buyer_wallet_id": listing.buyer_wallet_id,
        "price": display_price,
        "status": listing.status,
        "market_mode": chain_state.mode if chain_state is not None else "LOCAL",
        "chain": listing_chain_state_to_dict(chain_state),
        "opened_at": listing.opened_at,
        "closed_at": listing.closed_at,
    }


def run_to_dict(run: AgentRun) -> dict:
    return {
        "id": run.id,
        "parent_run_id": run.parent_run_id,
        "agent_id": run.agent_id,
        "token_id": run.token_id,
        "requested_by_wallet_id": run.requested_by_wallet_id,
        "source": run.source,
        "task_input": run.task_input,
        "status": run.status,
        "attempt_count": run.attempt_count,
        "max_attempts": run.max_attempts,
        "timeout_seconds": run.timeout_seconds,
        "celery_task_id": run.celery_task_id,
        "failure_reason": run.failure_reason,
        "output": run.output_json,
        "queued_at": run.queued_at,
        "started_at": run.started_at,
        "finished_at": run.finished_at,
        "next_retry_at": run.next_retry_at,
        "cancel_requested_at": run.cancel_requested_at,
        "dead_lettered_at": run.dead_lettered_at,
    }


def schedule_to_dict(schedule: AgentSchedule) -> dict:
    return {
        "id": schedule.id,
        "agent_id": schedule.agent_id,
        "task_template": schedule.task_template,
        "interval_seconds": schedule.interval_seconds,
        "enabled": schedule.enabled,
        "next_run_at": schedule.next_run_at,
        "last_enqueued_at": schedule.last_enqueued_at,
        "created_at": schedule.created_at,
    }


def transaction_record_to_dict(record: TransactionRecord) -> dict:
    return {
        "id": record.id,
        "entity_type": record.entity_type,
        "entity_id": record.entity_id,
        "tx_hash": record.tx_hash,
        "tx_kind": record.tx_kind,
        "status": record.status,
        "chain_id": record.chain_id,
        "from_address": record.from_address,
        "to_address": record.to_address,
        "payload": record.payload_json,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }


def market_order_event_to_dict(event: MarketOrderEvent) -> dict:
    return {
        "id": event.id,
        "listing_id": event.listing_id,
        "chain_listing_id": event.chain_listing_id,
        "event_type": event.event_type,
        "tx_hash": event.tx_hash,
        "block_number": event.block_number,
        "payload": event.payload_json,
        "created_at": event.created_at,
    }

from __future__ import annotations

from app.core.config import get_settings
from app.db.models import AgentNFT


def normalize_chain_address(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    return normalized or None


def get_nft_sync_mode(nft: AgentNFT) -> str:
    has_chain_mapping = bool(nft.contract_address and nft.chain_token_id)
    if not has_chain_mapping:
        return "LOCAL_ONLY"

    settings = get_settings()
    active_contract = normalize_chain_address(settings.nft_contract_address)
    nft_contract = normalize_chain_address(nft.contract_address)
    if settings.web3_provider_url and active_contract and nft_contract == active_contract:
        return "CHAIN_SYNCED"
    return "CHAIN_MAPPED_INACTIVE"

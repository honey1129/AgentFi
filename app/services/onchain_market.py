from __future__ import annotations

from decimal import Decimal, ROUND_DOWN

from app.core.config import get_settings


AGENT_MARKETPLACE_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint256", "name": "listingId", "type": "uint256"},
            {"indexed": True, "internalType": "address", "name": "seller", "type": "address"},
            {"indexed": True, "internalType": "uint256", "name": "tokenId", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "price", "type": "uint256"},
        ],
        "name": "ListingCreated",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint256", "name": "listingId", "type": "uint256"},
            {"indexed": True, "internalType": "address", "name": "seller", "type": "address"},
            {"indexed": True, "internalType": "uint256", "name": "tokenId", "type": "uint256"},
        ],
        "name": "ListingCancelled",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint256", "name": "listingId", "type": "uint256"},
            {"indexed": True, "internalType": "address", "name": "buyer", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "seller", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "tokenId", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "price", "type": "uint256"},
        ],
        "name": "ListingPurchased",
        "type": "event",
    },
]


def is_market_sync_ready() -> bool:
    settings = get_settings()
    return bool(settings.web3_provider_url and settings.marketplace_contract_address and settings.nft_contract_address)


def wei_to_display_price(price_wei: str, *, decimals: int = 18, precision: str = "0.000001") -> str:
    value = Decimal(price_wei) / (Decimal(10) ** decimals)
    normalized = value.quantize(Decimal(precision), rounding=ROUND_DOWN)
    return format(normalized.normalize(), "f")

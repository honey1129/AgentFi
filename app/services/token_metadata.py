from __future__ import annotations

import html
from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models import Agent, AgentNFT, MarketListing, Wallet
from app.services.nft_modes import get_nft_sync_mode


@dataclass(frozen=True)
class TokenMetadataBundle:
    agent: Agent
    nft: AgentNFT
    owner_wallet: Wallet
    open_listing: MarketListing | None


def build_token_metadata_uri(token_id: str) -> str:
    settings = get_settings()
    return f"{settings.public_base_url}/v1/nfts/{token_id}/metadata"


def build_token_image_uri(token_id: str) -> str:
    settings = get_settings()
    return f"{settings.public_base_url}/v1/nfts/{token_id}/image.svg"


def _clip(value: str, limit: int) -> str:
    trimmed = " ".join(value.strip().split())
    if len(trimmed) <= limit:
        return trimmed
    return f"{trimmed[: limit - 1].rstrip()}..."


def _shorten(value: str | None, *, prefix: int = 6, suffix: int = 4) -> str:
    if not value:
        return "Unavailable"
    if len(value) <= prefix + suffix + 3:
        return value
    return f"{value[:prefix]}...{value[-suffix:]}"


def _format_listing_price(listing: MarketListing | None) -> str:
    if listing is None:
        return "Not listed"
    return f"{listing.price} runtime credits"


async def load_token_metadata_bundle(session: AsyncSession, token_id: str) -> TokenMetadataBundle:
    row = await session.execute(
        select(AgentNFT, Agent, Wallet)
        .join(Agent, Agent.id == AgentNFT.agent_id)
        .join(Wallet, Wallet.id == AgentNFT.owner_wallet_id)
        .where(AgentNFT.token_id == token_id)
    )
    result = row.first()
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NFT not found.")

    nft, agent, owner_wallet = result
    open_listing = await session.scalar(
        select(MarketListing)
        .where(MarketListing.token_id == token_id, MarketListing.status == "OPEN")
        .order_by(MarketListing.opened_at.desc())
    )
    return TokenMetadataBundle(agent=agent, nft=nft, owner_wallet=owner_wallet, open_listing=open_listing)


async def build_nft_metadata_payload(session: AsyncSession, token_id: str) -> dict:
    bundle = await load_token_metadata_bundle(session, token_id)
    sync_mode = get_nft_sync_mode(bundle.nft)
    owner_chain_address = bundle.owner_wallet.chain_address or ""
    owner_display = owner_chain_address or bundle.owner_wallet.name
    description = (
        f"Ownership NFT for the hosted agent '{bundle.agent.name}'. "
        "Holding this token controls execution rights inside the AgentFi runtime."
    )
    if bundle.agent.description:
        description = f"{description}\n\nAgent summary: {_clip(bundle.agent.description, 180)}"

    attributes: list[dict] = [
        {"trait_type": "Agent ID", "value": bundle.agent.id},
        {"trait_type": "Runtime Token ID", "value": bundle.nft.token_id},
        {"trait_type": "Ownership Mode", "value": sync_mode},
        {"trait_type": "Agent Status", "value": bundle.agent.status},
        {"trait_type": "Current Owner", "value": owner_display},
        {"trait_type": "Listing", "value": "OPEN" if bundle.open_listing else "NOT_LISTED"},
    ]
    if owner_chain_address:
        attributes.append({"trait_type": "Owner Address", "value": owner_chain_address})
    if bundle.nft.chain_token_id:
        attributes.append({"trait_type": "Chain Token ID", "value": bundle.nft.chain_token_id})
    if bundle.open_listing:
        attributes.append({"trait_type": "Listing Price", "value": str(bundle.open_listing.price)})
    if bundle.nft.created_at is not None:
        attributes.append(
            {
                "display_type": "date",
                "trait_type": "Created At",
                "value": int(bundle.nft.created_at.timestamp()),
            }
        )

    return {
        "name": f"{bundle.agent.name} Ownership NFT",
        "description": description,
        "image": build_token_image_uri(bundle.nft.token_id),
        "external_url": f"{get_settings().public_base_url}/v1/agents/{bundle.agent.id}",
        "background_color": "0b1220",
        "attributes": attributes,
        "properties": {
            "agent_id": bundle.agent.id,
            "token_id": bundle.nft.token_id,
            "chain_token_id": bundle.nft.chain_token_id,
            "sync_mode": sync_mode,
            "owner_wallet_id": bundle.owner_wallet.id,
            "owner_chain_address": owner_chain_address or None,
            "metadata_uri": bundle.nft.metadata_uri,
        },
    }


async def build_nft_image_svg(session: AsyncSession, token_id: str) -> str:
    bundle = await load_token_metadata_bundle(session, token_id)
    sync_mode = get_nft_sync_mode(bundle.nft)
    owner_label = bundle.owner_wallet.chain_address or bundle.owner_wallet.name
    listing_label = _format_listing_price(bundle.open_listing)
    title = html.escape(_clip(bundle.agent.name, 28))
    description = html.escape(_clip(bundle.agent.description, 120))
    agent_id = html.escape(bundle.agent.id)
    runtime_token_id = html.escape(bundle.nft.token_id)
    chain_token_id = html.escape(bundle.nft.chain_token_id or "Pending")
    owner_display = html.escape(_shorten(owner_label, prefix=10, suffix=6))
    sync_mode_label = html.escape(sync_mode.replace("_", " "))
    listing_display = html.escape(listing_label)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 1200" width="1200" height="1200" role="img" aria-labelledby="title desc">
  <title id="title">{title} Ownership NFT</title>
  <desc id="desc">{description}</desc>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#08111f" />
      <stop offset="55%" stop-color="#123047" />
      <stop offset="100%" stop-color="#1a4d4f" />
    </linearGradient>
    <linearGradient id="panel" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0f1e35" stop-opacity="0.94" />
      <stop offset="100%" stop-color="#132a42" stop-opacity="0.78" />
    </linearGradient>
    <linearGradient id="accent" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#f59e0b" />
      <stop offset="100%" stop-color="#f97316" />
    </linearGradient>
  </defs>
  <rect width="1200" height="1200" fill="url(#bg)" />
  <circle cx="940" cy="220" r="210" fill="#f59e0b" fill-opacity="0.10" />
  <circle cx="1020" cy="910" r="270" fill="#14b8a6" fill-opacity="0.11" />
  <circle cx="180" cy="980" r="220" fill="#38bdf8" fill-opacity="0.10" />
  <rect x="60" y="60" width="1080" height="1080" rx="42" fill="url(#panel)" stroke="rgba(255,255,255,0.14)" />
  <rect x="92" y="96" width="220" height="42" rx="21" fill="rgba(255,255,255,0.08)" />
  <text x="120" y="124" fill="#dbeafe" font-family="Verdana, DejaVu Sans, sans-serif" font-size="24">AgentFi Runtime</text>
  <text x="92" y="240" fill="#f8fafc" font-family="Verdana, DejaVu Sans, sans-serif" font-size="82" font-weight="700">{title}</text>
  <text x="92" y="310" fill="#fdba74" font-family="Courier New, monospace" font-size="28" letter-spacing="2">OWNERSHIP NFT</text>
  <text x="92" y="382" fill="#cbd5e1" font-family="Verdana, DejaVu Sans, sans-serif" font-size="32">{description}</text>

  <rect x="92" y="460" width="476" height="250" rx="28" fill="rgba(255,255,255,0.05)" />
  <text x="126" y="518" fill="#f8fafc" font-family="Verdana, DejaVu Sans, sans-serif" font-size="28">Control Surface</text>
  <text x="126" y="580" fill="#93c5fd" font-family="Courier New, monospace" font-size="23">Agent ID</text>
  <text x="126" y="616" fill="#f8fafc" font-family="Courier New, monospace" font-size="27">{agent_id}</text>
  <text x="126" y="672" fill="#93c5fd" font-family="Courier New, monospace" font-size="23">Runtime Token</text>
  <text x="126" y="708" fill="#f8fafc" font-family="Courier New, monospace" font-size="27">{runtime_token_id}</text>

  <rect x="606" y="460" width="502" height="250" rx="28" fill="rgba(255,255,255,0.05)" />
  <text x="640" y="518" fill="#f8fafc" font-family="Verdana, DejaVu Sans, sans-serif" font-size="28">Chain State</text>
  <text x="640" y="580" fill="#93c5fd" font-family="Courier New, monospace" font-size="23">Sync Mode</text>
  <text x="640" y="616" fill="#f8fafc" font-family="Courier New, monospace" font-size="27">{sync_mode_label}</text>
  <text x="640" y="672" fill="#93c5fd" font-family="Courier New, monospace" font-size="23">Chain Token</text>
  <text x="640" y="708" fill="#f8fafc" font-family="Courier New, monospace" font-size="27">{chain_token_id}</text>

  <rect x="92" y="764" width="1016" height="286" rx="32" fill="rgba(7,13,24,0.40)" />
  <rect x="126" y="808" width="250" height="132" rx="24" fill="rgba(255,255,255,0.05)" />
  <text x="152" y="854" fill="#93c5fd" font-family="Courier New, monospace" font-size="21">Owner</text>
  <text x="152" y="902" fill="#f8fafc" font-family="Courier New, monospace" font-size="26">{owner_display}</text>

  <rect x="410" y="808" width="308" height="132" rx="24" fill="rgba(255,255,255,0.05)" />
  <text x="436" y="854" fill="#93c5fd" font-family="Courier New, monospace" font-size="21">Listing</text>
  <text x="436" y="902" fill="#f8fafc" font-family="Courier New, monospace" font-size="24">{listing_display}</text>

  <rect x="752" y="808" width="322" height="132" rx="24" fill="url(#accent)" fill-opacity="0.22" stroke="rgba(255,255,255,0.12)" />
  <text x="778" y="854" fill="#fed7aa" font-family="Courier New, monospace" font-size="21">Token URI</text>
  <text x="778" y="902" fill="#fff7ed" font-family="Verdana, DejaVu Sans, sans-serif" font-size="22">Dynamic metadata + SVG</text>

  <path d="M918 210C980 270 1032 337 1076 412" stroke="#fff7ed" stroke-opacity="0.20" stroke-width="4" stroke-linecap="round" />
  <path d="M930 252C1002 312 1060 395 1098 486" stroke="#fdba74" stroke-opacity="0.45" stroke-width="10" stroke-linecap="round" />
</svg>
"""

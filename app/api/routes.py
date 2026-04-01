from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_bearer_token, require_authenticated_wallet
from app.core.config import get_settings
from app.db.models import Wallet
from app.db.session import get_session
from app.runtime.ownership_cache import OwnershipCache
from app.runtime.redis_client import get_redis
from app.schemas.api import (
    AgentCreateRequest,
    AgentScheduleCreateRequest,
    AgentRunRequest,
    ListingBuyRequest,
    ListingCreateRequest,
    MetaMaskChallengeRequest,
    MetaMaskVerifyRequest,
    NFTTransferRequest,
    WalletConnectRequest,
    WalletCreateRequest,
)
from app.services.auth import MetaMaskAuthService, ensure_valid_chain_address
from app.services.chain_runtime import ChainRuntimeService
from app.services.onchain_market import is_market_sync_ready
from app.services.rate_limit import enforce_rate_limit
from app.services.runtime import (
    AgentService,
    MarketplaceService,
    RunService,
    ScheduleService,
    WalletService,
    load_agent_bundle,
    normalize_chain_address,
)
from app.services.serializers import nft_to_dict, wallet_to_dict
from app.services.token_metadata import build_nft_image_svg, build_nft_metadata_payload


router = APIRouter()


def _assert_authenticated_wallet(auth_wallet: Wallet, expected_wallet_id: str, detail: str) -> None:
    if auth_wallet.id != expected_wallet_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


async def _assert_agent_owner(session: AsyncSession, agent_id: str, wallet_id: str) -> None:
    redis = await get_redis()
    agent, nft = await load_agent_bundle(session, agent_id)
    owner_wallet_id = await OwnershipCache(redis).get_owner_wallet_id(
        session,
        agent_id=agent.id,
        token_id=nft.token_id,
    )
    if owner_wallet_id != wallet_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the current NFT owner can schedule this agent.",
        )


def _request_fingerprint(request: Request) -> str:
    return request.client.host if request.client and request.client.host else "unknown"


async def _enforce_auth_limit(redis, request: Request, action: str, subject: str) -> None:
    settings = get_settings()
    await enforce_rate_limit(
        redis,
        namespace=f"auth:{action}",
        subject=f"{_request_fingerprint(request)}:{subject}",
        limit=settings.auth_challenge_rate_limit if action == "challenge" else settings.auth_verify_rate_limit,
        window_seconds=settings.auth_rate_limit_window_seconds,
    )


async def _enforce_mutation_limit(redis, action: str, wallet: Wallet) -> None:
    settings = get_settings()
    await enforce_rate_limit(
        redis,
        namespace=f"mutation:{action}",
        subject=wallet.id,
        limit=settings.mutation_rate_limit_per_wallet,
        window_seconds=settings.mutation_rate_limit_window_seconds,
    )


@router.get("/health")
async def healthcheck() -> dict:
    return {"status": "ok"}


@router.get("/runtime/config")
async def get_runtime_config() -> dict:
    settings = get_settings()
    chain = ChainRuntimeService.inspect_runtime_chain()
    return {
        "app_name": settings.app_name,
        "chain_sync_state": chain["status"],
        "chain_sync_enabled": chain["chain_sync_enabled"],
        "auto_onchain_mint_enabled": bool(chain["chain_sync_enabled"] and settings.nft_minter_private_key),
        "nft_contract_address": settings.nft_contract_address or None,
        "marketplace_contract_address": settings.marketplace_contract_address or None,
        "nft_minter_configured": bool(settings.nft_minter_private_key),
        "market_sync_enabled": is_market_sync_ready(),
        "market_sync_state": "READY" if is_market_sync_ready() else "DISABLED",
        "public_base_url": settings.public_base_url,
        "web3_provider_configured": bool(settings.web3_provider_url),
        "metamask_auth_required": True,
        "chain": chain,
    }


@router.post("/wallets")
async def create_wallet(payload: WalletCreateRequest, session: AsyncSession = Depends(get_session)) -> dict:
    return await WalletService.create_wallet(
        session,
        name=payload.name,
        initial_balance=payload.initial_balance,
        chain_address=payload.chain_address,
    )


@router.get("/wallets")
async def list_wallets(session: AsyncSession = Depends(get_session)) -> list[dict]:
    return await WalletService.list_wallets(session)


@router.post("/auth/metamask/challenge")
async def create_metamask_challenge(payload: MetaMaskChallengeRequest, request: Request) -> dict:
    redis = await get_redis()
    await _enforce_auth_limit(redis, request, "challenge", payload.chain_address)
    return await MetaMaskAuthService.create_challenge(
        redis,
        chain_address=payload.chain_address,
        chain_id=payload.chain_id,
        initial_balance=payload.initial_balance,
        label=payload.label,
    )


@router.post("/auth/metamask/verify")
async def verify_metamask_signature(
    payload: MetaMaskVerifyRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict:
    redis = await get_redis()
    await _enforce_auth_limit(redis, request, "verify", payload.chain_address)
    return await MetaMaskAuthService.verify_signature(
        session,
        redis,
        chain_address=payload.chain_address,
        signature=payload.signature,
    )


@router.get("/auth/me")
async def get_authenticated_wallet(auth_wallet: Wallet = Depends(require_authenticated_wallet)) -> dict:
    return wallet_to_dict(auth_wallet)


@router.post("/auth/logout")
async def logout_metamask(session_token: str = Depends(get_bearer_token)) -> dict:
    redis = await get_redis()
    await MetaMaskAuthService.revoke_session(redis, session_token)
    return {"status": "ok"}


@router.post("/wallets/connect")
async def connect_wallet(
    payload: WalletConnectRequest,
    session: AsyncSession = Depends(get_session),
    auth_wallet: Wallet = Depends(require_authenticated_wallet),
) -> dict:
    redis = await get_redis()
    await _enforce_mutation_limit(redis, "wallet-connect", auth_wallet)
    if normalize_chain_address(auth_wallet.chain_address) != ensure_valid_chain_address(payload.chain_address):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authenticated MetaMask wallet does not match the requested chain address.",
        )
    return await WalletService.connect_wallet(
        session,
        chain_address=payload.chain_address,
        initial_balance=payload.initial_balance,
        label=payload.label,
    )


@router.get("/wallets/{wallet_id}")
async def get_wallet(wallet_id: str, session: AsyncSession = Depends(get_session)) -> dict:
    wallet = await WalletService.get_wallet(session, wallet_id)
    return wallet_to_dict(wallet)


@router.post("/agents")
async def create_agent(
    payload: AgentCreateRequest,
    session: AsyncSession = Depends(get_session),
    auth_wallet: Wallet = Depends(require_authenticated_wallet),
) -> dict:
    owner_wallet_id = payload.owner_wallet_id or auth_wallet.id
    redis = await get_redis()
    await _enforce_mutation_limit(redis, "create-agent", auth_wallet)
    _assert_authenticated_wallet(
        auth_wallet,
        owner_wallet_id,
        "Authenticated MetaMask wallet must be the owner wallet when creating an agent.",
    )
    return await AgentService.create_agent(
        session,
        redis,
        name=payload.name,
        description=payload.description,
        system_prompt=payload.system_prompt,
        owner_wallet_id=owner_wallet_id,
        seed_memory=payload.seed_memory,
        contract_address=payload.contract_address,
        chain_token_id=payload.chain_token_id,
    )


@router.get("/agents")
async def list_agents(
    tradeable_only: bool = Query(default=False),
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    return await AgentService.list_agents(session, only_tradeable=tradeable_only)


@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str, session: AsyncSession = Depends(get_session)) -> dict:
    return await AgentService.get_agent(session, agent_id)


@router.post("/agents/{agent_id}/run")
async def run_agent(
    payload: AgentRunRequest,
    agent_id: str,
    session: AsyncSession = Depends(get_session),
    auth_wallet: Wallet = Depends(require_authenticated_wallet),
) -> dict:
    wallet_id = payload.wallet_id or auth_wallet.id
    redis = await get_redis()
    await _enforce_mutation_limit(redis, "queue-run", auth_wallet)
    _assert_authenticated_wallet(
        auth_wallet,
        wallet_id,
        "Authenticated MetaMask wallet must match the owner wallet used to dispatch this agent.",
    )
    return await RunService.queue_manual_run(
        session,
        redis,
        agent_id=agent_id,
        wallet_id=wallet_id,
        task=payload.task,
        max_attempts=payload.max_attempts,
        timeout_seconds=payload.timeout_seconds,
    )


@router.get("/agents/{agent_id}/runs")
async def list_agent_runs(
    agent_id: str,
    status_filter: str | None = Query(default=None),
    dead_letter_only: bool = Query(default=False),
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    return await RunService.list_runs(
        session,
        agent_id=agent_id,
        status_filter=status_filter,
        dead_letter_only=dead_letter_only,
    )


@router.get("/runs")
async def list_runs(
    status_filter: str | None = Query(default=None),
    dead_letter_only: bool = Query(default=False),
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    return await RunService.list_runs(
        session,
        status_filter=status_filter,
        dead_letter_only=dead_letter_only,
    )


@router.get("/runs/metrics")
async def get_run_metrics(session: AsyncSession = Depends(get_session)) -> dict:
    redis = await get_redis()
    return await RunService.get_metrics(session, redis)

@router.get("/runs/{run_id}")
async def get_run(run_id: str, session: AsyncSession = Depends(get_session)) -> dict:
    return await RunService.get_run(session, run_id)


@router.post("/runs/{run_id}/retry")
async def retry_run(
    run_id: str,
    session: AsyncSession = Depends(get_session),
    auth_wallet: Wallet = Depends(require_authenticated_wallet),
) -> dict:
    redis = await get_redis()
    await _enforce_mutation_limit(redis, "retry-run", auth_wallet)
    return await RunService.retry_run(session, redis, run_id=run_id, wallet_id=auth_wallet.id)


@router.post("/runs/{run_id}/cancel")
async def cancel_run(
    run_id: str,
    session: AsyncSession = Depends(get_session),
    auth_wallet: Wallet = Depends(require_authenticated_wallet),
) -> dict:
    redis = await get_redis()
    await _enforce_mutation_limit(redis, "cancel-run", auth_wallet)
    return await RunService.cancel_run(session, redis, run_id=run_id, wallet_id=auth_wallet.id)


@router.get("/runtime/logs")
async def get_runtime_logs(
    limit: int = Query(default=50, ge=1, le=500),
) -> list[dict]:
    redis = await get_redis()
    return await RunService.list_runtime_logs(redis, limit=limit)


@router.get("/nfts")
async def list_nfts(session: AsyncSession = Depends(get_session)) -> list[dict]:
    return await AgentService.list_nfts(session)


@router.get("/nfts/{token_id}")
async def get_nft(token_id: str, session: AsyncSession = Depends(get_session)) -> dict:
    nft = await AgentService.get_nft(session, token_id)
    metadata = await build_nft_metadata_payload(session, token_id)
    return {**metadata, **nft_to_dict(nft)}


@router.get("/nfts/{token_id}/metadata")
async def get_nft_metadata(token_id: str, session: AsyncSession = Depends(get_session)) -> JSONResponse:
    metadata = await build_nft_metadata_payload(session, token_id)
    return JSONResponse(content=metadata, headers={"Cache-Control": "public, max-age=60"})


@router.get("/nfts/{token_id}/image.svg")
async def get_nft_image(token_id: str, session: AsyncSession = Depends(get_session)) -> Response:
    svg = await build_nft_image_svg(session, token_id)
    return Response(
        content=svg,
        media_type="image/svg+xml",
        headers={"Cache-Control": "public, max-age=60"},
    )


@router.post("/nfts/{token_id}/transfer")
async def transfer_nft(
    payload: NFTTransferRequest,
    token_id: str,
    session: AsyncSession = Depends(get_session),
    auth_wallet: Wallet = Depends(require_authenticated_wallet),
) -> dict:
    from_wallet_id = payload.from_wallet_id or auth_wallet.id
    redis = await get_redis()
    await _enforce_mutation_limit(redis, "transfer-nft", auth_wallet)
    _assert_authenticated_wallet(
        auth_wallet,
        from_wallet_id,
        "Authenticated MetaMask wallet must match the sender wallet for NFT transfers.",
    )
    return await MarketplaceService.transfer_nft(
        session,
        redis,
        token_id=token_id,
        from_wallet_id=from_wallet_id,
        to_wallet_id=payload.to_wallet_id,
        to_chain_address=payload.to_chain_address,
    )


@router.post("/listings")
async def create_listing(
    payload: ListingCreateRequest,
    session: AsyncSession = Depends(get_session),
    auth_wallet: Wallet = Depends(require_authenticated_wallet),
) -> dict:
    seller_wallet_id = payload.seller_wallet_id or auth_wallet.id
    redis = await get_redis()
    await _enforce_mutation_limit(redis, "create-listing", auth_wallet)
    _assert_authenticated_wallet(
        auth_wallet,
        seller_wallet_id,
        "Authenticated MetaMask wallet must match the seller wallet for listing creation.",
    )
    return await MarketplaceService.create_listing(
        session,
        redis,
        token_id=payload.token_id,
        seller_wallet_id=seller_wallet_id,
        price=payload.price,
    )


@router.get("/listings")
async def list_listings(
    status_filter: str = Query(default="OPEN"),
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    return await MarketplaceService.list_listings(session, status_filter=status_filter)


@router.get("/listings/{listing_id}")
async def get_listing(listing_id: str, session: AsyncSession = Depends(get_session)) -> dict:
    return await MarketplaceService.get_listing(session, listing_id)


@router.get("/listings/{listing_id}/events")
async def get_listing_events(listing_id: str, session: AsyncSession = Depends(get_session)) -> list[dict]:
    return await MarketplaceService.list_listing_events(session, listing_id)


@router.get("/listings/{listing_id}/transactions")
async def get_listing_transactions(listing_id: str, session: AsyncSession = Depends(get_session)) -> list[dict]:
    return await MarketplaceService.list_listing_transactions(session, listing_id)


@router.post("/listings/{listing_id}/buy")
async def buy_listing(
    payload: ListingBuyRequest,
    listing_id: str,
    session: AsyncSession = Depends(get_session),
    auth_wallet: Wallet = Depends(require_authenticated_wallet),
) -> dict:
    buyer_wallet_id = payload.buyer_wallet_id or auth_wallet.id
    redis = await get_redis()
    await _enforce_mutation_limit(redis, "buy-listing", auth_wallet)
    _assert_authenticated_wallet(
        auth_wallet,
        buyer_wallet_id,
        "Authenticated MetaMask wallet must match the buyer wallet for purchases.",
    )
    return await MarketplaceService.buy_listing(session, redis, listing_id=listing_id, buyer_wallet_id=buyer_wallet_id)


@router.post("/listings/{listing_id}/cancel")
async def cancel_listing(
    listing_id: str,
    session: AsyncSession = Depends(get_session),
    auth_wallet: Wallet = Depends(require_authenticated_wallet),
) -> dict:
    redis = await get_redis()
    await _enforce_mutation_limit(redis, "cancel-listing", auth_wallet)
    return await MarketplaceService.cancel_listing(session, redis, listing_id=listing_id, seller_wallet_id=auth_wallet.id)


@router.post("/agent-schedules")
async def create_agent_schedule(
    payload: AgentScheduleCreateRequest,
    session: AsyncSession = Depends(get_session),
    auth_wallet: Wallet = Depends(require_authenticated_wallet),
) -> dict:
    redis = await get_redis()
    await _enforce_mutation_limit(redis, "create-schedule", auth_wallet)
    await _assert_agent_owner(session, payload.agent_id, auth_wallet.id)
    return await ScheduleService.create_schedule(
        session,
        agent_id=payload.agent_id,
        task=payload.task,
        interval_seconds=payload.interval_seconds,
        starts_in_seconds=payload.starts_in_seconds,
    )


@router.get("/agent-schedules")
async def list_agent_schedules(session: AsyncSession = Depends(get_session)) -> list[dict]:
    return await ScheduleService.list_schedules(session)

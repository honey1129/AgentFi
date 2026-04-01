from __future__ import annotations

import asyncio
from datetime import timedelta
from decimal import Decimal

from fastapi import HTTPException, status
from redis.asyncio import Redis
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from web3 import Web3

from app.core.config import get_settings
from app.core.logging import get_logger, log_event
from app.core.utils import new_id, utcnow
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
from app.db.session import SessionLocal
from app.runtime.events import emit_runtime_event
from app.runtime.executor import RuntimeExecutionError, build_executor
from app.runtime.locks import AgentLockManager
from app.runtime.ownership_cache import OwnershipCache
from app.runtime.redis_client import init_redis
from app.services.nft_modes import get_nft_sync_mode
from app.services.onchain_nft import OnchainMintError, build_metadata_uri, is_runtime_mint_ready, mint_agent_ownership_nft
from app.services.serializers import (
    agent_to_dict,
    listing_to_dict,
    market_order_event_to_dict,
    nft_to_dict,
    run_to_dict,
    schedule_to_dict,
    transaction_record_to_dict,
    wallet_to_dict,
)


logger = get_logger("agentfi.runtime")


def normalize_chain_address(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    return normalized or None


def ensure_valid_chain_address(value: str | None) -> str:
    normalized = normalize_chain_address(value)
    if normalized is None or not Web3.is_address(normalized):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid chain address.")
    return normalized


async def load_agent_bundle(session: AsyncSession, agent_id: str) -> tuple[Agent, AgentNFT]:
    row = await session.execute(
        select(Agent, AgentNFT).join(AgentNFT, AgentNFT.agent_id == Agent.id).where(Agent.id == agent_id)
    )
    result = row.first()
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found.")
    return result


async def load_listing_chain_state(session: AsyncSession, listing_id: str) -> MarketListingChainState | None:
    return await session.scalar(
        select(MarketListingChainState).where(MarketListingChainState.listing_id == listing_id)
    )


async def load_listing_chain_states(
    session: AsyncSession,
    listing_ids: list[str],
) -> dict[str, MarketListingChainState]:
    if not listing_ids:
        return {}
    chain_states = (
        await session.scalars(
            select(MarketListingChainState).where(MarketListingChainState.listing_id.in_(listing_ids))
        )
    ).all()
    return {state.listing_id: state for state in chain_states}


class WalletService:
    @staticmethod
    async def _validate_wallet_name_uniqueness(
        session: AsyncSession,
        *,
        name: str,
        ignore_wallet_id: str | None = None,
    ) -> None:
        existing = await session.scalar(select(Wallet).where(Wallet.name == name))
        if existing is not None and existing.id != ignore_wallet_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Wallet name already exists.")

    @staticmethod
    def _default_wallet_label(chain_address: str) -> str:
        return f"metamask_{chain_address[:10]}"

    @staticmethod
    async def create_wallet(
        session: AsyncSession,
        *,
        name: str,
        initial_balance: Decimal,
        chain_address: str | None = None,
    ) -> dict:
        normalized_address = ensure_valid_chain_address(chain_address) if chain_address is not None else None
        await WalletService._validate_wallet_name_uniqueness(session, name=name)

        if normalized_address:
            existing_address = await session.scalar(select(Wallet).where(Wallet.chain_address == normalized_address))
            if existing_address is not None:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Wallet chain address already exists.")

        wallet = Wallet(
            id=new_id("wallet"),
            name=name,
            chain_address=normalized_address,
            balance=initial_balance,
        )
        session.add(wallet)
        await session.commit()
        await session.refresh(wallet)
        return wallet_to_dict(wallet)

    @staticmethod
    async def connect_wallet(
        session: AsyncSession,
        *,
        chain_address: str,
        initial_balance: Decimal = Decimal("0"),
        label: str | None = None,
    ) -> dict:
        normalized_address = ensure_valid_chain_address(chain_address)

        wallet = await session.scalar(select(Wallet).where(Wallet.chain_address == normalized_address))
        if wallet is not None:
            if label and label != wallet.name:
                await WalletService._validate_wallet_name_uniqueness(session, name=label, ignore_wallet_id=wallet.id)
                wallet.name = label
                await session.commit()
                await session.refresh(wallet)
            return wallet_to_dict(wallet)

        wallet_name = label or WalletService._default_wallet_label(normalized_address)
        await WalletService._validate_wallet_name_uniqueness(session, name=wallet_name)
        wallet = Wallet(
            id=new_id("wallet"),
            name=wallet_name,
            chain_address=normalized_address,
            balance=initial_balance,
        )
        session.add(wallet)
        await session.commit()
        await session.refresh(wallet)
        return wallet_to_dict(wallet)

    @staticmethod
    async def list_wallets(session: AsyncSession) -> list[dict]:
        wallets = (await session.scalars(select(Wallet).order_by(Wallet.created_at.desc()))).all()
        return [wallet_to_dict(wallet) for wallet in wallets]

    @staticmethod
    async def get_wallet(session: AsyncSession, wallet_id: str) -> Wallet:
        wallet = await session.get(Wallet, wallet_id)
        if wallet is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found.")
        return wallet

    @staticmethod
    async def get_or_create_chain_wallet(session: AsyncSession, chain_address: str) -> Wallet:
        normalized_address = ensure_valid_chain_address(chain_address)

        wallet = await session.scalar(select(Wallet).where(Wallet.chain_address == normalized_address))
        if wallet is not None:
            return wallet

        wallet = Wallet(
            id=new_id("wallet"),
            name=f"chain_{normalized_address}",
            chain_address=normalized_address,
            balance=Decimal("0"),
        )
        session.add(wallet)
        await session.flush()
        return wallet


class AgentService:
    @staticmethod
    async def create_agent(
        session: AsyncSession,
        redis: Redis,
        *,
        name: str,
        description: str,
        system_prompt: str,
        owner_wallet_id: str,
        seed_memory: list[dict],
        contract_address: str | None = None,
        chain_token_id: str | None = None,
    ) -> dict:
        owner = await WalletService.get_wallet(session, owner_wallet_id)
        settings = get_settings()
        explicit_contract = ensure_valid_chain_address(contract_address) if contract_address else None
        default_contract = ensure_valid_chain_address(settings.nft_contract_address) if settings.nft_contract_address else None
        resolved_contract = explicit_contract or default_contract or None

        agent = Agent(
            id=new_id("agent"),
            name=name,
            description=description,
            system_prompt=system_prompt,
            memory_json=seed_memory,
        )
        token_id = new_id("nft")
        resolved_chain_token_id = chain_token_id
        metadata_uri = build_metadata_uri(token_id)
        mint_result = None

        if resolved_chain_token_id is None and is_runtime_mint_ready(resolved_contract):
            if owner.chain_address is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Owner wallet needs a chain address for on-chain mint.",
                )
            try:
                mint_result = await asyncio.to_thread(
                    mint_agent_ownership_nft,
                    contract_address=resolved_contract,
                    owner_chain_address=owner.chain_address,
                    runtime_token_id=token_id,
                )
            except OnchainMintError as exc:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"On-chain mint failed: {exc}",
                ) from exc
            resolved_contract = mint_result.contract_address
            resolved_chain_token_id = mint_result.chain_token_id
            metadata_uri = mint_result.metadata_uri

        if resolved_chain_token_id is not None and resolved_contract is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contract address is required when binding an existing chain token.",
            )

        contract_address_for_record = resolved_contract if (resolved_chain_token_id or explicit_contract or mint_result) else None
        nft = AgentNFT(
            token_id=token_id,
            agent=agent,
            owner_wallet_id=owner.id,
            contract_address=contract_address_for_record,
            chain_token_id=resolved_chain_token_id,
            metadata_uri=metadata_uri,
            last_synced_tx_hash=mint_result.tx_hash if mint_result else None,
            last_synced_block=mint_result.block_number if mint_result else None,
            last_transfer_at=utcnow(),
        )
        session.add_all([agent, nft])
        await session.commit()
        await session.refresh(agent)
        await session.refresh(nft)

        ownership_cache = OwnershipCache(redis)
        await ownership_cache.set_owner_wallet_id(agent_id=agent.id, token_id=nft.token_id, owner_wallet_id=owner.id)
        await emit_runtime_event(
            redis,
            "agent_created",
            {"agent_id": agent.id, "token_id": nft.token_id, "owner_wallet_id": owner.id},
        )
        return agent_to_dict(agent, nft)

    @staticmethod
    async def list_agents(session: AsyncSession, only_tradeable: bool = False) -> list[dict]:
        stmt: Select[tuple[Agent, AgentNFT]] = (
            select(Agent, AgentNFT)
            .join(AgentNFT, AgentNFT.agent_id == Agent.id)
            .order_by(Agent.created_at.desc())
        )
        pairs = (await session.execute(stmt)).all()
        results: list[dict] = []
        for agent, nft in pairs:
            active_listing = await session.scalar(
                select(MarketListing)
                .where(MarketListing.token_id == nft.token_id, MarketListing.status == "OPEN")
                .order_by(MarketListing.opened_at.desc())
            )
            active_listing_chain_state = None
            if active_listing is not None:
                active_listing_chain_state = await load_listing_chain_state(session, active_listing.id)
            if only_tradeable and active_listing is None:
                continue
            results.append(agent_to_dict(agent, nft, active_listing, active_listing_chain_state))
        return results

    @staticmethod
    async def get_agent(session: AsyncSession, agent_id: str) -> dict:
        agent, nft = await load_agent_bundle(session, agent_id)
        active_listing = await session.scalar(
            select(MarketListing).where(MarketListing.token_id == nft.token_id, MarketListing.status == "OPEN")
        )
        active_listing_chain_state = None
        if active_listing is not None:
            active_listing_chain_state = await load_listing_chain_state(session, active_listing.id)
        return agent_to_dict(agent, nft, active_listing, active_listing_chain_state)

    @staticmethod
    async def list_nfts(session: AsyncSession) -> list[dict]:
        nfts = (await session.scalars(select(AgentNFT).order_by(AgentNFT.created_at.desc()))).all()
        return [nft_to_dict(nft) for nft in nfts]

    @staticmethod
    async def get_nft(session: AsyncSession, token_id: str) -> AgentNFT:
        nft = await session.get(AgentNFT, token_id)
        if nft is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NFT not found.")
        return nft


class RunService:
    ACTIVE_STATUSES = {"QUEUED", "RUNNING", "CANCEL_REQUESTED"}
    TERMINAL_STATUSES = {"COMPLETED", "FAILED", "TIMED_OUT", "CANCELLED"}

    @staticmethod
    def _resolve_run_timeout(timeout_seconds: int | None = None) -> int:
        settings = get_settings()
        return max(int(timeout_seconds or settings.run_default_timeout_seconds), 1)

    @staticmethod
    def _resolve_run_attempts(max_attempts: int | None = None) -> int:
        settings = get_settings()
        return max(int(max_attempts or settings.run_default_max_attempts), 1)

    @staticmethod
    async def queue_manual_run(
        session: AsyncSession,
        redis: Redis,
        *,
        agent_id: str,
        wallet_id: str,
        task: str,
        max_attempts: int | None = None,
        timeout_seconds: int | None = None,
    ) -> dict:
        requester = await WalletService.get_wallet(session, wallet_id)
        agent, nft = await load_agent_bundle(session, agent_id)
        ownership_cache = OwnershipCache(redis)
        owner_wallet_id = await ownership_cache.get_owner_wallet_id(session, agent_id=agent.id, token_id=nft.token_id)
        if owner_wallet_id != requester.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the current NFT owner can dispatch this agent.",
            )
        return await RunService._create_and_dispatch_run(
            session,
            redis,
            agent=agent,
            nft=nft,
            requested_by_wallet_id=requester.id,
            task=task,
            source="MANUAL",
            max_attempts=max_attempts,
            timeout_seconds=timeout_seconds,
        )

    @staticmethod
    async def queue_owner_run(
        session: AsyncSession,
        redis: Redis,
        *,
        agent_id: str,
        task: str,
        source: str,
        max_attempts: int | None = None,
        timeout_seconds: int | None = None,
    ) -> dict:
        agent, nft = await load_agent_bundle(session, agent_id)
        ownership_cache = OwnershipCache(redis)
        owner_wallet_id = await ownership_cache.get_owner_wallet_id(session, agent_id=agent.id, token_id=nft.token_id)
        return await RunService._create_and_dispatch_run(
            session,
            redis,
            agent=agent,
            nft=nft,
            requested_by_wallet_id=owner_wallet_id,
            task=task,
            source=source,
            max_attempts=max_attempts,
            timeout_seconds=timeout_seconds,
        )

    @staticmethod
    async def _create_and_dispatch_run(
        session: AsyncSession,
        redis: Redis,
        *,
        agent: Agent,
        nft: AgentNFT,
        requested_by_wallet_id: str,
        task: str,
        source: str,
        max_attempts: int | None = None,
        timeout_seconds: int | None = None,
        parent_run_id: str | None = None,
    ) -> dict:
        run = AgentRun(
            id=new_id("run"),
            parent_run_id=parent_run_id,
            agent_id=agent.id,
            token_id=nft.token_id,
            requested_by_wallet_id=requested_by_wallet_id,
            task_input=task,
            source=source,
            status="QUEUED",
            attempt_count=0,
            max_attempts=RunService._resolve_run_attempts(max_attempts),
            timeout_seconds=RunService._resolve_run_timeout(timeout_seconds),
            queued_at=utcnow(),
        )
        session.add(run)
        await session.commit()
        await session.refresh(run)

        log_event(
            logger,
            "run_queued",
            run_id=run.id,
            agent_id=agent.id,
            requested_by_wallet_id=requested_by_wallet_id,
            source=source,
            max_attempts=run.max_attempts,
            timeout_seconds=run.timeout_seconds,
            parent_run_id=parent_run_id,
        )
        await emit_runtime_event(
            redis,
            "agent_run_queued",
            {"agent_id": agent.id, "run_id": run.id, "requested_by_wallet_id": requested_by_wallet_id, "source": source},
        )
        await RunService._dispatch_run_task(session, redis, run)
        return run_to_dict(run)

    @staticmethod
    async def _dispatch_run_task(
        session: AsyncSession,
        redis: Redis,
        run: AgentRun,
        *,
        countdown: int = 0,
    ) -> None:
        from app.tasks.agent_tasks import execute_agent_run_task

        try:
            if countdown and countdown > 0:
                task = execute_agent_run_task.apply_async(args=[run.id], countdown=countdown)
                run.next_retry_at = utcnow() + timedelta(seconds=countdown)
            else:
                task = execute_agent_run_task.delay(run.id)
                run.next_retry_at = None
            run.celery_task_id = task.id
            await session.commit()
            log_event(
                logger,
                "run_dispatched",
                run_id=run.id,
                celery_task_id=run.celery_task_id,
                countdown=countdown,
                next_retry_at=run.next_retry_at,
            )
        except Exception as exc:
            await RunService._mark_failed(session, redis, run, f"Queue dispatch failed: {exc}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to enqueue run to Celery.",
            ) from exc

    @staticmethod
    async def get_run(session: AsyncSession, run_id: str) -> dict:
        run = await session.get(AgentRun, run_id)
        if run is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found.")
        return run_to_dict(run)

    @staticmethod
    async def list_runs(
        session: AsyncSession,
        agent_id: str | None = None,
        *,
        status_filter: str | None = None,
        dead_letter_only: bool = False,
    ) -> list[dict]:
        stmt = select(AgentRun).order_by(AgentRun.queued_at.desc())
        if agent_id:
            stmt = stmt.where(AgentRun.agent_id == agent_id)
        if status_filter:
            stmt = stmt.where(AgentRun.status == status_filter)
        if dead_letter_only:
            stmt = stmt.where(AgentRun.dead_lettered_at.is_not(None))
        runs = (await session.scalars(stmt)).all()
        return [run_to_dict(run) for run in runs]

    @staticmethod
    async def execute_queued_run(run_id: str) -> None:
        redis = await init_redis()
        async with SessionLocal() as session:
            row = await session.execute(
                select(AgentRun, Agent, AgentNFT, Wallet)
                .join(Agent, Agent.id == AgentRun.agent_id)
                .join(AgentNFT, AgentNFT.token_id == AgentRun.token_id)
                .join(Wallet, Wallet.id == AgentRun.requested_by_wallet_id)
                .where(AgentRun.id == run_id)
            )
            result = row.first()
            if result is None:
                return

            run, agent, nft, requester = result
            if run.status not in RunService.ACTIVE_STATUSES:
                return
            if run.status == "CANCEL_REQUESTED":
                await RunService._mark_cancelled(session, redis, run, "Cancellation requested before execution started.")
                return

            ownership_cache = OwnershipCache(redis)
            current_owner_wallet_id = await ownership_cache.get_owner_wallet_id(
                session,
                agent_id=agent.id,
                token_id=nft.token_id,
            )
            if current_owner_wallet_id != requester.id:
                await RunService._mark_failed(
                    session,
                    redis,
                    run,
                    "Ownership changed before execution started.",
                )
                return

            attempt_number = run.attempt_count + 1
            lock_manager = AgentLockManager(redis)
            lock_value = await lock_manager.acquire(agent.id)
            if lock_value is None:
                run.attempt_count = attempt_number
                await RunService._handle_retryable_failure(
                    session,
                    redis,
                    run,
                    "Agent is busy.",
                    terminal_status="FAILED",
                )
                return

            run.status = "RUNNING"
            run.attempt_count = attempt_number
            run.started_at = utcnow()
            run.finished_at = None
            run.failure_reason = None
            run.next_retry_at = None
            await session.commit()
            log_event(
                logger,
                "run_started",
                run_id=run.id,
                agent_id=agent.id,
                requested_by_wallet_id=requester.id,
                attempt_count=run.attempt_count,
                timeout_seconds=run.timeout_seconds,
            )
            await emit_runtime_event(
                redis,
                "agent_run_started",
                {"agent_id": agent.id, "run_id": run.id, "attempt_count": run.attempt_count},
            )

            executor = build_executor()
            try:
                output = await asyncio.wait_for(
                    executor.execute(agent=agent, nft=nft, owner=requester, task=run.task_input),
                    timeout=run.timeout_seconds,
                )
                await session.refresh(run)
                if run.cancel_requested_at is not None or run.status == "CANCEL_REQUESTED":
                    await RunService._mark_cancelled(session, redis, run, "Run was cancelled while executing.")
                    return
                agent.memory_json = [
                    *agent.memory_json,
                    {"task": run.task_input, "output": output, "at": utcnow().isoformat()},
                ][-20:]
                run.output_json = output
                run.status = "COMPLETED"
                run.failure_reason = None
                run.finished_at = utcnow()
                await session.commit()
                log_event(
                    logger,
                    "run_completed",
                    run_id=run.id,
                    agent_id=agent.id,
                    attempt_count=run.attempt_count,
                    finished_at=run.finished_at,
                )
                await emit_runtime_event(
                    redis,
                    "agent_run_completed",
                    {"agent_id": agent.id, "run_id": run.id, "requested_by_wallet_id": requester.id},
                )
            except asyncio.TimeoutError:
                await session.refresh(run)
                await RunService._handle_retryable_failure(
                    session,
                    redis,
                    run,
                    f"Run exceeded timeout of {run.timeout_seconds} seconds.",
                    terminal_status="TIMED_OUT",
                )
            except RuntimeExecutionError as exc:
                await session.refresh(run)
                await RunService._handle_retryable_failure(
                    session,
                    redis,
                    run,
                    str(exc),
                    terminal_status="FAILED",
                )
            except Exception as exc:
                await session.refresh(run)
                await RunService._handle_retryable_failure(
                    session,
                    redis,
                    run,
                    f"Unhandled runtime failure: {exc}",
                    terminal_status="FAILED",
                )
            finally:
                await lock_manager.release(agent.id, lock_value)

    @staticmethod
    async def retry_run(session: AsyncSession, redis: Redis, *, run_id: str, wallet_id: str) -> dict:
        original = await session.get(AgentRun, run_id)
        if original is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found.")
        if original.status not in RunService.TERMINAL_STATUSES:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only terminal runs can be retried.")

        agent, nft = await load_agent_bundle(session, original.agent_id)
        ownership_cache = OwnershipCache(redis)
        owner_wallet_id = await ownership_cache.get_owner_wallet_id(session, agent_id=agent.id, token_id=nft.token_id)
        if owner_wallet_id != wallet_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the current NFT owner can retry this run.",
            )

        return await RunService._create_and_dispatch_run(
            session,
            redis,
            agent=agent,
            nft=nft,
            requested_by_wallet_id=wallet_id,
            task=original.task_input,
            source="RETRY",
            max_attempts=original.max_attempts,
            timeout_seconds=original.timeout_seconds,
            parent_run_id=original.id,
        )

    @staticmethod
    async def cancel_run(session: AsyncSession, redis: Redis, *, run_id: str, wallet_id: str) -> dict:
        row = await session.execute(
            select(AgentRun, AgentNFT)
            .join(AgentNFT, AgentNFT.token_id == AgentRun.token_id)
            .where(AgentRun.id == run_id)
        )
        result = row.first()
        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found.")

        run, nft = result
        ownership_cache = OwnershipCache(redis)
        owner_wallet_id = await ownership_cache.get_owner_wallet_id(session, agent_id=run.agent_id, token_id=nft.token_id)
        if owner_wallet_id != wallet_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the current NFT owner can cancel this run.",
            )
        if run.status in RunService.TERMINAL_STATUSES:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Run is already terminal.")

        run.cancel_requested_at = utcnow()
        if run.status == "QUEUED":
            run.status = "CANCELLED"
            run.failure_reason = "Cancelled before execution started."
            run.output_json = {"error": run.failure_reason}
            run.finished_at = utcnow()
        else:
            run.status = "CANCEL_REQUESTED"
        await session.commit()

        if run.celery_task_id:
            from app.core.celery_app import celery_app

            celery_app.control.revoke(run.celery_task_id, terminate=False)

        log_event(
            logger,
            "run_cancel_requested",
            run_id=run.id,
            status=run.status,
            requested_by_wallet_id=wallet_id,
        )
        await emit_runtime_event(
            redis,
            "agent_run_cancel_requested",
            {"run_id": run.id, "agent_id": run.agent_id, "status": run.status},
        )
        return run_to_dict(run)

    @staticmethod
    async def get_metrics(session: AsyncSession, redis: Redis) -> dict:
        runs = (await session.scalars(select(AgentRun).order_by(AgentRun.queued_at.desc()))).all()
        counts: dict[str, int] = {}
        for run in runs:
            counts[run.status] = counts.get(run.status, 0) + 1

        completed = [run for run in runs if run.status == "COMPLETED" and run.started_at and run.finished_at]
        average_duration_seconds = None
        if completed:
            total_seconds = sum((run.finished_at - run.started_at).total_seconds() for run in completed)
            average_duration_seconds = round(total_seconds / len(completed), 2)

        dead_letter_count = sum(1 for run in runs if run.dead_lettered_at is not None)
        retry_pending_count = sum(1 for run in runs if run.status == "QUEUED" and run.attempt_count > 0)
        queued_runs = [run for run in runs if run.status == "QUEUED" and run.queued_at is not None]
        oldest_queued_at = min((run.queued_at for run in queued_runs), default=None)

        return {
            "totals": counts,
            "queue_depth": counts.get("QUEUED", 0),
            "running": counts.get("RUNNING", 0),
            "cancel_requested": counts.get("CANCEL_REQUESTED", 0),
            "dead_letter_count": dead_letter_count,
            "retry_pending_count": retry_pending_count,
            "average_duration_seconds": average_duration_seconds,
            "oldest_queued_at": oldest_queued_at,
            "event_stream_length": await redis.xlen("agent_runtime_events"),
        }

    @staticmethod
    async def list_runtime_logs(redis: Redis, *, limit: int | None = None) -> list[dict]:
        settings = get_settings()
        entries = await redis.xrevrange("agent_runtime_events", count=limit or settings.runtime_log_default_limit)
        logs: list[dict] = []
        for entry_id, fields in entries:
            stream_ms = int(entry_id.split("-", 1)[0])
            logs.append(
                {
                    "id": entry_id,
                    "timestamp_ms": stream_ms,
                    "event_type": fields.get("event_type"),
                    "fields": fields,
                }
            )
        return logs

    @staticmethod
    async def _mark_failed(session: AsyncSession, redis: Redis, run: AgentRun, reason: str) -> None:
        run.status = "FAILED"
        run.failure_reason = reason
        run.output_json = {"error": reason}
        run.finished_at = utcnow()
        await session.commit()
        log_event(logger, "run_failed", run_id=run.id, reason=reason, attempt_count=run.attempt_count)
        await emit_runtime_event(redis, "agent_run_failed", {"run_id": run.id, "reason": reason})

    @staticmethod
    async def _mark_cancelled(session: AsyncSession, redis: Redis, run: AgentRun, reason: str) -> None:
        run.status = "CANCELLED"
        run.failure_reason = reason
        run.output_json = {"error": reason}
        run.finished_at = utcnow()
        await session.commit()
        log_event(logger, "run_cancelled", run_id=run.id, reason=reason, attempt_count=run.attempt_count)
        await emit_runtime_event(redis, "agent_run_cancelled", {"run_id": run.id, "reason": reason})

    @staticmethod
    async def _handle_retryable_failure(
        session: AsyncSession,
        redis: Redis,
        run: AgentRun,
        reason: str,
        *,
        terminal_status: str,
    ) -> None:
        if run.cancel_requested_at is not None or run.status == "CANCEL_REQUESTED":
            await RunService._mark_cancelled(session, redis, run, "Run was cancelled before retry handling.")
            return

        run.failure_reason = reason
        run.output_json = {"error": reason, "attempt_count": run.attempt_count}

        if run.attempt_count < run.max_attempts:
            backoff_seconds = get_settings().run_retry_backoff_seconds * max(run.attempt_count, 1)
            run.status = "QUEUED"
            run.finished_at = None
            run.next_retry_at = utcnow() + timedelta(seconds=backoff_seconds)
            await session.commit()
            log_event(
                logger,
                "run_retry_scheduled",
                run_id=run.id,
                reason=reason,
                attempt_count=run.attempt_count,
                next_retry_at=run.next_retry_at,
            )
            await emit_runtime_event(
                redis,
                "agent_run_retry_scheduled",
                {"run_id": run.id, "reason": reason, "attempt_count": run.attempt_count},
            )
            await RunService._dispatch_run_task(session, redis, run, countdown=backoff_seconds)
            return

        run.status = terminal_status
        run.dead_lettered_at = utcnow()
        run.finished_at = utcnow()
        await session.commit()
        log_event(
            logger,
            "run_dead_lettered",
            run_id=run.id,
            terminal_status=terminal_status,
            reason=reason,
            attempt_count=run.attempt_count,
        )
        await emit_runtime_event(
            redis,
            "agent_run_dead_lettered",
            {"run_id": run.id, "status": terminal_status, "reason": reason, "attempt_count": run.attempt_count},
        )


class ScheduleService:
    @staticmethod
    async def create_schedule(
        session: AsyncSession,
        *,
        agent_id: str,
        task: str,
        interval_seconds: int,
        starts_in_seconds: int = 0,
    ) -> dict:
        await load_agent_bundle(session, agent_id)
        schedule = AgentSchedule(
            id=new_id("schedule"),
            agent_id=agent_id,
            task_template=task,
            interval_seconds=interval_seconds,
            next_run_at=utcnow() + timedelta(seconds=starts_in_seconds or interval_seconds),
        )
        session.add(schedule)
        await session.commit()
        await session.refresh(schedule)
        return schedule_to_dict(schedule)

    @staticmethod
    async def list_schedules(session: AsyncSession) -> list[dict]:
        schedules = (await session.scalars(select(AgentSchedule).order_by(AgentSchedule.created_at.desc()))).all()
        return [schedule_to_dict(schedule) for schedule in schedules]

    @staticmethod
    async def dispatch_due_schedules() -> None:
        redis = await init_redis()
        now = utcnow()
        due_run_ids: list[str] = []

        async with SessionLocal() as session:
            due_schedules = (
                await session.scalars(
                    select(AgentSchedule)
                    .where(AgentSchedule.enabled.is_(True), AgentSchedule.next_run_at <= now)
                    .order_by(AgentSchedule.next_run_at.asc())
                )
            ).all()

            for schedule in due_schedules:
                try:
                    agent, nft = await load_agent_bundle(session, schedule.agent_id)
                except HTTPException:
                    schedule.enabled = False
                    continue

                ownership_cache = OwnershipCache(redis)
                owner_wallet_id = await ownership_cache.get_owner_wallet_id(
                    session,
                    agent_id=agent.id,
                    token_id=nft.token_id,
                )

                run = AgentRun(
                    id=new_id("run"),
                    agent_id=agent.id,
                    token_id=nft.token_id,
                    requested_by_wallet_id=owner_wallet_id,
                    task_input=schedule.task_template,
                    source="SCHEDULED",
                    status="QUEUED",
                    attempt_count=0,
                    max_attempts=RunService._resolve_run_attempts(),
                    timeout_seconds=RunService._resolve_run_timeout(),
                    queued_at=utcnow(),
                )
                session.add(run)
                schedule.last_enqueued_at = now
                next_run_at = schedule.next_run_at
                while next_run_at <= now:
                    next_run_at = next_run_at + timedelta(seconds=schedule.interval_seconds)
                schedule.next_run_at = next_run_at
                due_run_ids.append(run.id)

            await session.commit()

            if due_run_ids:
                for run_id in due_run_ids:
                    run = await session.get(AgentRun, run_id)
                    if run is None:
                        continue
                    await emit_runtime_event(redis, "agent_run_queued", {"run_id": run_id, "source": "SCHEDULED"})
                    await RunService._dispatch_run_task(session, redis, run)


class MarketplaceService:
    @staticmethod
    async def create_listing(
        session: AsyncSession,
        redis: Redis,
        *,
        token_id: str,
        seller_wallet_id: str,
        price: Decimal,
    ) -> dict:
        nft = await AgentService.get_nft(session, token_id)
        if get_nft_sync_mode(nft) == "CHAIN_SYNCED":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Chain-synced NFTs cannot use the local marketplace yet. Use direct on-chain transfer.",
            )
        if nft.owner_wallet_id != seller_wallet_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can list this NFT.")

        lock_manager = AgentLockManager(redis)
        if await lock_manager.is_locked(nft.agent_id):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Agent is busy; listing is blocked.")

        existing = await session.scalar(
            select(MarketListing).where(MarketListing.token_id == token_id, MarketListing.status == "OPEN")
        )
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This NFT is already listed.")

        listing = MarketListing(
            id=new_id("listing"),
            token_id=token_id,
            agent_id=nft.agent_id,
            seller_wallet_id=seller_wallet_id,
            price=price,
            status="OPEN",
        )
        session.add(listing)
        await session.commit()
        await session.refresh(listing)
        await emit_runtime_event(
            redis,
            "listing_opened",
            {"listing_id": listing.id, "token_id": token_id, "price": price},
        )
        return listing_to_dict(listing)

    @staticmethod
    async def list_listings(session: AsyncSession, status_filter: str = "OPEN") -> list[dict]:
        stmt = select(MarketListing).order_by(MarketListing.opened_at.desc())
        if status_filter:
            stmt = stmt.where(MarketListing.status == status_filter)
        listings = (await session.scalars(stmt)).all()
        chain_states = await load_listing_chain_states(session, [listing.id for listing in listings])
        return [listing_to_dict(listing, chain_states.get(listing.id)) for listing in listings]

    @staticmethod
    async def get_listing(session: AsyncSession, listing_id: str) -> dict:
        listing = await session.get(MarketListing, listing_id)
        if listing is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found.")
        chain_state = await load_listing_chain_state(session, listing.id)
        return listing_to_dict(listing, chain_state)

    @staticmethod
    async def list_listing_events(session: AsyncSession, listing_id: str) -> list[dict]:
        events = (
            await session.scalars(
                select(MarketOrderEvent)
                .where(MarketOrderEvent.listing_id == listing_id)
                .order_by(MarketOrderEvent.created_at.desc())
            )
        ).all()
        return [market_order_event_to_dict(event) for event in events]

    @staticmethod
    async def list_listing_transactions(session: AsyncSession, listing_id: str) -> list[dict]:
        records = (
            await session.scalars(
                select(TransactionRecord)
                .where(TransactionRecord.entity_type == "LISTING", TransactionRecord.entity_id == listing_id)
                .order_by(TransactionRecord.created_at.desc())
            )
        ).all()
        return [transaction_record_to_dict(record) for record in records]

    @staticmethod
    async def cancel_listing(session: AsyncSession, redis: Redis, *, listing_id: str, seller_wallet_id: str) -> dict:
        listing = await session.scalar(select(MarketListing).where(MarketListing.id == listing_id).with_for_update())
        if listing is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found.")
        if listing.status != "OPEN":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Listing is not open.")
        if listing.seller_wallet_id != seller_wallet_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the listing seller can cancel it.")

        chain_state = await load_listing_chain_state(session, listing.id)
        if chain_state is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="On-chain listings must be cancelled on-chain via MetaMask.",
            )

        listing.status = "CANCELLED"
        listing.closed_at = utcnow()
        await session.commit()
        await emit_runtime_event(
            redis,
            "listing_cancelled",
            {
                "listing_id": listing.id,
                "token_id": listing.token_id,
                "seller_wallet_id": listing.seller_wallet_id,
            },
        )
        return listing_to_dict(listing)

    @staticmethod
    async def buy_listing(session: AsyncSession, redis: Redis, *, listing_id: str, buyer_wallet_id: str) -> dict:
        listing = await session.scalar(select(MarketListing).where(MarketListing.id == listing_id).with_for_update())
        if listing is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found.")
        if listing.status != "OPEN":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Listing is not open.")

        nft = await session.scalar(select(AgentNFT).where(AgentNFT.token_id == listing.token_id).with_for_update())
        if nft is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NFT not found.")
        if get_nft_sync_mode(nft) == "CHAIN_SYNCED":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Chain-synced NFTs cannot be settled by the local marketplace. Use an on-chain transfer flow.",
            )

        lock_manager = AgentLockManager(redis)
        if await lock_manager.is_locked(nft.agent_id):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Agent is busy; purchase is blocked.")

        seller = await session.scalar(select(Wallet).where(Wallet.id == listing.seller_wallet_id).with_for_update())
        buyer = await session.scalar(select(Wallet).where(Wallet.id == buyer_wallet_id).with_for_update())
        if seller is None or buyer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buyer or seller wallet not found.")
        if buyer.id == seller.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Seller cannot buy their own listing.")
        if buyer.balance < listing.price:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Buyer has insufficient balance.")

        buyer.balance -= listing.price
        seller.balance += listing.price
        listing.buyer_wallet_id = buyer.id
        listing.status = "SOLD"
        listing.closed_at = utcnow()
        nft.owner_wallet_id = buyer.id
        nft.last_transfer_at = utcnow()

        await session.commit()

        ownership_cache = OwnershipCache(redis)
        await ownership_cache.set_owner_wallet_id(agent_id=nft.agent_id, token_id=nft.token_id, owner_wallet_id=buyer.id)
        await emit_runtime_event(
            redis,
            "listing_sold",
            {
                "listing_id": listing.id,
                "token_id": nft.token_id,
                "buyer_wallet_id": buyer.id,
                "seller_wallet_id": seller.id,
            },
        )
        return listing_to_dict(listing)

    @staticmethod
    async def transfer_nft(
        session: AsyncSession,
        redis: Redis,
        *,
        token_id: str,
        from_wallet_id: str,
        to_wallet_id: str | None = None,
        to_chain_address: str | None = None,
    ) -> dict:
        nft = await session.scalar(select(AgentNFT).where(AgentNFT.token_id == token_id).with_for_update())
        if nft is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NFT not found.")
        if get_nft_sync_mode(nft) == "CHAIN_SYNCED":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Chain-synced NFTs must be transferred on-chain via MetaMask.",
            )
        if nft.owner_wallet_id != from_wallet_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Transfer caller is not the NFT owner.")

        if to_wallet_id is not None:
            destination_wallet = await WalletService.get_wallet(session, to_wallet_id)
        elif to_chain_address is not None:
            destination_wallet = await WalletService.get_or_create_chain_wallet(session, to_chain_address)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transfer target is required.",
            )

        if destination_wallet.id == from_wallet_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transfer target must be different from the current owner.",
            )

        lock_manager = AgentLockManager(redis)
        if await lock_manager.is_locked(nft.agent_id):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Agent is busy; transfer is blocked.")

        open_listing = await session.scalar(
            select(MarketListing).where(MarketListing.token_id == token_id, MarketListing.status == "OPEN").with_for_update()
        )
        if open_listing:
            open_listing.status = "CANCELLED"
            open_listing.closed_at = utcnow()

        nft.owner_wallet_id = destination_wallet.id
        nft.last_transfer_at = utcnow()
        await session.commit()

        ownership_cache = OwnershipCache(redis)
        await ownership_cache.set_owner_wallet_id(
            agent_id=nft.agent_id,
            token_id=nft.token_id,
            owner_wallet_id=destination_wallet.id,
        )
        await emit_runtime_event(
            redis,
            "nft_transferred",
            {
                "token_id": token_id,
                "from_wallet_id": from_wallet_id,
                "to_wallet_id": destination_wallet.id,
                "to_chain_address": destination_wallet.chain_address,
            },
        )
        return nft_to_dict(nft)

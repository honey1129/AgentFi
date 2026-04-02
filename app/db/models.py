from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Wallet(Base):
    __tablename__ = "wallets"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    chain_address: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0"))
    created_at: Mapped[Any] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")
    memory_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[Any] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[Any] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    nft: Mapped["AgentNFT"] = relationship(back_populates="agent", uselist=False)
    runs: Mapped[list["AgentRun"]] = relationship(back_populates="agent")


class AgentNFT(Base):
    __tablename__ = "agent_nfts"

    token_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    agent_id: Mapped[str] = mapped_column(ForeignKey("agents.id"), nullable=False, unique=True)
    owner_wallet_id: Mapped[str] = mapped_column(ForeignKey("wallets.id"), nullable=False)
    contract_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    chain_token_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    metadata_uri: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_synced_tx_hash: Mapped[str | None] = mapped_column(String(120), nullable=True)
    last_synced_block: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[Any] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_transfer_at: Mapped[Any] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    agent: Mapped[Agent] = relationship(back_populates="nft")


class MarketListing(Base):
    __tablename__ = "market_listings"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    token_id: Mapped[str] = mapped_column(ForeignKey("agent_nfts.token_id"), nullable=False)
    agent_id: Mapped[str] = mapped_column(ForeignKey("agents.id"), nullable=False)
    seller_wallet_id: Mapped[str] = mapped_column(ForeignKey("wallets.id"), nullable=False)
    buyer_wallet_id: Mapped[str | None] = mapped_column(ForeignKey("wallets.id"), nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="OPEN")
    opened_at: Mapped[Any] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    closed_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True), nullable=True)


class MarketListingChainState(Base):
    __tablename__ = "market_listing_chain_states"
    __table_args__ = (
        UniqueConstraint(
            "market_contract_address",
            "chain_listing_id",
            name="uq_market_listing_chain_states_market_contract_chain_listing_id",
        ),
    )

    listing_id: Mapped[str] = mapped_column(ForeignKey("market_listings.id"), primary_key=True)
    market_contract_address: Mapped[str] = mapped_column(String(64), nullable=False)
    chain_listing_id: Mapped[str] = mapped_column(String(120), nullable=False)
    mode: Mapped[str] = mapped_column(String(32), nullable=False, default="ONCHAIN")
    currency_symbol: Mapped[str] = mapped_column(String(16), nullable=False, default="ETH")
    price_wei: Mapped[str] = mapped_column(String(120), nullable=False)
    seller_chain_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    buyer_chain_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    open_tx_hash: Mapped[str | None] = mapped_column(String(120), nullable=True)
    close_tx_hash: Mapped[str | None] = mapped_column(String(120), nullable=True)
    last_synced_block: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[Any] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[Any] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class TransactionRecord(Base):
    __tablename__ = "transaction_records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    tx_hash: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    tx_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="CONFIRMED")
    chain_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    from_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    to_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[Any] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[Any] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class MarketOrderEvent(Base):
    __tablename__ = "market_order_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    listing_id: Mapped[str | None] = mapped_column(ForeignKey("market_listings.id"), nullable=True)
    chain_listing_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    tx_hash: Mapped[str] = mapped_column(String(120), nullable=False)
    block_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[Any] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AgentRun(Base):
    __tablename__ = "agent_runs"
    __table_args__ = (
        Index("ix_agent_runs_status_queued_at", "status", "queued_at"),
        Index("ix_agent_runs_agent_id_queued_at", "agent_id", "queued_at"),
        Index("ix_agent_runs_dead_lettered_at", "dead_lettered_at"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    parent_run_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    agent_id: Mapped[str] = mapped_column(ForeignKey("agents.id"), nullable=False)
    token_id: Mapped[str] = mapped_column(ForeignKey("agent_nfts.token_id"), nullable=False)
    requested_by_wallet_id: Mapped[str] = mapped_column(ForeignKey("wallets.id"), nullable=False)
    task_input: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="MANUAL")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="QUEUED")
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=90)
    celery_task_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    queued_at: Mapped[Any] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    started_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_retry_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancel_requested_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dead_lettered_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True), nullable=True)

    agent: Mapped[Agent] = relationship(back_populates="runs")


class AgentSchedule(Base):
    __tablename__ = "agent_schedules"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    agent_id: Mapped[str] = mapped_column(ForeignKey("agents.id"), nullable=False)
    task_template: Mapped[str] = mapped_column(Text, nullable=False)
    interval_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    next_run_at: Mapped[Any] = mapped_column(DateTime(timezone=True), nullable=False)
    last_enqueued_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[Any] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class RuntimeCheckpoint(Base):
    __tablename__ = "runtime_checkpoints"

    key: Mapped[str] = mapped_column(String(120), primary_key=True)
    value: Mapped[str] = mapped_column(String(255), nullable=False)
    updated_at: Mapped[Any] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

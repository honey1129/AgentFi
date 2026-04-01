from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field


class WalletCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    initial_balance: Decimal = Field(default=Decimal("0"), ge=0)
    chain_address: str | None = Field(default=None)


class WalletConnectRequest(BaseModel):
    chain_address: str = Field(min_length=1)
    initial_balance: Decimal = Field(default=Decimal("0"), ge=0)
    label: str | None = Field(default=None, min_length=2, max_length=120)


class MetaMaskChallengeRequest(BaseModel):
    chain_address: str = Field(min_length=1)
    chain_id: str | None = Field(default=None, min_length=1)
    initial_balance: Decimal = Field(default=Decimal("0"), ge=0)
    label: str | None = Field(default=None, min_length=2, max_length=120)


class MetaMaskVerifyRequest(BaseModel):
    chain_address: str = Field(min_length=1)
    signature: str = Field(min_length=1)


class AgentCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(min_length=1)
    system_prompt: str = Field(min_length=1)
    owner_wallet_id: str | None = Field(default=None, min_length=1)
    seed_memory: list[dict] = Field(default_factory=list)
    contract_address: str | None = Field(default=None)
    chain_token_id: str | None = Field(default=None)


class AgentRunRequest(BaseModel):
    wallet_id: str | None = Field(default=None, min_length=1)
    task: str = Field(min_length=1)
    max_attempts: int | None = Field(default=None, ge=1, le=10)
    timeout_seconds: int | None = Field(default=None, ge=1, le=3600)


class ListingCreateRequest(BaseModel):
    token_id: str = Field(min_length=1)
    seller_wallet_id: str | None = Field(default=None, min_length=1)
    price: Decimal = Field(gt=0)


class ListingBuyRequest(BaseModel):
    buyer_wallet_id: str | None = Field(default=None, min_length=1)


class NFTTransferRequest(BaseModel):
    from_wallet_id: str | None = Field(default=None, min_length=1)
    to_wallet_id: str | None = Field(default=None, min_length=1)
    to_chain_address: str | None = Field(default=None, min_length=1)


class AgentScheduleCreateRequest(BaseModel):
    agent_id: str = Field(min_length=1)
    task: str = Field(min_length=1)
    interval_seconds: int = Field(gt=0)
    starts_in_seconds: int = Field(default=0, ge=0)

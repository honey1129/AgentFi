from __future__ import annotations

import json
import secrets
from decimal import Decimal

from eth_account import Account
from eth_account.messages import encode_defunct
from fastapi import HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from web3 import Web3

from app.core.config import get_settings
from app.core.utils import utcnow
from app.db.models import Wallet
from app.services.runtime import WalletService, ensure_valid_chain_address, normalize_chain_address


def _challenge_key(chain_address: str) -> str:
    return f"auth:metamask:challenge:{chain_address}"


def _session_key(token: str) -> str:
    return f"auth:metamask:session:{token}"


def _display_address(chain_address: str) -> str:
    try:
        return Web3.to_checksum_address(chain_address)
    except ValueError:
        return chain_address

class MetaMaskAuthService:
    @staticmethod
    def _build_message(*, chain_address: str, chain_id: str | None, nonce: str, issued_at: str) -> str:
        settings = get_settings()
        return "\n".join(
            [
                f"{settings.app_name} requests wallet authentication",
                "",
                f"Address: {_display_address(chain_address)}",
                "Purpose: Control NFT-backed agents inside the runtime.",
                f"Chain ID: {chain_id or 'unknown'}",
                f"Nonce: {nonce}",
                f"Issued At: {issued_at}",
            ]
        )

    @staticmethod
    async def create_challenge(
        redis: Redis,
        *,
        chain_address: str,
        chain_id: str | None = None,
        initial_balance: Decimal = Decimal("0"),
        label: str | None = None,
    ) -> dict:
        normalized_address = ensure_valid_chain_address(chain_address)
        nonce = secrets.token_hex(16)
        issued_at = utcnow().isoformat()
        message = MetaMaskAuthService._build_message(
            chain_address=normalized_address,
            chain_id=chain_id,
            nonce=nonce,
            issued_at=issued_at,
        )
        payload = {
            "chain_address": normalized_address,
            "chain_id": chain_id,
            "initial_balance": str(initial_balance),
            "issued_at": issued_at,
            "label": label,
            "message": message,
            "nonce": nonce,
        }
        ttl = get_settings().wallet_auth_challenge_ttl_seconds
        await redis.set(_challenge_key(normalized_address), json.dumps(payload), ex=ttl)
        return {
            "chain_address": normalized_address,
            "chain_id": chain_id,
            "expires_in": ttl,
            "issued_at": issued_at,
            "message": message,
            "nonce": nonce,
        }

    @staticmethod
    async def verify_signature(
        session: AsyncSession,
        redis: Redis,
        *,
        chain_address: str,
        signature: str,
    ) -> dict:
        normalized_address = ensure_valid_chain_address(chain_address)
        raw_challenge = await redis.get(_challenge_key(normalized_address))
        if raw_challenge is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="MetaMask challenge expired. Request a new challenge.",
            )

        challenge = json.loads(raw_challenge)
        try:
            recovered_address = normalize_chain_address(
                Account.recover_message(
                    encode_defunct(text=challenge["message"]),
                    signature=signature,
                )
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid MetaMask signature.",
            ) from exc

        if recovered_address != normalized_address:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Signature does not match the connected MetaMask address.",
            )

        wallet = await WalletService.connect_wallet(
            session,
            chain_address=normalized_address,
            initial_balance=Decimal(challenge.get("initial_balance", "0")),
            label=challenge.get("label"),
        )

        session_token = secrets.token_urlsafe(32)
        ttl = get_settings().wallet_auth_session_ttl_seconds
        await redis.set(
            _session_key(session_token),
            json.dumps(
                {
                    "chain_address": normalized_address,
                    "chain_id": challenge.get("chain_id"),
                    "issued_at": utcnow().isoformat(),
                    "wallet_id": wallet["id"],
                }
            ),
            ex=ttl,
        )
        await redis.delete(_challenge_key(normalized_address))
        return {
            "access_token": session_token,
            "token_type": "bearer",
            "expires_in": ttl,
            "chain_address": normalized_address,
            "wallet": wallet,
        }

    @staticmethod
    async def get_authenticated_wallet(session: AsyncSession, redis: Redis, session_token: str) -> Wallet:
        raw_session = await redis.get(_session_key(session_token))
        if raw_session is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="MetaMask session expired. Sign again.",
            )

        session_payload = json.loads(raw_session)
        wallet = await WalletService.get_wallet(session, session_payload["wallet_id"])
        if normalize_chain_address(wallet.chain_address) != session_payload["chain_address"]:
            await redis.delete(_session_key(session_token))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Wallet session no longer matches the runtime wallet.",
            )

        await redis.expire(_session_key(session_token), get_settings().wallet_auth_session_ttl_seconds)
        return wallet

    @staticmethod
    async def revoke_session(redis: Redis, session_token: str) -> None:
        await redis.delete(_session_key(session_token))

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Wallet
from app.db.session import get_session
from app.runtime.redis_client import get_redis
from app.services.auth import MetaMaskAuthService


bearer_scheme = HTTPBearer(auto_error=False)


async def get_bearer_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="MetaMask authentication required.",
        )
    return credentials.credentials


async def require_authenticated_wallet(
    session_token: str = Depends(get_bearer_token),
    session: AsyncSession = Depends(get_session),
) -> Wallet:
    redis = await get_redis()
    return await MetaMaskAuthService.get_authenticated_wallet(session, redis, session_token)

"""API dependencies for dependency injection."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.database import get_db
from src.infra.database.repositories import (
    UserRepository,
    StrategyRepository,
    SubscriptionRepository,
    SignalRepository,
)
from src.services import (
    UserService,
    StrategyService,
    SubscriptionService,
    SignalService,
    NotificationService,
)
from src.domain.entities.user import UserEntity
from src.core.security import verify_access_token
from src.core.exceptions import InvalidTokenError

security = HTTPBearer()


async def get_user_repo(session: Annotated[AsyncSession, Depends(get_db)]) -> UserRepository:
    return UserRepository(session)


async def get_strategy_repo(session: Annotated[AsyncSession, Depends(get_db)]) -> StrategyRepository:
    return StrategyRepository(session)


async def get_subscription_repo(session: Annotated[AsyncSession, Depends(get_db)]) -> SubscriptionRepository:
    return SubscriptionRepository(session)


async def get_signal_repo(session: Annotated[AsyncSession, Depends(get_db)]) -> SignalRepository:
    return SignalRepository(session)


async def get_user_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repo)],
) -> UserService:
    return UserService(user_repo)


async def get_strategy_service(
    strategy_repo: Annotated[StrategyRepository, Depends(get_strategy_repo)],
) -> StrategyService:
    return StrategyService(strategy_repo)


async def get_subscription_service(
    subscription_repo: Annotated[SubscriptionRepository, Depends(get_subscription_repo)],
    strategy_repo: Annotated[StrategyRepository, Depends(get_strategy_repo)],
    user_repo: Annotated[UserRepository, Depends(get_user_repo)],
) -> SubscriptionService:
    return SubscriptionService(subscription_repo, strategy_repo, user_repo)


async def get_signal_service(
    signal_repo: Annotated[SignalRepository, Depends(get_signal_repo)],
    subscription_repo: Annotated[SubscriptionRepository, Depends(get_subscription_repo)],
) -> SignalService:
    return SignalService(signal_repo, subscription_repo)


async def get_notification_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> NotificationService:
    return NotificationService(session)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserEntity:
    """Get current authenticated user."""
    token = credentials.credentials
    payload = verify_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    try:
        user = await user_service.get_by_id(UUID(user_id))
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled",
            )
        return user
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )


async def get_optional_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(HTTPBearer(auto_error=False))],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserEntity | None:
    """Get current user if authenticated, otherwise None."""
    if not credentials:
        return None

    token = credentials.credentials
    payload = verify_access_token(token)

    if not payload:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    try:
        return await user_service.get_by_id(UUID(user_id))
    except Exception:
        return None


def require_tier(min_tier: str):
    """Dependency factory: require minimum user tier."""
    from src.core.constants import UserTier

    tier_order = {UserTier.FREE: 0, UserTier.PRO: 1, UserTier.ENTERPRISE: 2}

    async def checker(
        current_user: Annotated[UserEntity, Depends(get_current_user)],
    ) -> UserEntity:
        min_tier_enum = UserTier(min_tier)
        if tier_order.get(current_user.tier, 0) < tier_order.get(min_tier_enum, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {min_tier} tier or above",
            )
        return current_user

    return checker


def require_admin():
    """Dependency: require admin role."""
    from src.core.constants import UserRole

    async def checker(
        current_user: Annotated[UserEntity, Depends(get_current_user)],
    ) -> UserEntity:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required",
            )
        return current_user

    return checker

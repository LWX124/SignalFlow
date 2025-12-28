"""User service for authentication and user management."""

from datetime import datetime
from uuid import UUID

from src.infra.database.repositories.user_repo import UserRepository
from src.infra.database.models import User
from src.domain.entities.user import UserEntity
from src.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from src.core.constants import UserRole, UserTier
from src.core.exceptions import (
    InvalidCredentialsError,
    EmailAlreadyExistsError,
    UserNotFoundError,
)


class UserService:
    """Service for user operations."""

    def __init__(self, user_repo: UserRepository):
        self._repo = user_repo

    async def register(
        self,
        email: str,
        password: str,
        nickname: str | None = None,
    ) -> UserEntity:
        """Register a new user."""
        if await self._repo.email_exists(email):
            raise EmailAlreadyExistsError(email)

        user = User(
            email=email,
            password_hash=hash_password(password),
            nickname=nickname or email.split("@")[0],
            role=UserRole.USER,
            tier=UserTier.FREE,
        )

        saved = await self._repo.create(user)
        return self._repo.to_entity(saved)

    async def authenticate(self, email: str, password: str) -> tuple[UserEntity, str, str]:
        """Authenticate user and return tokens."""
        user = await self._repo.get_by_email(email)

        if not user or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError()

        if not user.is_active:
            raise InvalidCredentialsError()

        await self._repo.update_last_login(user.id)

        access_token = create_access_token({"sub": str(user.id), "email": user.email})
        refresh_token = create_refresh_token({"sub": str(user.id)})

        return self._repo.to_entity(user), access_token, refresh_token

    async def get_by_id(self, user_id: UUID) -> UserEntity:
        """Get user by ID."""
        user = await self._repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(str(user_id))
        return self._repo.to_entity(user)

    async def get_by_email(self, email: str) -> UserEntity | None:
        """Get user by email."""
        user = await self._repo.get_by_email(email)
        return self._repo.to_entity(user) if user else None

    async def update_profile(
        self,
        user_id: UUID,
        nickname: str | None = None,
        avatar_url: str | None = None,
        phone: str | None = None,
    ) -> UserEntity:
        """Update user profile."""
        user = await self._repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(str(user_id))

        if nickname is not None:
            user.nickname = nickname
        if avatar_url is not None:
            user.avatar_url = avatar_url
        if phone is not None:
            user.phone = phone

        user.updated_at = datetime.utcnow()
        updated = await self._repo.update(user)
        return self._repo.to_entity(updated)

    async def change_password(
        self,
        user_id: UUID,
        old_password: str,
        new_password: str,
    ) -> bool:
        """Change user password."""
        user = await self._repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(str(user_id))

        if not verify_password(old_password, user.password_hash):
            raise InvalidCredentialsError()

        user.password_hash = hash_password(new_password)
        user.updated_at = datetime.utcnow()
        await self._repo.update(user)
        return True

    async def upgrade_tier(
        self,
        user_id: UUID,
        tier: UserTier,
        expires_at: datetime | None = None,
    ) -> UserEntity:
        """Upgrade user tier."""
        user = await self._repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(str(user_id))

        await self._repo.update_tier(user_id, tier, expires_at)
        user.tier = tier
        user.tier_expires_at = expires_at
        return self._repo.to_entity(user)

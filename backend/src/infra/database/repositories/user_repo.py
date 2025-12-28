"""User repository."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update

from src.infra.database.models import User
from src.infra.database.repositories.base import BaseRepository
from src.domain.entities.user import UserEntity
from src.core.constants import UserRole, UserTier


class UserRepository(BaseRepository[User]):
    """Repository for User model."""

    model = User

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email."""
        result = await self._session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def email_exists(self, email: str) -> bool:
        """Check if email exists."""
        user = await self.get_by_email(email)
        return user is not None

    async def get_active_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        """Get all active users."""
        result = await self._session.execute(
            select(User)
            .where(User.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_tier(self, tier: UserTier, skip: int = 0, limit: int = 100) -> list[User]:
        """Get users by tier."""
        result = await self._session.execute(
            select(User)
            .where(User.tier == tier)
            .where(User.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_last_login(self, user_id: UUID) -> None:
        """Update user's last login time."""
        await self._session.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_login_at=datetime.utcnow())
        )

    async def update_tier(
        self,
        user_id: UUID,
        tier: UserTier,
        expires_at: datetime | None = None,
    ) -> None:
        """Update user's subscription tier."""
        await self._session.execute(
            update(User)
            .where(User.id == user_id)
            .values(tier=tier, tier_expires_at=expires_at)
        )

    async def deactivate(self, user_id: UUID) -> None:
        """Deactivate a user."""
        await self._session.execute(
            update(User)
            .where(User.id == user_id)
            .values(is_active=False)
        )

    def to_entity(self, model: User) -> UserEntity:
        """Convert model to entity."""
        return UserEntity(
            id=model.id,
            email=model.email,
            password_hash=model.password_hash,
            nickname=model.nickname,
            avatar_url=model.avatar_url,
            phone=model.phone,
            role=model.role,
            tier=model.tier,
            tier_expires_at=model.tier_expires_at,
            preferences=model.preferences,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
            last_login_at=model.last_login_at,
        )

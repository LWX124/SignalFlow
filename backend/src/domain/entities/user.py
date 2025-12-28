"""User entity."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from src.core.constants import UserRole, UserTier, SUBSCRIPTION_LIMITS


@dataclass
class UserEntity:
    """User domain entity."""

    id: UUID
    email: str
    password_hash: str
    role: UserRole = UserRole.USER
    tier: UserTier = UserTier.FREE
    nickname: str | None = None
    avatar_url: str | None = None
    phone: str | None = None
    tier_expires_at: datetime | None = None
    preferences: dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_login_at: datetime | None = None

    @property
    def subscription_limit(self) -> int:
        """Get user's subscription limit based on tier."""
        return SUBSCRIPTION_LIMITS.get(self.tier, 5)

    @property
    def is_pro(self) -> bool:
        """Check if user has Pro tier or higher."""
        return self.tier in (UserTier.PRO, UserTier.ENTERPRISE)

    @property
    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.role == UserRole.ADMIN

    def can_subscribe_to_strategy(self, tier_required: UserTier) -> bool:
        """Check if user can subscribe to a strategy based on tier."""
        tier_order = [UserTier.FREE, UserTier.PRO, UserTier.ENTERPRISE]
        user_tier_index = tier_order.index(self.tier)
        required_tier_index = tier_order.index(tier_required)
        return user_tier_index >= required_tier_index

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary (excluding sensitive data)."""
        return {
            "id": str(self.id),
            "email": self.email,
            "nickname": self.nickname,
            "avatar_url": self.avatar_url,
            "role": self.role.value,
            "tier": self.tier.value,
            "tier_expires_at": self.tier_expires_at.isoformat() if self.tier_expires_at else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

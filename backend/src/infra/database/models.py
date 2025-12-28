"""SQLAlchemy ORM models."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    ARRAY,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from src.core.constants import (
    DeliveryChannel,
    DeliveryStatus,
    InstrumentType,
    Market,
    NotificationType,
    RiskLevel,
    SignalSide,
    StrategyType,
    SubscriptionStatus,
    UserRole,
    UserTier,
)


class Base(DeclarativeBase):
    """Base class for all models."""

    type_annotation_map = {
        dict[str, Any]: JSONB,
        list[str]: ARRAY(String),
    }


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class User(Base, TimestampMixin):
    """User model."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nickname: Mapped[str | None] = mapped_column(String(100))
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    phone: Mapped[str | None] = mapped_column(String(20))
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"),
        default=UserRole.USER,
    )
    tier: Mapped[UserTier] = mapped_column(
        Enum(UserTier, name="user_tier"),
        default=UserTier.FREE,
        index=True,
    )
    tier_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    preferences: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    subscriptions: Mapped[list["Subscription"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Instrument(Base, TimestampMixin):
    """Instrument/Security model."""

    __tablename__ = "instruments"
    __table_args__ = (
        Index("idx_instruments_market_type", "market", "type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    market: Mapped[Market] = mapped_column(Enum(Market, name="market"), nullable=False)
    type: Mapped[InstrumentType] = mapped_column(
        Enum(InstrumentType, name="instrument_type"),
        nullable=False,
    )
    exchange: Mapped[str | None] = mapped_column(String(20))
    currency: Mapped[str] = mapped_column(String(10), default="CNY")
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Strategy(Base, TimestampMixin):
    """Strategy model."""

    __tablename__ = "strategies"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    type: Mapped[StrategyType] = mapped_column(
        Enum(StrategyType, name="strategy_type"),
        nullable=False,
        index=True,
    )
    markets: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    risk_level: Mapped[RiskLevel | None] = mapped_column(Enum(RiskLevel, name="risk_level"))
    frequency_hint: Mapped[str | None] = mapped_column(String(20))
    params_schema: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    default_params: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    default_cooldown: Mapped[int] = mapped_column(Integer, default=3600)
    metrics_summary: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    tier_required: Mapped[UserTier] = mapped_column(
        Enum(UserTier, name="user_tier", create_type=False),
        default=UserTier.FREE,
    )

    # Relationships
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="strategy")
    signals: Mapped[list["Signal"]] = relationship(back_populates="strategy")


class Subscription(Base, TimestampMixin):
    """Subscription model."""

    __tablename__ = "subscriptions"
    __table_args__ = (
        Index("idx_subscriptions_user", "user_id"),
        Index("idx_subscriptions_strategy", "strategy_id"),
        Index("idx_subscriptions_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    strategy_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("strategies.id"),
        nullable=False,
    )
    params: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    channels: Mapped[list[str]] = mapped_column(ARRAY(String), default=lambda: ["site"])
    cooldown_seconds: Mapped[int] = mapped_column(Integer, default=3600)
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus, name="subscription_status"),
        default=SubscriptionStatus.ACTIVE,
    )
    last_signal_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    signal_count: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="subscriptions")
    strategy: Mapped["Strategy"] = relationship(back_populates="subscriptions")


class Signal(Base):
    """Signal model."""

    __tablename__ = "signals"
    __table_args__ = (
        Index("idx_signals_strategy", "strategy_id"),
        Index("idx_signals_symbol", "symbol"),
        Index("idx_signals_created", "created_at"),
        Index("idx_signals_dedup", "dedup_key", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    strategy_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("strategies.id"),
        nullable=False,
    )
    strategy_version: Mapped[str] = mapped_column(String(20), nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    market: Mapped[Market] = mapped_column(Enum(Market, name="market", create_type=False), nullable=False)
    side: Mapped[SignalSide] = mapped_column(
        Enum(SignalSide, name="signal_side"),
        nullable=False,
    )
    confidence: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False)
    reason_points: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    risk_tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    dedup_key: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    strategy: Mapped["Strategy"] = relationship(back_populates="signals")
    explain: Mapped["SignalExplain | None"] = relationship(
        back_populates="signal",
        uselist=False,
        cascade="all, delete-orphan",
    )


class SignalExplain(Base):
    """Signal AI explanation model."""

    __tablename__ = "signal_explains"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    signal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("signals.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[str | None] = mapped_column(String(50))
    prompt_version: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    signal: Mapped["Signal"] = relationship(back_populates="explain")


class DeliveryPlan(Base):
    """Delivery plan model for notifications."""

    __tablename__ = "delivery_plans"
    __table_args__ = (
        Index("idx_delivery_status", "status"),
        Index("idx_delivery_user", "user_id"),
        Index("idx_delivery_scheduled", "scheduled_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    signal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("signals.id"),
        nullable=False,
    )
    subscription_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subscriptions.id"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    channel: Mapped[DeliveryChannel] = mapped_column(
        Enum(DeliveryChannel, name="delivery_channel"),
        nullable=False,
    )
    status: Mapped[DeliveryStatus] = mapped_column(
        Enum(DeliveryStatus, name="delivery_status"),
        default=DeliveryStatus.PENDING,
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class Notification(Base):
    """In-app notification model."""

    __tablename__ = "notifications"
    __table_args__ = (Index("idx_notifications_user", "user_id", "is_read", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, name="notification_type"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str | None] = mapped_column(Text)
    link: Mapped[str | None] = mapped_column(String(500))
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="notifications")


class AuditLog(Base):
    """Audit log model."""

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("idx_audit_user", "user_id"),
        Index("idx_audit_action", "action"),
        Index("idx_audit_entity", "entity_type", "entity_id"),
        Index("idx_audit_time", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(50))
    entity_id: Mapped[str | None] = mapped_column(String(100))
    old_value: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    new_value: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(Text)
    request_id: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

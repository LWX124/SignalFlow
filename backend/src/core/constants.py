"""Application constants."""

from enum import Enum


class UserRole(str, Enum):
    """User roles in the system."""

    USER = "user"
    ADMIN = "admin"
    OPERATOR = "operator"


class UserTier(str, Enum):
    """User subscription tiers."""

    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, Enum):
    """Subscription status."""

    ACTIVE = "active"
    PAUSED = "paused"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class SignalSide(str, Enum):
    """Signal direction/type."""

    BUY = "buy"
    SELL = "sell"
    OPPORTUNITY = "opportunity"
    OBSERVE = "observe"
    WARNING = "warning"


class DeliveryStatus(str, Enum):
    """Notification delivery status."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NotificationType(str, Enum):
    """Notification types."""

    SIGNAL = "signal"
    SYSTEM = "system"
    ANNOUNCEMENT = "announcement"


class StrategyType(str, Enum):
    """Strategy types."""

    ARBITRAGE = "arbitrage"
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    AI = "ai"


class Market(str, Enum):
    """Supported markets."""

    SH = "SH"  # Shanghai
    SZ = "SZ"  # Shenzhen
    HK = "HK"  # Hong Kong
    US = "US"  # United States


class InstrumentType(str, Enum):
    """Instrument types."""

    STOCK = "stock"
    ETF = "etf"
    QDII = "qdii"
    BOND = "bond"


class RiskLevel(str, Enum):
    """Risk levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class FrequencyHint(str, Enum):
    """Strategy frequency hints."""

    REALTIME = "realtime"
    INTRADAY = "intraday"
    DAILY = "daily"


class DeliveryChannel(str, Enum):
    """Notification delivery channels."""

    SITE = "site"
    EMAIL = "email"
    WECHAT = "wechat"
    APP = "app"


# Subscription limits by tier
SUBSCRIPTION_LIMITS = {
    UserTier.FREE: 5,
    UserTier.PRO: 50,
    UserTier.ENTERPRISE: 500,
}

# Default cooldown periods (in seconds)
DEFAULT_COOLDOWN = 3600  # 1 hour

# Pagination defaults
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

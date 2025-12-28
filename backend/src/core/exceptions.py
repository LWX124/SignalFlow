"""Custom exceptions for the application."""

from typing import Any


class SignalFlowError(Exception):
    """Base exception for SignalFlow application."""

    def __init__(self, message: str = "An error occurred", details: Any = None):
        self.message = message
        self.details = details
        super().__init__(self.message)


# Authentication errors
class AuthenticationError(SignalFlowError):
    """Authentication failed."""

    pass


class InvalidCredentialsError(AuthenticationError):
    """Invalid username or password."""

    def __init__(self):
        super().__init__("Invalid email or password")


class TokenExpiredError(AuthenticationError):
    """Token has expired."""

    def __init__(self):
        super().__init__("Token has expired")


class InvalidTokenError(AuthenticationError):
    """Invalid token."""

    def __init__(self):
        super().__init__("Invalid token")


# Authorization errors
class AuthorizationError(SignalFlowError):
    """Authorization failed."""

    pass


class PermissionDeniedError(AuthorizationError):
    """User does not have permission."""

    def __init__(self, action: str = "perform this action"):
        super().__init__(f"Permission denied: you cannot {action}")


# Resource errors
class NotFoundError(SignalFlowError):
    """Resource not found."""

    def __init__(self, resource: str, identifier: str | None = None):
        message = f"{resource} not found"
        if identifier:
            message = f"{resource} with id '{identifier}' not found"
        super().__init__(message)


class StrategyNotFoundError(NotFoundError):
    """Strategy not found."""

    def __init__(self, strategy_id: str):
        super().__init__("Strategy", strategy_id)


class SubscriptionNotFoundError(NotFoundError):
    """Subscription not found."""

    def __init__(self, subscription_id: str):
        super().__init__("Subscription", subscription_id)


class SignalNotFoundError(NotFoundError):
    """Signal not found."""

    def __init__(self, signal_id: str):
        super().__init__("Signal", signal_id)


class UserNotFoundError(NotFoundError):
    """User not found."""

    def __init__(self, user_id: str):
        super().__init__("User", user_id)


class InstrumentNotFoundError(NotFoundError):
    """Instrument not found."""

    def __init__(self, symbol: str):
        super().__init__("Instrument", symbol)


# Validation errors
class ValidationError(SignalFlowError):
    """Validation failed."""

    pass


class InvalidParamsError(ValidationError):
    """Invalid parameters."""

    def __init__(self, errors: list[str]):
        super().__init__("Invalid parameters", details=errors)


# Business logic errors
class BusinessError(SignalFlowError):
    """Business logic error."""

    pass


class SubscriptionLimitExceededError(BusinessError):
    """User has reached subscription limit."""

    def __init__(self):
        super().__init__("Subscription limit exceeded. Please upgrade your plan.")


class DuplicateSubscriptionError(BusinessError):
    """User already subscribed to this strategy."""

    def __init__(self, strategy_id: str):
        super().__init__(f"You are already subscribed to strategy '{strategy_id}'")


class EmailAlreadyExistsError(BusinessError):
    """Email already registered."""

    def __init__(self, email: str):
        super().__init__(f"Email '{email}' is already registered")


class StrategyInactiveError(BusinessError):
    """Strategy is not active."""

    def __init__(self, strategy_id: str):
        super().__init__(f"Strategy '{strategy_id}' is currently inactive")


# External service errors
class ExternalServiceError(SignalFlowError):
    """External service error."""

    pass


class DataProviderError(ExternalServiceError):
    """Data provider error."""

    def __init__(self, provider: str, message: str):
        super().__init__(f"Data provider '{provider}' error: {message}")


class AIServiceError(ExternalServiceError):
    """AI service error."""

    def __init__(self, message: str):
        super().__init__(f"AI service error: {message}")


# Rate limiting
class RateLimitError(SignalFlowError):
    """Rate limit exceeded."""

    def __init__(self, retry_after: int | None = None):
        message = "Rate limit exceeded"
        if retry_after:
            message += f". Please retry after {retry_after} seconds"
        super().__init__(message)
        self.retry_after = retry_after

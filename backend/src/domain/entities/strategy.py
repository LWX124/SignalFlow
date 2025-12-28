"""Strategy entity."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.core.constants import StrategyType, RiskLevel, UserTier


@dataclass
class StrategyEntity:
    """Strategy domain entity."""

    id: str
    version: str
    name: str
    type: StrategyType
    params_schema: dict[str, Any]
    description: str | None = None
    markets: list[str] = field(default_factory=list)
    risk_level: RiskLevel | None = None
    frequency_hint: str | None = None
    default_params: dict[str, Any] = field(default_factory=dict)
    default_cooldown: int = 3600
    metrics_summary: dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    is_public: bool = True
    tier_required: UserTier = UserTier.FREE
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def validate_params(self, params: dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate user params against schema.
        Returns (is_valid, error_messages).
        """
        errors = []
        schema = self.params_schema

        # Check required params
        required = schema.get("required", [])
        for param in required:
            if param not in params:
                errors.append(f"Missing required parameter: {param}")

        # Check param types and constraints
        properties = schema.get("properties", {})
        for param_name, param_value in params.items():
            if param_name not in properties:
                continue

            prop_schema = properties[param_name]
            prop_type = prop_schema.get("type")

            # Type validation
            if prop_type == "number" and not isinstance(param_value, (int, float)):
                errors.append(f"Parameter '{param_name}' must be a number")
                continue

            if prop_type == "string" and not isinstance(param_value, str):
                errors.append(f"Parameter '{param_name}' must be a string")
                continue

            # Range validation for numbers
            if prop_type == "number":
                min_val = prop_schema.get("minimum")
                max_val = prop_schema.get("maximum")

                if min_val is not None and param_value < min_val:
                    errors.append(f"Parameter '{param_name}' must be >= {min_val}")

                if max_val is not None and param_value > max_val:
                    errors.append(f"Parameter '{param_name}' must be <= {max_val}")

        return len(errors) == 0, errors

    def merge_params(self, user_params: dict[str, Any]) -> dict[str, Any]:
        """Merge user params with default params."""
        result = self.default_params.copy()
        result.update(user_params)
        return result

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "version": self.version,
            "name": self.name,
            "description": self.description,
            "type": self.type.value,
            "markets": self.markets,
            "risk_level": self.risk_level.value if self.risk_level else None,
            "frequency_hint": self.frequency_hint,
            "params_schema": self.params_schema,
            "default_params": self.default_params,
            "default_cooldown": self.default_cooldown,
            "metrics_summary": self.metrics_summary,
            "is_active": self.is_active,
            "is_public": self.is_public,
            "tier_required": self.tier_required.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

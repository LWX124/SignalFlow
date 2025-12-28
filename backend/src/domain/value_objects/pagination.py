"""Pagination value objects."""

import base64
import json
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

T = TypeVar("T")


@dataclass
class CursorPagination:
    """Cursor-based pagination parameters."""

    cursor: str | None = None
    limit: int = 20

    def decode_cursor(self) -> dict[str, Any] | None:
        """Decode cursor string to dictionary."""
        if not self.cursor:
            return None
        try:
            decoded = base64.b64decode(self.cursor).decode("utf-8")
            return json.loads(decoded)
        except Exception:
            return None

    @staticmethod
    def encode_cursor(data: dict[str, Any]) -> str:
        """Encode dictionary to cursor string."""
        json_str = json.dumps(data, default=str)
        return base64.b64encode(json_str.encode("utf-8")).decode("utf-8")


@dataclass
class PagedResult(Generic[T]):
    """Paginated result container."""

    items: list[T] = field(default_factory=list)
    next_cursor: str | None = None
    has_more: bool = False
    total: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result: dict[str, Any] = {
            "items": [
                item.to_dict() if hasattr(item, "to_dict") else item
                for item in self.items
            ],
            "next_cursor": self.next_cursor,
            "has_more": self.has_more,
        }
        if self.total is not None:
            result["total"] = self.total
        return result

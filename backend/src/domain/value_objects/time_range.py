"""Time range value object."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any


@dataclass(frozen=True)
class TimeRange:
    """Represents a time range with start and end."""

    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        if self.start > self.end:
            raise ValueError("Start time must be before end time")

    @property
    def duration(self) -> timedelta:
        """Get duration of the time range."""
        return self.end - self.start

    @property
    def duration_seconds(self) -> float:
        """Get duration in seconds."""
        return self.duration.total_seconds()

    def contains(self, dt: datetime) -> bool:
        """Check if a datetime is within the range."""
        return self.start <= dt <= self.end

    def overlaps(self, other: "TimeRange") -> bool:
        """Check if this range overlaps with another."""
        return self.start <= other.end and other.start <= self.end

    @classmethod
    def last_n_days(cls, days: int) -> "TimeRange":
        """Create a time range for the last N days."""
        end = datetime.utcnow()
        start = end - timedelta(days=days)
        return cls(start=start, end=end)

    @classmethod
    def last_n_hours(cls, hours: int) -> "TimeRange":
        """Create a time range for the last N hours."""
        end = datetime.utcnow()
        start = end - timedelta(hours=hours)
        return cls(start=start, end=end)

    @classmethod
    def today(cls) -> "TimeRange":
        """Create a time range for today."""
        now = datetime.utcnow()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
        return cls(start=start, end=end)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "duration_seconds": self.duration_seconds,
        }

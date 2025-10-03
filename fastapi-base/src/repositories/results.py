from datetime import datetime
from typing import Any, Dict, Generic, List, Optional

from src.repositories.types import ModelType


class TimeBasedPaginationResult(Generic[ModelType]):
    """
    Result container for time-based pagination.

    Attributes:
        items: List of items for the current page
        has_next: Whether there are more items after this page
        has_previous: Whether there are items before this page
        next_cursor: Cursor for the next page (timestamp)
        previous_cursor: Cursor for the previous page (timestamp)
        total_count: Optional total count of items (expensive to compute)
    """

    def __init__(
        self,
        items: List[ModelType],
        has_next: bool = False,
        has_previous: bool = False,
        next_cursor: Optional[datetime] = None,
        previous_cursor: Optional[datetime] = None,
        total_count: Optional[int] = None,
    ):
        self.items = items
        self.has_next = has_next
        self.has_previous = has_previous
        self.next_cursor = next_cursor
        self.previous_cursor = previous_cursor
        self.total_count = total_count

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "items": self.items,
            "has_next": self.has_next,
            "has_previous": self.has_previous,
            "next_cursor": self.next_cursor.isoformat() if self.next_cursor else None,
            "previous_cursor": self.previous_cursor.isoformat() if self.previous_cursor else None,
            "total_count": self.total_count,
            "count": len(self.items),
        }

"""Repositories package for data persistence."""

from .deduplication import (
    DeduplicationRepository,
    InMemoryDeduplicationRepository,
    SQLiteDeduplicationRepository,
)

__all__ = [
    "DeduplicationRepository",
    "InMemoryDeduplicationRepository",
    "SQLiteDeduplicationRepository",
]

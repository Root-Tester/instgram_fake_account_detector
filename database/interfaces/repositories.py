"""Persistence contracts without a concrete database dependency."""

from collections.abc import Sequence
from typing import Any, Protocol


class AnalysisRepository(Protocol):
    """Store and retrieve analysis records when persistence is enabled."""

    def save(self, record: dict[str, Any]) -> str:
        """Persist a record and return its identifier."""

    def get(self, record_id: str) -> dict[str, Any] | None:
        """Retrieve a record by identifier."""

    def list_recent(self, limit: int = 100) -> Sequence[dict[str, Any]]:
        """Return recent records."""


class UnitOfWork(Protocol):
    """Transaction boundary for future repository implementations."""

    analyses: AnalysisRepository

    def __enter__(self) -> "UnitOfWork":
        """Open a unit of work."""

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        """Commit or roll back a unit of work."""

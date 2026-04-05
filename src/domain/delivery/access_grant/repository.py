from __future__ import annotations

from typing import Protocol

from .entity import AccessGrant


class AccessGrantRepository(Protocol):
    """Репозиторий агрегата AccessGrant."""

    def get(self, grant_id: str) -> AccessGrant | None:
        """Получить grant по id."""

    def save(self, grant: AccessGrant) -> None:
        """Сохранить агрегат AccessGrant."""

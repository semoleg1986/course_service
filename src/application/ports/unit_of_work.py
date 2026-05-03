"""Порт Unit of Work для write-side use-case курса."""

from __future__ import annotations

from typing import Protocol

from src.application.ports.repositories import RepositoryProvider


class UnitOfWork(Protocol):
    """Контракт явной транзакционной границы application-слоя."""

    @property
    def repositories(self) -> RepositoryProvider:
        """Возвращает write-side репозитории текущей транзакции."""

    def commit(self) -> None:
        """Фиксирует изменения."""

    def rollback(self) -> None:
        """Откатывает изменения."""

    def close(self) -> None:
        """Освобождает ресурсы транзакции."""

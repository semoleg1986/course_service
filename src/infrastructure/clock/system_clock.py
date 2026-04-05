"""Системные часы UTC."""

from __future__ import annotations

from datetime import UTC, datetime


class SystemClock:
    """Реализация порта времени через системные UTC-часы."""

    def now(self) -> datetime:
        """Возвращает текущее UTC-время."""

        return datetime.now(UTC)


"""Порт времени application-слоя."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    """Контракт поставщика времени."""

    def now(self) -> datetime:
        """Возвращает текущее время в UTC."""


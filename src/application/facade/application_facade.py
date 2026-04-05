"""Фасад application-слоя."""

from __future__ import annotations

from typing import Any, Callable


class ApplicationFacade:
    """Единая точка входа в use-cases application-слоя."""

    def __init__(self) -> None:
        self._query_handlers: dict[type, Callable[[Any], Any]] = {}

    def register_query_handler(self, query_type: type, handler: Callable[[Any], Any]) -> None:
        """Регистрирует обработчик query."""

        self._query_handlers[query_type] = handler

    def query(self, query: Any) -> Any:
        """Выполняет query через зарегистрированный handler."""

        handler = self._query_handlers.get(type(query))
        if handler is None:
            raise LookupError(f"Обработчик query не найден: {type(query).__name__}")
        return handler(query)


"""Порт верификации Bearer access token."""

from __future__ import annotations

from typing import Protocol


class AccessTokenVerifier(Protocol):
    """Контракт верификации access token."""

    def decode_access(self, access_token: str) -> dict[str, str | list[str]]:
        """Декодирует access token в claims (`sub`, опциональный `user_id`, `roles`)."""

"""Port for bonus wallet accrual side-effects."""

from __future__ import annotations

from typing import Protocol


class BonusWalletPort(Protocol):
    """Contract for crediting parent bonus wallets."""

    def accrue(
        self,
        *,
        parent_id: str,
        amount: int,
        reason_code: str,
        reference_id: str,
        idempotency_key: str,
    ) -> None:
        """Credit a bonus wallet in a replay-safe way."""

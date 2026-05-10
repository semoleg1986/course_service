"""In-memory bonus wallet adapter for tests."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RecordedBonusAccrual:
    parent_id: str
    amount: int
    reason_code: str
    reference_id: str
    idempotency_key: str


class InMemoryBonusWalletPort:
    """Captures accrual requests for tests and local runtime."""

    def __init__(self) -> None:
        self.accruals: list[RecordedBonusAccrual] = []
        self._seen_keys: set[str] = set()

    def accrue(
        self,
        *,
        parent_id: str,
        amount: int,
        reason_code: str,
        reference_id: str,
        idempotency_key: str,
    ) -> None:
        if idempotency_key in self._seen_keys:
            return
        self._seen_keys.add(idempotency_key)
        self.accruals.append(
            RecordedBonusAccrual(
                parent_id=parent_id,
                amount=amount,
                reason_code=reason_code,
                reference_id=reference_id,
                idempotency_key=idempotency_key,
            )
        )

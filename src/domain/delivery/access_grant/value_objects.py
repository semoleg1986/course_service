from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.domain.errors import InvariantViolationError
from src.domain.shared.statuses import AttributionChannel


@dataclass(frozen=True, slots=True)
class AttributionSnapshot:
    """
    Снимок атрибуции, фиксируемый в access grant.

    :param channel: Канал привлечения.
    :type channel: AttributionChannel
    :param referral_token: Реферальный токен (опционально).
    :type referral_token: str | None
    """

    channel: AttributionChannel
    referral_token: str | None = None
    campaign: str | None = None
    discount_amount: float | None = None
    discount_currency: str | None = None


@dataclass(frozen=True, slots=True)
class PaymentConfirmation:
    """
    Ручное подтверждение оплаты администратором.

    :param paid_amount: Сумма оплаты.
    :type paid_amount: float
    :param currency: Валюта (ISO-4217).
    :type currency: str
    """

    paid_amount: float
    currency: str
    confirmed_by_admin_id: str
    confirmed_at: datetime
    note: str | None = None

    def __post_init__(self) -> None:
        if self.paid_amount < 0:
            raise InvariantViolationError("Сумма оплаты не может быть отрицательной")
        if len(self.currency) != 3:
            raise InvariantViolationError("Валюта должна быть в формате ISO-4217")

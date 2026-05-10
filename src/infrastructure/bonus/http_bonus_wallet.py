"""HTTP adapter for bonus_wallet_service accrual calls."""

from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from src.domain.errors import InvariantViolationError
from src.interface.http.observability import current_correlation_id


class HttpBonusWalletPort:
    """Calls internal bonus wallet accrual endpoint."""

    def __init__(
        self, *, base_url: str, service_token: str, timeout_seconds: float = 2.0
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._service_token = service_token
        self._timeout_seconds = timeout_seconds

    def accrue(
        self,
        *,
        parent_id: str,
        amount: int,
        reason_code: str,
        reference_id: str,
        idempotency_key: str,
    ) -> None:
        request = Request(
            f"{self._base_url}/internal/v1/bonus/accruals",
            data=json.dumps(
                {
                    "parent_id": parent_id,
                    "amount": amount,
                    "reason_code": reason_code,
                    "reference_id": reference_id,
                    "idempotency_key": idempotency_key,
                }
            ).encode("utf-8"),
            headers={
                "X-Service-Token": self._service_token,
                "Content-Type": "application/json",
                **(
                    {"X-Correlation-ID": current_correlation_id()}
                    if current_correlation_id() is not None
                    else {}
                ),
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self._timeout_seconds):
                return
        except HTTPError as exc:
            raise InvariantViolationError(
                "Не удалось начислить бонусы в bonus_wallet_service."
            ) from exc
        except (TimeoutError, URLError) as exc:
            raise InvariantViolationError(
                "Не удалось начислить бонусы в bonus_wallet_service."
            ) from exc

from __future__ import annotations

import pytest
from fastapi import HTTPException

from src.interface.http.common.actor import get_http_actor


class _Verifier:
    def __init__(self, claims: dict | None = None, error: Exception | None = None) -> None:
        self._claims = claims or {}
        self._error = error

    def decode_access(self, _: str) -> dict:
        if self._error is not None:
            raise self._error
        return self._claims


def test_get_http_actor_validation_errors() -> None:
    with pytest.raises(HTTPException):
        get_http_actor(authorization=None, verifier=_Verifier())

    with pytest.raises(HTTPException):
        get_http_actor(authorization="Bearer   ", verifier=_Verifier())

    with pytest.raises(HTTPException):
        get_http_actor(authorization="Bearer token", verifier=_Verifier(error=RuntimeError("bad")))

    with pytest.raises(HTTPException):
        get_http_actor(authorization="Bearer token", verifier=_Verifier(claims={"sub": "", "roles": []}))


def test_get_http_actor_success() -> None:
    actor = get_http_actor(
        authorization="Bearer token",
        verifier=_Verifier(claims={"sub": "acc-1", "roles": ["student", " "]}),
    )
    assert actor.actor_id == "acc-1"
    assert actor.roles == ["student"]

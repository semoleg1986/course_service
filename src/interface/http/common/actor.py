"""Извлечение actor context из Bearer токена."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException

from src.application.ports.access_token_verifier import AccessTokenVerifier
from src.interface.http.wiring import get_access_token_verifier


@dataclass(frozen=True, slots=True)
class HttpActor:
    """Контекст актора, извлеченный из токена."""

    actor_id: str
    roles: list[str]


def get_http_actor(
    authorization: str | None = Header(default=None, alias="Authorization"),
    verifier: AccessTokenVerifier = Depends(get_access_token_verifier),
) -> HttpActor:
    """Возвращает actor context из заголовка Authorization."""

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Требуется Bearer токен.")
    access_token = authorization.removeprefix("Bearer ").strip()
    if not access_token:
        raise HTTPException(status_code=401, detail="Некорректный Bearer токен.")

    try:
        claims = verifier.decode_access(access_token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Некорректный access token.") from exc

    actor_id = str(claims.get("sub", "")).strip()
    roles = [str(role).strip() for role in claims.get("roles", []) if str(role).strip()]
    if not actor_id or not roles:
        raise HTTPException(
            status_code=401,
            detail="Access token не содержит обязательные claims.",
        )
    return HttpActor(actor_id=actor_id, roles=roles)

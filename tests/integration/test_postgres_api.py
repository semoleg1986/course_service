from __future__ import annotations

import base64
import json
import os
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi.testclient import TestClient

from src.interface.http.app import create_app
from src.interface.http.wiring import get_runtime

pytestmark = pytest.mark.integration

_PRIVATE_KEY = Ed25519PrivateKey.generate()
_PUBLIC_KEY = _PRIVATE_KEY.public_key()
_AUDIENCE = "platform_clients"


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _jwks_json() -> str:
    raw = _PUBLIC_KEY.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return json.dumps(
        {
            "keys": [
                {
                    "kty": "OKP",
                    "crv": "Ed25519",
                    "x": _b64url(raw),
                    "alg": "EdDSA",
                    "use": "sig",
                    "kid": "course-it-kid",
                }
            ]
        }
    )


def _access_token(*, sub: str, roles: list[str]) -> str:
    now = datetime.now(UTC)
    claims = {
        "iss": "auth_service",
        "aud": _AUDIENCE,
        "typ": "access",
        "sub": sub,
        "jti": f"jti-{sub}",
        "roles": roles,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=30)).timestamp()),
    }
    return jwt.encode(
        claims,
        _PRIVATE_KEY,
        algorithm="EdDSA",
        headers={"kid": "course-it-kid", "typ": "JWT"},
    )


def _client() -> TestClient:
    os.environ["COURSE_AUTH_JWKS_JSON"] = _jwks_json()
    os.environ["COURSE_AUTH_ISSUER"] = "auth_service"
    os.environ["COURSE_AUTH_AUDIENCE"] = _AUDIENCE
    get_runtime.cache_clear()
    return TestClient(create_app())


def test_postgres_check_by_token_flow() -> None:
    client = _client()
    token = _access_token(sub="admin-it-1", roles=["admin"])

    response = client.post(
        "/internal/v1/access/check-by-token",
        json={
            "course_id": "00000000-0000-0000-0000-000000000001",
            "student_id": "student-1",
            "require_active_grant": True,
            "require_enrollment": True,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["decision"] == "allow"
    assert body["reason_code"] == "admin_override"

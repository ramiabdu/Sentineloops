from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

from fastapi import Depends, Header

from app.core.config import settings
from app.core.errors import AuthenticationError, AuthorizationError

Role = str

ROLE_ADMIN: Role = "admin"
ROLE_ANALYST: Role = "analyst"
ROLE_VIEWER: Role = "viewer"
SUPPORTED_ROLES: tuple[Role, ...] = (ROLE_ADMIN, ROLE_ANALYST, ROLE_VIEWER)
READ_ROLES: tuple[Role, ...] = SUPPORTED_ROLES
SCAN_WRITE_ROLES: tuple[Role, ...] = (ROLE_ADMIN, ROLE_ANALYST)
ACCOUNT_WRITE_ROLES: tuple[Role, ...] = (ROLE_ADMIN,)


@dataclass(frozen=True)
class CurrentUser:
    subject: str
    email: str
    display_name: str
    role: str


def create_session_token(
    user: CurrentUser,
    *,
    now: datetime | None = None,
    ttl_minutes: int | None = None,
) -> str:
    issued_at = now or datetime.now(timezone.utc)
    ttl = ttl_minutes if ttl_minutes is not None else settings.AUTH_TOKEN_TTL_MINUTES
    expires_at = issued_at + timedelta(minutes=ttl)
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user.subject,
        "email": user.email,
        "name": user.display_name,
        "role": user.role,
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    signing_input = ".".join((_encode_json(header), _encode_json(payload)))
    signature = _sign(signing_input)

    return f"{signing_input}.{signature}"


def decode_session_token(token: str, *, now: datetime | None = None) -> CurrentUser:
    token_parts = token.split(".")
    if len(token_parts) != 3:
        raise AuthenticationError()

    encoded_header, encoded_payload, signature = token_parts
    signing_input = f"{encoded_header}.{encoded_payload}"
    expected_signature = _sign(signing_input)
    if not hmac.compare_digest(signature, expected_signature):
        raise AuthenticationError()

    header = _decode_json(encoded_header)
    payload = _decode_json(encoded_payload)
    if header.get("alg") != "HS256" or header.get("typ") != "JWT":
        raise AuthenticationError()

    expires_at = _require_int(payload, "exp")
    current_time = int((now or datetime.now(timezone.utc)).timestamp())
    if current_time >= expires_at:
        raise AuthenticationError()

    return CurrentUser(
        subject=_require_text(payload, "sub"),
        email=_require_text(payload, "email"),
        display_name=_require_text(payload, "name"),
        role=_require_role(payload, "role"),
    )


def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> CurrentUser:
    if authorization is None:
        raise AuthenticationError()

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise AuthenticationError()

    return decode_session_token(token.strip())


def require_roles(*allowed_roles: Role):
    allowed_role_set = set(allowed_roles)

    def require_role(
        current_user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        if current_user.role not in allowed_role_set:
            raise AuthorizationError()

        return current_user

    return require_role


def _encode_json(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    return _base64url_encode(raw)


def _decode_json(value: str) -> dict[str, Any]:
    try:
        decoded = _base64url_decode(value)
        payload = json.loads(decoded)
    except (binascii.Error, ValueError, json.JSONDecodeError) as exc:
        raise AuthenticationError() from exc

    if not isinstance(payload, dict):
        raise AuthenticationError()

    return payload


def _sign(value: str) -> str:
    digest = hmac.new(
        settings.AUTH_SECRET_KEY.encode(),
        value.encode(),
        hashlib.sha256,
    ).digest()
    return _base64url_encode(digest)


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}".encode())


def _require_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or value.strip() == "":
        raise AuthenticationError()
    return value


def _require_role(payload: dict[str, Any], key: str) -> Role:
    role = _require_text(payload, key).lower()
    if role not in SUPPORTED_ROLES:
        raise AuthorizationError()

    return role


def _require_int(payload: dict[str, Any], key: str) -> int:
    value = payload.get(key)
    if not isinstance(value, int):
        raise AuthenticationError()
    return value

"""OIDC discovery + JWKS client with bounded cache and one rotation refresh."""

from __future__ import annotations

import json
import time
from typing import Any
from urllib.request import urlopen

import jwt
from jwt import PyJWKClient
from memdot_core.auth.bearer import BearerValidationError

_CACHE: dict[str, tuple[float, str, PyJWKClient]] = {}
_CACHE_TTL_SECONDS = 300


def discover_jwks_uri(issuer: str) -> str:
    discovery = f"{issuer.rstrip('/')}/.well-known/openid-configuration"
    with urlopen(discovery, timeout=5) as response:  # noqa: S310 — operator-configured issuer
        data = json.loads(response.read().decode("utf-8"))
    jwks_uri = str(data.get("jwks_uri") or "")
    if not jwks_uri.startswith("http"):
        raise BearerValidationError("jwks_uri_missing")
    return jwks_uri


def get_jwks_client(issuer: str) -> PyJWKClient:
    if not issuer.strip():
        raise BearerValidationError("issuer_or_audience_unconfigured")
    now = time.time()
    cached = _CACHE.get(issuer)
    if cached and cached[0] > now:
        return cached[2]
    jwks_uri = discover_jwks_uri(issuer)
    client = PyJWKClient(jwks_uri, cache_keys=True, lifespan=_CACHE_TTL_SECONDS)
    _CACHE[issuer] = (now + _CACHE_TTL_SECONDS, jwks_uri, client)
    return client


def clear_jwks_cache() -> None:
    _CACHE.clear()


def decode_with_jwks_rotation(
    token: str,
    *,
    issuer: str,
    decode_kwargs: dict[str, Any],
) -> dict[str, Any]:
    client = get_jwks_client(issuer)
    try:
        key = client.get_signing_key_from_jwt(token).key
        return jwt.decode(token, key, **decode_kwargs)
    except jwt.PyJWTError:
        _CACHE.pop(issuer, None)
        client = get_jwks_client(issuer)
        try:
            key = client.get_signing_key_from_jwt(token).key
            return jwt.decode(token, key, **decode_kwargs)
        except jwt.PyJWTError as exc:
            raise BearerValidationError("invalid_token") from exc

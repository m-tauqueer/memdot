"""OIDC issuer adapter and token validation."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Any, cast
from urllib.parse import urlencode

import httpx
import jwt
from jwt import PyJWKClient


@dataclass(frozen=True)
class OidcClaims:
    issuer: str
    audience: str
    subject: str
    email: str | None
    provider: str | None
    nonce: str | None
    expires_at: int
    jti: str | None


class OidcValidationError(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class OidcIssuerAdapter:
    """Replaceable issuer adapter for hosted Google broker and self-host OIDC."""

    def __init__(
        self,
        *,
        issuer: str,
        audience: str,
        jwks_client: PyJWKClient | None = None,
        hosted_google_only: bool = False,
        google_issuer_hint: str = "accounts.google.com",
        authorization_endpoint: str | None = None,
        token_endpoint: str | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.issuer = issuer.rstrip("/")
        self.audience = audience
        self.hosted_google_only = hosted_google_only
        self.google_issuer_hint = google_issuer_hint
        self._authorization_endpoint = authorization_endpoint
        self._token_endpoint = token_endpoint
        self._http_client = http_client or httpx.Client(timeout=5.0)
        self._jwks_client = jwks_client or PyJWKClient(
            f"{self.issuer}/protocol/openid-connect/certs"
        )

    def _endpoints(self) -> tuple[str, str]:
        if self._authorization_endpoint and self._token_endpoint:
            return self._authorization_endpoint, self._token_endpoint
        response = self._http_client.get(self.issuer + "/.well-known/openid-configuration")
        response.raise_for_status()
        body = response.json()
        authorization_endpoint = str(body.get("authorization_endpoint", ""))
        token_endpoint = str(body.get("token_endpoint", ""))
        if not authorization_endpoint or not token_endpoint:
            raise OidcValidationError("invalid_discovery")
        self._authorization_endpoint = authorization_endpoint
        self._token_endpoint = token_endpoint
        return authorization_endpoint, token_endpoint

    def authorization_url(
        self,
        *,
        client_id: str,
        redirect_uri: str,
        state: str,
        nonce: str,
        code_challenge: str,
    ) -> str:
        authorization_endpoint, _ = self._endpoints()
        query = urlencode(
            {
                "response_type": "code",
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "scope": "openid email profile",
                "state": state,
                "nonce": nonce,
                "code_challenge": code_challenge,
                "code_challenge_method": "S256",
            }
        )
        return f"{authorization_endpoint}?{query}"

    def exchange_code(
        self,
        *,
        code: str,
        code_verifier: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
    ) -> str:
        _, token_endpoint = self._endpoints()
        try:
            response = self._http_client.post(
                token_endpoint,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "code_verifier": code_verifier,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri,
                },
                headers={"accept": "application/json"},
            )
            response.raise_for_status()
            id_token = str(response.json().get("id_token", ""))
        except (httpx.HTTPError, ValueError, TypeError) as exc:
            raise OidcValidationError("oidc_code_exchange_failed") from exc
        if not id_token:
            raise OidcValidationError("oidc_id_token_missing")
        return id_token

    def validate_id_token(
        self,
        token: str,
        *,
        expected_nonce: str | None = None,
        seen_jti: set[str] | None = None,
    ) -> OidcClaims:
        try:
            signing_key = self._jwks_client.get_signing_key_from_jwt(token)
            payload: dict[str, Any] = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256", "ES256"],
                audience=self.audience,
                issuer=self.issuer,
                options={"require": ["exp", "sub", "iss", "aud"]},
            )
        except jwt.ExpiredSignatureError as exc:
            raise OidcValidationError("token_expired") from exc
        except jwt.InvalidAudienceError as exc:
            raise OidcValidationError("invalid_audience") from exc
        except jwt.InvalidIssuerError as exc:
            raise OidcValidationError("invalid_issuer") from exc
        except jwt.InvalidSignatureError as exc:
            raise OidcValidationError("invalid_signature") from exc
        except jwt.PyJWTError as exc:
            raise OidcValidationError("invalid_token") from exc

        sub = str(payload.get("sub", "")).strip()
        if not sub:
            raise OidcValidationError("missing_sub")

        if expected_nonce is not None:
            token_nonce = payload.get("nonce")
            if token_nonce != expected_nonce:
                raise OidcValidationError("invalid_nonce")

        jti = str(payload.get("jti", "")).strip()
        if seen_jti is not None and jti:
            if jti in seen_jti:
                raise OidcValidationError("replay_detected")
            seen_jti.add(jti)

        provider = self._resolve_provider(payload)
        if self.hosted_google_only and provider != "google":
            raise OidcValidationError("non_google_provider")

        exp = int(payload.get("exp", 0))
        nbf = payload.get("nbf")
        if nbf is not None and int(nbf) > int(time.time()):
            raise OidcValidationError("token_not_yet_valid")

        audience_raw = payload["aud"]
        if isinstance(audience_raw, list):
            audience = str(cast(Any, audience_raw[0]))
        else:
            audience = str(audience_raw)

        return OidcClaims(
            issuer=str(payload["iss"]),
            audience=audience,
            subject=sub,
            email=str(payload.get("email")) if payload.get("email") else None,
            provider=provider,
            nonce=str(payload.get("nonce")) if payload.get("nonce") else None,
            expires_at=exp,
            jti=jti or None,
        )

    def _resolve_provider(self, payload: dict[str, Any]) -> str | None:
        issuer = str(payload.get("iss", ""))
        if self.google_issuer_hint in issuer:
            return "google"
        identity_provider = payload.get("identity_provider") or payload.get("idp")
        if identity_provider is not None:
            return str(identity_provider)
        return None


def fetch_discovery(issuer: str, *, timeout: float = 5.0) -> dict[str, Any]:
    url = issuer.rstrip("/") + "/.well-known/openid-configuration"
    response = httpx.get(url, timeout=timeout)
    response.raise_for_status()
    body: dict[str, Any] = response.json()
    return body


def new_oidc_state() -> str:
    return uuid.uuid4().hex

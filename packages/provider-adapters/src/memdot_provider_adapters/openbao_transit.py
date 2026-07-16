"""OpenBao Transit adapter implementing SecretCipherPort."""

from __future__ import annotations

import base64
from typing import Any, cast
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class OpenBaoTransitAdapter:
    """Least-privilege Transit encrypt/decrypt client.

    Expects an application token scoped to transit encrypt/decrypt only.
    Root/bootstrap tokens must never be supplied through application config.
    """

    def __init__(
        self,
        *,
        address: str,
        token: str,
        mount: str = "transit",
        timeout_seconds: float = 5.0,
    ) -> None:
        if not address.strip():
            msg = "OpenBao address must be non-empty"
            raise ValueError(msg)
        if not token.strip():
            msg = "OpenBao transit token must be non-empty"
            raise ValueError(msg)
        if token.strip().lower() in {"root", "replace_with_operator_secret"}:
            msg = "Refusing root/placeholder OpenBao tokens in application config"
            raise ValueError(msg)
        self._address = address.rstrip("/")
        self._token = token
        self._mount = mount.strip("/") or "transit"
        self._timeout = timeout_seconds

    def encrypt(self, plaintext: bytes, *, key_name: str) -> bytes:
        payload = {
            "plaintext": base64.b64encode(plaintext).decode("ascii"),
        }
        data = self._request("POST", f"{self._mount}/encrypt/{key_name}", payload)
        ciphertext = data.get("data", {}).get("ciphertext")
        if not isinstance(ciphertext, str) or not ciphertext:
            msg = "OpenBao encrypt response missing ciphertext"
            raise RuntimeError(msg)
        return ciphertext.encode("utf-8")

    def decrypt(self, ciphertext: bytes, *, key_name: str) -> bytes:
        payload = {
            "ciphertext": ciphertext.decode("utf-8"),
        }
        data = self._request("POST", f"{self._mount}/decrypt/{key_name}", payload)
        plaintext_b64 = data.get("data", {}).get("plaintext")
        if not isinstance(plaintext_b64, str) or not plaintext_b64:
            msg = "OpenBao decrypt response missing plaintext"
            raise RuntimeError(msg)
        return base64.b64decode(plaintext_b64.encode("ascii"))

    def _request(self, method: str, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        import json

        body = json.dumps(payload).encode("utf-8")
        request = Request(
            f"{self._address}/v1/{path}",
            data=body,
            method=method,
            headers={
                "Content-Type": "application/json",
                "X-Vault-Token": self._token,
            },
        )
        try:
            with urlopen(request, timeout=self._timeout) as response:  # noqa: S310
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            msg = f"OpenBao Transit request failed with HTTP {exc.code}"
            raise RuntimeError(msg) from None
        except URLError as exc:
            msg = "OpenBao Transit request failed"
            raise RuntimeError(msg) from exc
        parsed: object = json.loads(raw)
        if not isinstance(parsed, dict):
            msg = "OpenBao Transit returned unexpected payload"
            raise RuntimeError(msg)
        typed = cast(dict[str, Any], parsed)
        return typed

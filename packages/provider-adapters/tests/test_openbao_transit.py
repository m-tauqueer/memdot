"""OpenBao Transit adapter unit tests (no network)."""

from __future__ import annotations

import base64
import json
from typing import Any

import pytest
from memdot_provider_adapters.openbao_transit import OpenBaoTransitAdapter


class _FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *_args: object) -> None:
        return None


def test_rejects_root_token() -> None:
    with pytest.raises(ValueError, match="root/placeholder"):
        OpenBaoTransitAdapter(address="http://openbao:8200", token="root")


def test_encrypt_decrypt_round_trip(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = OpenBaoTransitAdapter(address="http://openbao:8200", token="app-transit-token")
    calls: list[str] = []

    def fake_urlopen(request: Any, timeout: float = 0) -> _FakeResponse:  # noqa: ARG001
        path = request.full_url
        calls.append(path)
        body = json.loads(request.data.decode("utf-8"))
        if path.endswith("/encrypt/memdot-local"):
            return _FakeResponse(
                {"data": {"ciphertext": "vault:v1:" + body["plaintext"]}},
            )
        plaintext = body["ciphertext"].removeprefix("vault:v1:")
        return _FakeResponse({"data": {"plaintext": plaintext}})

    monkeypatch.setattr(
        "memdot_provider_adapters.openbao_transit.urlopen",
        fake_urlopen,
    )

    ciphertext = adapter.encrypt(b"fixture-secret", key_name="memdot-local")
    plaintext = adapter.decrypt(ciphertext, key_name="memdot-local")
    assert plaintext == b"fixture-secret"
    assert any("encrypt" in item for item in calls)
    assert any("decrypt" in item for item in calls)
    # Ensure adapter never base64-decodes incorrectly
    assert base64.b64encode(b"fixture-secret").decode("ascii") in ciphertext.decode("utf-8")

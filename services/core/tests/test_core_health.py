from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from memdot_core.app import create_app
from memdot_core.settings import CoreSettings
from memdot_domain.health_probes import ProbeResult


def test_live_and_ready() -> None:
    client = TestClient(create_app(CoreSettings(env="test")))
    assert client.get("/health/live").json()["status"] == "ok"
    ready = client.get("/health/ready").json()
    assert ready["status"] == "ok"
    assert ready["service"] == "core"


def test_ready_degrades_on_postgres() -> None:
    settings = CoreSettings(
        env="test",
        database_url="postgres://memdot:x@postgres:5432/memdot",
    )
    with patch(
        "memdot_core.app.probe_postgres_select1",
        return_value=ProbeResult(ok=False, dependency="postgres"),
    ):
        client = TestClient(create_app(settings))
        resp = client.get("/health/ready")
    assert resp.status_code == 503
    assert resp.json()["dependency"] == "postgres"


def test_ready_degrades_on_openbao() -> None:
    settings = CoreSettings(
        env="test",
        openbao_addr="http://openbao:8200",
        openbao_transit_token="test-token",
    )
    with (
        patch(
            "memdot_core.app.probe_postgres_select1",
            return_value=ProbeResult(ok=True, dependency="postgres"),
        ),
        patch(
            "memdot_core.app.probe_openbao_transit",
            return_value=ProbeResult(ok=False, dependency="openbao"),
        ),
    ):
        client = TestClient(create_app(settings))
        resp = client.get("/health/ready")
    assert resp.status_code == 503
    assert resp.json()["dependency"] == "openbao"


def test_ready_degrades_on_seaweed() -> None:
    settings = CoreSettings(
        env="test",
        object_store_endpoint="http://seaweedfs:8333",
        object_store_access_key="ak",
        object_store_secret_key="sk",
    )
    with (
        patch(
            "memdot_core.app.probe_postgres_select1",
            return_value=ProbeResult(ok=True, dependency="postgres"),
        ),
        patch(
            "memdot_core.app.probe_openbao_transit",
            return_value=ProbeResult(ok=True, dependency="openbao"),
        ),
        patch(
            "memdot_core.app.probe_seaweed_s3",
            return_value=ProbeResult(ok=False, dependency="seaweedfs"),
        ),
    ):
        client = TestClient(create_app(settings))
        resp = client.get("/health/ready")
    assert resp.status_code == 503
    assert resp.json()["dependency"] == "seaweedfs"


def test_settings_reject_blank_env() -> None:
    settings = CoreSettings(env="   ")
    with pytest.raises(ValueError, match="non-empty|CORE_ENV"):
        settings.validate_runtime()


def test_error_code_registry() -> None:
    client = TestClient(create_app(CoreSettings(env="test")))
    codes = client.get("/api/v1/meta/error-codes").json()["codes"]
    assert "internal_error" in codes

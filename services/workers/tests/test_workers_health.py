from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from memdot_domain.health_probes import ProbeResult
from memdot_workers.app import create_app
from memdot_workers.settings import WorkersSettings


def test_workers_health() -> None:
    with patch(
        "memdot_workers.app.probe_tcp_host_port",
        return_value=ProbeResult(ok=True, dependency="tcp"),
    ):
        client = TestClient(create_app(WorkersSettings(env="test")))
        assert client.get("/health/live").json()["status"] == "ok"
        assert client.get("/health/ready").json()["service"] == "workers"


def test_workers_ready_degrades_when_hatchet_down() -> None:
    with patch(
        "memdot_workers.app.probe_tcp_host_port",
        return_value=ProbeResult(ok=False, dependency="tcp"),
    ):
        client = TestClient(create_app(WorkersSettings(env="test")))
        resp = client.get("/health/ready")
    assert resp.status_code == 503
    assert resp.json()["dependency"] == "hatchet"


def test_workers_settings_reject_blank_env() -> None:
    settings = WorkersSettings(env=" ")
    with pytest.raises(ValueError, match="WORKERS_ENV"):
        settings.validate_runtime()

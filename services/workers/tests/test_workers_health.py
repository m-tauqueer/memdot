import pytest
from fastapi.testclient import TestClient
from memdot_workers.app import create_app
from memdot_workers.settings import WorkersSettings


def test_workers_health() -> None:
    client = TestClient(create_app(WorkersSettings(env="test")))
    assert client.get("/health/live").json()["status"] == "ok"
    assert client.get("/health/ready").json()["service"] == "workers"


def test_workers_settings_reject_blank_env() -> None:
    settings = WorkersSettings(env=" ")
    with pytest.raises(ValueError, match="WORKERS_ENV"):
        settings.validate_runtime()

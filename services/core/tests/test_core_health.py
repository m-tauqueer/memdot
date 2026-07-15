import pytest
from fastapi.testclient import TestClient
from memdot_core.app import create_app
from memdot_core.settings import CoreSettings


def test_live_and_ready() -> None:
    client = TestClient(create_app(CoreSettings(env="test")))
    assert client.get("/health/live").json()["status"] == "ok"
    ready = client.get("/health/ready").json()
    assert ready["status"] == "ok"
    assert ready["service"] == "core"


def test_settings_reject_blank_env() -> None:
    settings = CoreSettings(env="   ")
    with pytest.raises(ValueError, match="CORE_ENV"):
        settings.validate_runtime()


def test_error_code_registry() -> None:
    client = TestClient(create_app(CoreSettings(env="test")))
    codes = client.get("/api/v1/meta/error-codes").json()["codes"]
    assert "internal_error" in codes

import pytest
from fastapi.testclient import TestClient
from memdot_model_router.app import create_app
from memdot_model_router.settings import ModelRouterSettings


def test_model_router_health() -> None:
    client = TestClient(create_app(ModelRouterSettings(env="test")))
    assert client.get("/health/live").json()["status"] == "ok"
    assert client.get("/health/ready").json()["service"] == "model-router"


def test_model_router_settings_reject_blank_env() -> None:
    settings = ModelRouterSettings(env=" ")
    with pytest.raises(ValueError, match="MODEL_ROUTER_ENV"):
        settings.validate_runtime()

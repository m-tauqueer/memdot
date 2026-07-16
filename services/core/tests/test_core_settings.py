"""Expanded Core settings negatives for Phase 2 correction."""

import pytest
from memdot_core.settings import CoreSettings


def test_self_host_requires_oidc_issuer() -> None:
    settings = CoreSettings(
        env="self_host",
        database_url="postgres://memdot:x@postgres:5432/memdot",
        object_store_endpoint="http://seaweedfs:8333",
        oidc_issuer="",
        openbao_addr="http://openbao:8200",
        openbao_transit_token="app-token-value",
    )
    with pytest.raises(ValueError, match="CORE_OIDC_ISSUER"):
        settings.validate_runtime()


def test_self_host_rejects_root_transit_token() -> None:
    settings = CoreSettings(
        env="self_host",
        database_url="postgres://memdot:x@postgres:5432/memdot",
        object_store_endpoint="http://seaweedfs:8333",
        oidc_issuer="https://localhost/realms/memdot",
        openbao_addr="http://openbao:8200",
        openbao_transit_token="root",
    )
    with pytest.raises(ValueError, match="root/bootstrap"):
        settings.validate_runtime()


def test_self_host_rejects_placeholder_transit_token() -> None:
    settings = CoreSettings(
        env="self_host",
        database_url="postgres://memdot:x@postgres:5432/memdot",
        object_store_endpoint="http://seaweedfs:8333",
        oidc_issuer="https://localhost/realms/memdot",
        openbao_addr="http://openbao:8200",
        openbao_transit_token="REPLACE_WITH_OPERATOR_SECRET",
    )
    with pytest.raises(ValueError, match="production secrets"):
        settings.validate_runtime()


def test_rejects_wildcard_origins() -> None:
    settings = CoreSettings(env="development", allowed_origins="https://*")
    with pytest.raises(ValueError, match="wildcard"):
        settings.validate_runtime()


def test_rejects_exporter_without_endpoint() -> None:
    settings = CoreSettings(
        env="development",
        telemetry_export="otlp",
        otel_exporter_otlp_endpoint="",
    )
    with pytest.raises(ValueError, match="exporter"):
        settings.validate_runtime()

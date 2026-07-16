"""Negative Compose policy fixtures."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "infra" / "compose" / "scripts"))

from validate_compose_policy import validate_document  # noqa: E402


def _base_doc() -> dict[str, Any]:
    # Minimal valid-shaped document; tests mutate to prove rules fire.
    return {
        "services": {
            "caddy": {
                "image": "caddy:2.9.1-alpine@sha256:" + ("a" * 64),
                "networks": ["memdot_public", "memdot_app"],
                "ports": ["80:80"],
                "healthcheck": {"test": ["CMD", "true"]},
            },
            "web": {
                "image": "memdot-web:local",
                "networks": ["memdot_app", "memdot_observability"],
                "healthcheck": {"test": ["CMD", "true"]},
                "environment": {"OTEL_SDK_DISABLED": "true", "OTEL_EXPORTER_OTLP_ENDPOINT": ""},
            },
            "core": {
                "image": "memdot-core:local",
                "networks": [
                    "memdot_app",
                    "memdot_data",
                    "memdot_workflow",
                    "memdot_observability",
                ],
                "healthcheck": {"test": ["CMD", "true"]},
                "environment": {"OTEL_SDK_DISABLED": "true", "OTEL_EXPORTER_OTLP_ENDPOINT": ""},
            },
            "mcp": {
                "image": "memdot-mcp:local",
                "networks": ["memdot_app", "memdot_observability"],
                "healthcheck": {"test": ["CMD", "true"]},
                "environment": {"OTEL_SDK_DISABLED": "true", "OTEL_EXPORTER_OTLP_ENDPOINT": ""},
            },
            "workers": {
                "image": "memdot-workers:local",
                "networks": [
                    "memdot_app",
                    "memdot_data",
                    "memdot_workflow",
                    "memdot_observability",
                ],
                "healthcheck": {"test": ["CMD", "true"]},
                "environment": {"OTEL_SDK_DISABLED": "true", "OTEL_EXPORTER_OTLP_ENDPOINT": ""},
            },
            "model-router": {
                "image": "memdot-model-router:local",
                "networks": ["memdot_app", "memdot_observability"],
                "healthcheck": {"test": ["CMD", "true"]},
                "environment": {"OTEL_SDK_DISABLED": "true", "OTEL_EXPORTER_OTLP_ENDPOINT": ""},
            },
            "postgres": {
                "image": "pgvector/pgvector:pg16@sha256:" + ("b" * 64),
                "networks": ["memdot_data", "memdot_workflow"],
                "healthcheck": {"test": ["CMD", "true"]},
            },
            "seaweedfs": {
                "image": "chrislusf/seaweedfs:3.80@sha256:" + ("c" * 64),
                "networks": ["memdot_data"],
                "healthcheck": {"test": ["CMD", "true"]},
            },
            "keycloak": {
                "image": "quay.io/keycloak/keycloak:26.0.7@sha256:" + ("d" * 64),
                "networks": ["memdot_app", "memdot_data"],
                "healthcheck": {"test": ["CMD", "true"]},
            },
            "openbao": {
                "image": "openbao/openbao:2.1.0@sha256:" + ("e" * 64),
                "command": ["server", "-config=/openbao/config/config.hcl"],
                "networks": ["memdot_data"],
                "healthcheck": {"test": ["CMD", "true"]},
            },
            "openbao-bootstrap": {
                "image": "openbao/openbao:2.1.0@sha256:" + ("e" * 64),
                "networks": ["memdot_data"],
            },
            "otel-lgtm": {
                "image": "grafana/otel-lgtm:0.11.0@sha256:" + ("f" * 64),
                "networks": ["memdot_observability"],
                "healthcheck": {"test": ["CMD", "true"]},
            },
            "hatchet-migrate": {
                "image": "ghcr.io/hatchet-dev/hatchet/hatchet-migrate:v0.55.0@sha256:" + ("1" * 64),
                "networks": ["memdot_workflow", "memdot_data"],
            },
            "hatchet-setup-config": {
                "image": "ghcr.io/hatchet-dev/hatchet/hatchet-admin:v0.55.0@sha256:" + ("2" * 64),
                "networks": ["memdot_workflow", "memdot_data"],
            },
            "hatchet-engine": {
                "image": "ghcr.io/hatchet-dev/hatchet/hatchet-engine:v0.55.0@sha256:" + ("3" * 64),
                "networks": ["memdot_workflow", "memdot_data"],
                "healthcheck": {"test": ["CMD", "true"]},
            },
            "hatchet-api": {
                "image": "ghcr.io/hatchet-dev/hatchet/hatchet-api:v0.55.0@sha256:" + ("4" * 64),
                "networks": ["memdot_workflow", "memdot_data", "memdot_app"],
                "healthcheck": {"test": ["CMD", "true"]},
            },
        },
        "networks": {
            "memdot_public": {},
            "memdot_app": {},
            "memdot_data": {"internal": True},
            "memdot_workflow": {"internal": True},
            "memdot_observability": {"internal": True},
        },
        "volumes": {
            "postgres_data": {},
            "seaweed_data": {},
            "openbao_data": {},
            "keycloak_data": {},
            "hatchet_certs": {},
            "hatchet_config": {},
            "otel_data": {},
        },
    }


def test_rejects_tex_service() -> None:
    doc = _base_doc()
    doc["services"]["tex"] = {"image": "tex:1@sha256:" + ("a" * 64)}
    errors = validate_document(doc, label="fixture")
    assert any("forbidden services" in e for e in errors)


def test_rejects_openbao_dev_mode() -> None:
    doc = _base_doc()
    doc["services"]["openbao"]["command"] = ["server", "-dev"]
    errors = validate_document(doc, label="fixture")
    assert any("not use -dev" in e for e in errors)


def test_rejects_public_postgres_port() -> None:
    doc = _base_doc()
    doc["services"]["postgres"]["ports"] = ["5432:5432"]
    errors = validate_document(doc, label="fixture")
    assert any("forbidden host bind" in e for e in errors)


def test_rejects_missing_internal_network_flag() -> None:
    doc = _base_doc()
    doc["networks"]["memdot_data"] = {}
    errors = validate_document(doc, label="fixture")
    assert any("internal: true" in e for e in errors)


def test_rejects_floating_image() -> None:
    doc = _base_doc()
    doc["services"]["caddy"]["image"] = "caddy:2.9.1-alpine"
    errors = validate_document(doc, label="fixture")
    assert any("digest pin" in e for e in errors)


def test_rejects_docker_socket() -> None:
    doc = _base_doc()
    doc["services"]["caddy"]["volumes"] = ["/var/run/docker.sock:/var/run/docker.sock"]
    errors = validate_document(doc, label="fixture")
    assert any("docker.sock" in e for e in errors)


def test_rejects_credential_fragment() -> None:
    doc = _base_doc()
    doc["services"]["core"]["environment"]["CORE_X"] = "memdot-local-dev-only-secret"
    errors = validate_document(doc, label="fixture")
    assert any("forbidden credential fragment" in e for e in errors)


def test_valid_base_fixture_passes() -> None:
    errors = validate_document(_base_doc(), label="fixture")
    assert errors == []

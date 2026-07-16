#!/usr/bin/env python3
"""Validate rendered Memdot Compose policy invariants (Phase 2 correction)."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
COMPOSE_DIR = ROOT / "infra" / "compose"

REQUIRED_NETWORKS = {
    "memdot_public",
    "memdot_app",
    "memdot_data",
    "memdot_workflow",
    "memdot_observability",
}
INTERNAL_NETWORKS = {"memdot_data", "memdot_workflow", "memdot_observability"}

REQUIRED_VOLUMES = {
    "postgres_data",
    "seaweed_data",
    "openbao_data",
    "keycloak_data",
    "hatchet_certs",
    "hatchet_config",
    "otel_data",
}

REQUIRED_DEFAULT_SERVICES = {
    "caddy",
    "web",
    "core",
    "mcp",
    "workers",
    "model-router",
    "postgres",
    "seaweedfs",
    "keycloak",
    "openbao",
    "openbao-bootstrap",
    "otel-lgtm",
    "hatchet-migrate",
    "hatchet-setup-config",
    "hatchet-engine",
    "hatchet-api",
}

ONE_SHOT_SERVICES = {"hatchet-migrate", "hatchet-setup-config", "openbao-bootstrap"}
FORBIDDEN_SERVICES = {"tex"}
PUBLIC_PUBLISH_SERVICES = {"caddy"}
# Allowed only as an additive overlay network for loopback operator publishes.
OPTIONAL_OVERLAY_NETWORKS = {"memdot_ops"}

LOCAL_IMAGE_PATTERN = re.compile(r"^memdot-[a-z0-9-]+:local$")
DIGEST_PATTERN = re.compile(r"@sha256:[a-f0-9]{64}$")

FORBIDDEN_CREDENTIAL_FRAGMENTS = (
    "phase2-core-client-secret-not-for-production",
    "phase2-mcp-client-secret-not-for-production",
    "memdot-local-access",
    "memdot-local-secret-not-for-production",
    "memdot-local-dev-only-secret",
    "-dev-root-token-id",
    "REPLACE_WITH_OPERATOR_SECRET",
)

ALLOWED_NETWORK_ATTACHMENTS: dict[str, set[str]] = {
    "caddy": {"memdot_public", "memdot_app"},
    "web": {"memdot_app", "memdot_observability"},
    "core": {"memdot_app", "memdot_data", "memdot_workflow", "memdot_observability"},
    "mcp": {"memdot_app", "memdot_observability"},
    "workers": {"memdot_app", "memdot_data", "memdot_workflow", "memdot_observability"},
    "model-router": {"memdot_app", "memdot_observability"},
    "postgres": {"memdot_data", "memdot_workflow"},
    "seaweedfs": {"memdot_data"},
    "keycloak": {"memdot_app", "memdot_data"},
    "openbao": {"memdot_data"},
    "openbao-bootstrap": {"memdot_data"},
    "otel-lgtm": {"memdot_observability"},
    "hatchet-migrate": {"memdot_workflow", "memdot_data"},
    "hatchet-setup-config": {"memdot_workflow", "memdot_data"},
    "hatchet-engine": {"memdot_workflow", "memdot_data"},
    "hatchet-api": {"memdot_workflow", "memdot_data", "memdot_app"},
}


def env_file_args() -> list[str]:
    for candidate in (COMPOSE_DIR / ".env", COMPOSE_DIR / ".env.example"):
        if candidate.is_file():
            return ["--env-file", str(candidate)]
    return []


def render_compose(extra_files: list[Path] | None = None) -> dict[str, Any]:
    # Use a fixed valid project name so a disposable smoke .env with an invalid
    # COMPOSE_PROJECT_NAME cannot break policy rendering.
    cmd = [
        "docker",
        "compose",
        "--project-name",
        "memdot-policy-check",
        *env_file_args(),
        "-f",
        str(COMPOSE_DIR / "compose.yaml"),
    ]
    for extra in extra_files or []:
        cmd.extend(["-f", str(extra)])
    cmd.extend(["config", "--format", "json"])
    env = {**os.environ, "COMPOSE_PROJECT_NAME": "memdot-policy-check"}
    result = subprocess.run(
        cmd,
        check=True,
        capture_output=True,
        text=True,
        cwd=ROOT,
        env=env,
    )
    data = json.loads(result.stdout)
    return data if isinstance(data, dict) else {}


def parse_port_binding(binding: Any) -> tuple[str | None, str | None]:
    if isinstance(binding, dict):
        host = binding.get("host_ip")
        published = binding.get("published")
        return (
            str(host) if host not in (None, "") else None,
            str(published) if published is not None else None,
        )
    if isinstance(binding, int):
        return None, str(binding)
    if not isinstance(binding, str):
        return None, None
    parts = binding.split(":")
    if len(parts) == 1:
        return None, parts[0]
    if len(parts) == 2:
        return None, parts[0]
    if len(parts) == 3:
        return parts[0], parts[1]
    return None, binding


def is_loopback_host(host: str | None) -> bool:
    return host in {"127.0.0.1", "::1"}


def service_networks(service: dict[str, Any]) -> set[str]:
    raw = service.get("networks")
    if raw is None:
        return set()
    if isinstance(raw, list):
        return {str(item) for item in raw}
    if isinstance(raw, dict):
        return set(raw.keys())
    return set()


def validate_document(document: dict[str, Any], *, label: str) -> list[str]:
    errors: list[str] = []
    services: dict[str, Any] = document.get("services", {}) or {}
    networks_doc: dict[str, Any] = document.get("networks", {}) or {}
    volumes = set((document.get("volumes", {}) or {}).keys())

    missing_networks = REQUIRED_NETWORKS - set(networks_doc.keys())
    if missing_networks:
        errors.append(f"{label}: missing networks: {sorted(missing_networks)}")

    for name in INTERNAL_NETWORKS:
        net = networks_doc.get(name) or {}
        if not net.get("internal"):
            errors.append(f"{label}: network '{name}' must set internal: true")

    missing_volumes = REQUIRED_VOLUMES - volumes
    if missing_volumes:
        errors.append(f"{label}: missing volumes: {sorted(missing_volumes)}")

    present = set(services.keys())
    missing_services = REQUIRED_DEFAULT_SERVICES - present
    if missing_services:
        errors.append(f"{label}: missing default services: {sorted(missing_services)}")

    forbidden = FORBIDDEN_SERVICES & present
    if forbidden:
        errors.append(f"{label}: forbidden services present: {sorted(forbidden)}")

    rendered = json.dumps(document)
    for fragment in FORBIDDEN_CREDENTIAL_FRAGMENTS:
        if fragment in rendered:
            errors.append(f"{label}: forbidden credential fragment in render: {fragment}")

    if "server -dev" in rendered or '"-dev"' in rendered or " -dev" in rendered:
        # Allow only if openbao command is not -dev in base; check openbao specifically
        openbao = services.get("openbao") or {}
        cmd = openbao.get("command")
        cmd_text = " ".join(cmd) if isinstance(cmd, list) else str(cmd or "")
        if "-dev" in cmd_text:
            errors.append(f"{label}: openbao base must not use -dev mode")

    for service_name, service in services.items():
        if service.get("privileged") is True:
            errors.append(f"{label}: service '{service_name}' is privileged")
        if service.get("network_mode") == "host":
            errors.append(f"{label}: service '{service_name}' uses host networking")

        for volume in service.get("volumes", []) or []:
            volume_text = str(volume)
            if "docker.sock" in volume_text:
                errors.append(f"{label}: service '{service_name}' mounts docker.sock")

        image = service.get("image")
        if isinstance(image, str):
            if LOCAL_IMAGE_PATTERN.match(image):
                pass
            elif not DIGEST_PATTERN.search(image):
                errors.append(
                    f"{label}: service '{service_name}' image lacks digest pin: {image}",
                )

        if service_name not in ONE_SHOT_SERVICES and not service.get("healthcheck"):
            errors.append(f"{label}: service '{service_name}' missing healthcheck")

        expected_nets = ALLOWED_NETWORK_ATTACHMENTS.get(service_name)
        if expected_nets is not None:
            actual = service_networks(service)
            missing = expected_nets - actual
            extra = actual - expected_nets
            if missing:
                errors.append(
                    f"{label}: service '{service_name}' missing networks "
                    f"{sorted(missing)} (have {sorted(actual)})",
                )
            forbidden_extra = extra - OPTIONAL_OVERLAY_NETWORKS
            if forbidden_extra:
                errors.append(
                    f"{label}: service '{service_name}' has forbidden extra networks "
                    f"{sorted(forbidden_extra)}",
                )

        for binding in service.get("ports", []) or []:
            host, _published = parse_port_binding(binding)
            if is_loopback_host(host):
                continue
            if host in (None, "", "0.0.0.0"):
                if service_name in PUBLIC_PUBLISH_SERVICES:
                    continue
                errors.append(
                    f"{label}: service '{service_name}' publishes forbidden host bind: {binding}",
                )

        # Telemetry export must stay disabled by default for app services
        env = service.get("environment") or {}
        if isinstance(env, dict):
            export = str(env.get("OTEL_EXPORTER_OTLP_ENDPOINT", "") or "")
            disabled = str(env.get("OTEL_SDK_DISABLED", "") or "").lower()
            if export.strip() and disabled not in {"true", "1", "yes"}:
                if service_name in {"web", "core", "mcp", "workers", "model-router"}:
                    errors.append(
                        f"{label}: service '{service_name}' enables OTLP export "
                        "without SDK disabled",
                    )

    return errors


def validate_source_tree() -> list[str]:
    errors: list[str] = []
    for path in (
        COMPOSE_DIR / "config" / "keycloak" / "realm-memdot.json",
        COMPOSE_DIR / "config" / "seaweedfs" / "s3.json.template",
    ):
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            for fragment in FORBIDDEN_CREDENTIAL_FRAGMENTS:
                if fragment in text:
                    errors.append(f"source: committed credential in {path}: {fragment}")
            if '"secret"' in text and "template" not in path.name:
                errors.append(f"source: committed Keycloak secret field in {path}")
            if "accessKey" in text and "template" not in path.name:
                errors.append(f"source: committed S3 accessKey in {path}")
    return errors


def main() -> int:
    all_errors: list[str] = []
    all_errors.extend(validate_source_tree())

    try:
        base_doc = render_compose()
    except Exception as exc:  # noqa: BLE001
        all_errors.append(f"Failed to render base compose: {exc}")
        base_doc = {}

    if base_doc:
        all_errors.extend(validate_document(base_doc, label="base-rendered"))

    for extra_name in ("compose.dev.yaml", "compose.test.yaml"):
        extra_path = COMPOSE_DIR / extra_name
        if not extra_path.is_file():
            all_errors.append(f"Missing compose overlay: {extra_path}")
            continue
        try:
            merged = render_compose([extra_path])
        except Exception as exc:  # noqa: BLE001
            all_errors.append(f"Failed to render with {extra_name}: {exc}")
            continue
        all_errors.extend(validate_document(merged, label=f"merged-{extra_name}"))

    if not (COMPOSE_DIR / "images.lock.yaml").is_file():
        all_errors.append("Missing image lock registry")

    if all_errors:
        print("Compose policy validation FAILED:", file=sys.stderr)
        for error in all_errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print("Compose policy validation passed.")
    print(f"  default services: {len(REQUIRED_DEFAULT_SERVICES)}")
    print(f"  networks: {len(REQUIRED_NETWORKS)}")
    print(f"  volumes: {len(REQUIRED_VOLUMES)}")
    print("  tex: absent")
    print("  openbao: not -dev")
    return 0


if __name__ == "__main__":
    sys.exit(main())

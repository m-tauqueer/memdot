"""Content-free dependency probes for Phase 2 readiness (no product behavior)."""

from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, cast
from urllib.parse import urlparse


@dataclass(frozen=True)
class ProbeResult:
    ok: bool
    dependency: str
    detail: str = ""


def probe_postgres_select1(database_url: str, *, timeout: float = 2.0) -> ProbeResult:
    """Bounded SELECT 1 against PostgreSQL (not TCP-only)."""
    if not database_url.strip():
        return ProbeResult(ok=True, dependency="postgres", detail="unset")
    try:
        import psycopg
    except ImportError:
        return ProbeResult(ok=False, dependency="postgres", detail="psycopg_missing")
    try:
        with psycopg.connect(database_url, connect_timeout=max(1, int(timeout))) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                row = cur.fetchone()
        if row and int(row[0]) == 1:
            return ProbeResult(ok=True, dependency="postgres")
        return ProbeResult(ok=False, dependency="postgres", detail="unexpected_result")
    except Exception as exc:  # noqa: BLE001 — readiness must not raise
        return ProbeResult(ok=False, dependency="postgres", detail=type(exc).__name__)


def probe_openbao_transit(
    addr: str,
    token: str,
    *,
    key_name: str = "memdot-local",
    timeout: float = 1.0,
) -> ProbeResult:
    """Require initialized/unsealed OpenBao and Transit key readability."""
    if not addr.strip():
        return ProbeResult(ok=True, dependency="openbao", detail="unset")
    base = addr.rstrip("/")
    try:
        health_req = urllib.request.Request(f"{base}/v1/sys/health", method="GET")
        with urllib.request.urlopen(health_req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        if body.get("initialized") is False:
            return ProbeResult(ok=False, dependency="openbao", detail="uninitialized")
        if body.get("sealed") is True:
            return ProbeResult(ok=False, dependency="openbao", detail="sealed")
    except urllib.error.HTTPError as exc:
        # OpenBao may return non-200 for sealed/uninit with a JSON body.
        try:
            body = json.loads(exc.read().decode("utf-8"))
        except Exception:  # noqa: BLE001
            return ProbeResult(ok=False, dependency="openbao", detail=f"http_{exc.code}")
        if body.get("initialized") is False:
            return ProbeResult(ok=False, dependency="openbao", detail="uninitialized")
        if body.get("sealed") is True:
            return ProbeResult(ok=False, dependency="openbao", detail="sealed")
        if exc.code not in {200, 429, 472, 473, 501, 503}:
            return ProbeResult(ok=False, dependency="openbao", detail=f"http_{exc.code}")
    except Exception as exc:  # noqa: BLE001
        return ProbeResult(ok=False, dependency="openbao", detail=type(exc).__name__)

    if not token.strip():
        return ProbeResult(ok=False, dependency="openbao", detail="missing_transit_token")
    try:
        req = urllib.request.Request(
            f"{base}/v1/transit/keys/{key_name}",
            method="GET",
            headers={"X-Vault-Token": token},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                return ProbeResult(ok=False, dependency="openbao", detail=f"transit_{resp.status}")
        return ProbeResult(ok=True, dependency="openbao")
    except Exception as exc:  # noqa: BLE001
        return ProbeResult(ok=False, dependency="openbao", detail=type(exc).__name__)


def probe_seaweed_s3(
    endpoint: str,
    access_key: str,
    secret_key: str,
    *,
    timeout: float = 2.0,
) -> ProbeResult:
    """Bounded authenticated S3 ListBuckets against SeaweedFS."""
    if not endpoint.strip():
        return ProbeResult(ok=True, dependency="seaweedfs", detail="unset")
    if not access_key.strip() or not secret_key.strip():
        return ProbeResult(ok=False, dependency="seaweedfs", detail="missing_credentials")
    try:
        import boto3
        from botocore.config import Config
    except ImportError:
        return ProbeResult(ok=False, dependency="seaweedfs", detail="boto3_missing")
    try:
        # boto3 stubs are incomplete in this workspace; keep runtime probe typed loosely.
        client = boto3.client(  # type: ignore[reportUnknownMemberType]
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name="us-east-1",
            config=Config(
                connect_timeout=timeout,
                read_timeout=timeout,
                retries={"max_attempts": 1},
            ),
        )
        cast(Any, client).list_buckets()
        return ProbeResult(ok=True, dependency="seaweedfs")
    except Exception as exc:  # noqa: BLE001
        return ProbeResult(ok=False, dependency="seaweedfs", detail=type(exc).__name__)


def probe_tcp_host_port(host: str, port: int, *, timeout: float = 1.5) -> ProbeResult:
    if not host.strip():
        return ProbeResult(ok=True, dependency="tcp", detail="unset")
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return ProbeResult(ok=True, dependency="tcp")
    except OSError as exc:
        return ProbeResult(ok=False, dependency="tcp", detail=type(exc).__name__)


def probe_oidc_discovery(issuer: str, *, timeout: float = 2.0) -> ProbeResult:
    if not issuer.strip():
        return ProbeResult(ok=True, dependency="oidc", detail="unset")
    url = issuer.rstrip("/") + "/.well-known/openid-configuration"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        if not body.get("issuer") or not body.get("jwks_uri"):
            return ProbeResult(ok=False, dependency="oidc", detail="incomplete_discovery")
        return ProbeResult(ok=True, dependency="oidc")
    except Exception as exc:  # noqa: BLE001
        return ProbeResult(ok=False, dependency="oidc", detail=type(exc).__name__)


def parse_host_port_from_url(url: str, default_port: int) -> tuple[str | None, int]:
    parsed = urlparse(url)
    host = parsed.hostname
    port = parsed.port or default_port
    return host, port

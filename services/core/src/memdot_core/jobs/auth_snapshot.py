"""Versioned, signed, expiring authorization snapshots for durable jobs."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
import uuid
from typing import Any, cast

from memdot_core.db.models.ledger import Source
from memdot_core.db.models.tenancy import Account, Actor, Space
from memdot_core.deletion import service as deletion_service
from memdot_core.request_context import RequestContext
from memdot_domain.tenancy import RequestPurpose
from sqlalchemy import select
from sqlalchemy.orm import Session

SNAPSHOT_VERSION = 1
DEFAULT_TTL_SECONDS = 3600


def _signing_key() -> bytes:
    value = (os.environ.get("CORE_JOB_AUTH_SNAPSHOT_KEY") or "").strip()
    if len(value.encode("utf-8")) < 32:
        msg = "CORE_JOB_AUTH_SNAPSHOT_KEY must contain at least 32 bytes (no session-key fallback)"
        raise RuntimeError(msg)
    return value.encode("utf-8")


def _canonical_payload(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sign(payload: dict[str, Any], *, key: bytes | None = None) -> str:
    signing_key = key if key is not None else _signing_key()
    return hmac.new(signing_key, _canonical_payload(payload), hashlib.sha256).hexdigest()


def auth_snapshot_from_context(
    ctx: RequestContext,
    *,
    space_id: uuid.UUID | None = None,
    resource_ids: dict[str, str] | None = None,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
    now: int | None = None,
    key: bytes | None = None,
) -> dict[str, object]:
    accepted_at = now if now is not None else int(time.time())
    body: dict[str, Any] = {
        "v": SNAPSHOT_VERSION,
        "account_id": str(ctx.account_id),
        "actor_id": str(ctx.actor_id),
        "purpose": ctx.purpose.value,
        "scopes": sorted(ctx.scopes),
        "space_id": str(space_id) if space_id is not None else None,
        "resource_ids": resource_ids or {},
        "request_id": str(ctx.correlation_id),
        "correlation_id": str(ctx.correlation_id),
        "accepted_at": accepted_at,
        "exp": accepted_at + ttl_seconds,
    }
    signature = _sign(body, key=key)
    return {**body, "sig": signature}


def _unsigned_fields(snapshot: dict[str, object]) -> dict[str, Any]:
    return {key: value for key, value in snapshot.items() if key != "sig"}


def verify_snapshot_signature(
    snapshot: dict[str, object],
    *,
    key: bytes | None = None,
    now: int | None = None,
) -> bool:
    version_raw = snapshot.get("v")
    try:
        version = int(str(version_raw))
    except (TypeError, ValueError):
        return False
    if version != SNAPSHOT_VERSION:
        return False
    signature = snapshot.get("sig")
    if not isinstance(signature, str) or not signature:
        return False
    expected = _sign(_unsigned_fields(snapshot), key=key)
    if not hmac.compare_digest(expected, signature):
        return False
    try:
        exp = int(str(snapshot["exp"]))
    except (KeyError, TypeError, ValueError):
        return False
    current = now if now is not None else int(time.time())
    return current <= exp


def validate_auth_snapshot(
    db: Session,
    *,
    account_id: uuid.UUID,
    snapshot: dict[str, object] | None,
    expected_space_id: uuid.UUID | None = None,
    key: bytes | None = None,
    now: int | None = None,
) -> bool:
    """Verify signature/expiry and revalidate account/actor/membership/space/source."""
    if snapshot is None:
        return False
    if not verify_snapshot_signature(snapshot, key=key, now=now):
        return False
    if str(snapshot.get("account_id")) != str(account_id):
        return False
    try:
        actor_id = uuid.UUID(str(snapshot["actor_id"]))
        purpose = RequestPurpose(str(snapshot["purpose"]))
    except (KeyError, ValueError, TypeError):
        return False
    if purpose not in {RequestPurpose.FIRST_PARTY, RequestPurpose.WORKER}:
        return False

    account = db.execute(select(Account).where(Account.id == account_id)).scalar_one_or_none()
    if account is None:
        return False
    if getattr(account, "status", "active") not in {"active", None}:
        return False
    actor = db.execute(
        select(Actor).where(Actor.account_id == account_id, Actor.id == actor_id)
    ).scalar_one_or_none()
    if actor is None:
        return False
    if getattr(actor, "revoked_at", None) is not None:
        return False
    space_raw = snapshot.get("space_id")
    if space_raw:
        try:
            space_id = uuid.UUID(str(space_raw))
        except ValueError:
            return False
        if expected_space_id is not None and space_id != expected_space_id:
            return False
        space = db.execute(
            select(Space).where(Space.account_id == account_id, Space.id == space_id)
        ).scalar_one_or_none()
        if space is None:
            return False

    resource_raw = snapshot.get("resource_ids")
    source_raw: object | None = None
    if isinstance(resource_raw, dict):
        maybe_source = cast(dict[str, object], resource_raw).get("source_id")
        source_raw = maybe_source
    if source_raw is not None:
        try:
            source_id = uuid.UUID(str(source_raw))
        except ValueError:
            return False
        if deletion_service.is_tombstoned(
            db, account_id=account_id, entity_type="source", entity_id=source_id
        ):
            return False
        source = db.execute(
            select(Source.id).where(Source.account_id == account_id, Source.id == source_id)
        ).scalar_one_or_none()
        if source is None:
            return False
    return True

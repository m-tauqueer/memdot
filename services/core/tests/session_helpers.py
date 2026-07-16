"""Helpers to mint first-party session cookies + CSRF for API tests."""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime, timedelta

from memdot_core.auth.sessions import SessionCookieNames, hash_secret, new_session_material
from sqlalchemy import text
from sqlalchemy.orm import Session


def ensure_session_pepper() -> None:
    os.environ.setdefault("CORE_SESSION_SIGNING_PEPPER", "test-session-pepper-16xxxxxxxx")
    os.environ.setdefault(
        "CORE_TENANT_CONTEXT_SIGNING_KEY", "test-tenant-context-signing-key-32-bytes"
    )
    os.environ.setdefault("CORE_MCP_SERVICE_SECRET", "test-mcp-service-secret-32bytes-xx")
    os.environ.setdefault("CORE_JOB_AUTH_SNAPSHOT_KEY", "test-job-auth-snapshot-key-32bytes!!")
    os.environ.setdefault("CORE_CONVERSATION_PAYLOAD_KEY", "test-conversation-payload-key-32b!")


def mint_session_cookies(
    db: Session,
    *,
    account_id: uuid.UUID,
    user_id: uuid.UUID,
    actor_id: uuid.UUID,
) -> tuple[dict[str, str], dict[str, str]]:
    """Return (cookies, headers) for authenticated first-party mutating requests."""
    ensure_session_pepper()
    material = new_session_material()
    expires = datetime.now(UTC) + timedelta(hours=1)
    idle = datetime.now(UTC) + timedelta(hours=1)
    db.execute(
        text(
            """
            INSERT INTO browser_session
              (id, account_id, user_id, actor_id, secret_hash, csrf_token_hash,
               expires_at, idle_expires_at, last_auth_at)
            VALUES
              (:id, :aid, :uid, :actor, :secret, :csrf, :exp, :idle, now())
            """
        ),
        {
            "id": material.session_id,
            "aid": account_id,
            "uid": user_id,
            "actor": actor_id,
            "secret": hash_secret(material.secret),
            "csrf": hash_secret(material.csrf_token),
            "exp": expires,
            "idle": idle,
        },
    )
    db.flush()
    names = SessionCookieNames()
    cookies = {
        names.session: f"{material.session_id}.{material.secret}",
        names.csrf: material.csrf_token,
    }
    headers = {"X-CSRF-Token": material.csrf_token}
    return cookies, headers

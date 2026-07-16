"""Authentication route handlers."""

from __future__ import annotations

import base64
import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse
from memdot_core.auth.activation import (
    AttestationDeclinedError,
    AttestationRequiredError,
    link_or_create_hosted_identity,
    record_adult_attestation,
)
from memdot_core.auth.bootstrap import (
    BootstrapReplayError,
    complete_operator_bootstrap,
    operator_bootstrap_exists,
)
from memdot_core.auth.oidc import OidcIssuerAdapter, OidcValidationError
from memdot_core.auth.sessions import (
    SessionCookieNames,
    decrypt_ephemeral_secret,
    encrypt_ephemeral_secret,
    hash_secret,
    is_session_active,
    new_session_material,
    recent_auth_satisfied,
    session_expiry,
    verify_session_secret,
)
from memdot_core.db.models.tenancy import (
    BrowserSession,
    SessionRevocation,
)
from memdot_core.db.tenant import TenantContext, tenant_scope
from memdot_core.deps import get_db_session, get_oidc_adapter, get_settings
from memdot_core.settings import CoreSettings
from memdot_domain.ids import new_uuid7
from memdot_domain.tenancy import RequestPurpose
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class OidcBeginBody(BaseModel):
    """Empty body reserved for future PKCE/client metadata."""


class AttestationBody(BaseModel):
    confirmed: bool


def _problem(status: int, code: str) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={"type": f"about:memdot/problems/{code}", "title": code, "status": status},
        media_type="application/problem+json",
    )


def _http_exc_code(exc: HTTPException, default: str = "unauthorized") -> str:
    detail: object = exc.detail
    if not isinstance(detail, dict):
        return default
    code_obj = detail.get("code")  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    if code_obj is None:
        return default
    return str(code_obj)  # pyright: ignore[reportUnknownArgumentType]


@router.post("/oidc/begin")
def oidc_begin(
    response: Response,
    db: Annotated[Session, Depends(get_db_session)],
    settings: Annotated[CoreSettings, Depends(get_settings)],
    adapter: Annotated[OidcIssuerAdapter, Depends(get_oidc_adapter)],
) -> dict[str, str]:
    """Issue server-side OIDC state and nonce (hashed, expiring, single-use)."""
    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode("ascii")).digest())
        .rstrip(b"=")
        .decode("ascii")
    )
    db.execute(
        text(
            "SELECT memdot_oidc_create_challenge("
            ":id,:state_hash,:nonce_hash,:pkce_verifier_ciphertext,:expires_at)"
        ),
        {
            "id": str(new_uuid7()),
            "state_hash": hash_secret(state),
            "nonce_hash": hash_secret(nonce),
            "pkce_verifier_ciphertext": encrypt_ephemeral_secret(code_verifier),
            "expires_at": datetime.now(UTC) + timedelta(minutes=10),
        },
    )
    names = SessionCookieNames()
    secure = settings.env in {"hosted", "self_host", "production"}
    response.set_cookie(
        names.oidc_state,
        state,
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=600,
    )
    try:
        authorization_url = adapter.authorization_url(
            client_id=settings.oidc_client_id,
            redirect_uri=settings.oidc_redirect_uri,
            state=state,
            nonce=nonce,
            code_challenge=code_challenge,
        )
    except OidcValidationError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail={"code": exc.code}) from exc
    return {"status": "challenge_issued", "authorization_url": authorization_url}


@router.get("/oidc/callback", response_model=None)
def oidc_callback(
    code: Annotated[str, Query(min_length=4)],
    state: Annotated[str, Query(min_length=8)],
    request: Request,
    response: Response,
    settings: Annotated[CoreSettings, Depends(get_settings)],
    adapter: Annotated[OidcIssuerAdapter, Depends(get_oidc_adapter)],
    db: Annotated[Session, Depends(get_db_session)],
) -> dict[str, str] | JSONResponse:
    names = SessionCookieNames()
    cookie_state = request.cookies.get(names.oidc_state, "")
    if not cookie_state or cookie_state != state:
        return _problem(401, "invalid_oidc_state")

    challenge = (
        db.execute(
            text("SELECT * FROM memdot_oidc_load_challenge(:state_hash)"),
            {"state_hash": hash_secret(state)},
        )
        .mappings()
        .one_or_none()
    )
    if challenge is None or challenge["consumed_at"] is not None:
        return _problem(401, "oidc_challenge_invalid")
    if challenge["expires_at"] <= datetime.now(UTC):
        return _problem(401, "oidc_challenge_expired")

    try:
        code_verifier = decrypt_ephemeral_secret(challenge["pkce_verifier_ciphertext"])
        id_token = adapter.exchange_code(
            code=code,
            code_verifier=code_verifier,
            client_id=settings.oidc_client_id,
            client_secret=settings.oidc_client_secret,
            redirect_uri=settings.oidc_redirect_uri,
        )
        claims = adapter.validate_id_token(id_token, expected_nonce=None)
    except OidcValidationError as exc:
        return _problem(401, exc.code)

    token_nonce = claims.nonce
    if not token_nonce or hash_secret(token_nonce) != challenge["nonce_hash"]:
        return _problem(401, "invalid_nonce")

    if claims.jti:
        try:
            db.execute(
                text("SELECT memdot_oidc_record_replay(:id,:issuer,:jti,:expires_at)"),
                {
                    "id": str(new_uuid7()),
                    "issuer": claims.issuer,
                    "jti": claims.jti,
                    "expires_at": datetime.fromtimestamp(claims.expires_at, tz=UTC),
                },
            )
            db.flush()
        except IntegrityError:
            db.rollback()
            return _problem(401, "replay_detected")

    consumed = db.execute(
        text("SELECT memdot_oidc_consume_challenge(:id,:consumed_at)"),
        {"id": str(challenge["id"]), "consumed_at": datetime.now(UTC)},
    ).scalar()
    if consumed is not True:
        return _problem(401, "oidc_challenge_invalid")

    if settings.is_self_host() and not operator_bootstrap_exists(db):
        try:
            identity = complete_operator_bootstrap(db, claims)
            account_id = identity.account_id
            user_id = identity.user_id
            actor_id = identity.actor_id
        except BootstrapReplayError:
            return _problem(409, "bootstrap_replay")
    else:
        linked = link_or_create_hosted_identity(db, claims)
        account_id = linked.account_id
        user_id = linked.user_id
        actor_id = linked.actor_id

    material = new_session_material()
    expires_at, idle_expires_at = session_expiry()
    with tenant_scope(
        db,
        TenantContext(
            account_id=account_id,
            actor_id=actor_id,
            purpose=RequestPurpose.FIRST_PARTY,
        ),
    ):
        db.add(
            BrowserSession(
                id=material.session_id,
                account_id=account_id,
                user_id=user_id,
                actor_id=actor_id,
                secret_hash=hash_secret(material.secret),
                csrf_token_hash=hash_secret(material.csrf_token),
                expires_at=expires_at,
                idle_expires_at=idle_expires_at,
                last_auth_at=datetime.now(UTC),
            )
        )

    secure = settings.env in {"hosted", "self_host", "production"}
    response.set_cookie(
        names.session,
        f"{material.session_id}.{material.secret}",
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=86400,
    )
    response.set_cookie(
        names.csrf,
        material.csrf_token,
        httponly=False,
        secure=secure,
        samesite="lax",
        max_age=86400,
    )
    response.delete_cookie(names.oidc_state)
    return {"status": "authenticated", "account_id": str(account_id)}


@router.post("/attestation", response_model=None)
def adult_attestation(
    body: AttestationBody,
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
) -> dict[str, str] | JSONResponse:
    try:
        ctx, browser_session = _load_browser_session(request, db)
    except HTTPException as exc:
        return _problem(exc.status_code, _http_exc_code(exc))
    try:
        require_csrf(request, browser_session)
    except HTTPException:
        return _problem(403, "csrf_failed")
    try:
        with tenant_scope(db, ctx):
            record_adult_attestation(
                db,
                account_id=browser_session.account_id,
                user_id=browser_session.user_id,
                confirmed=body.confirmed,
            )
    except AttestationDeclinedError:
        return _problem(403, "attestation_declined")
    except AttestationRequiredError:
        return _problem(400, "attestation_required")
    return {"status": "active"}


@router.post("/logout", response_model=None)
def logout(
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db_session)],
) -> dict[str, str] | JSONResponse:
    try:
        ctx, browser_session = _load_browser_session(request, db)
    except HTTPException as exc:
        return _problem(exc.status_code, _http_exc_code(exc))
    try:
        require_csrf(request, browser_session)
    except HTTPException:
        return _problem(403, "csrf_failed")
    with tenant_scope(db, ctx):
        browser_session.revoked_at = datetime.now(UTC)
        db.add(
            SessionRevocation(
                id=new_uuid7(),
                account_id=browser_session.account_id,
                session_id=browser_session.id,
            )
        )
    names = SessionCookieNames()
    response.delete_cookie(names.session)
    response.delete_cookie(names.csrf)
    return {"status": "logged_out"}


@router.get("/session")
def session_status(
    request: Request, db: Annotated[Session, Depends(get_db_session)]
) -> JSONResponse:
    try:
        ctx, browser_session = _load_browser_session(request, db)
    except HTTPException:
        return _problem(401, "session_invalid")
    return JSONResponse(
        content={
            "authenticated": True,
            "account_id": str(ctx.account_id),
            "recent_auth": recent_auth_satisfied(browser_session.last_auth_at),
        }
    )


@router.post("/session/rotate", response_model=None)
def rotate_session(
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db_session)],
    settings: Annotated[CoreSettings, Depends(get_settings)],
) -> dict[str, str] | JSONResponse:
    try:
        ctx, browser_session = _load_browser_session(request, db)
    except HTTPException as exc:
        return _problem(exc.status_code, _http_exc_code(exc))
    try:
        require_csrf(request, browser_session)
    except HTTPException:
        return _problem(403, "csrf_failed")
    material = new_session_material()
    expires_at, idle_expires_at = session_expiry()
    with tenant_scope(db, ctx):
        browser_session.revoked_at = datetime.now(UTC)
        db.add(
            SessionRevocation(
                id=new_uuid7(),
                account_id=browser_session.account_id,
                session_id=browser_session.id,
            )
        )
        db.add(
            BrowserSession(
                id=material.session_id,
                account_id=browser_session.account_id,
                user_id=browser_session.user_id,
                actor_id=browser_session.actor_id,
                secret_hash=hash_secret(material.secret),
                csrf_token_hash=hash_secret(material.csrf_token),
                expires_at=expires_at,
                idle_expires_at=idle_expires_at,
                last_auth_at=browser_session.last_auth_at,
                rotated_at=datetime.now(UTC),
            )
        )
    names = SessionCookieNames()
    secure = settings.env in {"hosted", "self_host", "production"}
    response.set_cookie(
        names.session,
        f"{material.session_id}.{material.secret}",
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=86400,
    )
    response.set_cookie(
        names.csrf,
        material.csrf_token,
        httponly=False,
        secure=secure,
        samesite="lax",
        max_age=86400,
    )
    return {"status": "rotated"}


def _load_browser_session(request: Request, db: Session) -> tuple[TenantContext, BrowserSession]:
    names = SessionCookieNames()
    raw = request.cookies.get(names.session, "")
    if "." not in raw:
        raise HTTPException(status_code=401, detail={"code": "session_missing"})
    session_id_str, secret = raw.split(".", 1)
    try:
        session_id = UUID(session_id_str)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail={"code": "session_malformed"}) from exc
    secret_digest = hash_secret(secret)
    row = (
        db.execute(
            text(
                """
            SELECT * FROM memdot_auth_load_session(:session_id, :secret_hash)
            """
            ),
            {"session_id": str(session_id), "secret_hash": secret_digest},
        )
        .mappings()
        .first()
    )
    if row is None:
        raise HTTPException(status_code=401, detail={"code": "session_invalid"})
    if not is_session_active(
        expires_at=row["expires_at"],
        idle_expires_at=row["idle_expires_at"],
        revoked_at=row["revoked_at"],
    ):
        raise HTTPException(status_code=401, detail={"code": "session_expired"})
    ctx = TenantContext(
        account_id=row["account_id"],
        actor_id=row["actor_id"],
        purpose=RequestPurpose.FIRST_PARTY,
    )
    # Rehydrate ORM under protected context (no session-table enumeration).
    with tenant_scope(db, ctx):
        browser_session = db.get(BrowserSession, row["id"])
        if browser_session is None:
            raise HTTPException(status_code=401, detail={"code": "session_invalid"})
    return ctx, browser_session


def require_csrf(request: Request, browser_session: BrowserSession) -> None:
    header = request.headers.get("x-csrf-token", "")
    if not header or not verify_session_secret(header, browser_session.csrf_token_hash):
        raise HTTPException(status_code=403, detail={"code": "csrf_failed"})


def require_recent_auth(browser_session: BrowserSession, *, max_age_minutes: int = 15) -> None:
    if not recent_auth_satisfied(browser_session.last_auth_at, max_age_minutes=max_age_minutes):
        raise HTTPException(status_code=401, detail={"code": "recent_auth_required"})

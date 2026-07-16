"""Learning attempts: server grades, reject forged grades / foreign user_id."""

from __future__ import annotations

import pytest
from factories import create_account_bundle
from memdot_core.learning import service as learning_service
from memdot_core.request_context import RequestContext
from memdot_domain.ids import new_uuid7
from memdot_domain.tenancy import RequestPurpose
from session_helpers import ensure_session_pepper, mint_session_cookies
from sqlalchemy import text

pytestmark = pytest.mark.usefixtures("truncate_tables")


def _ctx(bundle) -> RequestContext:
    return RequestContext(
        account_id=bundle.account_id,
        actor_id=bundle.actor_id,
        user_id=bundle.user_id,
        purpose=RequestPurpose.FIRST_PARTY,
        correlation_id=new_uuid7(),
    )


def _api_client(migrated_engine):
    from collections.abc import Generator

    from fastapi.testclient import TestClient
    from memdot_core.app import create_app
    from memdot_core.deps import get_db_session
    from memdot_core.settings import CoreSettings
    from sqlalchemy.orm import Session, sessionmaker

    ensure_session_pepper()
    settings = CoreSettings(
        env="test",
        database_url=migrated_engine.url.render_as_string(hide_password=False),
        tenant_context_signing_key="test-tenant-context-signing-key-32-bytes",
        session_signing_pepper="test-session-pepper-16xxxxxxxx",
        mcp_service_secret="test-mcp-service-secret-32bytes-xx",
        job_auth_snapshot_key="test-job-auth-snapshot-key-32bytes!!",
    )
    app = create_app(settings)
    factory = sessionmaker(bind=migrated_engine, expire_on_commit=False)

    def _db() -> Generator[Session, None, None]:
        session = factory()
        session.execute(text("SET ROLE memdot_core"))
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            try:
                session.execute(text("RESET ROLE"))
            except Exception:
                session.rollback()
            session.close()

    app.dependency_overrides[get_db_session] = _db
    return TestClient(app)


def test_server_grades_from_sealed_answer(db_session) -> None:
    bundle, space_id = create_account_bundle(db_session)
    ctx = _ctx(bundle)
    course = learning_service.create_course(db_session, ctx, space_id=space_id, title="C")
    item_id, rev_id = learning_service.create_assessment(
        db_session,
        ctx,
        course_id=course.course_id,
        title="Q1",
        item_type="mcq",
        prompt="2+2?",
        sealed_answer={"correctOption": "b"},
    )
    learning_service.start_assessment_attempt(
        db_session,
        ctx,
        course_id=course.course_id,
        assessment_item_id=item_id,
        assessment_revision_id=rev_id,
        client_attempt_id="a1",
    )
    result = learning_service.submit_assessment_attempt(
        db_session,
        ctx,
        course_id=course.course_id,
        assessment_item_id=item_id,
        assessment_revision_id=rev_id,
        response={"selectedOption": "b"},
        confidence="sure",
        client_attempt_id="a1",
    )
    assert result["correct"] is True
    assert result["status"] == "graded"


def test_forged_grade_in_event_payload_stripped(db_session) -> None:
    bundle, space_id = create_account_bundle(db_session)
    ctx = _ctx(bundle)
    course = learning_service.create_course(db_session, ctx, space_id=space_id, title="C")
    from datetime import UTC, datetime

    event_id = learning_service.append_learner_event(
        db_session,
        ctx,
        course_id=course.course_id,
        event_type="confidence_recorded",
        occurred_at=datetime.now(UTC),
        payload={"correct": True, "grade": "A", "eligibility": "eligible", "note": "ok"},
    )
    row = (
        db_session.execute(
            text("SELECT payload FROM learner_event WHERE id = :id"),
            {"id": event_id},
        )
        .mappings()
        .one()
    )
    payload = row["payload"]
    assert "correct" not in payload
    assert "grade" not in payload
    assert "eligibility" not in payload
    assert payload.get("note") == "ok"


def test_foreign_user_id_ignored_by_api(db_session, migrated_engine) -> None:
    bundle, space_id = create_account_bundle(db_session)
    other = create_account_bundle(db_session)[0]
    cookies, headers = mint_session_cookies(
        db_session,
        account_id=bundle.account_id,
        user_id=bundle.user_id,
        actor_id=bundle.actor_id,
    )
    ctx = _ctx(bundle)
    course = learning_service.create_course(db_session, ctx, space_id=space_id, title="C")
    item_id, rev_id = learning_service.create_assessment(
        db_session,
        ctx,
        course_id=course.course_id,
        title="Q1",
        item_type="mcq",
        prompt="q",
        sealed_answer={"correctOption": "a"},
    )
    db_session.commit()

    client = _api_client(migrated_engine)
    for key, value in cookies.items():
        client.cookies.set(key, value)
    started = client.post(
        "/api/v1/learning/attempts/start",
        json={
            "course_id": str(course.course_id),
            "assessment_item_id": str(item_id),
            "assessment_revision_id": str(rev_id),
            "client_attempt_id": "api-foreign-user-test",
        },
        headers=headers,
    )
    assert started.status_code == 201
    response = client.post(
        "/api/v1/learning/attempts",
        json={
            "course_id": str(course.course_id),
            "assessment_item_id": str(item_id),
            "assessment_revision_id": str(rev_id),
            "response": {"selectedOption": "a"},
            "confidence": "sure",
            "client_attempt_id": "api-foreign-user-test",
            "user_id": str(other.user_id),
        },
        headers=headers,
    )
    assert response.status_code == 201
    # App TestClient may leave pooled connections as memdot_core; reset for bypass read.
    db_session.rollback()
    db_session.execute(text("RESET ROLE"))
    attempt_user = db_session.execute(
        text("SELECT user_id FROM assessment_attempt WHERE account_id = :aid"),
        {"aid": bundle.account_id},
    ).scalar_one()
    assert str(attempt_user) == str(bundle.user_id)
    assert str(attempt_user) != str(other.user_id)


def test_answer_revealed_attempt_not_eligible_for_mastery(db_session) -> None:
    bundle, space_id = create_account_bundle(db_session)
    ctx = _ctx(bundle)
    course = learning_service.create_course(db_session, ctx, space_id=space_id, title="C")
    item_id, rev_id = learning_service.create_assessment(
        db_session,
        ctx,
        course_id=course.course_id,
        title="Q1",
        item_type="mcq",
        prompt="q",
        sealed_answer={"correctOption": "a"},
    )
    started = learning_service.start_assessment_attempt(
        db_session,
        ctx,
        course_id=course.course_id,
        assessment_item_id=item_id,
        assessment_revision_id=rev_id,
        client_attempt_id="reveal-1",
    )
    learning_service.record_attempt_reveal(
        db_session,
        ctx,
        attempt_id=__import__("uuid").UUID(started["attemptId"]),
        answer=True,
    )
    result = learning_service.submit_assessment_attempt(
        db_session,
        ctx,
        course_id=course.course_id,
        assessment_item_id=item_id,
        assessment_revision_id=rev_id,
        response={"selectedOption": "a"},
        confidence="sure",
        answer_revealed=False,  # client lie ignored; server recorded reveal
        client_attempt_id="reveal-1",
    )
    assert result["correct"] is True
    assert result["eligibility"] != "eligible"
    events = (
        db_session.execute(
            text(
                """
            SELECT event_type, eligibility
            FROM learner_event
            WHERE account_id = :aid
            """
            ),
            {"aid": bundle.account_id},
        )
        .mappings()
        .all()
    )
    assert events
    assert all(row["eligibility"] != "eligible" for row in events)


def test_confidence_required(db_session) -> None:
    bundle, space_id = create_account_bundle(db_session)
    ctx = _ctx(bundle)
    course = learning_service.create_course(db_session, ctx, space_id=space_id, title="C")
    item_id, rev_id = learning_service.create_assessment(
        db_session,
        ctx,
        course_id=course.course_id,
        title="Q1",
        item_type="mcq",
        prompt="q",
        sealed_answer={"correctOption": "a"},
    )
    with pytest.raises(ValueError, match="confidence"):
        learning_service.submit_assessment_attempt(
            db_session,
            ctx,
            course_id=course.course_id,
            assessment_item_id=item_id,
            assessment_revision_id=rev_id,
            response={"selectedOption": "a"},
            confidence="",
        )

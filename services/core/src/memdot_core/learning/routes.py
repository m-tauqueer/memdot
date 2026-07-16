"""Learning API routes."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from memdot_core.deps import get_db_session, get_request_context
from memdot_core.errors import ErrorCode, problem_response, safe_not_found
from memdot_core.learning import service as learning_service
from memdot_core.policy import GLOBAL_RATE_LIMITER, rate_limited_response
from memdot_core.request_context import RequestContext

router = APIRouter(prefix="/api/v1/learning", tags=["learning"])


def _require_ctx(ctx: RequestContext | None, request: Request) -> RequestContext | Response:
    del request
    if ctx is None:
        return safe_not_found(correlation_id=uuid.uuid4())
    if not GLOBAL_RATE_LIMITER.allow(str(ctx.account_id)):
        return rate_limited_response(correlation_id=ctx.correlation_id)
    return ctx


class CreateCourseBody(BaseModel):
    space_id: uuid.UUID
    title: str = Field(min_length=1, max_length=512)


class AddNodeBody(BaseModel):
    kind: str
    title: str = Field(min_length=1, max_length=512)
    confirmation: str = "suggested"


class AddEdgeBody(BaseModel):
    from_node_id: uuid.UUID
    to_node_id: uuid.UUID
    confirmation: str = "confirmed"


class CreateAssessmentBody(BaseModel):
    course_id: uuid.UUID
    title: str = Field(min_length=1, max_length=512)
    item_type: str
    prompt: str = Field(min_length=1)
    sealed_answer: dict[str, Any]
    concept_node_id: uuid.UUID | None = None
    sealed_rubric: dict[str, Any] | None = None
    source_locators: list[Any] | None = None


class AppendEventBody(BaseModel):
    course_id: uuid.UUID
    event_type: str
    occurred_at: datetime | None = None
    client_event_id: str | None = None
    concept_node_id: uuid.UUID | None = None
    assessment_item_id: uuid.UUID | None = None
    assessment_revision_id: uuid.UUID | None = None
    attempt_id: uuid.UUID | None = None
    payload: dict[str, Any] | None = None
    answer_revealed: bool = False
    substantive_hint: bool = False
    response_before_feedback: bool = True


class SubmitAttemptBody(BaseModel):
    course_id: uuid.UUID
    assessment_item_id: uuid.UUID
    assessment_revision_id: uuid.UUID
    response: dict[str, Any]
    confidence: str = Field(min_length=1, max_length=32)
    client_attempt_id: str = Field(min_length=1, max_length=128)
    hint_revealed: bool = False
    answer_revealed: bool = False


class StartAttemptBody(BaseModel):
    course_id: uuid.UUID
    assessment_item_id: uuid.UUID
    assessment_revision_id: uuid.UUID
    client_attempt_id: str | None = None


class RevealAttemptBody(BaseModel):
    attempt_id: uuid.UUID
    hint: bool = False
    answer: bool = False


class RebuildBody(BaseModel):
    course_id: uuid.UUID


@router.post("/courses", response_model=None)
def create_course(
    body: CreateCourseBody,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db_session)],
    ctx: Annotated[RequestContext | None, Depends(get_request_context)],
) -> dict[str, Any] | Response:
    resolved = _require_ctx(ctx, request)
    if isinstance(resolved, Response):
        return resolved
    try:
        created = learning_service.create_course(
            db, resolved, space_id=body.space_id, title=body.title
        )
    except Exception:
        return safe_not_found(correlation_id=resolved.correlation_id)
    response.status_code = 201
    return {
        "courseId": str(created.course_id),
        "spaceId": str(created.space_id),
        "correlationId": str(resolved.correlation_id),
    }


@router.post("/courses/{course_id}/nodes", response_model=None)
def add_node(
    course_id: uuid.UUID,
    body: AddNodeBody,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db_session)],
    ctx: Annotated[RequestContext | None, Depends(get_request_context)],
) -> dict[str, Any] | Response:
    resolved = _require_ctx(ctx, request)
    if isinstance(resolved, Response):
        return resolved
    try:
        node_id = learning_service.add_curriculum_node(
            db,
            resolved,
            course_id=course_id,
            kind=body.kind,
            title=body.title,
            confirmation=body.confirmation,
        )
    except Exception:
        return safe_not_found(correlation_id=resolved.correlation_id)
    response.status_code = 201
    return {"nodeId": str(node_id), "correlationId": str(resolved.correlation_id)}


@router.post("/courses/{course_id}/edges", response_model=None)
def add_edge(
    course_id: uuid.UUID,
    body: AddEdgeBody,
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
    ctx: Annotated[RequestContext | None, Depends(get_request_context)],
) -> dict[str, Any] | Response:
    resolved = _require_ctx(ctx, request)
    if isinstance(resolved, Response):
        return resolved
    try:
        edge_id = learning_service.add_prerequisite_edge(
            db,
            resolved,
            course_id=course_id,
            from_node_id=body.from_node_id,
            to_node_id=body.to_node_id,
            confirmation=body.confirmation,
        )
    except ValueError as exc:
        if str(exc) == "confirmed_prerequisite_cycle":
            return problem_response(
                status=409,
                code=ErrorCode.CONFLICT,
                detail="Confirmed prerequisite edge would create a cycle.",
                correlation_id=resolved.correlation_id,
            )
        return problem_response(
            status=422,
            code=ErrorCode.VALIDATION_ERROR,
            detail="Invalid curriculum edge.",
            correlation_id=resolved.correlation_id,
        )
    except Exception:
        return safe_not_found(correlation_id=resolved.correlation_id)
    return {"edgeId": str(edge_id), "correlationId": str(resolved.correlation_id)}


@router.post("/assessments", response_model=None)
def create_assessment(
    body: CreateAssessmentBody,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db_session)],
    ctx: Annotated[RequestContext | None, Depends(get_request_context)],
) -> dict[str, Any] | Response:
    resolved = _require_ctx(ctx, request)
    if isinstance(resolved, Response):
        return resolved
    try:
        item_id, rev_id = learning_service.create_assessment(
            db,
            resolved,
            course_id=body.course_id,
            title=body.title,
            item_type=body.item_type,
            prompt=body.prompt,
            sealed_answer=body.sealed_answer,
            concept_node_id=body.concept_node_id,
            sealed_rubric=body.sealed_rubric,
            source_locators=body.source_locators,
        )
    except Exception:
        return safe_not_found(correlation_id=resolved.correlation_id)
    response.status_code = 201
    return {
        "assessmentItemId": str(item_id),
        "revisionId": str(rev_id),
        "correlationId": str(resolved.correlation_id),
    }


@router.get(
    "/assessments/{assessment_item_id}/revisions/{revision_id}/attempt",
    response_model=None,
)
def get_attempt_view(
    assessment_item_id: uuid.UUID,
    revision_id: uuid.UUID,
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
    ctx: Annotated[RequestContext | None, Depends(get_request_context)],
) -> dict[str, Any] | Response:
    resolved = _require_ctx(ctx, request)
    if isinstance(resolved, Response):
        return resolved
    try:
        payload = learning_service.get_assessment_for_attempt(
            db,
            resolved,
            assessment_item_id=assessment_item_id,
            revision_id=revision_id,
        )
    except Exception:
        return safe_not_found(correlation_id=resolved.correlation_id)
    payload["correlationId"] = str(resolved.correlation_id)
    return payload


@router.post("/attempts/start", response_model=None)
def start_attempt(
    body: StartAttemptBody,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db_session)],
    ctx: Annotated[RequestContext | None, Depends(get_request_context)],
) -> dict[str, Any] | Response:
    resolved = _require_ctx(ctx, request)
    if isinstance(resolved, Response):
        return resolved
    try:
        result = learning_service.start_assessment_attempt(
            db,
            resolved,
            course_id=body.course_id,
            assessment_item_id=body.assessment_item_id,
            assessment_revision_id=body.assessment_revision_id,
            client_attempt_id=body.client_attempt_id,
        )
    except Exception:
        return safe_not_found(correlation_id=resolved.correlation_id)
    response.status_code = 201
    result["correlationId"] = str(resolved.correlation_id)
    return result


@router.post("/attempts/reveal", response_model=None)
def reveal_attempt(
    body: RevealAttemptBody,
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
    ctx: Annotated[RequestContext | None, Depends(get_request_context)],
) -> dict[str, Any] | Response:
    resolved = _require_ctx(ctx, request)
    if isinstance(resolved, Response):
        return resolved
    result = learning_service.record_attempt_reveal(
        db,
        resolved,
        attempt_id=body.attempt_id,
        hint=body.hint,
        answer=body.answer,
    )
    if result is None:
        return safe_not_found(correlation_id=resolved.correlation_id)
    result["correlationId"] = str(resolved.correlation_id)
    return result


@router.post("/attempts", response_model=None)
def submit_attempt(
    body: SubmitAttemptBody,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db_session)],
    ctx: Annotated[RequestContext | None, Depends(get_request_context)],
) -> dict[str, Any] | Response:
    resolved = _require_ctx(ctx, request)
    if isinstance(resolved, Response):
        return resolved
    try:
        result = learning_service.submit_assessment_attempt(
            db,
            resolved,
            course_id=body.course_id,
            assessment_item_id=body.assessment_item_id,
            assessment_revision_id=body.assessment_revision_id,
            response=body.response,
            confidence=body.confidence,
            client_attempt_id=body.client_attempt_id,
            hint_revealed=body.hint_revealed,
            answer_revealed=body.answer_revealed,
        )
    except ValueError as exc:
        return problem_response(
            status=422,
            code=ErrorCode.VALIDATION_ERROR,
            detail=str(exc),
            correlation_id=resolved.correlation_id,
        )
    except Exception:
        return safe_not_found(correlation_id=resolved.correlation_id)
    response.status_code = 201
    result["correlationId"] = str(resolved.correlation_id)
    return result


@router.post("/events", response_model=None)
def append_event(
    body: AppendEventBody,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db_session)],
    ctx: Annotated[RequestContext | None, Depends(get_request_context)],
) -> dict[str, Any] | Response:
    """Public arbitrary learner-event append is removed (Round 2).

    Evidence must flow through the server-owned attempt lifecycle only.
    """
    del body, response, db
    resolved = _require_ctx(ctx, request)
    if isinstance(resolved, Response):
        return resolved
    return problem_response(
        status=410,
        code=ErrorCode.VALIDATION_ERROR,
        detail="learner_event_append_removed_use_attempt_lifecycle",
        correlation_id=resolved.correlation_id,
    )


@router.post("/evidence/rebuild", response_model=None)
def rebuild_evidence(
    body: RebuildBody,
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
    ctx: Annotated[RequestContext | None, Depends(get_request_context)],
) -> dict[str, Any] | Response:
    resolved = _require_ctx(ctx, request)
    if isinstance(resolved, Response):
        return resolved
    try:
        projections = learning_service.rebuild_evidence_projections(
            db, resolved, course_id=body.course_id
        )
    except Exception:
        return safe_not_found(correlation_id=resolved.correlation_id)
    return {
        "projections": projections,
        "correlationId": str(resolved.correlation_id),
    }

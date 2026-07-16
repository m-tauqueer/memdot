/**
 * First-party Core client. Browser calls same-origin `/api/v1/*` (rewritten to Core).
 * Session cookie is HttpOnly; CSRF comes from readable `memdot_csrf` cookie.
 */

import type {
  AddNodeBody,
  AppendTurnBody,
  CompileContextBody,
  CreateAssessmentBody,
  CreateConversationBody,
  CreateCourseBody,
  CreateDocumentBody,
  CreateMemoryItemBody,
  CreateProposalBody,
  CreateSourceBody,
  CreateTombstoneBody,
  RevealAttemptBody,
  SaveRevisionBody,
  SelectPagesBody,
  StartAttemptBody,
  SubmitAttemptBody,
  UploadIntentBody,
} from "./types";
import { sha256File } from "../crypto/sha256";

export const CSRF_COOKIE = "memdot_csrf";
export const CSRF_HEADER = "X-CSRF-Token";

export type ProblemDetail = {
  type?: string;
  title?: string;
  status?: number;
  code?: string;
  detail?: string;
  correlation_id?: string;
  correlationId?: string;
  currentRevisionId?: string | null;
  current_revision_id?: string | null;
};

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly correlationId: string | undefined;
  readonly currentRevisionId: string | undefined;
  readonly problem: ProblemDetail;
  readonly retryAfterSeconds: number | undefined;

  constructor(problem: ProblemDetail, status: number, retryAfterSeconds?: number) {
    super(problem.detail || problem.title || `Request failed (${status})`);
    this.name = "ApiError";
    this.status = status;
    this.code = problem.code || "unknown";
    this.correlationId = problem.correlation_id || problem.correlationId;
    this.currentRevisionId = problem.currentRevisionId || problem.current_revision_id || undefined;
    this.problem = problem;
    this.retryAfterSeconds = retryAfterSeconds;
  }

  get isUnauthorized(): boolean {
    return this.status === 401;
  }

  get isRateLimited(): boolean {
    return this.status === 429 || this.code === "rate_limited";
  }

  get isConflict(): boolean {
    return this.status === 409 || this.code === "conflict";
  }

  get needsRecentAuth(): boolean {
    return this.status === 403 && /recent.?auth/i.test(`${this.code} ${this.message}`);
  }
}

function readCookie(name: string): string | null {
  if (typeof document === "undefined") {
    return null;
  }
  const parts = document.cookie.split(";").map((part) => part.trim());
  for (const part of parts) {
    if (part.startsWith(`${name}=`)) {
      return decodeURIComponent(part.slice(name.length + 1));
    }
  }
  return null;
}

export function newCorrelationId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `web-${Date.now()}`;
}

export type ApiRequestOptions = {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
  signal?: AbortSignal;
  /** Skip CSRF for GET-like safety; mutations always send when cookie present. */
  csrf?: boolean;
};

export async function apiRequest<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const method = (options.method ?? "GET").toUpperCase();
  const correlationId = newCorrelationId();
  const headers: Record<string, string> = {
    Accept: "application/json",
    "X-Correlation-Id": correlationId,
    ...options.headers,
  };

  const needsCsrf = options.csrf ?? !["GET", "HEAD", "OPTIONS"].includes(method);
  if (needsCsrf) {
    const csrf = readCookie(CSRF_COOKIE);
    if (csrf) {
      headers[CSRF_HEADER] = csrf;
    }
  }

  const init: RequestInit = {
    method,
    headers,
    credentials: "include",
    cache: "no-store",
  };
  if (options.body !== undefined) {
    headers["Content-Type"] = "application/json";
    init.body = JSON.stringify(options.body);
  }
  if (options.signal) {
    init.signal = options.signal;
  }

  const response = await fetch(path.startsWith("/") ? path : `/${path}`, init);

  const contentType = response.headers.get("content-type") || "";
  const isJson = contentType.includes("application/json");
  const payload = isJson ? ((await response.json()) as unknown) : null;

  if (!response.ok) {
    const problem =
      payload && typeof payload === "object"
        ? (payload as ProblemDetail)
        : { status: response.status, detail: response.statusText, code: "http_error" };
    if (!problem.correlation_id && !problem.correlationId) {
      problem.correlation_id = correlationId;
    }
    const retryAfterHeader = response.headers.get("Retry-After");
    const retryAfterSeconds = retryAfterHeader ? Number.parseInt(retryAfterHeader, 10) : undefined;
    throw new ApiError(
      problem,
      response.status,
      Number.isFinite(retryAfterSeconds) ? retryAfterSeconds : undefined,
    );
  }

  return payload as T;
}

export type SessionStatus = {
  authenticated: boolean;
  account_id?: string;
  recent_auth?: boolean;
  adult_attested?: boolean;
};

export function fetchSession(signal?: AbortSignal): Promise<SessionStatus> {
  const options: ApiRequestOptions = { csrf: false };
  if (signal) {
    options.signal = signal;
  }
  return apiRequest<SessionStatus>("/api/v1/auth/session", options);
}

export function beginOidc(): Promise<{
  authorization_url?: string;
  authorize_url?: string;
  url?: string;
}> {
  return apiRequest("/api/v1/auth/oidc/begin", { method: "POST", body: {} });
}

export function logout(): Promise<{ status: string }> {
  return apiRequest("/api/v1/auth/logout", { method: "POST", body: {} });
}

export function rotateSession(): Promise<{ status?: string }> {
  return apiRequest("/api/v1/auth/session/rotate", { method: "POST", body: {} });
}

export function attestAdult(confirmed: boolean): Promise<{ status: string }> {
  return apiRequest("/api/v1/auth/attestation", {
    method: "POST",
    body: { confirmed },
  });
}

export type CreatedSource = {
  sourceId: string;
  spaceId: string;
  correlationId?: string;
};

export function createSource(body: CreateSourceBody): Promise<CreatedSource> {
  return apiRequest("/api/v1/sources", { method: "POST", body });
}

export function getSourceStatus(sourceId: string): Promise<Record<string, unknown>> {
  return apiRequest(`/api/v1/sources/${sourceId}/status`);
}

export function listSourceVersions(sourceId: string): Promise<{ items?: unknown[] }> {
  return apiRequest(`/api/v1/sources/${sourceId}/versions`);
}

export function cancelSource(sourceId: string): Promise<unknown> {
  return apiRequest(`/api/v1/sources/${sourceId}/cancel`, { method: "POST", body: {} });
}

export function retrySource(sourceId: string, revisionId: string): Promise<unknown> {
  return apiRequest(`/api/v1/sources/${sourceId}/retry`, {
    method: "POST",
    body: { revision_id: revisionId },
  });
}

export function reprocessSource(
  sourceId: string,
  revisionId: string,
  shadow = false,
): Promise<unknown> {
  return apiRequest(`/api/v1/sources/${sourceId}/reprocess`, {
    method: "POST",
    body: { revision_id: revisionId, shadow },
  });
}

export function getMemoryItem(memoryItemId: string): Promise<Record<string, unknown>> {
  return apiRequest(`/api/v1/memory/items/${memoryItemId}`);
}

export function approveProposal(proposalId: string): Promise<unknown> {
  return apiRequest(`/api/v1/memory/proposals/${proposalId}/approve`, {
    method: "POST",
    body: {},
  });
}

export function rejectProposal(proposalId: string): Promise<unknown> {
  return apiRequest(`/api/v1/memory/proposals/${proposalId}/reject`, {
    method: "POST",
    body: {},
  });
}

export function startAttempt(
  body: StartAttemptBody,
): Promise<{ attemptId?: string; status?: string }> {
  return apiRequest("/api/v1/learning/attempts/start", { method: "POST", body });
}

export function revealAttempt(body: RevealAttemptBody): Promise<unknown> {
  return apiRequest("/api/v1/learning/attempts/reveal", { method: "POST", body });
}

export type SubmitAttemptInput = {
  course_id: string;
  assessment_item_id: string;
  assessment_revision_id: string;
  response: SubmitAttemptBody["response"];
  confidence: string;
  client_attempt_id: string;
  hint_revealed?: boolean;
  answer_revealed?: boolean;
};

export function submitAttempt(body: SubmitAttemptInput): Promise<unknown> {
  const payload: SubmitAttemptBody = {
    course_id: body.course_id,
    assessment_item_id: body.assessment_item_id,
    assessment_revision_id: body.assessment_revision_id,
    response: body.response,
    confidence: body.confidence,
    client_attempt_id: body.client_attempt_id,
    hint_revealed: body.hint_revealed ?? false,
    answer_revealed: body.answer_revealed ?? false,
  };
  return apiRequest("/api/v1/learning/attempts", { method: "POST", body: payload });
}

export function requestAccountExport(): Promise<unknown> {
  return apiRequest("/api/v1/export/account", { method: "POST", body: {} });
}

export function compileContext(
  body: Pick<CompileContextBody, "query"> & Partial<CompileContextBody>,
): Promise<Record<string, unknown>> {
  return apiRequest("/api/v1/context/compile", {
    method: "POST",
    body: {
      max_items: 32,
      max_tokens: 4096,
      ...body,
    },
  });
}

export function listConversations(spaceId?: string): Promise<{ items?: unknown[] }> {
  const query = spaceId ? `?space_id=${encodeURIComponent(spaceId)}` : "";
  return apiRequest(`/api/v1/conversations${query}`);
}

export type UploadIntent = {
  uploadId: string;
  uploadUrl: string;
  objectKey?: string;
  expiresAt?: string;
  correlationId?: string;
};

export function createUploadIntent(
  sourceId: string,
  body: UploadIntentBody,
): Promise<UploadIntent> {
  return apiRequest(`/api/v1/sources/${sourceId}/uploads`, { method: "POST", body });
}

export function completeUpload(
  sourceId: string,
  uploadId: string,
): Promise<{ revisionId?: string; jobId?: string; correlationId?: string }> {
  return apiRequest(`/api/v1/sources/${sourceId}/uploads/complete`, {
    method: "POST",
    body: { upload_id: uploadId },
  });
}

/** Create source → upload intent → PUT bytes → complete (202 job). */
export async function uploadSourceFile(input: {
  spaceId: string;
  title: string;
  file: File;
}): Promise<{ sourceId: string; revisionId?: string; jobId?: string }> {
  const created = await createSource({ space_id: input.spaceId, title: input.title });
  const sha256 = await sha256File(input.file);
  const intent = await createUploadIntent(created.sourceId, {
    filename: input.file.name,
    content_type: input.file.type || "application/octet-stream",
    byte_count: input.file.size,
    sha256,
  });
  const put = await fetch(intent.uploadUrl, {
    method: "PUT",
    body: input.file,
    headers: {
      "Content-Type": input.file.type || "application/octet-stream",
    },
  });
  if (!put.ok) {
    throw new ApiError(
      {
        status: put.status,
        detail: `Object upload failed (${put.status})`,
        code: "upload_put_failed",
      },
      put.status,
    );
  }
  const completed = await completeUpload(created.sourceId, intent.uploadId);
  return {
    sourceId: created.sourceId,
    ...(completed.revisionId ? { revisionId: completed.revisionId } : {}),
    ...(completed.jobId ? { jobId: completed.jobId } : {}),
  };
}

export function createDocument(
  body: CreateDocumentBody,
): Promise<{ documentId: string; revisionId: string; spaceId: string }> {
  return apiRequest("/api/v1/documents", { method: "POST", body });
}

export function getDocument(documentId: string): Promise<Record<string, unknown>> {
  return apiRequest(`/api/v1/documents/${documentId}`);
}

export function listDocumentRevisions(documentId: string): Promise<{ items?: unknown[] }> {
  return apiRequest(`/api/v1/documents/${documentId}/revisions`);
}

export function saveDocumentRevision(
  documentId: string,
  body: SaveRevisionBody,
): Promise<{ revisionId?: string; correlationId?: string }> {
  return apiRequest(`/api/v1/documents/${documentId}/revisions`, { method: "POST", body });
}

export function createConversation(
  body: CreateConversationBody,
): Promise<{ conversationId?: string; id?: string; conversation_id?: string }> {
  return apiRequest("/api/v1/conversations", { method: "POST", body });
}

export function getConversation(conversationId: string): Promise<Record<string, unknown>> {
  return apiRequest(`/api/v1/conversations/${conversationId}`);
}

export function appendConversationTurn(
  conversationId: string,
  body: AppendTurnBody,
): Promise<unknown> {
  return apiRequest(`/api/v1/conversations/${conversationId}/turns`, {
    method: "POST",
    body,
  });
}

export function deleteConversation(conversationId: string): Promise<unknown> {
  return apiRequest(`/api/v1/conversations/${conversationId}`, { method: "DELETE" });
}

export function createCourse(body: CreateCourseBody): Promise<{ courseId?: string; id?: string }> {
  return apiRequest("/api/v1/learning/courses", { method: "POST", body });
}

export function addCourseNode(courseId: string, body: AddNodeBody): Promise<unknown> {
  return apiRequest(`/api/v1/learning/courses/${courseId}/nodes`, {
    method: "POST",
    body,
  });
}

export function createAssessment(
  body: CreateAssessmentBody,
): Promise<{ assessmentItemId?: string; revisionId?: string }> {
  return apiRequest("/api/v1/learning/assessments", { method: "POST", body });
}

export function getAttemptView(
  assessmentItemId: string,
  revisionId: string,
): Promise<Record<string, unknown>> {
  return apiRequest(
    `/api/v1/learning/assessments/${assessmentItemId}/revisions/${revisionId}/attempt`,
  );
}

export function createMemoryItem(body: CreateMemoryItemBody): Promise<unknown> {
  return apiRequest("/api/v1/memory/items", { method: "POST", body });
}

export function createProposal(body: CreateProposalBody): Promise<{ proposalId?: string }> {
  return apiRequest("/api/v1/memory/proposals", { method: "POST", body });
}

export function createTombstone(body: CreateTombstoneBody): Promise<unknown> {
  return apiRequest("/api/v1/deletion/tombstones", { method: "POST", body });
}

export function restoreReplay(body: Record<string, unknown> = {}): Promise<unknown> {
  return apiRequest("/api/v1/deletion/restore-replay", { method: "POST", body });
}

export function notionConnect(): Promise<Record<string, unknown>> {
  return apiRequest("/api/v1/notion/connect", { method: "POST", body: {} });
}

export function notionListPages(connectionId: string): Promise<unknown> {
  return apiRequest(`/api/v1/notion/connections/${connectionId}/pages`);
}

export function notionSelectPages(body: SelectPagesBody): Promise<unknown> {
  return apiRequest("/api/v1/notion/pages/select", { method: "POST", body });
}

export function notionSyncBinding(
  bindingId: string,
  fixtureContent?: string | null,
): Promise<unknown> {
  return apiRequest(`/api/v1/notion/bindings/${bindingId}/sync`, {
    method: "POST",
    body: { fixture_content: fixtureContent ?? null },
  });
}

export function notionResolveConflict(
  bindingId: string,
  body: Record<string, unknown>,
): Promise<unknown> {
  return apiRequest(`/api/v1/notion/bindings/${bindingId}/resolve`, {
    method: "POST",
    body,
  });
}

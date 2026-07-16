/**
 * Typed OpenAPI surface for the web app — generated contracts only.
 * Runtime calls go through `apiRequest`; this module is the type contract.
 */
import type { components, paths } from "@memdot/contracts";

export type ApiPaths = paths;
export type ApiSchemas = components["schemas"];

export type CreateSourceBody = ApiSchemas["CreateSourceBody"];
export type UploadIntentBody = ApiSchemas["UploadIntentBody"];
export type CompleteUploadBody = ApiSchemas["CompleteUploadBody"];
export type ReprocessBody = ApiSchemas["ReprocessBody"];
export type CreateMemoryItemBody = ApiSchemas["CreateMemoryItemBody"];
export type CreateProposalBody = ApiSchemas["CreateProposalBody"];
export type StartAttemptBody = ApiSchemas["StartAttemptBody"];
export type RevealAttemptBody = ApiSchemas["RevealAttemptBody"];
export type SubmitAttemptBody = ApiSchemas["SubmitAttemptBody"];
export type CompileContextBody = ApiSchemas["CompileContextBody"];
export type AttestationBody = ApiSchemas["AttestationBody"];
export type CreateDocumentBody = ApiSchemas["CreateDocumentBody"];
export type SaveRevisionBody = ApiSchemas["SaveRevisionBody"];
export type CreateConversationBody = ApiSchemas["CreateConversationBody"];
export type AppendTurnBody = ApiSchemas["AppendTurnBody"];
export type CreateCourseBody = ApiSchemas["CreateCourseBody"];
export type AddNodeBody = ApiSchemas["AddNodeBody"];
export type CreateAssessmentBody = ApiSchemas["CreateAssessmentBody"];
export type CreateTombstoneBody = ApiSchemas["CreateTombstoneBody"];
export type SelectPagesBody = ApiSchemas["SelectPagesBody"];

/** Paths the browser may call via same-origin rewrite. */
export const BROWSER_API_PATHS = [
  "/api/v1/auth/session",
  "/api/v1/auth/oidc/begin",
  "/api/v1/auth/attestation",
  "/api/v1/auth/logout",
  "/api/v1/auth/session/rotate",
  "/api/v1/sources",
  "/api/v1/documents",
  "/api/v1/memory/items",
  "/api/v1/memory/proposals",
  "/api/v1/learning/courses",
  "/api/v1/learning/assessments",
  "/api/v1/learning/attempts/start",
  "/api/v1/learning/attempts/reveal",
  "/api/v1/learning/attempts",
  "/api/v1/context/compile",
  "/api/v1/conversations",
  "/api/v1/export/account",
  "/api/v1/deletion/tombstones",
  "/api/v1/notion/connect",
] as const satisfies ReadonlyArray<keyof paths>;

export type BrowserApiPath = (typeof BROWSER_API_PATHS)[number];

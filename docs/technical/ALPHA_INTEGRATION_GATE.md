# Alpha Integration Gate

Status: **planned; manual owner configuration pending**

This gate is deliberately after local implementation and before final release
acceptance. It is the only gate allowed to use owner-provided credentials,
connect an authorized third-party workspace, or make a non-production deployment
validation call. Fixture, emulator, and stub tests do not satisfy any item in
this document.

## Purpose

Prove that production integration boundaries behave safely with real systems
while preserving the product invariants: PostgreSQL remains canonical, Private
Spaces are never externally retrievable, and provider outages fail closed or
visibly degrade rather than changing canonical truth.

## Required owner-provided dependencies

| Dependency | Owner input required | Acceptance proof |
|---|---|---|
| Google hosted authentication | OAuth client ID/secret, approved redirect URIs, authorized test account | Authorization-code + PKCE login, 18+ gate, logout and revocation |
| Notion | Test integration token/OAuth app and a disposable authorized workspace | Selected-page read, bounded Memdot-area write, conflict pause, revoke |
| Encryption/KMS | Hosted KMS or OpenBao deployment configuration and rotation plan | Conversation/connector-secret envelope encrypt/decrypt, denied-key failure, rotation readback |
| Docling/OCR | Approved parser image/dependency and test corpus | Native office/deep-PDF parse provenance; OCR only when gating conditions permit |
| MCP clients | Authorized test clients for ChatGPT, Claude, and Gemini as available | OAuth/resource validation, frozen tools, citation URLs, Private-Space exclusion |
| Hosted environment | Owner-approved Mumbai primary and Delhi DR test configuration | No live customer data; telemetry policy, backup/restore and Tex-disabled fallback |

## Execution order

1. Provision test-only credentials through the approved secret store; do not
   commit them or place them in fixtures.
2. Complete Google OIDC and session/revocation validation.
3. Complete KMS/OpenBao envelope-key validation before enabling capture or
   connector-token persistence.
4. Validate Notion against the authorized disposable workspace, including
   pagination, selected-page scope, rate limits, per-item conflict pause, and
   revoke.
5. Validate production Docling/OCR against the parser corpus; retain parser
   version, source revision, and failure evidence.
6. Validate each real MCP host independently. A host that cannot provide a
   required OAuth capability remains unsupported and is not advertised.
7. Run owner-authorized hosted/DR checks and the final combined self-host
   checkpoint only after all fast gates are green.

## Exit criteria

- Live credentials and test data are revoked or retained only under the
  documented operator policy.
- Every integration has an automated, secret-free regression test plus a dated
  manual acceptance record outside the repository.
- No provider response is accepted as canonical source truth without stored
  provenance and a canonical revision.
- A provider outage, revoked grant, KMS denial, parser failure, or MCP scope
  reduction has a tested safe failure state.
- The owner explicitly accepts the evidence before the final end-to-end audit
  and any release decision.

## Explicit non-claims before this gate

Memdot must not claim live Google sign-in, live Notion synchronization,
production Docling/OCR, hosted KMS-backed encryption, compatibility with a
specific MCP host, Mumbai/Delhi deployment, SBOM/signing, or end-to-end
self-host parity until the corresponding evidence above passes.

## Final-audit handoff

After the owner completes the manual configuration and the above evidence is
collected, perform one final end-to-end logic and architecture audit. It must
cover the public contracts, authorization/RLS, Private-Space exclusion, learning
integrity, citations, lifecycle/deletion, external-provider failure states,
frontend honesty, and the release-acceptance matrix. Run the combined full
self-host smoke once only after its fast-gate prerequisites are green. The audit
does not authorize a release; a separate owner decision does.

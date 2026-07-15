# ADR 0010: India-Regional Inference and Direct Adapters

- Status: Accepted
- Date: 2026-07-15

## Context

Memdot handles private learning content and needs a strong India-first hosted default while supporting managed AI and user-supplied provider keys. Provider-specific sessions, storage, and global routing would weaken residency, deletion, and self-host portability.

## Decision

- Hosted Memdot uses paid Google Cloud regional inference in Mumbai (`asia-south1`) as the managed default. Calls use regional endpoints, not `global`.
- The managed path is stateless: no provider-owned memory, sessions, files, grounding, or persistent context cache. Request/response logging and optional provider caching are disabled where supported.
- Gemini is the initial managed model family. Claude through Google's Mumbai regional endpoint may be enabled only after its current partner-model processing and retention terms are verified.
- OpenAI, Anthropic, and Gemini Developer API are direct optional adapters for BYOK or explicit provider choice. Memdot does not route private content through a model aggregator.
- Every adapter implements the same request, streaming, cancellation, usage, retention-capability, region, and error contract. The Context Compiler—not the adapter—owns context selection.
- BYOK credentials are envelope-encrypted, never logged or returned after entry, and can be tested, rotated, and deleted.
- Provider/region and policy are shown before activation and recorded in each context receipt. No silent provider or region fallback is permitted.
- Canonical data stays in PostgreSQL/object storage; provider responses enter memory only through normal product writes and proposals.

## Alternatives

- Use global provider endpoints by default: rejected because they weaken the India-first promise.
- Use a single model aggregator: rejected because it obscures subprocessors, region, retention, and direct self-host parity.
- Couple product features to provider sessions or file stores: rejected because deletion and migration become provider-specific.

## Consequences

- Some models and features are unavailable in managed mode until they have an approved regional route.
- Direct providers remain useful but require an explicit cross-border/retention disclosure.
- Provider policy and regional availability require scheduled re-verification.

## Security effect

Only the minimum compiled context is sent. BYOK changes credentials and billing, not the provider's data practices. Direct OpenAI India storage does not imply India processing; direct Anthropic is not India-resident; unpaid Gemini Developer API is prohibited for personal learner data. Egress is allowlisted and secrets use dedicated encryption keys.

## Reversal strategy

Add or replace adapters behind the common contract, shadow-evaluate approved regional models, and change the managed default only with an explicit residency/policy migration. Canonical memory never needs migration.

## Links

- [Google model deployment locations](https://docs.cloud.google.com/gemini-enterprise-agent-platform/resources/locations)
- [Google zero-data-retention controls](https://docs.cloud.google.com/gemini-enterprise-agent-platform/resources/zero-data-retention)
- [OpenAI API data controls](https://developers.openai.com/api/docs/guides/your-data)
- [Anthropic data residency](https://platform.claude.com/docs/en/manage-claude/data-residency)
- [Gemini API terms](https://ai.google.dev/gemini-api/terms)
- [ADR 0006: Context Compiler and receipts](0006-context-compiler-and-receipts.md)

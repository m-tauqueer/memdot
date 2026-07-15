# ADR 0013: PWA Offline Boundary

- Status: Accepted
- Date: 2026-07-15

## Context

Learners need reliable access on inconsistent networks, but silently caching an entire private memory system on a browser creates security, sync, and false-capability risks. Retrieval, AI, imports, and MCP also depend on server-side authorization and current projections.

## Decision

- The web client is an installable Progressive Web App with an explicit, bounded offline V1.
- Offline V1 supports only the application shell, **pinned reading**, and a downloaded **seven-day review pack**. Users choose documents to pin; ordinary recently viewed content is not cached automatically.
- A review pack contains the prompts and source context needed for reviews due during the next seven days. It excludes sealed answer keys and expires after its seven-day window.
- Review responses captured offline are provisional attempts with idempotent client event IDs. Evaluation, canonical learning events, Evidence Twin changes, and FSRS updates occur only after online server acknowledgement.
- Offline note or document editing and a general queued-write system are not part of V1.
- If connectivity drops during an already-open online edit, the client may keep an encrypted, short-lived **dirty buffer** solely for crash recovery. It submits only after reconnection and only when the server accepts its base-revision precondition; conflicts require explicit user resolution.
- AI tutoring, hybrid retrieval, MCP, integration sync, parsing, account/security changes, and new model evaluation require an online connection. The UI never simulates these as completed offline.
- Authenticated API responses are network-only by default; service-worker caching uses an explicit allowlist for pinned documents and review packs.

## Alternatives

- Make all data and AI available offline: rejected because it requires a separate local inference/search/security architecture.
- Cache all recently viewed private content automatically: rejected because shared or lost devices create excessive exposure.
- Queue note and document edits offline: rejected in V1 because conflict, authorization, and provenance semantics are not ready.
- Provide no offline support: rejected because reading and scheduled review should survive intermittent connectivity.

## Consequences

- Offline capability is useful but deliberately narrower than the online product.
- Pack expiry, provisional-attempt sync, storage quota, dirty-buffer recovery, and base-revision conflicts require browser-level testing.
- Users must be told when a review is provisional or an online edit remains only in crash recovery.

## Security effect

Tokens are never placed in general service-worker caches. Offline data is minimized, encrypted where browser capabilities permit, namespaced per account, expired, and cleared on explicit logout/removal on a best-effort basis. Dirty buffers use a device-local encryption key and short expiry. The product warns that browser storage cannot protect data on a compromised unlocked device.

## Reversal strategy

Offline allowlisted data classes can expand behind versioned local schemas and migrations. General offline editing or local inference/search requires a separate ADR; disabling pinned data and review packs does not affect canonical server data.

## Links

- [Progressive Web Apps](https://web.dev/explore/progressive-web-apps)
- [Service Worker API](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)
- [ADR 0002: PostgreSQL Evidence Ledger](0002-postgres-evidence-ledger.md)
- [ADR 0012: Evidence Twin, event ledger, and FSRS](0012-evidence-twin-event-ledger-and-fsrs.md)

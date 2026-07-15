# Prompt for Grok — Implement Memdot Phase 2

Copy everything below this line into Grok in Cursor.

---

You are the implementation builder for Memdot Phase 2.

Implement the complete **Self-host infrastructure and local developer platform**
macro-phase across micro-phases 2.1, 2.2, and 2.3. Complete and self-validate
each micro-phase in order, fix its failures, and continue without routine Codex
review. Stop only after the complete Phase 2 exit gate passes or a genuine
owner-controlled blocker prevents safe progress.

Tauqueer owns decisions and has authorized Phase 2. Codex reviews once at the
macro-phase boundary. Do not commit, push, merge, deploy, rotate real
credentials, create paid resources, trust local certificates system-wide, or
mutate production or third-party data. Do not begin Phase 3.

## A. Mandatory reading before editing

Read completely, in this order:

1. `AGENTS.md`
2. `CONTEXT.md`
3. `IMPLEMENTATION_PLAN.md`
4. `IMPLEMENTATION_TRACKER.md` sections 1–3 and the complete Phase 2 section
5. `docs/README.md`
6. `docs/ai/CODEBASE_CONTEXT_MAP.md`
7. `docs/technical/TRD.md` sections 2, 11, 12, 13, 14, and 16
8. `docs/technical/SYSTEM_ARCHITECTURE.md` sections 2, 4, 7, 17, 18, 19, and 20
9. `docs/adr/0011-apache-2-and-self-host-parity.md`
10. `docs/technical/SECURITY_PRIVACY_THREAT_MODEL.md` sections 2, 3, 5, 8, 9, 11, and 12
11. `docs/technical/EVALUATION_RELEASE_GATES.md` sections 1, 8, 11, 12, and 13
12. `docs/architecture/DEPENDENCY_BOUNDARIES.md`
13. `docs/execution/PHASE_REPORT_TEMPLATE.md`

Primary contracts are `TRD-DEP-004..008`, `TRD-SEC-005..007`,
`TRD-OPS-009..013`, and ADR-0011. Inspect actual manifests, Dockerfiles,
settings, tests, and scripts before changing them. Documentation target state is
not proof that a component exists.

## B. Establish the baseline

Before editing:

1. Confirm the working directory and that `AGENTS.md` governs the repository.
2. Record branch, `HEAD`, `git status --short`, remotes, and pre-existing changes.
3. Confirm the accepted base commit is
   `4138239ea31eff267af3e9a9d9984ca51a763991`. If it differs, stop and report
   instead of rebasing, resetting, or discarding anything.
4. Verify Node, pnpm, Python, uv, Docker, Docker Compose, Git, curl, OpenSSL, and
   Make versions without printing environment secrets.
5. Run the existing fast baseline gates: `make format-check`, `make lint`,
   `make typecheck`, `make test`, `make contracts`, `make docs-validate`, and
   `make build`.
6. Inspect Docker/Compose host limits: available memory, disk, ports, and Docker
   Compose capabilities. Record constraints before selecting observability or
   workflow profiles.
7. Preserve unrelated changes. Never use destructive Git commands.

## C. Locked scope

Phase 2 establishes a production-like, Tex-disabled local platform. It may add
infrastructure configuration, provider-health wiring, generic secret-encryption
ports/adapters, operational canaries, and test-only durability fixtures.

Do not implement:

- canonical product tables, Alembic domain migrations, RLS, tenancy, or accounts;
- hosted Google login, user sessions, CSRF, adult activation, or product permissions;
- ingestion, parsing, rich documents, memory, retrieval, learning, MCP tools,
  Notion, export, or deletion product behavior;
- hosted GCP infrastructure;
- Tex integration or paid/local model functionality;
- fake product data or product APIs to make infrastructure tests pass;
- production credentials, externally trusted certificates, public deployments,
  or automatic destructive migrations.

Keycloak proves the OIDC infrastructure boundary only; Phase 3 owns application
authentication and authorization. PostgreSQL and object-store durability tests
must use explicitly isolated operational fixtures, not invented canonical tables.

## D. Implementation rules

- Default Compose must be fully functional with **Tex absent and disabled**.
- Use one production-like base Compose file plus clearly bounded development,
  test, or optional profiles. Do not copy topology into competing files.
- Pin every upstream image by immutable digest with a readable version comment
  or machine-readable version registry. Do not use `latest` or floating majors.
- Phase 11 owns full SBOM, signing, provenance, and vulnerability-disposition
  release machinery. Phase 2 must create clean extension seams and must not
  falsely claim those later gates complete.
- Only Caddy may expose the application entrypoint. Bind any operator-only local
  ports explicitly to `127.0.0.1`; PostgreSQL, SeaweedFS internals, Hatchet
  internals, OpenBao, telemetry stores, and service backends must not bind all
  host interfaces.
- Use health checks and `depends_on: condition: service_healthy`; do not use
  sleeps as readiness.
- Use bounded restart policies, resource-conscious defaults, named volumes, and
  isolated networks. Avoid privileged mode, host networking, Docker socket
  mounts, broad Linux capabilities, and writable root filesystems unless a
  documented component-specific need is proven and tested.
- Images and processes remain non-root wherever the upstream component supports
  it. Document unavoidable upstream exceptions with compensating controls.
- Secret values live in ignored runtime files, Docker secrets, or encrypted
  storage. Example files contain placeholders only. Never place secrets in image
  layers, command arguments, Compose-rendered logs, workflow payloads, traces,
  dashboards, or committed state.
- Self-host telemetry has no external exporter by default. Observability data
  must follow the strict content denylist.
- Application startup never runs destructive migrations. A separate bounded
  migration job seam may report that domain migrations are unavailable until
  Phase 3; do not add fake migrations.
- All new root commands must be deterministic, documented, and exercised.

## E. Micro-phase 2.1 — Tex-disabled Compose topology

Implement and validate:

1. A Compose topology containing:
   - Caddy;
   - web;
   - Core API;
   - MCP edge;
   - workers;
   - model router;
   - Hatchet and its required self-hosted dependencies;
   - PostgreSQL with pgvector;
   - SeaweedFS with an S3-compatible endpoint;
   - Keycloak;
   - OpenBao;
   - OpenTelemetry Collector and a documented Grafana-compatible local stack.
2. Public, application, data, workflow, and observability networks with the
   minimum required cross-network attachments.
3. Named persistent volumes for every stateful component.
4. Deterministic liveness/readiness checks and health-based startup ordering.
5. Safe bounded restart policies and shutdown grace periods.
6. A production-like base configuration and a development override that changes
   only developer ergonomics, never security invariants.
7. Optional profiles for operator tooling and future providers. Tex must not be
   required, configured, pulled, or started by the default profile.
8. Caddy routing for the web, `/api`, MCP, OIDC, and approved operator surfaces
   without exposing internal stores.
9. Automated assertions over rendered Compose configuration proving:
   - no floating images;
   - no forbidden host ports;
   - no privileged services or Docker socket;
   - required networks, volumes, health checks, and secret references exist;
   - Tex is absent from the default dependency graph.

### Micro-phase 2.1 self-check

Run and fix:

- `docker compose config` for base, development, test, and optional profiles;
- negative configuration fixtures;
- a fresh build/pull and Tex-disabled boot from empty Phase 2 volumes;
- health convergence with a bounded timeout and useful failure logs;
- network/port inspection from both host and containers;
- restart-policy and non-root inspection;
- existing Phase 1 validation affected by the changes;
- whitespace and secret scans.

Record image names, versions, digests, service count, network attachments,
published ports, health convergence time, failures fixed, and raw evidence.
Continue only after the self-check passes.

## F. Micro-phase 2.2 — Configuration, secrets, and local trust

Implement and validate:

1. Typed, fail-fast configuration for web, MCP, Core, workers, and model router
   across `hosted`, `self_host`, `test`, and `development` modes.
2. A single documented configuration inventory naming owner, type, required
   mode, default, secrecy, reload behavior, and validation rule.
3. Safe example environment and secret templates with no usable credential.
4. Startup rejection for blank/default production secrets, malformed URLs,
   invalid issuer/audience combinations, unsafe origins, wildcard trust,
   plaintext provider credentials, and telemetry exporters enabled without
   explicit operator configuration.
5. Reproducible Keycloak realm/client import for web, Core, and MCP trust
   boundaries. Keep roles/permissions out of Keycloak and out of this phase.
6. Local TLS termination through Caddy. Generate development CA/cert material
   into ignored paths, verify SAN/expiry/permissions, and document optional
   operator trust steps. Do not modify the host trust store automatically.
7. A generic secret-cipher port and OpenBao Transit adapter that performs a
   dummy encrypt/decrypt round trip without adding product credential storage.
8. A hosted key-provider interface or configuration seam only—no hosted cloud
   credentials or deployment.
9. OpenBao policy/token scopes limited to the required Transit operations.
   Root/bootstrap tokens must never enter application configuration.
10. Secret-redaction and telemetry-denylist tests covering environment values,
    URLs, headers, errors, health output, Compose output, and traces.
11. Correlation propagation and content-free health/dependency telemetry. Do not
    implement later product metrics or claim `TRD-OPS-011..013` complete beyond
    the infrastructure foundation.

### Micro-phase 2.2 self-check

Run and fix:

- typed configuration unit/property tests for every mode;
- invalid-secret, origin, issuer, audience, and exporter negative tests;
- Keycloak import/restart and OIDC discovery/JWKS smoke;
- HTTPS route and certificate verification using an explicit test CA;
- OpenBao initialization/bootstrap idempotency in disposable state;
- Transit encrypt/decrypt and least-privilege denial tests;
- telemetry-off and forbidden-content log-sink tests;
- repository and rendered-configuration secret scans;
- full micro-phase 2.1 smoke after configuration integration.

Continue only after the self-check passes.

## G. Micro-phase 2.3 — Durability and operational smoke

Implement and validate:

1. Separate PostgreSQL backup and restore commands using compressed/custom
   format, checksums, bounded timeouts, explicit target validation, and safe
   refusal to overwrite a non-disposable restore target.
2. A separate migration-job entrypoint. Until Phase 3 supplies migrations, it
   must validate configuration and exit with an explicit safe `N/A`, never
   invent schema or run from application startup.
3. SeaweedFS durability tooling that writes, hashes, restarts, reads, and deletes
   an isolated immutable test object.
4. PostgreSQL durability tooling using an isolated operational fixture/database,
   not a Memdot product table.
5. Hatchet infrastructure canary work with timeout, bounded retry, idempotency,
   terminal-state reporting, and no user content.
6. Restart tests for PostgreSQL, SeaweedFS, Hatchet, workers, OpenBao, Keycloak,
   observability, and the complete stack while accepted dummy work exists.
7. Persistent-volume recreation tests that distinguish container replacement
   from deliberate volume deletion.
8. Restore into a clean disposable stack and compare canonical fixture/object
   checksums. The restore test must fail closed on corruption or wrong target.
9. Dependency-failure tests for database, object storage, workflow engine,
   OpenBao, identity, and telemetry. Required services must report truthful
   readiness/degraded state and recover without an unbounded restart loop.
10. Content-free dashboards for service health, request failures, workflow queue
    depth/age, PostgreSQL, object storage, and workflow availability. Do not add
    user content, filenames, queries, prompts, answers, cookies, or credentials.
11. A single bounded end-to-end self-host smoke command that starts fresh with
    Tex disabled and external telemetry disabled, verifies TLS/routing/health,
    runs durability and restart checks, and tears down only its own disposable
    resources.
12. Operator documentation for prerequisites, sizing, first boot, local trust,
    configuration, secrets, backup, restore, upgrade/migration seam, telemetry,
    troubleshooting, recovery, and complete removal. Never market development
    defaults as production hardening.

### Micro-phase 2.3 self-check

Run and fix:

- fresh-stack smoke with Tex disabled and no paid model/API keys;
- dependency readiness and bounded failure/recovery tests;
- PostgreSQL and SeaweedFS persistence across restarts;
- Hatchet canary retry/idempotency/recovery;
- backup checksum, clean restore, corruption refusal, and wrong-target refusal;
- complete stack restart during accepted dummy work;
- telemetry-off assertion and dashboard content scan;
- host exposure/network policy assertions;
- Compose cleanup that preserves named volumes unless destructive cleanup is
  explicitly requested;
- the complete existing `make check` suite.

Continue only after all required checks pass without unexplained skips.

## H. Required command and CI integration

Add the smallest coherent root command surface, with exact names chosen only
after inspecting existing conventions. It must cover:

- Compose render/config validation;
- fresh stack start, health/status, logs, and non-destructive stop;
- destructive disposable-test cleanup with an explicit confirmation/test guard;
- configuration-negative and exposure-policy tests;
- TLS, OIDC, OpenBao, and telemetry-off smoke;
- persistence, restart, backup, and restore smoke;
- the complete Phase 2 self-host gate.

Integrate fast static/configuration checks into normal CI. Put the full
multi-service smoke in a dedicated CI job with bounded timeouts, diagnostic
artifact capture, and guaranteed cleanup. Never hide infrastructure failures
behind `continue-on-error`, unconditional `|| true`, sleeps, or skipped profiles.

## I. Phase 2 exit gate

Prove every item from `IMPLEMENTATION_TRACKER.md`:

1. A fresh operator can start the complete self-host topology using documented
   commands and safe example configuration.
2. The skeleton works without Tex or paid model APIs.
3. Internal services/stores are not unintentionally internet-facing.
4. Secrets are encrypted or referenced and never logged.
5. Restart, volume persistence, backup, and restore smoke tests pass.
6. Compose, health, configuration-negative, and secret-scan gates pass.
7. Caddy, web, Core, MCP, workers, model router, Hatchet, PostgreSQL+pgvector,
   SeaweedFS, Keycloak, OpenBao, OTel, and Grafana-compatible observability all
   reach their documented healthy state.
8. Tex and external telemetry exporters are disabled in the tested default.
9. No product/domain functionality or Phase 3 schema is implemented or claimed.
10. Documentation and AI-agent maps describe only verified paths and commands.
11. No unauthorized commit, push, deploy, credential action, paid resource, or
    external/production mutation occurred.

Update `AGENTS.md`, `CONTEXT.md`, `IMPLEMENTATION_PLAN.md`,
`IMPLEMENTATION_TRACKER.md`, `docs/README.md`, the Codebase Context Map, and
operator documentation to the truthful **Phase 2 candidate pending Codex audit**
state. Do not mark Codex PASS or authorize Phase 3.

## J. Blocker rules

Stop only when:

- the accepted documents materially contradict each other;
- required image/tool licensing or architecture cannot satisfy the contract;
- the host cannot safely run the required stack after bounded profile/resource
  diagnosis;
- a real credential, paid resource, public DNS, system trust-store mutation, or
  production/third-party action is required;
- a choice would weaken a locked security, privacy, self-host, or canonical-data
  invariant.

Report the exact micro-phase, command/error, diagnosis, safe attempts, and
smallest owner decision needed. Do not silently skip or replace a required
component.

## K. Final Grok report

After the complete exit gate passes, stop and produce one report using
`docs/execution/PHASE_REPORT_TEMPLATE.md` with heading:

`GROK PHASE REPORT — PHASE 2`

In addition to the template, include:

- baseline commit and final dirty-tree inventory;
- all image versions/digests and license notes;
- rendered service/profile/network/volume/port matrix;
- exact configuration and secret ownership inventory;
- proof Tex and external telemetry are absent from the default graph;
- TLS, OIDC discovery/JWKS, OpenBao Transit, and least-privilege evidence;
- health convergence and resource-usage measurements;
- restart, canary, persistence, backup, restore, corruption, and failure-recovery evidence;
- host-exposure scan and content-denylist results;
- every test count, skip, warning, flaky rerun, failure fixed, and raw command exit code;
- complete patch/diff and documentation traceability;
- explicit Phase 3+ deferrals;
- authority confirmation.

Do not commit. Wait for Tauqueer to bring the report and complete diff to Codex.

---

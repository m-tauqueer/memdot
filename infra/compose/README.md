# Memdot self-host Compose operator guide (Phase 2 candidate)

## Prerequisites

- Docker Engine + Compose v2 (system `dockerd` / `unix:///var/run/docker.sock`)
- OpenSSL, curl, Make, pnpm/uv for repository gates
- ~6–8 GiB free memory recommended for the full stack

## First boot

```bash
# From repository root
cp infra/compose/.env.example infra/compose/.env
# Replace REPLACE_WITH_OPERATOR_SECRET with disposable local values (never production)
bash infra/compose/scripts/materialize_local_secrets.sh

export MEMDOT_HTTP_PORT=8080 MEMDOT_HTTPS_PORT=8443
make compose-config
make compose-up
make compose-ps
```

Public entrypoint: Caddy on `MEMDOT_HTTP_PORT` / `MEMDOT_HTTPS_PORT`.
Operator-only ports (dev overlay) bind to `127.0.0.1` only.

## Local TLS trust

Certificates are generated under `infra/compose/tls/` (gitignored).
Memdot never modifies the host trust store automatically. Trust the generated
**CA certificate** (`infra/compose/tls/ca.crt`) in browsers and tools — not the
leaf/server certificate alone.

## Resource requirements

- Full stack + `make selfhost-smoke`: **~8–10 GiB free RAM** recommended.
- If another heavy Docker workload is running locally, pause it for the smoke run
  or use the isolated CI job (`selfhost-smoke` workflow) instead of marking smoke
  passed on a resource-starved host.

## Configuration and secrets

Canonical inventory: [docs/ops/CONFIG_INVENTORY.md](../../docs/ops/CONFIG_INVENTORY.md).
Secret files live in ignored `secrets/*.env`. Example templates contain placeholders only.
OpenBao root/unseal material is bootstrap-only under `secrets/openbao_bootstrap/`
(0700/0600) and must not enter application config. Application Transit access uses
`CORE_OPENBAO_TRANSIT_TOKEN_FILE` (0600, uid `10001`). Hatchet uses `DATABASE_URL`
in `secrets/hatchet.env`.

Compose bind roots may be overridden with `MEMDOT_SECRETS_DIR`, `MEMDOT_TLS_DIR`,
and `MEMDOT_ENV_FILE` so disposable smoke does not rewrite operator files.

## Tex and telemetry

Default graph has **no Tex service**. Model router keeps `TEX_ENABLED=false`.
External OTLP export is off (`OTEL_SDK_DISABLED=true`, empty exporter endpoint).
Telemetry outage must not fail required product readiness.

## Health, logs, stop

```bash
make compose-ps
make compose-logs
make compose-down   # preserves named volumes
```

Destructive disposable cleanup (explicit):

```bash
docker compose --env-file infra/compose/.env -f infra/compose/compose.yaml down -v
```

## Backup / restore / migration seam

```bash
bash infra/compose/scripts/postgres_backup.sh /tmp/memdot-backups
bash infra/compose/scripts/postgres_restore.sh path/to/dump memdot_restore_<unique-id>
bash infra/compose/scripts/migration_job.sh   # exits N/A until Phase 3
```

Restore targets must be disposable `memdot_restore_<unique-id>` databases only.

## Full smoke

```bash
make selfhost-smoke
```

Smoke uses an exclusive flock (`/tmp/memdot-selfhost-smoke.lock`), an isolated
runtime directory for secrets/TLS/`.env`, and writes the Compose project name to
`/tmp/memdot-smoke-project-name` for CI cleanup. Concurrent smoke is refused.
Operator `infra/compose/secrets` and `tls` remain byte-identical.

Development defaults are not production hardening.

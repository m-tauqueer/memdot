# Memdot configuration inventory (Phase 2.2)

Owner-facing inventory of typed runtime settings. Values in example files are
placeholders only. Secret material lives in ignored `infra/compose/secrets/*.env`
or OpenBao Transit — never in image layers or committed state.

Modes: `hosted` | `self_host` | `test` | `development`

| Owner        | Key                               | Type        | Required modes      | Default                   | Secret | Reload  | Validation                     |
| ------------ | --------------------------------- | ----------- | ------------------- | ------------------------- | ------ | ------- | ------------------------------ |
| web          | `WEB_ENV`                         | enum        | all                 | `development`             | no     | restart | one of four modes              |
| web          | `WEB_ALLOWED_ORIGINS`             | CSV origins | all                 | `http://localhost:3000`   | no     | restart | absolute http(s), no `*`       |
| web          | `WEB_OIDC_ISSUER`                 | URL         | self_host, hosted   | empty                     | no     | restart | absolute URL when required     |
| web          | `WEB_OIDC_AUDIENCE`               | string      | all                 | `memdot-web`              | no     | restart | non-empty                      |
| web          | `WEB_TELEMETRY_EXPORT`            | string      | all                 | `off`                     | no     | restart | if enabled, endpoint required  |
| web          | `WEB_OTEL_EXPORTER_OTLP_ENDPOINT` | URL         | when export on      | empty                     | no     | restart | absolute URL when export on    |
| mcp          | `MCP_ENV`                         | enum        | all                 | required                  | no     | restart | one of four modes              |
| mcp          | `MCP_HOST` / `MCP_PORT`           | host/port   | all                 | `0.0.0.0` / `8100`        | no     | restart | positive port                  |
| mcp          | `MCP_OIDC_ISSUER`                 | URL         | self_host, hosted   | empty                     | no     | restart | absolute URL                   |
| mcp          | `MCP_OIDC_DISCOVERY_URL`          | URL         | self_host (compose) | issuer                    | no     | restart | in-cluster discovery for ready |
| mcp          | `MCP_OIDC_AUDIENCE`               | string      | self_host, hosted   | `memdot-mcp`              | no     | restart | non-empty                      |
| mcp          | `MCP_ALLOWED_ORIGINS`             | CSV origins | all                 | `http://localhost:3000`   | no     | restart | absolute http(s), no `*`       |
| mcp          | `MCP_TELEMETRY_EXPORT`            | string      | all                 | `off`                     | no     | restart | endpoint required if enabled   |
| mcp          | `MCP_PROVIDER_API_KEY`            | string      | optional            | empty                     | yes    | restart | reject plaintext provider keys |
| core         | `CORE_ENV`                        | enum        | all                 | `development`             | no     | restart | one of four modes              |
| core         | `CORE_HOST` / `CORE_PORT`         | host/port   | all                 | `0.0.0.0` / `8000`        | no     | restart | positive port                  |
| core         | `CORE_DATABASE_URL`               | DSN         | self_host, hosted   | empty                     | yes    | restart | absolute postgres URL          |
| core         | `CORE_OBJECT_STORE_ENDPOINT`      | URL         | self_host, hosted   | empty                     | no     | restart | absolute URL                   |
| core         | `CORE_OBJECT_STORE_ACCESS_KEY`    | string      | self_host           | empty                     | yes    | restart | required for S3 readiness      |
| core         | `CORE_OBJECT_STORE_SECRET_KEY`    | string      | self_host           | empty                     | yes    | restart | required for S3 readiness      |
| core         | `CORE_OIDC_ISSUER`                | URL         | self_host, hosted   | empty                     | no     | restart | absolute URL                   |
| core         | `CORE_OIDC_AUDIENCE`              | string      | all                 | `memdot-core`             | no     | restart | non-empty                      |
| core         | `CORE_OPENBAO_ADDR`               | URL         | self_host           | empty                     | no     | restart | absolute URL                   |
| core         | `CORE_OPENBAO_TRANSIT_TOKEN_FILE` | path        | self_host           | `/run/secrets/...`        | yes    | restart | file token; not root/dev       |
| core         | `CORE_OPENBAO_TRANSIT_TOKEN`      | token       | optional override   | empty                     | yes    | restart | reject placeholders/root       |
| core         | `CORE_ALLOWED_ORIGINS`            | CSV origins | all                 | `http://localhost:3000`   | no     | restart | absolute http(s), no `*`       |
| core         | `CORE_TELEMETRY_EXPORT`           | string      | all                 | `off`                     | no     | restart | endpoint required if enabled   |
| core         | `CORE_PROVIDER_API_KEY`           | string      | optional            | empty                     | yes    | restart | reject plaintext provider keys |
| workers      | `WORKERS_ENV`                     | enum        | all                 | `development`             | no     | restart | one of four modes              |
| workers      | `WORKERS_HATCHET_HOST` / `PORT`   | host/port   | all                 | `hatchet-engine` / `7070` | no     | restart | non-empty host                 |
| workers      | `WORKERS_TELEMETRY_EXPORT`        | string      | all                 | `off`                     | no     | restart | endpoint required if enabled   |
| workers      | `WORKERS_PROVIDER_API_KEY`        | string      | optional            | empty                     | yes    | restart | reject plaintext provider keys |
| model-router | `MODEL_ROUTER_ENV`                | enum        | all                 | `development`             | no     | restart | one of four modes              |
| model-router | `MODEL_ROUTER_TEX_ENABLED`        | bool        | all                 | `false`                   | no     | restart | must stay false until Phase 7  |
| model-router | `MODEL_ROUTER_TELEMETRY_EXPORT`   | string      | all                 | `off`                     | no     | restart | endpoint required if enabled   |
| model-router | `MODEL_ROUTER_PROVIDER_API_KEY`   | string      | optional            | empty                     | yes    | restart | reject plaintext provider keys |

## Readiness dependency classes (Phase 2)

| Service      | Readiness requires                                                                            | Notes                                                                |
| ------------ | --------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| core         | PostgreSQL `SELECT 1`; OpenBao initialized/unsealed + Transit key; SeaweedFS authenticated S3 | Telemetry never gates ready                                          |
| workers      | Hatchet engine TCP                                                                            | Telemetry never gates ready                                          |
| mcp          | OIDC discovery (`MCP_OIDC_DISCOVERY_URL` or issuer)                                           | Degrades when IdP unavailable                                        |
| web          | Process only                                                                                  | **OIDC is not required for server readiness**; enforced at auth time |
| model-router | Process only                                                                                  | Tex remains disabled                                                 |

## Secret cipher

| Component                                                       | Interface       | Notes                                       |
| --------------------------------------------------------------- | --------------- | ------------------------------------------- |
| `memdot_domain.ports.secret_cipher.SecretCipherPort`            | encrypt/decrypt | Domain port; no storage ownership           |
| `memdot_provider_adapters.OpenBaoTransitAdapter`                | Transit HTTP    | Rejects root/placeholder tokens             |
| `memdot_domain.ports.hosted_key_provider.HostedKeyProviderPort` | seam            | Hosted KMS later; no credentials in Phase 2 |
| `memdot_provider_adapters.UnconfiguredHostedKeyProvider`        | stub            | `is_configured() == false` by default       |

## Compose / operator secrets

| File                                          | Purpose                                                                          |
| --------------------------------------------- | -------------------------------------------------------------------------------- |
| `infra/compose/.env`                          | Non-secret operator overrides (ports, modes)                                     |
| `infra/compose/secrets/postgres.env`          | Postgres password                                                                |
| `infra/compose/secrets/hatchet.env`           | Hatchet `DATABASE_URL` (not `HATCHET_DATABASE_URL`)                              |
| `infra/compose/secrets/keycloak.env`          | Keycloak admin + DB password                                                     |
| `infra/compose/secrets/openbao.env`           | `BAO_ADDR` only (no root/dev token env)                                          |
| `infra/compose/secrets/openbao_transit_token` | App Transit token via `CORE_OPENBAO_TRANSIT_TOKEN_FILE` (0600, Core uid `10001`) |
| `infra/compose/secrets/openbao_bootstrap/`    | Init/unseal/root (0700/0600, bootstrap-only)                                     |
| `infra/compose/secrets/workers.env`           | `WORKERS_HATCHET_HOST` / `WORKERS_HATCHET_PORT`                                  |
| `infra/compose/secrets/seaweedfs.env`         | S3 access/secret                                                                 |
| `infra/compose/tls/ca.crt`                    | Trust anchor for local HTTPS                                                     |
| `infra/compose/tls/server.{crt,key}`          | Local Caddy TLS leaf (gitignored)                                                |

OpenBao runs non-dev file storage in Phase 2 Compose. There is **no**
`OPENBAO_DEV_ROOT_TOKEN_ID` application setting. Root/unseal material stays under
`secrets/openbao_bootstrap/` and must not enter application env files. Transit
tokens are written only to `openbao_transit_token` and consumed through
`CORE_OPENBAO_TRANSIT_TOKEN_FILE`.

## Compose bind overrides (smoke isolation)

| Variable                         | Default                           | Purpose                                     |
| -------------------------------- | --------------------------------- | ------------------------------------------- |
| `MEMDOT_SECRETS_DIR`             | `./secrets`                       | Secrets/bootstrap bind root                 |
| `MEMDOT_TLS_DIR`                 | `./tls`                           | TLS material bind root                      |
| `MEMDOT_ENV_FILE`                | `infra/compose/.env`              | Compose `--env-file`                        |
| `MEMDOT_SMOKE_RUNTIME_DIR`       | `/tmp/<project>-runtime`          | Disposable smoke secrets/tls/.env           |
| `MEMDOT_SMOKE_LOCK_FILE`         | `/tmp/memdot-selfhost-smoke.lock` | Exclusive flock; concurrent smoke refused   |
| `MEMDOT_SMOKE_PROJECT_NAME_FILE` | `/tmp/memdot-smoke-project-name`  | CI cleanup source (never `*-logs` basename) |

`make selfhost-smoke` materializes into `MEMDOT_SMOKE_RUNTIME_DIR` and does **not**
rewrite operator `infra/compose/secrets` or `tls`. Cleanup removes only the
generated smoke project/runtime.

## PostgreSQL restore targets

Restore is allowed only into disposable databases:

```bash
bash infra/compose/scripts/postgres_restore.sh <dump> memdot_restore_<unique-id>
```

Examples: `memdot_restore_1686882`, `memdot_restore_$RANDOM`. Restoring into
`memdot`, `memdot_ops`, `hatchet`, or `keycloak` must fail closed.

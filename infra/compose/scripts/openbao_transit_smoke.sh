#!/usr/bin/env bash
set -euo pipefail

# Live OpenBao Transit round-trip + least-privilege denial using OpenBaoTransitAdapter.
# App token stays owner-only (Core uid); host reads it via a root one-shot without chmod weaken.
# Uses the already-pinned OpenBao image (no BusyBox helper dependency).

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"

SECRETS_DIR="${MEMDOT_SECRETS_DIR:-$ROOT/infra/compose/secrets}"
ENV_FILE="${MEMDOT_ENV_FILE:-$ROOT/infra/compose/.env}"
TOKEN_FILE="$SECRETS_DIR/openbao_transit_token"
BOOTSTRAP_DIR="$SECRETS_DIR/openbao_bootstrap"
OPENBAO_IMAGE="openbao/openbao:2.1.0@sha256:7de07aa6df3937d44c96c2d65c188b2d4a70546f2a764ad4510301305af6a223"

[[ -s "$TOKEN_FILE" ]] || { echo "missing transit token" >&2; exit 1; }

# Permission assertions
perm_token="$(stat -c '%a' "$TOKEN_FILE")"
perm_boot="$(stat -c '%a' "$BOOTSTRAP_DIR")"
[[ "$perm_boot" == "700" ]] || { echo "bootstrap dir must be 0700 got $perm_boot" >&2; exit 1; }
[[ "$perm_token" == "600" ]] || { echo "transit token must be 0600 got $perm_token" >&2; exit 1; }
for f in init.json unseal.key root.token; do
  if [[ -f "$BOOTSTRAP_DIR/$f" ]]; then
    p="$(stat -c '%a' "$BOOTSTRAP_DIR/$f")"
    [[ "$p" == "600" ]] || { echo "$f must be 0600 got $p" >&2; exit 1; }
  fi
done
echo "openbao_permissions_ok"

export BAO_ADDR="${BAO_ADDR:-http://127.0.0.1:18200}"
if ! curl -fsS "${BAO_ADDR}/v1/sys/health?standbyok=true" >/dev/null 2>&1; then
  export BAO_ADDR="http://127.0.0.1:8200"
fi
if ! curl -fsS "${BAO_ADDR}/v1/sys/health?standbyok=true" >/dev/null 2>&1; then
  echo "openbao not reachable on loopback; publish 18200/8200 via test/dev overlay" >&2
  exit 1
fi

read_token() {
  docker run --rm -v "$TOKEN_FILE:/t:ro" --user 0 --entrypoint cat "$OPENBAO_IMAGE" /t | tr -d '[:space:]'
}

TOKEN="$(read_token)"
[[ -n "$TOKEN" ]] || { echo "empty transit token" >&2; exit 1; }
export MEMDOT_TRANSIT_TOKEN="$TOKEN"
unset TOKEN

uv run python - <<'PY'
from __future__ import annotations

import os
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from memdot_provider_adapters.openbao_transit import OpenBaoTransitAdapter

token = os.environ["MEMDOT_TRANSIT_TOKEN"]
addr = os.environ.get("BAO_ADDR", "http://127.0.0.1:8200")

adapter = OpenBaoTransitAdapter(address=addr, token=token)
plaintext = b"memdot-ops-transit-fixture"
ciphertext = adapter.encrypt(plaintext, key_name="memdot-local")
recovered = adapter.decrypt(ciphertext, key_name="memdot-local")
assert recovered == plaintext, "transit round-trip mismatch"

req = Request(
    f"{addr}/v1/sys/policies/acl",
    headers={"X-Vault-Token": token},
    method="GET",
)
try:
    with urlopen(req, timeout=5) as resp:  # noqa: S310
        body = resp.read()
    raise SystemExit(f"app token unexpectedly allowed sys/policies: {body[:80]!r}")
except HTTPError as exc:
    if exc.code not in {403, 404}:
        raise SystemExit(f"unexpected denial code {exc.code}") from None

for path in ("sys/auth", "transit/keys"):
    req = Request(f"{addr}/v1/{path}", headers={"X-Vault-Token": token}, method="GET")
    try:
        with urlopen(req, timeout=5) as resp:  # noqa: S310
            raise SystemExit(f"app token unexpectedly allowed {path}")
    except HTTPError as exc:
        if exc.code not in {403, 404}:
            raise SystemExit(f"unexpected denial for {path}: {exc.code}") from None

print("openbao_transit_roundtrip_ok")
print("openbao_least_privilege_ok")
PY

COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-memdot}"
FILES=(-f "$ROOT/infra/compose/compose.yaml")
if [[ "${COMPOSE_PROJECT_NAME}" == memdot-smoke-* ]] || [[ "${COMPOSE_PROJECT_NAME}" == memdot-test* ]]; then
  FILES+=(-f "$ROOT/infra/compose/compose.test.yaml")
fi
COMPOSE=(docker compose --project-name "$COMPOSE_PROJECT_NAME" --env-file "$ENV_FILE" "${FILES[@]}")

CIPHER_B64="$(BAO_ADDR="$BAO_ADDR" MEMDOT_TRANSIT_TOKEN="$MEMDOT_TRANSIT_TOKEN" uv run python - <<'PY'
import os
from memdot_provider_adapters.openbao_transit import OpenBaoTransitAdapter
adapter = OpenBaoTransitAdapter(address=os.environ["BAO_ADDR"], token=os.environ["MEMDOT_TRANSIT_TOKEN"])
ct = adapter.encrypt(b"persist-after-restart", key_name="memdot-local")
print(ct.decode())
PY
)"

"${COMPOSE[@]}" restart openbao
"${COMPOSE[@]}" run --rm --no-deps \
  -e BAO_ADDR=http://openbao:8200 \
  -e OPENBAO_BOOTSTRAP_DIR=/bootstrap \
  -e OPENBAO_TRANSIT_TOKEN_FILE=/secrets/openbao_transit_token \
  -v "$ROOT/infra/compose/scripts/openbao_bootstrap.sh:/bootstrap.sh:ro" \
  -v "$BOOTSTRAP_DIR:/bootstrap" \
  -v "$SECRETS_DIR:/secrets" \
  --entrypoint /bin/sh openbao /bootstrap.sh >/dev/null

TOKEN="$(read_token)"
export MEMDOT_TRANSIT_TOKEN="$TOKEN"
unset TOKEN

BAO_ADDR="$BAO_ADDR" CIPHER="$CIPHER_B64" MEMDOT_TRANSIT_TOKEN="$MEMDOT_TRANSIT_TOKEN" uv run python - <<'PY'
import os
from memdot_provider_adapters.openbao_transit import OpenBaoTransitAdapter
adapter = OpenBaoTransitAdapter(address=os.environ["BAO_ADDR"], token=os.environ["MEMDOT_TRANSIT_TOKEN"])
pt = adapter.decrypt(os.environ["CIPHER"].encode(), key_name="memdot-local")
assert pt == b"persist-after-restart"
print("openbao_transit_persist_ok")
PY

perm_token="$(stat -c '%a' "$TOKEN_FILE")"
[[ "$perm_token" == "600" ]] || { echo "transit token perms weakened after restart: $perm_token" >&2; exit 1; }
echo "openbao_permissions_persist_ok"

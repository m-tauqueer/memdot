#!/usr/bin/env bash
set -euo pipefail

# Content-safe local secret scan for common credential patterns in tracked trees.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PATTERN_FILE="$ROOT/scripts/secret_scan_patterns.txt"
mapfile -t patterns < <(grep -v '^[[:space:]]*#' "$PATTERN_FILE" | grep -v '^[[:space:]]*$' || true)

failed=0
for pattern in "${patterns[@]}"; do
  matches="$(rg -n -e "$pattern" \
    --glob '!**/node_modules/**' --glob '!**/.venv/**' --glob '!**/dist/**' \
    --glob '!**/.next/**' --glob '!**/.git/**' --glob '!pnpm-lock.yaml' --glob '!uv.lock' \
    --glob '!docs/execution/**' --glob '!LICENSE' \
    --glob '!**/PHASE_*_CANDIDATE*' \
    --glob '!infra/compose/secrets/**' \
    --glob '!infra/compose/tls/**' \
    --glob '!**/*.runtime.json' \
    --glob '!scripts/secret_scan.sh' \
    --glob '!scripts/secret_scan_patterns.txt' \
    --glob '!infra/compose/scripts/validate_compose_policy.py' \
    --glob '!infra/compose/scripts/observability_smoke.sh' \
    --glob '!tests/infra/test_compose_policy_negatives.py' \
    --glob '!tests/infra/test_materialize_secrets.py' \
    --glob '!tests/security/test_secret_scan.py' \
    --glob '!tests/security/secret_scan_fixtures/**' \
    . || true)"
  if [[ -n "$matches" ]]; then
    echo "Secret-scan hit for pattern: $pattern"
    echo "$matches"
    failed=1
  fi
done

# Generic committed Keycloak/S3 secret fields outside templates
if rg -n -e '"secret"\s*:\s*"[^"_]+"' \
  --glob '!**/node_modules/**' --glob '!**/.venv/**' --glob '!**/*.template' \
  --glob '!infra/compose/secrets/**' --glob '!**/*.runtime.json' \
  --glob '!tests/security/secret_scan_fixtures/**' \
  infra/compose/config 2>/dev/null; then
  echo "Secret-scan hit: committed Keycloak secret field"
  failed=1
fi
if rg -n -e '"accessKey"\s*:\s*"[^"_]+"' \
  --glob '!**/node_modules/**' --glob '!**/*.template' \
  --glob '!infra/compose/secrets/**' \
  --glob '!tests/security/secret_scan_fixtures/**' \
  infra/compose/config 2>/dev/null; then
  echo "Secret-scan hit: committed S3 accessKey field"
  failed=1
fi

if [[ "$failed" -ne 0 ]]; then
  exit 1
fi

echo "Secret scan passed (no high-confidence credential patterns found)."

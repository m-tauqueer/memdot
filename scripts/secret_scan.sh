#!/usr/bin/env bash
set -euo pipefail

# Content-safe local secret scan for common credential patterns in tracked trees.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

patterns=(
  'AKIA[0-9A-Z]{16}'
  '-----BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY-----'
  'xox[baprs]-[0-9A-Za-z-]{10,}'
  'ghp_[0-9A-Za-z]{36}'
  'sk-[a-zA-Z0-9]{20,}'
)

failed=0
for pattern in "${patterns[@]}"; do
  matches="$(rg -n -e "$pattern" \
    --glob '!**/node_modules/**' --glob '!**/.venv/**' --glob '!**/dist/**' \
    --glob '!**/.next/**' --glob '!**/.git/**' --glob '!pnpm-lock.yaml' --glob '!uv.lock' \
    --glob '!docs/execution/**' --glob '!LICENSE' \
    . || true)"
  if [[ -n "$matches" ]]; then
    echo "Secret-scan hit for pattern: $pattern"
    echo "$matches"
    failed=1
  fi
done

if [[ "$failed" -ne 0 ]]; then
  exit 1
fi

echo "Secret scan passed (no high-confidence credential patterns found)."

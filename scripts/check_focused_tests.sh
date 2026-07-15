#!/usr/bin/env bash
set -euo pipefail

# Fail if focused or disabled tests appear committed in source trees.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

patterns=(
  '\bit\.only\('
  '\bdescribe\.only\('
  '\btest\.only\('
  '\bfit\('
  '\bfdescribe\('
  '@pytest\.mark\.skip'
  'pytest\.skip\('
  '\bxit\('
  '\bxdescribe\('
)

failed=0
for pattern in "${patterns[@]}"; do
  matches="$(rg -n --glob '!**/node_modules/**' --glob '!**/.venv/**' --glob '!**/dist/**' --glob '!**/.next/**' \
    --glob '!docs/**' --glob '!IMPLEMENTATION_*' --glob '!CONTEXT.md' \
    "$pattern" apps packages services tests scripts || true)"
  if [[ -n "$matches" ]]; then
    echo "Found forbidden focused/skipped test pattern: $pattern"
    echo "$matches"
    failed=1
  fi
done

if [[ "$failed" -ne 0 ]]; then
  exit 1
fi

echo "No focused or disabled test markers found."

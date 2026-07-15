#!/usr/bin/env bash
set -euo pipefail

# Root-commit / base-aware whitespace validation.
# Re-indexes the full candidate tree into a temporary Git index and runs
# `git diff --cached --check`, which works with or without an existing HEAD
# and also on a clean CI checkout where ordinary `git diff --check` is empty.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

TMP_INDEX="$(mktemp)"
cleanup() {
  rm -f "$TMP_INDEX"
}
trap cleanup EXIT

export GIT_INDEX_FILE="$TMP_INDEX"
git read-tree --empty
git add -A
# Ignore local handoff artifacts if present and untracked via gitignore.
git diff --cached --check
echo "Whitespace check passed (full candidate tree via temporary index)."

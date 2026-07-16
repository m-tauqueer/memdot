#!/usr/bin/env bash
# Extract and validate a Compose project name for self-host smoke CI cleanup.
# Usage:
#   smoke_project_name.sh read [file]
#   smoke_project_name.sh validate <name>
set -euo pipefail

PATTERN='^memdot-smoke-[a-z0-9_-]+$'

validate_name() {
  local name="$1"
  [[ "$name" =~ $PATTERN ]] || return 1
  return 0
}

read_name() {
  local file="${1:-/tmp/memdot-smoke-project-name}"
  if [[ ! -f "$file" ]]; then
    echo "smoke_project_name_absent file=$file" >&2
    return 1
  fi
  local name
  name="$(tr -d '[:space:]' <"$file")"
  if [[ -z "$name" ]]; then
    echo "smoke_project_name_empty file=$file" >&2
    return 1
  fi
  if ! validate_name "$name"; then
    echo "smoke_project_name_invalid name=$name" >&2
    return 1
  fi
  printf '%s\n' "$name"
}

case "${1:-}" in
  validate)
    validate_name "${2:-}" && echo "valid" || {
      echo "invalid" >&2
      exit 1
    }
    ;;
  read)
    read_name "${2:-/tmp/memdot-smoke-project-name}"
    ;;
  *)
    echo "usage: $0 read [file] | validate <name>" >&2
    exit 2
    ;;
esac

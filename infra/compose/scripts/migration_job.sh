#!/usr/bin/env bash
set -euo pipefail

# Migration job seam: domain migrations are N/A until Phase 3.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
MODE="${1:-self_host}"

case "$MODE" in
  hosted|self_host|test|development) ;;
  *)
    echo "invalid mode: $MODE" >&2
    exit 2
    ;;
esac

echo "migration_job=N/A"
echo "reason=domain_migrations_deferred_to_phase_3"
echo "mode=$MODE"
echo "action=validated_configuration_only"
exit 0

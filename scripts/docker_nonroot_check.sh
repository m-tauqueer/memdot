#!/usr/bin/env bash
set -euo pipefail

# Inspect a local image for non-root USER. Usage: ./scripts/docker_nonroot_check.sh IMAGE
IMAGE="${1:?image tag required}"
user="$(docker image inspect "$IMAGE" --format '{{.Config.User}}')"
if [[ -z "$user" || "$user" == "root" || "$user" == "0" ]]; then
  echo "FAIL: $IMAGE runs as root (User='$user')"
  exit 1
fi
echo "OK: $IMAGE User=$user"

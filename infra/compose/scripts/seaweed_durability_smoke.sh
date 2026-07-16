#!/usr/bin/env bash
set -euo pipefail

# SeaweedFS durability via S3-compatible API (not direct /data writes).
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"

# shellcheck disable=SC1091
source "${MEMDOT_SECRETS_DIR:-$ROOT/infra/compose/secrets}/seaweedfs.env"

PROJECT="${COMPOSE_PROJECT_NAME:-memdot}"
FILES=(-f "$ROOT/infra/compose/compose.yaml")
if [[ "$PROJECT" == memdot-smoke-* || "$PROJECT" == memdot-test* ]]; then
  FILES+=(-f "$ROOT/infra/compose/compose.test.yaml")
fi
COMPOSE=(docker compose --project-name "$PROJECT" --env-file "${MEMDOT_ENV_FILE:-$ROOT/infra/compose/.env}" "${FILES[@]}")

# Host-side smoke must use published loopback ports — never the in-compose DNS name
# from seaweedfs.env (SEAWEEDFS_S3_ENDPOINT=http://seaweedfs:8333).
ENDPOINT=""
PUBLISHED="$("${COMPOSE[@]}" port seaweedfs 8333 2>/dev/null | head -n1 || true)"
if [[ -n "$PUBLISHED" ]]; then
  # docker compose port prints host:port (e.g. 127.0.0.1:18333)
  ENDPOINT="http://${PUBLISHED}"
elif [[ "$PROJECT" == memdot-smoke-* || "$PROJECT" == memdot-test* ]]; then
  ENDPOINT="http://127.0.0.1:18333"
elif nc -z 127.0.0.1 8333 2>/dev/null; then
  ENDPOINT="http://127.0.0.1:8333"
elif [[ -n "${SEAWEEDFS_S3_ENDPOINT_HOST:-}" ]]; then
  ENDPOINT="$SEAWEEDFS_S3_ENDPOINT_HOST"
else
  echo "seaweed_durability_failed reason=no_published_s3_port" >&2
  exit 1
fi
echo "seaweed_s3_endpoint=$ENDPOINT"

BUCKET="memdot-fixtures-ops"
KEY="durability-$(date -u +%Y%m%dT%H%M%SZ).bin"
PAYLOAD="memdot-s3-fixture-$(openssl rand -hex 8)"
CHECKSUM="$(printf '%s' "$PAYLOAD" | sha256sum | awk '{print $1}')"
TMP="$(mktemp)"
printf '%s' "$PAYLOAD" >"$TMP"

export AWS_ACCESS_KEY_ID="$SEAWEEDFS_S3_ACCESS_KEY"
export AWS_SECRET_ACCESS_KEY="$SEAWEEDFS_S3_SECRET_KEY"
export AWS_DEFAULT_REGION=us-east-1

run_s3() {
  if command -v aws >/dev/null 2>&1; then
    aws --endpoint-url "$ENDPOINT" --no-verify-ssl "$@"
  else
    uv run python - "$ENDPOINT" "$@" <<'PY'
import hashlib, hmac, datetime, sys, urllib.request, xml.etree.ElementTree as ET
# Minimal PUT/GET/DELETE for path-style S3 using aws4? Seaweed often allows unsigned in local.
# Prefer botocore if present.
endpoint, *args = sys.argv[1:]
try:
    import boto3
    from botocore.client import Config
    import os
    client = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )
except Exception as exc:
    raise SystemExit(f"aws cli and boto3 unavailable: {exc}")

# Translate a tiny subset of aws s3 commands used below
# argv after endpoint mirrors aws args without 'aws'
# We call this script with action markers instead.
raise SystemExit("use boto path via dedicated python block")
PY
  fi
}

# Prefer Python boto3 for portability
ACCESS="$SEAWEEDFS_S3_ACCESS_KEY" SECRET="$SEAWEEDFS_S3_SECRET_KEY" ENDPOINT="$ENDPOINT" \
BUCKET="$BUCKET" KEY="$KEY" TMP="$TMP" CHECKSUM="$CHECKSUM" \
uv run python - <<'PY'
from __future__ import annotations

import hashlib
import os
from pathlib import Path

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

endpoint = os.environ["ENDPOINT"]
bucket = os.environ["BUCKET"]
key = os.environ["KEY"]
path = Path(os.environ["TMP"])
expected = os.environ["CHECKSUM"]

client = boto3.client(
    "s3",
    endpoint_url=endpoint,
    aws_access_key_id=os.environ["ACCESS"],
    aws_secret_access_key=os.environ["SECRET"],
    config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    region_name="us-east-1",
)

try:
    client.create_bucket(Bucket=bucket)
except ClientError:
    pass

body = path.read_bytes()
client.put_object(Bucket=bucket, Key=key, Body=body)
head = client.head_object(Bucket=bucket, Key=key)
got = client.get_object(Bucket=bucket, Key=key)["Body"].read()
digest = hashlib.sha256(got).hexdigest()
assert digest == expected, f"checksum mismatch {digest} != {expected}"
print("s3_put_get_ok", digest)
print("s3_head_ok", head.get("ContentLength"))
PY

# Restart seaweed and re-GET (bounded retries — healthy can race S3 accept).
"${COMPOSE[@]}" restart seaweedfs
for _ in $(seq 1 60); do
  status="$("${COMPOSE[@]}" ps seaweedfs --format '{{.Status}}' || true)"
  if echo "$status" | grep -q healthy; then
    break
  fi
  sleep 2
done
sleep 3

ACCESS="$SEAWEEDFS_S3_ACCESS_KEY" SECRET="$SEAWEEDFS_S3_SECRET_KEY" ENDPOINT="$ENDPOINT" \
BUCKET="$BUCKET" KEY="$KEY" CHECKSUM="$CHECKSUM" \
uv run python - <<'PY'
import hashlib
import os
import time

import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError

client = boto3.client(
    "s3",
    endpoint_url=os.environ["ENDPOINT"],
    aws_access_key_id=os.environ["ACCESS"],
    aws_secret_access_key=os.environ["SECRET"],
    config=Config(
        signature_version="s3v4",
        s3={"addressing_style": "path"},
        connect_timeout=3,
        read_timeout=10,
        retries={"max_attempts": 3},
    ),
    region_name="us-east-1",
)
last_err: Exception | None = None
got = b""
for attempt in range(1, 16):
    try:
        got = client.get_object(Bucket=os.environ["BUCKET"], Key=os.environ["KEY"])["Body"].read()
        last_err = None
        break
    except (BotoCoreError, ClientError, OSError) as exc:
        last_err = exc
        time.sleep(2)
if last_err is not None:
    raise SystemExit(f"s3_persist_get_failed after_retries err={type(last_err).__name__}") from last_err
assert hashlib.sha256(got).hexdigest() == os.environ["CHECKSUM"]
client.delete_object(Bucket=os.environ["BUCKET"], Key=os.environ["KEY"])
print("s3_persist_delete_ok")
PY

# Wrong-credential negative
ACCESS="wrong" SECRET="wrong" ENDPOINT="$ENDPOINT" BUCKET="$BUCKET" \
uv run python - <<'PY'
import os
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
client = boto3.client(
    "s3",
    endpoint_url=os.environ["ENDPOINT"],
    aws_access_key_id=os.environ["ACCESS"],
    aws_secret_access_key=os.environ["SECRET"],
    config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    region_name="us-east-1",
)
try:
    client.list_objects_v2(Bucket=os.environ["BUCKET"])
except ClientError:
    print("s3_wrong_credential_ok")
else:
    raise SystemExit("wrong credentials unexpectedly succeeded")
PY

rm -f "$TMP"
echo "seaweed_durability_ok checksum=$CHECKSUM"

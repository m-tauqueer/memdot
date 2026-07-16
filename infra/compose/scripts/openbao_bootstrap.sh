#!/bin/sh
set -eu

# Idempotent OpenBao file-storage bootstrap: init/unseal, Transit, least-privilege app token.
# POSIX sh only — OpenBao image has no bash/python/jq. Never prints tokens.

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname "$0")" && pwd)"
COMPOSE_DIR="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"

# Host-side wrapper when bao is not on PATH: exec into the openbao service network.
if ! command -v bao >/dev/null 2>&1; then
  COMPOSE="docker compose --env-file $COMPOSE_DIR/.env -f $COMPOSE_DIR/compose.yaml"
  # shellcheck disable=SC2086
  exec $COMPOSE run --rm --no-deps \
    -e BAO_ADDR="${BAO_ADDR:-http://openbao:8200}" \
    -e OPENBAO_BOOTSTRAP_DIR=/secrets/openbao_bootstrap \
    -e OPENBAO_TRANSIT_TOKEN_FILE=/secrets/openbao_transit_token \
    -v "$COMPOSE_DIR/secrets:/secrets" \
    -v "$SCRIPT_DIR/openbao_bootstrap.sh:/bootstrap.sh:ro" \
    --entrypoint /bin/sh \
    openbao /bootstrap.sh
fi

export BAO_ADDR="${BAO_ADDR:-http://openbao:8200}"
BOOTSTRAP_DIR="${OPENBAO_BOOTSTRAP_DIR:-$COMPOSE_DIR/secrets/openbao_bootstrap}"
if [ -d /secrets ]; then
  TRANSIT_TOKEN_FILE="${OPENBAO_TRANSIT_TOKEN_FILE:-/secrets/openbao_transit_token}"
else
  TRANSIT_TOKEN_FILE="${OPENBAO_TRANSIT_TOKEN_FILE:-$COMPOSE_DIR/secrets/openbao_transit_token}"
fi
INIT_JSON="$BOOTSTRAP_DIR/init.json"
UNSEAL_KEY_FILE="$BOOTSTRAP_DIR/unseal.key"
ROOT_TOKEN_FILE="$BOOTSTRAP_DIR/root.token"

mkdir -p "$BOOTSTRAP_DIR"
chmod 700 "$BOOTSTRAP_DIR" 2>/dev/null || true

# Squeeze JSON to one line then extract string fields (no jq/python in image).
json_oneline() {
  tr -d '\n\r' <"$1"
}

json_string_field() {
  file="$1"
  field="$2"
  json_oneline "$file" | sed -n "s/.*\"${field}\"[[:space:]]*:[[:space:]]*\"\\([^\"]*\\)\".*/\\1/p" | head -n 1
}

json_first_array_string() {
  file="$1"
  field="$2"
  json_oneline "$file" | sed -n "s/.*\"${field}\"[[:space:]]*:[[:space:]]*\\[[[:space:]]*\"\\([^\"]*\\)\".*/\\1/p" | head -n 1
}

bao_responds() {
  wget -qO- "${BAO_ADDR}/v1/sys/health?standbyok=true&sealedcode=200&uninitcode=200" \
    >/dev/null 2>&1
}

wait_for_openbao() {
  i=0
  until bao_responds; do
    i=$((i + 1))
    if [ "$i" -gt 90 ]; then
      echo "openbao_unreachable" >&2
      exit 1
    fi
    sleep 1
  done
}

is_initialized() {
  bao status -format=json 2>/dev/null | tr -d '\n' | grep -q '"initialized"[[:space:]]*:[[:space:]]*true'
}

is_sealed() {
  bao status -format=json 2>/dev/null | tr -d '\n' | grep -q '"sealed"[[:space:]]*:[[:space:]]*true'
}

wait_for_openbao

if ! is_initialized; then
  bao operator init -key-shares=1 -key-threshold=1 -format=json >"$INIT_JSON"
  chmod 600 "$INIT_JSON" 2>/dev/null || true
  json_first_array_string "$INIT_JSON" "unseal_keys_b64" >"$UNSEAL_KEY_FILE"
  json_string_field "$INIT_JSON" "root_token" >"$ROOT_TOKEN_FILE"
  chmod 600 "$UNSEAL_KEY_FILE" "$ROOT_TOKEN_FILE" 2>/dev/null || true
fi

if [ ! -s "$UNSEAL_KEY_FILE" ] && [ -s "$INIT_JSON" ]; then
  json_first_array_string "$INIT_JSON" "unseal_keys_b64" >"$UNSEAL_KEY_FILE"
  chmod 600 "$UNSEAL_KEY_FILE" 2>/dev/null || true
fi

if [ ! -s "$ROOT_TOKEN_FILE" ] && [ -s "$INIT_JSON" ]; then
  json_string_field "$INIT_JSON" "root_token" >"$ROOT_TOKEN_FILE"
  chmod 600 "$ROOT_TOKEN_FILE" 2>/dev/null || true
fi

if [ -z "${BAO_TOKEN:-}" ]; then
  if [ ! -s "$ROOT_TOKEN_FILE" ]; then
    echo "openbao_root_token_missing" >&2
    exit 1
  fi
  BAO_TOKEN="$(tr -d '[:space:]' <"$ROOT_TOKEN_FILE")"
  export BAO_TOKEN
fi

if [ ! -s "$UNSEAL_KEY_FILE" ]; then
  echo "openbao_unseal_key_missing" >&2
  exit 1
fi

if is_sealed; then
  UNSEAL_KEY="$(tr -d '[:space:]' <"$UNSEAL_KEY_FILE")"
  if [ -z "$UNSEAL_KEY" ]; then
    echo "openbao_unseal_key_blank" >&2
    exit 1
  fi
  bao operator unseal "$UNSEAL_KEY" >/dev/null
fi

if ! bao secrets list 2>/dev/null | grep -q '^transit/'; then
  bao secrets enable transit >/dev/null
fi

if ! bao read transit/keys/memdot-local >/dev/null 2>&1; then
  bao write -f transit/keys/memdot-local >/dev/null
fi

POLICY='path "transit/encrypt/memdot-local" { capabilities = ["update"] }
path "transit/decrypt/memdot-local" { capabilities = ["update"] }
path "transit/keys/memdot-local" { capabilities = ["read"] }'

printf '%s\n' "$POLICY" | bao policy write memdot-transit-app - >/dev/null

if [ ! -s "$TRANSIT_TOKEN_FILE" ]; then
  bao token create -policy=memdot-transit-app -ttl=720h -format=json >/tmp/memdot-openbao-token.json
  json_string_field /tmp/memdot-openbao-token.json "client_token" >"$TRANSIT_TOKEN_FILE"
  rm -f /tmp/memdot-openbao-token.json
  chmod 600 "$TRANSIT_TOKEN_FILE" 2>/dev/null || true
else
  APP_TOKEN="$(tr -d '[:space:]' <"$TRANSIT_TOKEN_FILE")"
  if ! BAO_TOKEN="$APP_TOKEN" bao read transit/keys/memdot-local >/dev/null 2>&1; then
    bao token create -policy=memdot-transit-app -ttl=720h -format=json >/tmp/memdot-openbao-token.json
    json_string_field /tmp/memdot-openbao-token.json "client_token" >"$TRANSIT_TOKEN_FILE"
    rm -f /tmp/memdot-openbao-token.json
    chmod 600 "$TRANSIT_TOKEN_FILE" 2>/dev/null || true
  fi
fi

# App Transit token: readable only by Core (uid 10001). Bootstrap secrets stay root-only.
chmod 700 "$BOOTSTRAP_DIR" 2>/dev/null || true
chmod 600 "$INIT_JSON" "$UNSEAL_KEY_FILE" "$ROOT_TOKEN_FILE" 2>/dev/null || true
chown 10001:10001 "$TRANSIT_TOKEN_FILE" 2>/dev/null || true
chmod 600 "$TRANSIT_TOKEN_FILE" 2>/dev/null || true

echo "openbao_bootstrap_ok"

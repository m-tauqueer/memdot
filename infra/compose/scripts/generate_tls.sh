#!/usr/bin/env bash
set -euo pipefail

# Generate local CA + server certificate for Compose TLS (ignored paths).
# Idempotent: skips when server.crt, server.key, and ca.crt already exist.

TLS_DIR="${1:?usage: generate_tls.sh <tls-directory>}"
mkdir -p "$TLS_DIR"

CA_KEY="$TLS_DIR/ca.key"
CA_CERT="$TLS_DIR/ca.crt"
SERVER_KEY="$TLS_DIR/server.key"
SERVER_CSR="$TLS_DIR/server.csr"
SERVER_CERT="$TLS_DIR/server.crt"

if [[ -f "$SERVER_CERT" && -f "$SERVER_KEY" && -f "$CA_CERT" ]]; then
  exit 0
fi

openssl genrsa -out "$CA_KEY" 2048 2>/dev/null
openssl req -x509 -new -nodes \
  -key "$CA_KEY" \
  -sha256 \
  -days 3650 \
  -out "$CA_CERT" \
  -subj "/CN=Memdot Local CA" 2>/dev/null

openssl genrsa -out "$SERVER_KEY" 2048 2>/dev/null
openssl req -new \
  -key "$SERVER_KEY" \
  -out "$SERVER_CSR" \
  -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1" 2>/dev/null

openssl x509 -req \
  -in "$SERVER_CSR" \
  -CA "$CA_CERT" \
  -CAkey "$CA_KEY" \
  -CAcreateserial \
  -out "$SERVER_CERT" \
  -days 365 \
  -sha256 \
  -copy_extensions copyall 2>/dev/null

chmod 600 "$CA_KEY" "$SERVER_KEY"
chmod 644 "$CA_CERT" "$SERVER_CERT"
rm -f "$SERVER_CSR" "$TLS_DIR/ca.srl"

echo "tls_material_ready dir=$TLS_DIR"

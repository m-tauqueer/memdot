#!/usr/bin/env python3
"""Minimal AWS SigV4 S3 client for SeaweedFS durability smoke tests."""

from __future__ import annotations

import hashlib
import hmac
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping
from datetime import UTC, datetime


def _sign(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _signature_key(secret_key: str, date_stamp: str, region: str, service: str) -> bytes:
    key = ("AWS4" + secret_key).encode("utf-8")
    for part in (date_stamp, region, service, "aws4_request"):
        key = _sign(key, part)
    return key


def _canonical_query(params: Mapping[str, str]) -> str:
    return "&".join(
        f"{urllib.parse.quote(k, safe='')}={urllib.parse.quote(v, safe='')}"
        for k, v in sorted(params.items())
    )


def s3_request(
    *,
    method: str,
    endpoint: str,
    bucket: str,
    key: str,
    access_key: str,
    secret_key: str,
    body: bytes = b"",
    region: str = "us-east-1",
    service: str = "s3",
) -> tuple[int, bytes, dict[str, str]]:
    host = endpoint.replace("http://", "").replace("https://", "").rstrip("/")
    scheme = "https" if endpoint.startswith("https://") else "http"
    path = f"/{bucket}/{key}"
    now = datetime.now(UTC)
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = now.strftime("%Y%m%d")
    payload_hash = hashlib.sha256(body).hexdigest()
    canonical_headers = f"host:{host}\nx-amz-content-sha256:{payload_hash}\nx-amz-date:{amz_date}\n"
    signed_headers = "host;x-amz-content-sha256;x-amz-date"
    canonical_request = "\n".join(
        [method, path, "", canonical_headers, signed_headers, payload_hash]
    )
    credential_scope = f"{date_stamp}/{region}/{service}/aws4_request"
    string_to_sign = "\n".join(
        [
            "AWS4-HMAC-SHA256",
            amz_date,
            credential_scope,
            hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
        ]
    )
    signing_key = _signature_key(secret_key, date_stamp, region, service)
    signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
    authorization = (
        f"AWS4-HMAC-SHA256 Credential={access_key}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )
    url = f"{scheme}://{host}{path}"
    req = urllib.request.Request(url, data=body or None, method=method)
    req.add_header("Host", host)
    req.add_header("x-amz-date", amz_date)
    req.add_header("x-amz-content-sha256", payload_hash)
    req.add_header("Authorization", authorization)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            headers = {k.lower(): v for k, v in resp.headers.items()}
            return resp.status, resp.read(), headers
    except urllib.error.HTTPError as exc:
        headers = {k.lower(): v for k, v in exc.headers.items()} if exc.headers else {}
        return exc.code, exc.read(), headers


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: s3_smoke_helper.py <put|get|head|delete> ...", file=sys.stderr)
        return 2
    cmd = sys.argv[1]
    endpoint = sys.argv[2]
    bucket = sys.argv[3]
    key = sys.argv[4]
    access_key = sys.argv[5]
    secret_key = sys.argv[6]
    body = sys.argv[7].encode("utf-8") if len(sys.argv) > 7 and cmd == "put" else b""
    status, payload, headers = s3_request(
        method=cmd.upper(),
        endpoint=endpoint,
        bucket=bucket,
        key=key,
        access_key=access_key,
        secret_key=secret_key,
        body=body,
    )
    out = {
        "status": status,
        "etag": headers.get("etag", ""),
        "body_len": len(payload),
        "body_sha256": hashlib.sha256(payload).hexdigest() if payload else "",
    }
    print(json.dumps(out))
    return 0 if 200 <= status < 300 else 1


if __name__ == "__main__":
    raise SystemExit(main())

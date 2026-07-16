#!/usr/bin/env bash
# Generate SBOM when syft/cyclonedx are present; otherwise emit minimal SPDX from locks.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="${1:-/tmp/memdot-sbom}"
mkdir -p "${OUT_DIR}"

if command -v syft >/dev/null 2>&1; then
  syft dir:"${ROOT}" -o spdx-json="${OUT_DIR}/sbom.spdx.json"
  echo "Wrote ${OUT_DIR}/sbom.spdx.json via syft"
  exit 0
fi

if command -v cyclonedx-py >/dev/null 2>&1; then
  (cd "${ROOT}" && cyclonedx-py environment -o "${OUT_DIR}/sbom.cdx.json")
  echo "Wrote ${OUT_DIR}/sbom.cdx.json via cyclonedx-py"
  exit 0
fi

# Minimal SPDX document derived from lockfiles (not a substitute for syft in release).
UV_LOCK="${ROOT}/uv.lock"
PNPM_LOCK="${ROOT}/pnpm-lock.yaml"
if [[ ! -f "${UV_LOCK}" || ! -f "${PNPM_LOCK}" ]]; then
  echo "generate_sbom.sh: syft/cyclonedx not found and lockfiles missing" >&2
  exit 1
fi

python3 - <<'PY' "${OUT_DIR}" "${UV_LOCK}" "${PNPM_LOCK}"
import hashlib, json, sys
from pathlib import Path
out_dir, uv_lock, pnpm_lock = map(Path, sys.argv[1:])
packages = []
for path in (uv_lock, pnpm_lock):
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    packages.append({
        "SPDXID": f"SPDXRef-Package-{path.name.replace('.', '-')}",
        "name": path.name,
        "downloadLocation": "NOASSERTION",
        "filesAnalyzed": False,
        "checksums": [{"algorithm": "SHA256", "checksumValue": digest}],
    })
doc = {
    "spdxVersion": "SPDX-2.3",
    "dataLicense": "CC0-1.0",
    "SPDXID": "SPDXRef-DOCUMENT",
    "name": "memdot-minimal-lock-sbom",
    "documentNamespace": "https://memdot.local/spom/minimal",
    "creationInfo": {"created": "2026-07-16T00:00:00Z", "creators": ["Tool: generate_sbom.sh"]},
    "packages": packages,
}
out = out_dir / "sbom.minimal.spdx.json"
out.write_text(json.dumps(doc, indent=2), encoding="utf-8")
print(f"Wrote {out} (minimal SPDX from locks; install syft for full SBOM)")
PY

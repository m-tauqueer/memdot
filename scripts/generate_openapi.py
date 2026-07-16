#!/usr/bin/env python3
"""Generate Core-owned OpenAPI into packages/contracts/generated/openapi."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "packages" / "contracts" / "generated" / "openapi" / "openapi.json"


def main() -> int:
    sys.path.insert(0, str(ROOT / "services" / "core" / "src"))
    sys.path.insert(0, str(ROOT / "packages" / "domain-python" / "src"))

    from memdot_core.app import create_app
    from memdot_core.settings import CoreSettings

    app = create_app(CoreSettings(env="test"))
    schema = app.openapi()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(schema, indent=2, sort_keys=True) + "\n"
    OUT.write_text(rendered, encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

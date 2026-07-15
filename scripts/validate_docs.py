#!/usr/bin/env python3
"""Validate local documentation links. Mermaid syntax is validated separately."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DOC_GLOBS = [
    "AGENTS.md",
    "CONTEXT.md",
    "CONTRIBUTING.md",
    "OWNERS.md",
    "README.md",
    "IMPLEMENTATION_PLAN.md",
    "IMPLEMENTATION_TRACKER.md",
    "docs/**/*.md",
]

LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def iter_docs() -> list[Path]:
    files: list[Path] = []
    for pattern in DOC_GLOBS:
        files.extend(ROOT.glob(pattern))
    return sorted({path.resolve() for path in files if path.is_file()})


def check_links(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    for match in LINK_RE.finditer(text):
        target = match.group(2).strip()
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        href = target.split("#", 1)[0]
        if not href:
            continue
        resolved = (path.parent / href).resolve()
        if not resolved.exists():
            errors.append(f"{path.relative_to(ROOT)} -> missing {target}")
    return errors


def main() -> int:
    docs = iter_docs()
    if not docs:
        print("No documentation files found", file=sys.stderr)
        return 1
    errors: list[str] = []
    for path in docs:
        errors.extend(check_links(path))
    if errors:
        print("Documentation validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    print(f"Validated {len(docs)} documentation files (local links).")
    print("Mermaid syntax is validated by scripts/validate_mermaid.mjs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# Content-safe fixture rules (Phase 1)

- Fixtures MUST use synthetic, openly licensed, or explicitly authorized content.
- Fixtures MUST NOT contain real credentials, personal data, private account IDs,
  prompts, answers, or source document bodies from real users.
- Prefer minimal structural JSON that exercises schemas and boundaries.
- Evaluation corpora land under `tests/benchmark/` in later phases and remain
  content-safe.
- Secret scanning and CI fail closed on high-confidence credential patterns.

# Event schema compatibility policy (Phase 1 scaffold)

This directory holds versioned event schema fixtures for contract tooling.
Production domain events are introduced in later phases.

## Rules

1. **Additive changes are compatible within a major version.**
   New optional fields may be added to event payloads without bumping the
   major schema version.

2. **Unknown major versions are rejected.**
   Consumers must fail closed when `schemaVersion` or the schema filename major
   does not match a supported version.

3. **Breaking changes require a new major version.**
   Removing fields, changing field types, or altering required-field sets must
   produce a new `*.vN.json` file and updated compatibility tests.

4. **Fixtures only in Phase 1.**
   `scaffold.event.v1.json` exists to prove layout and validation tooling. Do
   not treat it as a committed production event contract.

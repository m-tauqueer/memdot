# Memdot Execution Documents

These files coordinate phase implementation. They do not replace product or
technical requirements.

## Workflow

1. Tauqueer starts one phase.
2. Grok reads the phase prompt, implementation plan, tracker, context, and mapped
   specification.
3. Grok completes all micro-phases in order.
4. Grok self-validates and fixes each micro-phase, then continues without a
   Codex review.
5. Grok runs the complete phase exit gate.
6. Grok submits one consolidated phase report.
7. Codex audits the complete phase.
8. Tauqueer decides whether to authorize the commit and next phase.

## Files

- [Phase 1 Grok Prompt](PHASE_01_GROK_PROMPT.md)
- [Phase 2 Grok Prompt](PHASE_02_GROK_PROMPT.md)
- [Phase Report Template](PHASE_REPORT_TEMPLATE.md)

Add later phase prompts only after the preceding phase receives a Codex PASS, so
each prompt can use verified repository paths and commands rather than founding
assumptions.

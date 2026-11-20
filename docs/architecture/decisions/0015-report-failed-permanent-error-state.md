# 0015 — Report failure → `ReportFailed` (permanent error state)

> **Status**: Accepted
> **Source**: specifications/workflow.md — v3 changes, scenario 8.7, invariant I5, open question #4 (decision #4)

## Context

The PDF scan report + the event journal are the **evidence** of a cycle. Report generation can fail (WeasyPrint exception, disk full, I/O error). Silently skipping the report, or auto-retrying in an unbounded loop, would either lose evidence or hang the workflow.

## Decision

A report-generation failure transitions the system to **`ReportFailed`**, a **permanent error state**: the user is informed, a **Reset is required**, and there is **no automatic retry**. The system stays in `ReportFailed` until the user acts; a Reset returns it to `SystemReady` (invariant **I9** clears counters/queue).

## Consequences

- Report generation is **atomic** (invariant **I5**): report + journal are generated sequentially, and a failure is a first-class terminal error state, not an exception.
- All screen columns are hidden in `ReportFailed`; the user sees an error indication prompting a Reset (as with `SystemMustBeReset`).
- There is no on-screen "report" element — the report is a generated PDF file, so a failure leaves nothing to copy.

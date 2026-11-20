# 0016 — No copy cancellation

> **Status**: Accepted
> **Source**: specifications/workflow.md — v2.2 changes, §3.2 "No cancel" note

## Context

A copy to the target disk is a long, sequential operation. Offering a cancel button would leave the target in a **partial, uncertain state** (some clean files copied, others not) with no clean recovery semantics. The user still needs a way to **exit** the "waiting for a target" phase without a reset.

## Decision

There is **no cancel button** for the copy — the copy-decline / copy-cancel transitions are removed. `SystemWaitingForTarget` (i.e. `AnalysisCompleted` while no target is connected) is a **stable terminal-ish state** whose **only exits** are: **insert a target disk** (→ `CopyCleanFiles`), **Reset**, or **Shutdown**.

## Consequences

- The user may stay in the waiting state indefinitely; the `FilesCopyPanel` summary screen is shown, prompting to insert a target.
- Cancel is never possible mid-copy either — a running copy can only be left via Reset (blocked while running, per invariant **I8**: pause first) or Shutdown.
- A single-disk cycle that never gets a target simply ends by Reset (no copy, no report) — scenario 8.5.

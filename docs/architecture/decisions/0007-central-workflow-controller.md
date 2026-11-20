# 0007 — Central `WorkflowController` as the only state mutator

> **Status**: Accepted
> **Source**: architecture.md §8 — D-arch-7 (and §5)

## Context

In the as-is code the state transitions are **not** centralised: `__set_system_state(...)` is called from several scattered message handlers (`__handle_disk_state`, `__on_results_changed`, `__handle_create_file`, …), and a few enum states are dead/unreachable. This makes the workflow hard to reason about and to test.

## Decision

A single **`WorkflowController`** owns the state machine and is the **only** component allowed to set `SystemState` (invariant **I3**). All other components signal events to it; it applies the transition rules and invariants of [`specifications/workflow.md`](../../specifications/workflow.md) and publishes the new state.

## Consequences

- The scattered-transition anti-pattern is removed: one place to read, one place to test.
- The workflow contract (states, transitions, invariants, UI mapping) has a single enforcement point.
- Other controllers become single-responsibility and communicate through Qt signals + `SystemState` transitions, never direct sibling calls (invariant **I5**).

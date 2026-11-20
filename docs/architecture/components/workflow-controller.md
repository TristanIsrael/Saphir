# Workflow Controller

> **Status**: Stable
> **Last updated**: 2026-11-20
> **Reference**: `python/gui/src/Saphir/Saphir/workflow_controller.py`

## Purpose

`WorkflowController` (QObject) is the **single state authority** for the system workflow with transition validation. All `SystemState` changes must go through `transition_to()`, which validates the transition against the canonical transition table before applying it (invariant **I3**: only `WorkflowController` sets `SystemState`). The full contract — canonical states, transition table, invariants, UI mapping, and scenarios — is defined in [../../specifications/workflow.md](../../specifications/workflow.md).

## As-is reality (important for the refactoring)

Before this component existed, the state transitions were **not** centralised: `__set_system_state(...)` was called from several scattered message handlers (`__handle_disk_state`, `__on_results_changed`, `__handle_create_file`, …), and a few enum states were dead/unreachable. The target architecture centralises this in `WorkflowController` — see the refactoring plan Phase 1 and [../overview.md](../overview.md) §5.

## Key API

| Member | Role |
|--------|------|
| `state` (property) | the current workflow state |
| `can_transition(to)` | returns whether a transition to the given state is valid |
| `transition_to(to)` | validates and applies a state transition; returns whether it was accepted. Blocked transitions are logged (`BLOCKED: from -> to`); in DEVMODE the event is appended to the state dump file `/tmp/saphir_state.log` |
| `force_state(state)` | sets the state **without** validation — use only for initialization or reset |
| `is_in_states(states)` | returns whether the current state is one of the given states |
| `systemStateChanged` (signal, `int`) | emitted on every accepted (or forced) transition |
| `_VALID_TRANSITIONS` (class-level dict) | the transition table: `SystemInactive → SystemStarting → SafecorReady → SystemReady → … → SystemResetting → SystemReady` (loop), with `SystemShuttingDown` reachable from most states and `ReportFailed` as a permanent error state after `GeneratingReport` |

`ApplicationController` connects `workflow_controller.systemStateChanged` to its own `systemStateChanged` signal, so the QML layer sees the state as the contract prescribes.

## Links

- Contract (states, transitions, invariants, UI mapping, scenarios): [../../specifications/workflow.md](../../specifications/workflow.md)
- State machine summary: [../overview.md](../overview.md) §5
- Invariants I1–I7: [../overview.md](../overview.md) §7.3
- God class (as-is): [application-controller.md](application-controller.md)
- Refactoring plan: [../../archive/plans/refactoring-plan.md](../../archive/plans/refactoring-plan.md)

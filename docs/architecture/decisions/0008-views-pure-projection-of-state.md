# 0008 — Views are a pure projection of `SystemState`

> **Status**: Accepted
> **Source**: architecture.md §8 — D-arch-8 (and §3.4 view-state rule)

## Context

When QML views decide visibility or enablement with their own business conditionals, the UI becomes non-deterministic: the same workflow state can render differently depending on hidden view-local state, and the UI can no longer be tested by driving the workflow alone.

## Decision

The QML views are **stateless projections of the workflow**. What is shown — the active panel, enabled/disabled buttons, open dialogs, editable fields — is **derived directly from `SystemState`** and the published bindings. A view must not *decide* visibility or enablement with its own business conditionals: bind it to a property that already encodes the state (e.g. `enabled: viewModel.canStartAnalysis`) and push any non-trivial derivation into the controller/ViewModel, exposed as a single property. Only **trivially presentational** logic with no workflow meaning (hover highlight, slider clamping, `width > 0 ? a : b`) may live in a view.

## Consequences

- The UI is **deterministic and testable** by driving `SystemState` alone.
- The state→screen mapping is defined once, in [`specifications/workflow.md` §7](../../specifications/workflow.md).
- Deviations are **rule-debt** and must be logged in the GUI backlog & rule-debt section of [`../../project-status.md`](../../project-status.md).

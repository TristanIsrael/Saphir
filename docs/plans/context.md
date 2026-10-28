# Saphir Refactoring - Session Context

> **Last update**: 2026-10-27
> **Previous session status**: Planning phase, documentation complete

## What was accomplished

### Documents created in `docs/plans/`

- **`refactoring-plan.md`** — Plan in 5 phases: Foundation, State Machine, Data Controllers, Transfer, QML Cleanup
- **`workflow-rules.md`** (moved to `docs/`) — State contract **v2**: 14 states, 25 transitions, 8 invariants, UI matrix, MQTT ownership

## Reference docs (English, in `docs/`)

- **`features.md`** — F1–F21 + NFR-1–5 (reference spec)
- **`implementation-coverage.md`** — spec↔code audit
- **`test-strategy.md`** — test strategy
- **`architecture.md`** — target architecture (validated)
- **`workflow-rules.md`** — v2: added `SystemWaitingForTarget` (waiting for 2nd target), Stop/Reset/Cancel transitions, AV error-vs-panic distinction

## Current state

- **Priority**: Workflow → Controllers → Views
- **Open questions**: 4 (see `workflow-rules.md` §9; single-disk resolved by `SystemWaitingForTarget`)

## Key decisions

- Single MQTT client via `Api()` singleton
- Inter-controller communication: Qt signals + `SystemState` only
- `WorkflowController` is the sole owner of `SystemState`
- Views modified last
- Handshake preserved (debt)
- Archives disabled (`MOUNT_ARCHIVES = False`)

## Known issues

- God class: `application_controller.py` (1268 lines)
- 4 dead states to remove
- Race condition: `storagesCount` vs `systemState` for UI visibility
- Race condition: `__get_transferred_ratio()` without lock
- Bug: `infected: nbInfected > 1` should be `> 0`
- Debug leftovers: `/tmp/data.txt`, prints

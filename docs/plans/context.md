# Saphir Refactoring - Session Context

> **Last update**: 2026-11-01
> **Session status**: Phases 0-12 done (see `refactoring-plan.md`); pending: Phase 13 (Viewer modernization) and Phase 14 (blocked on the external Safecor emulator)

## What was accomplished

- **`refactoring-plan.md`** — the phased refactoring plan (Phases 0-14)
- **`workflow-rules.md`** (in `docs/`) — the state contract, v3.1: states, transitions, invariants, UI matrix, MQTT ownership, scenarios 8.1-8.10

## Reference docs (English, in `docs/`)

- **`features.md`** — F1-F21 + NFR-1-5 (reference spec)
- **`implementation-coverage.md`** — spec-to-code audit
- **`test-strategy.md`** — test strategy
- **`architecture.md`** — target architecture (validated)
- **`workflow-rules.md`** — v3.1: scenarios 8.9/8.10, multi-source disk rule (I1)

## Current state

- **Phases 0-12 of `refactoring-plan.md` are done** (refactor, tests, lint, Alpine package validation in chroot, documentation debt, missing features & NFRs #145-#152, functional coverage #154, QML layer tests #155 + #156 + #157)
- **Pending**: Phase 13 (Viewer modernization) and Phase 14 (semi-automated validation env, blocked on the external Safecor emulator)
- **Test baseline**: 530 passed, 3 skipped, 1 xfailed (the single xfail documents the open D8 gap)
- Package validation: `setup/chroot/chroot-build.sh` (7/8 packages built, GUI boot in DEVMODE validated; `saphir-container-eset` blocked by a dead ESET URL)

## Key decisions

- A single MQTT client via the `Api()` singleton
- Inter-controller communication: Qt signals + `SystemState` only
- `WorkflowController` is the sole owner of `SystemState`
- Views are modified last
- Handshake kept (debt)
- Archives disabled (`MOUNT_ARCHIVES = False`)
- Multi-source disk rule (10.8): every disk connected before the scan starts is a source, no new source is accepted once the scan has started, the first disk connected after the analysis completes is the target

## Known issues

> **Note** (2026-10-29): the issues raised during planning were addressed
> during Phases 0-7 (see `refactoring-plan.md`).

- God class: `application_controller.py` (largest controller)
- Bug: `infected: nbInfected > 1` should be `> 0` (`Bindings.qml`, D8)
- Broker-contention flake: a workflow test may fail in the full suite under load (passes in isolation)

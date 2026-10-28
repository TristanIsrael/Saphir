# Saphir Refactoring - Session Context

> **Last update**: 2026-10-27
> **Previous session status**: Planning phase, documentation complete

## What was accomplished

### Documents created in `docs/plans/`

- **`refactoring-plan.md`** — Plan en 5 phases : Foundation, State Machine, Data Controllers, Transfer, QML Cleanup
- **`workflow-rules.md`** (moved to `docs/`) — Contrat d'états **v2** : 14 états, 25 transitions, 8 invariants, matrix UI, ownership MQTT

## Reference docs (English, in `docs/`)

- **`features.md`** — F1–F21 + NFR-1–5 (reference spec)
- **`implementation-coverage.md`** — spec↔code audit
- **`test-strategy.md`** — test strategy
- **`architecture.md`** — target architecture (validated)
- **`workflow-rules.md`** — v2: added `SystemWaitingForTarget` (waiting for 2nd target), Stop/Reset/Cancel transitions, AV error-vs-panic distinction

## Current state

- **Priorité**: Workflow → Contrôleurs → Vues
- **Questions ouvertes**: 4 (voir `workflow-rules.md` §9; single-disk résolue par `SystemWaitingForTarget`)

## Key decisions

- Un seul client MQTT via `Api()` singleton
- Communication inter-contrôleurs : signaux Qt + `SystemState` uniquement
- `WorkflowController` seul maître de `SystemState`
- Vues modifiées en dernier
- Handshake conservé (dette)
- Archives désactivées (`MOUNT_ARCHIVES = False`)

## Known issues

- God class : `application_controller.py` (1268 lignes)
- 4 dead states à supprimer
- Race condition : `storagesCount` vs `systemState` pour visibilité UI
- Race condition : `__get_transferred_ratio()` sans lock
- Bug : `infected: nbInfected > 1` devrait être `> 0`
- Debug leftovers : `/tmp/data.txt`, prints

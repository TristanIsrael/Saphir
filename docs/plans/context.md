# Saphir Refactoring - Session Context

> **Last update**: 2026-10-29
> **Session status**: Phases 0-9 ✅ done (see `refactoring-plan.md`); next: Phase 10 (Missing features & NFRs)

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

- **Phases 0-9 du `refactoring-plan.md` sont terminées** (refactor, tests, lint, validation des paquets Alpine en chroot, dette documentaire)
- **Prochaine phase**: Phase 10 - Missing features & NFRs (fingerprint NFR-1, ReportFailed, handlers de déconnexion, échec AV)
- **Test baseline**: 350 passed, 3 skipped, 0 failed
- Validation des paquets : `setup/chroot/chroot-build.sh` (7/8 paquets buildés, boot GUI DEVMODE validé ; `saphir-container-eset` bloqué par une URL ESET morte)

## Key decisions

- Un seul client MQTT via `Api()` singleton
- Communication inter-contrôleurs : signaux Qt + `SystemState` uniquement
- `WorkflowController` seul maître de `SystemState`
- Vues modifiées en dernier
- Handshake conservé (dette)
- Archives désactivées (`MOUNT_ARCHIVES = False`)

## Known issues

> **Note** (2026-10-29) : ces problèmes, relevés à la phase de planification, ont été traités
> durant les phases 0-7 (voir `refactoring-plan.md`).

- God class : `application_controller.py` (1268 lignes)
- 4 dead states à supprimer
- Race condition : `storagesCount` vs `systemState` pour visibilité UI
- Race condition : `__get_transferred_ratio()` sans lock
- Bug : `infected: nbInfected > 1` devrait être `> 0`
- Debug leftovers : `/tmp/data.txt`, prints

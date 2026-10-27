# Saphir Refactoring - Session Context

> **Last update**: 2026-10-27
> **Previous session status**: Planning phase, documentation complete

## What was accomplished

### Documents created in `docs/plans/`

- **`refactoring-plan.md`** — Plan en 5 phases : Foundation, State Machine, Data Controllers, Transfer, QML Cleanup
- **`workflow-rules.md`** — Contrat d'états : automate complet, 16 transitions, 7 invariants, matrix UI, ownership MQTT

## Current state

- **En attente de**: Description des fonctions du système → document de features pour référence du refactoring
- **Priorité**: Workflow → Contrôleurs → Vues
- **Questions ouvertes**: 5 (voir `workflow-rules.md` §10)

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

# 0018 — Archive mounting removed

> **Status**: Accepted
> **Source**: specifications/workflow.md — §9 open questions (#2); specifications/features.md — consolidated backlog (F3)

## Context

Saphir used to support **archive mounting**: a big archive could be mounted as a virtual disk (via `system/disks/mount_file`) and its contents scanned in place, gated by the constants `MOUNT_ARCHIVES` and `BIG_FILE_SIZE_IN_MB`. This code path was **dormant** — `MOUNT_ARCHIVES = False` and `BIG_FILE_SIZE_IN_MB = -1` (disabled) — and kept the analysis controller more complex than the active feature set required.

## Decision

The **dormant archive-mounting code is removed**. Archive mounting is **not** a current feature: re-introducing it is a **new, specified capability** (tracked as a `[feature]` backlog item under F3), not a switch that can be flipped on.

## Consequences

- Archives are treated as **regular files** — read to the repository and scanned like any other file; they are not mounted.
- The `system/disks/mount_file` / `system/disks/unmount` protocol functions are no longer used by Saphir (see [development/protocol.md](../../development/protocol.md) §4.1 note).
- Re-introduction requires a new specification (scope, size thresholds, nested-archive behaviour) before any code is written.

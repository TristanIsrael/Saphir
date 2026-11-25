# 0003 — Repository as the only data exchange point

> **Status**: **Superseded by [0019](0019-direct-usb-mount-data-path.md)** (2026-11-24)
> **Source**: architecture.md §8 — D-arch-3

> **Note**: This ADR described the v1 data path (shared 9p repository at `/mnt/storage`). It is superseded by ADR 0019, which adopts the direct USB mount as the analysis data path in Safecor v2. The repository is disabled (`repository.disabled: true` in the topology).

## Context

The GUI and the AV domains live in **separate VMs**. The AV engines must not touch the external source/target disks directly (isolation), and the disks may be disconnected at any time.

## Decision

All files pass through the **shared repository** on the `sys-usb` domain (`__repository__`, mounted at `/mnt/storage`). It is the **only** data exchange point between the GUI and the AV domains: the GUI stages a file with `read_file`, the AV domain scans it from the repository, and the GUI frees the slot with `delete_file`.

## Consequences

- The AV domains are **stateless with respect to file content** — they only ever see repository files.
- The staging step enables **parallel analysis** and a bounded number of in-flight files (the repository acts as the queue's buffer).
- Integrity (NFR-1) can be checked end-to-end around a single exchange point: source→repository at staging, repository at analysis.

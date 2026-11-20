# 0006 — Stateless system, no persistence

> **Status**: Accepted
> **Source**: architecture.md §8 — D-arch-6

## Context

Saphir's lifecycle is a **cycle**: boot → analyze → copy → report → reset/shutdown. The platform is driven by Safecor, and the disposable `sys-usb` domain (the repository) is destroyed on every reset. Carrying data across cycles would conflict with the disposable-domain model and with the security posture (a sheep-dip must not retain scanned content).

## Decision

The system is **stateless**: there is **no persistence between cycles**. A Reset destroys the disposable domains and returns the system to its initial state (invariant **I9**). A power loss or crash is handled the same way: a reboot returns the system to the initial (Ready) state, with no dedicated recovery state.

## Consequences

- Every cycle starts from a clean slate: the queue, counters, and the visual status are rebuilt in memory.
- There is no database, no journal of past scans, and no on-disk state to corrupt.
- Report + journal are the **only** artifacts a cycle produces, and they are written to the target disk (not retained by the system).
- The RAM cost of statelessness (VMs in RAM, `tmpfs` root) is being addressed on the Safecor side — see [0014](0014-stateless-volatile-encrypted-disks.md) (Deferred).

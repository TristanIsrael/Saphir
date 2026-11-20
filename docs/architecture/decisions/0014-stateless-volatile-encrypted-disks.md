# 0014 — Stateless redesign on volatile encrypted disks

> **Status**: **Deferred** (2026-10-28) — pending Safecor work
> **Source**: tech-stack-analysis.md §8 — D-T5

## Context

Saphir is already stateless by Safecor architecture (each VM created at boot, **packages in RAM**, root `/` a `tmpfs`, destroyed at shutdown). The **RAM impact** of that statelessness is significant. A **redesign is planned on the Safecor side** to cut the RAM cost of statelessness.

## Decision

**Deferred.** The direction is a **Safecor redesign** that uses **volatile encrypted disks** (with **ephemeral keys**) to install the system **on disk** instead of in RAM, while **guaranteeing system integrity**. This decision will be **re-evaluated after that Safecor work lands**.

## Consequences

- Not done yet (Safecor work in progress).
- The memory analysis in `tech-stack-analysis.md` §4/§5 **may change** once the system is on volatile encrypted disks rather than RAM, so D-T5 is re-evaluated then.
- Until it lands, Saphir keeps paying the RAM cost of in-RAM statelessness (see [0006](0006-stateless-system-no-persistence.md)).

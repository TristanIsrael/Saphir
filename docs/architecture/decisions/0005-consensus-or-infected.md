# 0005 — Consensus = OR on "infected"

> **Status**: Accepted
> **Source**: architecture.md §8 — D-arch-5 (and §6.2)

## Context

A sheep-dip must never let a potentially infected file through, and no single antivirus engine is reliable on its own. The product's value is the multi-engine vote.

## Decision

A file is **infected if *any* antivirus engine reports it infected**; it is **clean only when *all* engines agree clean** (OR logic, implemented in `AnalysisHelper.evaluate_result_consensus`). `ANTIVIRUS_NEEDED = 2` only gates whether analysis is **enabled** (the number of engines that must be *ready*); it is **not** a voting threshold.

## Consequences

- Conservative security posture: any hit ⇒ the file is not clean and is not copied.
- A file whose analysis returned an **error** is "not clean" (not copyable), but its error does not abort the analysis (NFR-3, invariant **I7**).
- Losing an engine below `ANTIVIRUS_NEEDED` mid-analysis aborts the analysis (scenario 8.9).

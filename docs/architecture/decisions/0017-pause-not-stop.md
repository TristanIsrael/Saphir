# 0017 — Pause, not Stop

> **Status**: Accepted
> **Source**: specifications/workflow.md — v2.3 changes, scenario 8.2, transition table §3.2

## Context

A hard **Stop** of the analysis would discard the in-flight work and force the user to restart the whole analysis from scratch, re-analysing files that were already processed. For a long multi-engine scan that is a poor UX and wastes engine time.

## Decision

The analysis **Stop** button is renamed **Pause** — there is **no hard stop**. Pausing **suspends** the analysis: the GUI publishes `saphir/analysis/stop` (the AV domains stop picking new files), the system transitions `SystemAnalysisRunning` → `SystemWaitingForUserAction`, and **files already analyzed keep their status**. The user can modify the queue and **resume** from the same state: on resume the GUI re-enqueues the files interrupted by the pause (copy-to-repository in flight, or analysis in progress) and the already-analyzed files are **not** re-analyzed (F3, scenario 8.2).

## Consequences

- The analysis is **interruptible and resumable** without losing completed results.
- The transition `SystemAnalysisRunning → SystemWaitingForUserAction` is triggered by user Pause (and also by an AV engine panic — NFR-3).
- Resume is gated by the **ready-to-analyze** condition (AV engines ready + core ready + non-empty queue).

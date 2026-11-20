# 0004 — Template Method for AV controllers

> **Status**: Accepted
> **Source**: architecture.md §8 — D-arch-4 (and §3.3)

## Context

Saphir must run **multiple antivirus engines with very different runtimes** (ClamAV: `clamdscan` subprocess with many workers; ESET: shell scripts wrapping a Debian LXC container, single worker) behind a single, stable contract for the GUI.

## Decision

`AbstractAntivirusController` implements the **Template Method**: it owns the MQTT client lifecycle, the bounded **worker pool** (a `Queue` + a capped number of `threading.Thread`s, rescheduled via `threading.Timer`), the request routing (`request|stop|resume|reset`), the **component state machine** (`STARTING` → `READY`), the NFR-1 repository integrity check, and the result publishing (`response`, `status`). Engine subclasses implement only the abstract hooks (`_on_api_ready`, `_analyse_file`, `_stop_immediately`, `_get_component_version`, `_get_component_description`, `_restart`), may override `_engine_is_ready()` to gate readiness on engine-specific state, and may observe requests via the optional `_on_analysis_requested` hook.

## Consequences

- A new engine plugs in by **implementing the hooks only** — no changes to the GUI.
- All engines report over the same `saphir/analysis/*` topics, so the GUI treats them identically (consensus aggregation is engine-agnostic).

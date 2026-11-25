# Architecture Decision Records (ADR)

> **Status**: Living registry
> **Last updated**: 2026-11-24
> **Scope**: one document per decision, numbered sequentially from `0001`. The registry consolidates the decisions previously recorded inline in `docs/architecture.md` §8 (D-arch-1…9), `docs/tech-stack-analysis.md` §8 (D-T1…5), and the workflow/specification documents (behaviour & scope decisions).

## Index

| # | Title | Status | One-line summary | Source |
|---|-------|--------|------------------|--------|
| [0001](0001-event-driven-no-polling.md) | Event-driven, no polling | Accepted | The GUI reacts to MQTT events; the only polling is the 5 s energy poll | architecture.md §8 — D-arch-1 |
| [0002](0002-per-domain-single-api-client.md) | Per-domain single API client | Accepted | One `Api()`/`MqttClient` per domain, all traffic over MQTT; `ApiLifecycle` is the sole owner (I1) | architecture.md §8 — D-arch-2 |
| [0003](0003-repository-only-data-exchange.md) | Repository as the only data exchange point | **Superseded by 0019** | Files passed only through the `sys-usb` repository; superseded by direct USB mount | architecture.md §8 — D-arch-3 |
| [0004](0004-template-method-av-controllers.md) | Template Method for AV controllers | Accepted | New engines plug in by implementing the abstract hooks — no changes to the GUI | architecture.md §8 — D-arch-4 |
| [0005](0005-consensus-or-infected.md) | Consensus = OR on "infected" | Accepted | Infected if any engine flags; clean only when all agree; `ANTIVIRUS_NEEDED` is a gate, not a voting threshold | architecture.md §8 — D-arch-5 |
| [0006](0006-stateless-system-no-persistence.md) | Stateless system, no persistence | Accepted | No persistence between cycles; reset destroys the disposable domains | architecture.md §8 — D-arch-6 |
| [0007](0007-central-workflow-controller.md) | Central `WorkflowController` as the only state mutator | Accepted | Only `WorkflowController` sets `SystemState` (I3) — removes the scattered-transition anti-pattern | architecture.md §8 — D-arch-7 |
| [0008](0008-views-pure-projection-of-state.md) | Views are a pure projection of `SystemState` | Accepted | No business logic in QML — the UI stays deterministic and testable by driving workflow state alone | architecture.md §8 — D-arch-8 |
| [0009](0009-responsive-input-agnostic-views.md) | Responsive, input-agnostic views | Accepted | One interface for now (touch tablet primary, desktop PC supported); layout tolerates future per-target specialisation | architecture.md §8 — D-arch-9 |
| [0010](0010-pyside6-tech-stack.md) | PySide6/Python GUI tech stack (no C++ rewrite) | Accepted (2026-10-28) | C++ would save only ~1–2 % of the total RAM at the cost of a full GUI + report + viewer rewrite | tech-stack-analysis.md §8 — D-T1 |
| [0011](0011-gui-vm-qt-network-strip.md) | Finish the GUI VM stripping | Accepted (2026-10-28; QtNetwork part superseded 2026-11-01) | Strip the unused Qt modules from the GUI bundle; **QtNetwork is required** (PySide6 probes it) and stays | tech-stack-analysis.md §8 — D-T2 |
| [0012](0012-keep-eset-debian-lxc.md) | Keep ESET in the Debian LXC | Accepted (2026-10-28) | Detection quality > saving ~2 100 MB; no quality MUSL-compatible engine exists | tech-stack-analysis.md §8 — D-T3 |
| [0013](0013-clamav-optimization.md) | Keep ClamAV as-is | Accepted (2026-10-28) | 3 000 MB resident, full signatures, `Bytecode true` — structural; follow-up: measure the real minimum | tech-stack-analysis.md §8 — D-T4 |
| [0014](0014-stateless-volatile-encrypted-disks.md) | Stateless redesign on volatile encrypted disks | **Deferred** (2026-10-28) | Safecor redesign: volatile encrypted disks + ephemeral keys instead of RAM; re-evaluate after that work lands | tech-stack-analysis.md §8 — D-T5 |
| [0015](0015-report-failed-permanent-error-state.md) | Report failure → `ReportFailed` (permanent error state) | Accepted | A report failure requires a Reset — no automatic retry | workflow-rules v3 — scenario 8.7 / open question #4 |
| [0016](0016-no-copy-cancellation.md) | No copy cancellation | Accepted | No cancel button; exits from the copy wait = target inserted / Reset / Shutdown | workflow-rules v2.2 |
| [0017](0017-pause-not-stop.md) | Pause, not Stop | Accepted | Stop renamed Pause — a suspended analysis can be resumed; files keep their status | workflow-rules v2.3 — scenario 8.2 |
| [0018](0018-archive-mounting-removed.md) | Archive mounting removed | Accepted | The dormant archive-mounting code is removed; re-introduction is a new, specified feature (F3) | workflow-rules — open question #2 / features backlog F3 |
| [0019](0019-direct-usb-mount-data-path.md) | Direct USB mount as the analysis data path | Accepted | Safecor v2 removes the shared 9p repository; AV domains read directly from `/media/usb` via `direct_mount` | migration-safecor-v2.md |

## How to add a decision

1. Create `NNNN-short-title.md` with the next free number (zero-padded to 4 digits).
2. Fill in **Status** / **Context** / **Decision** / **Consequences** / **Source** — extract faithfully from the source rationale, do not invent it.
3. Add a row to the index table above.
4. Never renumber existing entries: a decision that is overturned gets a **new** entry that references and supersedes the old one (status of the old entry → *Superseded by NNNN*).

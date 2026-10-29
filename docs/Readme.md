# Saphir documentation

This document is an entry point to the documentation of Saphir, the robust sheep-dip solution.

## Specification & contract

| Document | Concern |
|----------|---------|
| [`features.md`](features.md) | What the system must do (F1–F21, NFR-1 to NFR-5) |
| [`workflow-rules.md`](workflow-rules.md) | State machine contract (states, transitions, invariants, error handling, UI mapping, scenarios) |

## Architecture & UI

| Document | Concern |
|----------|---------|
| [`architecture.md`](architecture.md) | Architecture reference (the "what" and "how", ties the design together) |
| [`gui.md`](gui.md) | User interface (principles, screens, visual status, theming, localization) |
| [`gui-backlog.md`](gui-backlog.md) | GUI feature backlog & rule-debt |

## Audit & Safecor alignment

| Document | Concern |
|----------|---------|
| [`implementation-coverage.md`](implementation-coverage.md) | Spec ↔ implementation gap audit (divergences, to-fix, backlog) |
| [`safecor-refs.md`](safecor-refs.md) | Safecor API/platform references used by Saphir |
| [`safecor-divergences.md`](safecor-divergences.md) | Divergences between Saphir and the current Safecor |

## Plans & validation

| Document | Concern |
|----------|---------|
| [`plans/refactoring-plan.md`](plans/refactoring-plan.md) | Refactoring phases & effort |
| [`plans/context.md`](plans/context.md) | Session context / resume point |
| [`test-strategy.md`](test-strategy.md) | Validation / test strategy (unit → system, DevMode, simulator) |

## Development & packaging

| Resource | Concern |
|----------|---------|
| [`../setup/chroot/chroot-build.sh`](../setup/chroot/chroot-build.sh) | Build & validate the Saphir Alpine packages in a local chroot (`init`, `sync`, `build [all]`, `install [PKG...]`, `test-gui`, `validate`) |
| [`../setup/docker/local-dev/`](../setup/docker/local-dev/) | Local dev environment (Alpine + Saphir APK repository, `create-dev-image.sh` / `docker-cmd.sh`) |

## Analyses & decisions

| Document | Concern |
|----------|---------|
| [`tech-stack-analysis.md`](tech-stack-analysis.md) | GUI tech stack (PySide6 vs C++/Qt) & system memory strategy — decisions pending |

## Legacy

[`old/`](old/) — historical documents kept for reference (not maintained).

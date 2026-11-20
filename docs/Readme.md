# Saphir documentation

> **Audience**: AI coding agents (and developers) working on Saphir — an **offline** technical
> reference for the Saphir product built on the Safecor platform. Human-facing documentation
> (user manual, provisioning, translations) lives in the Saphir wiki.
>
> **Where to start**: [`project-status.md`](project-status.md) for the current state,
> [`architecture/overview.md`](architecture/overview.md) for the design, and
> [`specifications/features.md`](specifications/features.md) for the behaviour contract.

## Specifications & contracts

| Document | Concern |
|----------|---------|
| [`specifications/features.md`](specifications/features.md) | What the system must do (F1–F21, NFR-1 to NFR-5) |
| [`specifications/workflow.md`](specifications/workflow.md) | State machine contract (states, transitions, invariants, error handling, UI mapping, scenarios) |
| [`specifications/topology.md`](specifications/topology.md) | Multi-domain topology (domains, hardware profiles, VM allocation, direct mount) |
| [`specifications/python-api.md`](specifications/python-api.md) | Offline copy of the Safecor Python API as used by Saphir |

## Architecture

| Document | Concern |
|----------|---------|
| [`architecture/overview.md`](architecture/overview.md) | High-level design picture, deployment, layering, data model & consensus, target (to-be) layout |
| [`architecture/design-rules.md`](architecture/design-rules.md) | Saphir GUI design rules + Safecor platform design rules (offline copy) |
| [`architecture/configuration-management.md`](architecture/configuration-management.md) | Where configuration lives and how it flows (topology, boot services, runtime, dev environment) |
| [`architecture/components/`](architecture/components/) | One reference per component (application / workflow / analysis / transfer / report controllers, storage manager, antivirus controllers, QML layer, GUI, viewer) |
| [`architecture/decisions/`](architecture/decisions/) | ADR registry — one file per validated design decision |

## Development

| Document | Concern |
|----------|---------|
| [`development/protocol.md`](development/protocol.md) | MQTT contract: single-client constraint, `system/*` + `saphir/analysis/*` topics and payloads |
| [`development/testing.md`](development/testing.md) | Test levels, simulation tools (DevMode, Safecor emulator, mock AV), validation environment & scenarios |
| [`development/building.md`](development/building.md) | Local dev (Docker), chroot package build & validation, CI pipeline, ISO build, versioning rules |
| [`development/coding-rules.md`](development/coding-rules.md) | Coding standards & naming conventions (offline copy of `AGENTS.md`) |
| [`development/packaging.md`](development/packaging.md) | Package inventory, wheel → PyInstaller → APK flow, signed repo publishing, ISO |
| [`development/github-project-management.md`](development/github-project-management.md) | GitHub issue & Saphir Kanban (Project V2) management via GraphQL |

## Security

| Document | Concern |
|----------|---------|
| [`security/security-model.md`](security/security-model.md) | Sheep-dip threat model, defense layers, open integrity gaps, platform baseline |

## Project status & trackers

| Document | Concern |
|----------|---------|
| [`project-status.md`](project-status.md) | Current status: feature & NFR coverage, known issues & technical debt, GUI backlog & rule-debt |
| [`safecor-refs.md`](safecor-refs.md) | Safecor sources of truth (repo + wiki) and the offline-copy policy |
| [`safecor-divergences.md`](safecor-divergences.md) | Divergences & anomalies in Safecor (tracked here, handled in the Safecor project) |
| [`tech-stack-analysis.md`](tech-stack-analysis.md) | GUI tech stack & memory analysis (decision log extracted to `architecture/decisions/`, ADRs 0010–0014) |

## Archive

[`archive/`](archive/README.md) — frozen historical documents (legacy documentation, completed plans & analyses).

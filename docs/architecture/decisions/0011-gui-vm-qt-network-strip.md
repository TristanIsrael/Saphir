# 0011 — Finish the GUI VM stripping

> **Status**: Accepted (2026-10-28) — the **QtNetwork** part is **superseded** (2026-11-01, Phase 8.2, `4b0b1b2`)
> **Source**: tech-stack-analysis.md §8 — D-T2

## Context

The GUI bundle is a PyInstaller bundle (`bundle="yes"`). The PyInstaller spec **already strips** the unused Qt modules (Qt3D, QtCharts, QtMultimedia, QtWeb/WebEngine, QtSensors, QtSql, QtSvg, …). What remained: **QtNetwork** (~15–25 MB, a `hiddenimport`) and **MESA/LLVM** (~236 MB, OpenGL hardware acceleration).

## Decision

**Finish the GUI stripping without changing the stack**: drop **QtNetwork** (remove it from `hiddenimports` + the strip filter, test first); **keep MESA/LLVM** (OpenGL hardware acceleration is required on the target tablet for GPU rendering, and is paid by both PySide6 and C++).

## Consequences

- Modest gain (~15–25 MB), free, and it shrinks the attack surface. Action scheduled in the refactor (packaging phase); tracked in [`../../project-status.md`](../../project-status.md) (GUI backlog & rule-debt).
- **Superseded (2026-11-01, Phase 8.2, `4b0b1b2`)**: the bundle **fails to boot** without QtNetwork — PySide6's `__init__` probes it transitively. QtNetwork is **required** and remains in the bundle. The premise "the GUI talks over MQTT, not QtNetwork" is insufficient: the module is loaded by PySide6 internals at startup.

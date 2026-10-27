# Validation test strategy — Saphir

> **Status**: Draft (v1) — to be completed iteratively
> **Last updated**: 2026-10-27
> **Reference**: `docs/features.md` (F1–F21), `docs/plans/workflow-rules.md` (state machine), `docs/plans/refactoring-plan.md`

---

## 1. Objective

Define the approach and tools for the **validation** of Saphir, from the lowest level (unit) up to the system level (full user scenarios). The objective is to be able to validate the Saphir behavior **without a Safecor appliance** for the majority of cases, and to reserve on-appliance tests for platform integration checks.

This document is the container of the **validation strategy**; the simulation capabilities are grouped here (DevMode, Safecor simulator) as they serve this single purpose.

---

## 2. Test levels

| Level | Periphery | Tool | Target |
|--------|-----------|-------|-------|
| **Unit** | Isolated module | pytest | Pure logic: consensus (F3), EMA (F16), helpers, models |
| **Component** | Isolated controller | pytest + mocks | Each future sub-controller (WorkflowController, StorageManager, …) |
| **Integration** | GUI + mocks | pytest + DEVMODE / simulator | Orchestration, state transitions, MQTT |
| **System / E2E** | Real appliance | Manual / script | Platform verification (multi-VM, physical disks) |

---

## 3. Simulation tools

### 3.1 DevMode (development mode)

**Nature**: development tool, **not active in production**.

**Role**: allow the development and testing of the GUI **without a Safecor appliance** (no multi-VM).

**Current behavior**:

- Enabled by the **environment variable** `DEVMODE`.
- The MQTT client is created in **debug TCP mode** (localhost) instead of the Safecor channel.
- The **source disks** are simulated (local paths) and the local repository is a `/tmp` directory.
- **Fullscreen is disabled** (the GUI runs in a sized window) to ease development.
- A specific **set of Qt plugins** is loaded.

**Implementation**: `python/gui/src/Saphir/Saphir/devmode_helper.py`.

**Limits / debt**:

- The simulated disk paths are **hardcoded macOS paths** (`devmode_helper.py:8-10`) — to be made portable / configurable.
- The simulation relies on **local filesystem paths**, not on an emulation of the Safecor protocol: it does not allow driving the events (disk connection/disconnection, analysis results, energy, …).

---

### 3.2 Safecor simulator `[to build]`

**Nature**: test tool, **not active in production**.

**Objective**: emulate the **behavior of the Safecor appliance** (MQTT bus + components + disks) in order to drive the Saphir integration tests in a **deterministic and reproducible** way.

**Difference from DevMode**: DevMode simulates the disks via the filesystem; the Safecor simulator simulates the **message layer** (the MQTT / API contract) that Saphir consumes. It allows replaying any event sequence.

**Components to plan**:

- **Emulated MQTT bus**: serves the Safecor topics (`DISK_STATE`, `LIST_DISKS`, `LIST_FILES`, `DISCOVER_COMPONENTS`, `ENERGY_STATE`, `SYSTEM_INFO`, `COPY_FILE`, `CREATE_FILE`, …) and the Saphir topics (`saphir/analysis/*`).
- **Sequence scripting**: define parametrized scenarios (e.g. "plug in a disk → list the files → analyze (2 AV, 1 infected) → copy → generate the report").
- **Simulated components**: Safecor components (disk controller, main controller) + antivirus components (delay, result, failure).
- **Simulated disks**: file contents, partitions, fingerprints, on-demand disconnection.
- **Heating / injected failures**: an AV that fails during the analysis, a disk disconnected during the copy, a failing report generation, etc.

**Benefit**: deterministically cover the **workflow scenarios** (`docs/plans/workflow-rules.md` §9) and the **NFRs** (AV failure — NFR-3, disconnection — F4, fingerprint integrity — NFR-1) without an appliance.

**To decide**:

- [ ] Emulation technology (local MQTT service, library, container).
- [ ] Scenario format (declarative test files? Python API?).
- [ ] Minimal scope to start (which subset of topics/scenarios first).

---

## 4. Validation scenarios to cover

> Indicative list, to be derived from the features (`features.md`) and from the state machine (`workflow-rules.md`). To be completed.

| Scenario | Ref. | Level | Tool |
|----------|------|--------|-------|
| Full nominal cycle (boot → analysis → copy → report → reset) | F1–F6 | Integration / E2E | Simulator |
| File selection + queue (selection mode) | F2 | Integration | Simulator |
| Analysis with infected consensus | F3 | Integration | Simulator |
| AV failure during the analysis | NFR-3 | Integration | Simulator |
| Source disconnection during copy + resume | F4 | Integration | Simulator |
| Locking after use (different media) | NFR-4 | Integration | Simulator |
| Fingerprint verification (injected alteration) | NFR-1 | Integration | Simulator |
| Multilingual report (EN/FR) | F14 / NFR-5 | Unit / Integration | pytest |
| Consensus (pure logic) | F3 | Unit | pytest |
| EMA / ETA | F16 | Unit | pytest |

---

## 5. To be completed

- [ ] Test tools and framework (pytest, plugins, test directories structure).
- [ ] Naming and placement convention of the tests.
- [ ] Minimum required coverage per level.
- [ ] CI: which tests to run on each commit (see `setup/` / GitHub Actions).
- [ ] Integration of the Safecor simulator in the CI.
- [ ] Features × scenarios coverage matrix.

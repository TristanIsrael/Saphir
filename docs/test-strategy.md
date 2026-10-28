# Validation test strategy — Saphir

> **Status**: Active — pre-refactoring characterization phase
> **Last updated**: 2026-10-28
> **Reference**: `docs/features.md` (F1–F21), `docs/workflow-rules.md` (state machine), `docs/plans/testing-plan.md`

---

## 1. Objective

Define the approach and tools for the **validation** of Saphir, from the lowest level (unit) up to the system level (full user scenarios). The objective is to be able to validate the Saphir behavior **without a Safecor appliance** for the majority of cases, and to reserve on-appliance tests for platform integration checks.

This document is the container of the **validation strategy**; the simulation capabilities are grouped here (DevMode, Safecor emulator) as they serve this single purpose.

---

## 2. Test levels

| Level | Periphery | Tool | Target |
|--------|-----------|-------|-------|
| **Unit** | Isolated module | pytest | Pure logic: consensus (F3), EMA (F16), helpers, models |
| **Component** | Isolated controller | pytest + mocks | Each future sub-controller (WorkflowController, StorageManager, …) |
| **Integration** | GUI + emulator | pytest + Safecor emulator + mock AV | Orchestration, state transitions, MQTT, full workflow |
| **System / E2E** | Real appliance | Manual / script | Platform verification (multi-VM, physical disks) |

---

## 3. Simulation tools

### 3.1 DevMode (development mode)

**Nature**: development tool, **not active in production**.

**Role**: allow the development and testing of the GUI **without a Safecor appliance** (no multi-VM).

**Current behavior**:

- Enabled by the **environment variable** `DEVMODE`.
- The MQTT client is created in **debug TCP mode** (localhost) instead of the Safecor channel.
- In DEVMODE, the app **automatically starts a full-disk analysis** when the source disk is connected (auto-pilot for testing).
- A specific **set of Qt plugins** is loaded.

**Implementation**: `python/gui/src/Saphir/Saphir/devmode_helper.py`.

---

### 3.2 Safecor emulator

**Nature**: test tool, **not active in production**. Lives in the **Safecor** repository (`python/emulator/`).

**Objective**: emulate the **behavior of the Safecor appliance** (MQTT bus + components + disks) in order to drive the Saphir integration tests in a **deterministic and reproducible** way.

**Components**:

- **Mosquitto broker**: local MQTT broker (auto-started on port 1883, reuses existing if present).
- **Mock Dom0**: handles `DISCOVER_COMPONENTS`, `ENERGY_STATE`, `DEFAULT_LANGUAGE`, `RESTART_DOMAIN`.
- **Mock SysUSB**: handles `DISK_STATE`, `LIST_FILES`, `COPY_FILE`, `CREATE_FILE`, `LIST_DISKS`.
- **Scenario API**: `attach_disk()`, `detach_disk()`, `set_energy_state()`, `set_default_language()`, `restart_domain()`.
- **Pytest plugin**: provides an `emulator` fixture (see `safecor_emulator.pytest_plugin`).

**Usage in tests**:

```python
from safecor_emulator import Emulator, default_profile

em = Emulator(
    profile=default_profile(),
    source_disks={"disk0": "/path/to/files"},
    storage_path="/tmp/repo",
    destination_disk_path="/tmp/target",
)
em.start()
# ... drive scenario ...
em.attach_disk("disk1", "/path/to/target")
em.detach_disk("disk1")
em.stop()
```

---

### 3.3 Mock antivirus (Saphir)

**Nature**: test tool, lives in **Saphir** (`python/gui/tests/`).

**Role**: simulate antivirus engines during integration tests. Inherits from `AbstractAntivirusController` and runs in a **subprocess** (the `Api()` singleton forbids in-process sharing).

**Configuration** (passed via JSON file):

- `infected`: set of filepaths to report as infected.
- `default`: default verdict for unlisted files (`"clean"` or `"infected"`).
- `scan_delay`: seconds to simulate scan time per file.

**Usage in tests**:

```python
from tests.mock_av_manager import MockAVManager

with MockAVManager("mock-clam", infected={"/bad.txt"}, scan_delay=0.05) as av:
    # av is running as a subprocess, ready to receive analysis requests
    ...
```

**Important**: the mock AV subprocess needs ~5-10 seconds to start (Python imports). Tests must wait for the mock to be **discovered** (via `DISCOVER_COMPONENTS`) before sending analysis requests.

---

## 4. Test infrastructure

### 4.1 Environment setup

```bash
cd python/gui
bash setup_dev_env.sh
source .venv/bin/activate
```

This creates a venv, installs `requirements.txt` + `requirements-dev.txt`, and creates `.pth` files pointing to the local Safecor repositories (`safecor` + `safecor_emulator`).

### 4.2 Running tests

```bash
# All tests (unit + integration)
pytest tests/

# Integration tests only (require emulator + mock AV)
pytest tests/test_workflow_nominal.py tests/test_workflow_bug_target_disconnection.py

# Unit tests only (fast, no external dependencies)
pytest tests/ --ignore=tests/test_workflow_nominal.py --ignore=tests/test_workflow_bug_target_disconnection.py
```

### 4.3 Test files

| File | Level | Description |
|------|-------|-------------|
| `tests/test_analysis_controller.py` | Unit/Component | AnalysisController logic (queue, grouping, scan) |
| `tests/test_ema_estimator.py` | Unit | EMA remaining-time estimator |
| `tests/test_report_controller.py` | Unit | Report generation (Jinja2 + WeasyPrint) |
| `tests/test_workflow_nominal.py` | **Integration** | Full nominal cycle (C.1): boot → analysis → copy → report → SystemMustBeReset |
| `tests/test_workflow_bug_target_disconnection.py` | **Integration** | Bug characterization (C.2): target disconnect during copy → **xfail** (documents the bug) |

### 4.4 Test app entry point

`tests/test_app_entry.py` is a minimal Saphir app entry point (no QML) used by the integration tests. It runs the `ApplicationController` with an offscreen Qt platform:

```bash
QT_QPA_PLATFORM=offscreen DEVMODE=1 python tests/test_app_entry.py
```

The integration tests launch this as a subprocess and observe state transitions via its stdout.

### 4.5 Mock AV helper

`tests/mock_av.py` — the mock antivirus controller (inherits `AbstractAntivirusController`).
`tests/mock_av_manager.py` — lifecycle manager (start/stop subprocess, temp config).

---

## 5. Characterization testing (pre-refactoring)

The current phase uses **characterization testing** (inverse TDD): tests capture the **current behaviour, bugs included**, so the refactoring can be validated against them.

- A test that encodes **correct behaviour** must keep passing throughout the refactoring.
- A test that encodes a **current bug** (marked `xfail`) keeps failing until the refactoring fixes it.

**Current characterization tests**:

| Test | Documents | Expected |
|------|-----------|----------|
| `test_nominal_cycle` | Full workflow state sequence | **Pass** (valid behaviour) |
| `test_target_disconnection_during_copy` | Target disconnect ignored during copy (state gate) | **Xfail** (bug, to be fixed by refactoring) |

---

## 6. Validation scenarios to cover

> Derived from the features (`features.md`) and the state machine (`workflow-rules.md`).

| Scenario | Ref. | Level | Status |
|----------|------|--------|--------|
| Full nominal cycle (boot → analysis → copy → report → reset) | F1–F6 | Integration | ✅ `test_workflow_nominal.py` |
| Target disconnection during copy | F4 | Integration | ✅ `test_workflow_bug_target_disconnection.py` (xfail) |
| File selection + queue (selection mode) | F2 | Integration | ⬜ backlog |
| Analysis with infected consensus | F3 | Integration | ⬜ backlog |
| Pause / resume during analysis | F5 | Integration | ⬜ backlog |
| Single-disk mode (target inserted later) | F4 | Integration | ⬜ backlog |
| Source/target disconnection during copy + auto-resume | F4 | Integration | ⬜ backlog |
| Report generation failure → ReportFailed | F7 | Integration | ⬜ backlog |
| Source disconnection during analysis | F4 | Integration | ⬜ backlog |
| AV failure (NFR-3 — minimum number of engines) | NFR-3 | Integration | ⬜ backlog |
| Fingerprint integrity (NFR-1 — injected alteration) | NFR-1 | Integration | ⬜ backlog |
| Consensus (pure logic) | F3 | Unit | ✅ existing |
| EMA / ETA | F16 | Unit | ✅ existing |

---

## 7. Conventions

- Test files: `tests/test_<module>.py` for unit/component, `tests/test_workflow_<scenario>.py` for integration.
- Integration tests use the `StateTracker` class (in `test_workflow_nominal.py`) to observe app state transitions via subprocess stdout.
- The Saphir app runs as a **subprocess** in integration tests (the `Api()` singleton forbids in-process sharing with the emulator).
- Mock AVs also run as **subprocesses** (same constraint).
- `DEVMODE=1` enables auto-start of full analysis when the source disk is connected (test auto-pilot).

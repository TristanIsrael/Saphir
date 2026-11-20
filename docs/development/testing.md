# Saphir — Testing

> **Status**: Stable
> **Last updated**: 2026-11-20
> **Audience**: developers (human and AI agents) writing or running tests for Saphir, and QA operators driving manual validation
> **Scope**: the Saphir validation strategy — test levels, simulation tools (DevMode, Safecor emulator, mock antivirus), the test infrastructure (environment, commands, inventory, QML runner), the semi-automated manual validation environment, coverage gaps and backlog, historical decisions, and testing conventions.

## Related documents

| Concern | Document |
|---------|----------|
| Features referenced by the test scenarios (F1–F21, NFRs) | [`../specifications/features.md`](../specifications/features.md) |
| State machine referenced by the test scenarios | [`../specifications/workflow.md`](../specifications/workflow.md) |
| Coding & linting standards | [`coding-rules.md`](coding-rules.md) |
| Build & packaging (chroot test-gui step) | [`building.md`](building.md) |
| Project status (feature/NFR coverage audit, gaps, backlog) | [`../project-status.md`](../project-status.md) |

---

## 1. Objective

Define the approach and tools for the **validation** of Saphir, from the lowest level (unit) up to the system level (full user scenarios). The objective is to be able to validate the Saphir behavior **without a Safecor appliance** for the majority of cases, and to reserve on-appliance tests for platform integration checks.

This document is the container of the **validation strategy**; the simulation capabilities are grouped here (DevMode, Safecor emulator) as they serve this single purpose.

**Quality gate**: ≥ 85% code coverage on the full `Saphir` package.

---

## 2. Test levels

| Level | Periphery | Tool | Target |
|--------|-----------|-------|-------|
| **Unit** | Isolated module | pytest | Pure logic: consensus (F3), EMA (F16), helpers, models |
| **Component** | Isolated controller | pytest + mocks | Each sub-controller (WorkflowController, StorageManager, …), including **handler tests** (MQTT message handlers invoked directly with crafted payloads against a mocked `Api`) |
| **Integration** | GUI + emulator | pytest + Safecor emulator + mock AV | Orchestration, state transitions, MQTT, full workflow |
| **Packaging** | Alpine chroot (minirootfs) | `setup/chroot/chroot-build.sh` | Real APKs built with abuild, PyInstaller bundle boots in DEVMODE |
| **System / E2E** | Real appliance | Manual / script | Platform verification (multi-VM, physical disks) |

Layering in practice (top = most integration):

```
┌─────────────────────────────────────────────────────────┐
│  Integration (emulator + real MQTT)                     │
│  test_workflow_nominal.py, test_analysis_controller.py │
├─────────────────────────────────────────────────────────┤
│  Handler (mocked Api, direct method invocation)         │
│  test_application_controller_handlers.py               │
├─────────────────────────────────────────────────────────┤
│  Unit (mocked dependencies, isolated modules)           │
│  test_workflow_controller.py, test_file_queue.py, etc. │
└─────────────────────────────────────────────────────────┘
```

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
)
em.start()
# ... drive scenario ...
# The last attached disk is the copy target (no separate parameter needed)
em.attach_disk("disk1", "/path/to/target")
em.detach_disk("disk1")
em.stop()
```

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

This creates a venv, installs `requirements.txt` + `requirements-dev.txt`, and creates `.pth` files pointing to the local Safecor repositories (`safecor` + `safecor_emulator`). See §5.2 for the full manual-environment setup.

### 4.2 Running tests

```bash
# All tests (unit + integration)
pytest tests/

# Verbose variant (GUI suite)
DEVMODE=1 .venv/bin/python -m pytest tests/ -v

# Integration tests only (require emulator + mock AV)
pytest tests/test_workflow_*.py

# Unit tests only (fast, no external dependencies)
pytest tests/ --ignore=tests/test_workflow_nominal.py --ignore=tests/test_workflow_bug_target_disconnection.py --ignore=tests/test_workflow_pause_resume.py --ignore=tests/test_workflow_copy_failure.py --ignore=tests/test_workflow_fingerprint_corruption.py --ignore=tests/test_workflow_av_failure_analysis.py --ignore=tests/test_workflow_source_disconnection_analysis.py --ignore=tests/test_workflow_source_disconnection_copy.py --ignore=tests/test_workflow_multi_source.py

# GUI coverage
DEVMODE=1 .venv/bin/coverage run --source=src/Saphir -m pytest tests/ -q
.venv/bin/coverage report

# Viewer suite (shares the GUI venv)
cd python/viewer
DEVMODE=1 pytest tests/ -q

# Viewer coverage
DEVMODE=1 ../gui/.venv/bin/coverage run --source=src/viewer/Viewer -m pytest tests/ -q
../gui/.venv/bin/coverage report -m
```

### 4.3 Test files

| File | Level | Description |
|------|-------|-------------|
| `tests/test_analysis_controller.py` | Unit/Component | AnalysisController logic (queue, grouping, scan, 8.8 hold, NFR-1, AV failure) |
| `tests/test_av_integrity_check.py` | Unit | NFR-1 repository→AV fingerprint check (match/mismatch/missing/empty) |
| `tests/test_eta_ema.py` | Unit | EMA remaining-time estimator |
| `tests/test_report_controller.py` | Unit | Report generation (Jinja2 + WeasyPrint) |
| `tests/test_storage_manager.py` | Unit | Multi-source disk storage (`add_source`/`set_sources`/`remove_source`) |
| `tests/test_transfer_controller.py` | Unit | Copy orchestration, per-file disk, 8.6 pause/resume, NFR-1 target check, 8.10 final check |
| `tests/test_workflow_controller.py` | Unit | State machine transitions (incl. `ReportFailed`, scenario 8.7) |
| `tests/test_workflow_nominal.py` | **Integration** | Full nominal cycle (C.1): boot → analysis → copy → report → SystemMustBeReset |
| `tests/test_workflow_bug_target_disconnection.py` | **Integration** | Target disconnect during copy → `SystemMustBeReset` (bug C.2, fixed #148) |
| `tests/test_workflow_pause_resume.py` | **Integration** | Scenario 8.2: pause mid-analysis, resume → remaining files only |
| `tests/test_workflow_copy_failure.py` | **Integration** | Scenario 8.10: individual copy failure + final check |
| `tests/test_workflow_fingerprint_corruption.py` | **Integration** | NFR-1: a corrupted file is not copied |
| `tests/test_workflow_av_failure_analysis.py` | **Integration** | Scenario 8.9: AV engine failure during analysis |
| `tests/test_workflow_source_disconnection_analysis.py` | **Integration** | Scenario 8.8: source disconnect during analysis (hold + auto-resume) |
| `tests/test_workflow_source_disconnection_copy.py` | **Integration** | Scenario 8.6: source/target disconnect during copy (hold + auto-resume, NFR-4) |
| `tests/test_workflow_multi_source.py` | **Integration** | F1 (10.8): two source disks analyzed, every clean file copied to the single target |
| `tests/test_qml_bindings.py` | **Component** | QML declarative bindings (Phase 12): panel visibility for every `SystemState`, `Bindings.qml` derived properties, `AnalysisPanel` state transitions, `SystemLoadingPanel` progression |
| `tests/test_qml_signals.py` | **Component** | QML signal integration (Phase 12): Python→QML signal path (static notify check on the real controller + dynamic updates), `TopBar` (clock, battery, plugged, classification), analysis list filter toggles on the real `QueueListModel` |
| `tests/test_qml_panels.py` | **Component** | QML panel functional tests (Phase 12): `FilesCopyPanel` (status switch + colors, header, gauge), main menu & dialogs (open triggers, accepted/rejected actions), `FilesSelectionPanel` (queue counter, folder navigation, enqueue/dequeue, source rows) |
| `tests/test_qml_bindings_runner.py` | **Component** | Offscreen subprocess runner: loads the real `MainScreen.qml` against a fake `ApplicationController` (see §4.6) |

The viewer suite (`python/viewer/tests/`, run with `DEVMODE=1 pytest tests/ -q`, 99% coverage):

| File | Level | Description |
|------|-------|-------------|
| `tests/test_application_controller.py` | Component | Viewer ApplicationController (Phase 13): init, DEVMODE/production `start()`, subscription → ready flow, disk state / list disks / list files handlers, new-file Office→PDF conversion, energy state, message dispatch, slots, file-type detection, setters, translations |
| `tests/test_models.py` | Unit | `SafecorInputFilesListModel` (roles, data, reset), `SafecorInputFilesListProxyModel` (rows, `currentFolder` signal/property), `FileType`/`Roles`/`SystemState` enums |
| `tests/test_office_helper.py` | Unit | `OfficeHelper.convert_to_pdf` (DEVMODE vs production LibreOffice path, error path, extension stripping) |
| `tests/test_constants.py` | Unit | `ViewerConstants` extension lists and `FILES_FILTERS` union |

### 4.4 Test app entry point

`tests/test_app_entry.py` is a minimal Saphir app entry point (no QML) used by the integration tests. It runs the `ApplicationController` with an offscreen Qt platform:

```bash
QT_QPA_PLATFORM=offscreen DEVMODE=1 python tests/test_app_entry.py
```

The integration tests launch this as a subprocess and observe state transitions via its stdout.

### 4.5 Mock AV helper

- `libsaphir/_mock_antivirus_controller.py` — the mock antivirus controller (inherits `AbstractAntivirusController`, standalone-runnable).
- `tests/mock_av_manager.py` — lifecycle manager (start/stop subprocess, temp config).

The **manual** validation environment that uses these (launcher + operator runbook) is described in §5.

### 4.6 QML test runner

The QML layer is tested offscreen with the **real** `MainScreen.qml` (Phase 12, #155, #156). Two constraints shape the design:

- A `QGuiApplication` cannot be created in the pytest process (the handler tests already own a `QCoreApplication`), so the QML runs **in a subprocess**: `tests/test_qml_bindings_runner.py`.
- The app must boot **without an appliance**: the runner registers a **fake `ApplicationController`** (same `@Property` surface, `<name>Changed` signals and list models as the real one) plus the real Python `Enums` singleton, then loads the real QML.

The client side is shared between the three QML test modules through `tests/qml_test_client.py` (`QmlClient` + `launch_qml_runner`/`shutdown_qml_runner`/`reset_controller`) and a module-scoped `qml` fixture in `tests/conftest.py`, so the runner starts **once per test module**.

The tests drive the runner over a JSON-line protocol and assert on the live QML tree:

- `set` / `get` / `wait` — set fake-controller properties (which emit the same `<name>Changed` signals as the real controller), read any QML property, wait for a change
- `set_queue` / `set_model_prop` — populate the runner's **real `QueueListModel`** with `(filename, status)` rows (production filtering logic) and set properties on the queue model bound to the analysis list view
- `set_source` / `source_row` — populate/inspect the source file list model (a `QAbstractListModel` with the real role names: `type`, `filename`, `filepath`, `inqueue`, ...)
- `click` — synthesize a mouse click at an item's center (`QTest.mouseClick` on the window, which drives the real Qt6 input dispatch the QML `MouseArea`s listen to)
- `call` / `call_func` / `emit` — call a fake-controller `@Slot` method, a QML function without arguments (e.g. a `Bindings.qml` wrapper) or emit a QML signal (`QMetaObject.invokeMethod`), driving the same wiring a click would
- `get_calls` / `clear_calls` — inspect/clear the fake controller's call log (its `@Slot` methods record every QML-side call)

Objects are located by QML component class name (the volatile `_QMLTYPE_N` suffix is stripped; C++-native QML types report their C++ name, e.g. `QQuickMouseArea`); the loading panel's 1 s opacity fade is handled by waiting for the opacity to settle.

Known limitations: the runner stubs the QML singletons `Sensors`/`Energy` (not needed by the tested bindings); the open D8 gap (`infected: nbInfected > 1` should be `> 0`) is documented as an `xfail`; and in the offscreen platform (Qt 6.12) dynamically instantiated QML items (Repeater items, ListView delegates) are never materialized and item-activation notifications (`onVisibleChanged`) are never delivered — the affected QML paths (dialog buttons, file rows, panel show) are driven through the `call` / `call_func` / `emit` ops or verified statically, which exercise the same wiring as a click.

### 4.7 Key patterns

- **Api mocking**: `patch("Saphir.<module>.Api")` — each module that imports `Api` must be patched separately.
- **Mock AnalysisController**: `_make_mock_analysis_controller()` provides the interface without a real MQTT subscription.
- **Emulator integration**: `safecor_emulator.pytest_plugin` provides the `emulator` fixture with a real Mosquitto broker + mock peers.
- **DEVMODE**: set via environment variable (`DEVMODE=1`) to activate the dev MQTT client path.

---

## 5. Manual validation environment

This section describes how to set up and use the **semi-automated validation environment**. It allows a developer or QA operator to manually drive user scenarios (attach/detach disks, trigger analysis, observe the GUI) without a Safecor appliance.

### 5.1 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Host machine                                                   │
│                                                                 │
│  ┌────────────────────┐    MQTT (localhost:1883)   ┌────────┐  │
│  │  Safecor Emulator  │ ◄─────────────────────────► │  GUI   │  │
│  │  (GUI app:         │                             │ (Qt,   │  │
│  │   mosquitto +      │ ◄─────────────────────────► │ on-    │  │
│  │   mock Dom0 +      │                             │ screen)│  │
│  │   mock SysUSB +    │                             └────────┘  │
│  │   operator panel)  │                                         │
│  └────────────────────┘                                         │
│           ▲                                                     │
│           │ MQTT                                                 │
│  ┌────────┴────────┐  ┌──────────────────┐                      │
│  │  mock-clam      │  │  mock-eset       │                      │
│  │  (subprocess)   │  │  (subprocess)    │                      │
│  └─────────────────┘  └──────────────────┘                      │
└─────────────────────────────────────────────────────────────────┘
```

Three components must be running simultaneously:

| # | Component | Role | Started by |
|---|-----------|------|------------|
| 1 | **Emulator GUI** | Mosquitto broker + mock Dom0 + mock SysUSB + operator controls | Operator (prerequisite) |
| 2 | **mock-clam / mock-eset** | Mock antivirus engines | `validate_env.sh` |
| 3 | **Saphir GUI** | The application under test (on-screen) | `validate_env.sh` |

The **operator console** (a separate terminal) is used to drive the scenario.

### 5.2 Prerequisites

| Requirement | Check |
|-------------|-------|
| Saphir dev environment | `bash python/gui/setup_dev_env.sh` (venv + Safecor `.pth` links) |
| Safecor repository checkout | A local clone of the Safecor repo (path set via `SAFECOR_ROOT`) |
| A local directory emulating the source disk | e.g. `/tmp/source-disk/` with a few files |
| A local directory emulating the target disk | e.g. `/tmp/target-disk/` (empty) |
| Mosquitto broker | Auto-started by the emulator on port 1883 |

### 5.3 Setup (one-time)

```bash
cd /path/to/Saphir/python/gui
SAFECOR_ROOT=/path/to/Safecor bash setup_dev_env.sh
source .venv/bin/activate   # or venv.nosync/bin/activate on macOS
```

`SAFECOR_ROOT` must point to the root of your Safecor repository checkout (the directory containing `python/lib/src` and `python/emulator/src`).

> **macOS**: the venv is created in `venv.nosync` by default (Time Machine friendly). Linux-only dependencies (`evdev`, `inotify_simple`, `pyudev`) are skipped automatically with a warning. Override with `SAPHIR_VENV_DIR`.

Verify the emulator is importable:

```bash
python -c "from safecor_emulator import Emulator, default_profile; print('OK')"
```

### 5.4 Running the validation environment

**Terminal 1 — Emulator (GUI)**: launch the Safecor emulator GUI:

```bash
python -m safecor_emulator.cli --gui
```

The GUI provides:

- Configuration of topology, storage path (repository), and source disks
- Starting/stopping the emulator (mosquitto broker + mock Dom0 + mock SysUSB)
- Interactive controls: attach/detach disks, set energy state, restart domains, set language

**Important**: there is no "target disk" in the emulator setup. The **last attached disk** is automatically considered the copy target by Saphir.

**Terminal 2 — Saphir (GUI + mock AVs)**:

```bash
cd /path/to/Saphir/python/gui
bash validate_env.sh [--config /path/to/av_config.json]
```

The script:

1. Verifies the broker is reachable on `localhost:1883`.
2. Starts `mock-clam` and `mock-eset` as background subprocesses.
3. Launches the Saphir GUI **on-screen** (native platform, kiosk layout).

> **`--config`**: optional JSON file that controls the mock AV behaviour (which files are infected/clean). Without it, all files are reported clean. Example:
> ```json
> {
>     "default": "clean",
>     "infected": ["/tmp/source-disk/bad.txt"],
>     "scan_delay": 0.1
> }
> ```

> **Auto-start disabled**: `validate_env.sh` sets `DEVMODE_AUTO_START=0`, so the analysis does **not** start automatically. The operator must click "Yes" on the "Do you want to analyze the whole storage?" dialog.

Stop everything with **Ctrl+C** in Terminal 2 (mock AVs are cleaned up automatically).

### 5.5 Validation scenarios

Each scenario starts from a fresh boot (restart the GUI to reset). Use the operator console (Terminal 2) to drive events.

**5.5.1 Nominal cycle (C.1)**

Full end-to-end scan. A source disk is attached, the operator accepts the analysis, clean files are copied to the target, and a PDF report is generated.

| Step | Action | Expected state |
|------|--------|----------------|
| 1 | Emulator running, no disk attached. Start Saphir via `validate_env.sh` | `SystemReady` |
| 2 | Attach source disk via emulator GUI (Disks → id + path → Attach) | `SystemWaitingForUserAction` (GUI: "Do you want to analyze the whole storage?") |
| 3 | Accept the whole storage analysis (click "Yes") | `SystemAnalysisRunning` |
| 4 | Analysis completes | `AnalysisCompleted` |
| 5 | Attach target disk via emulator GUI (last attached = target) | `CopyCleanFiles` |
| 6 | Copy + report complete | `GeneratingReport` → `SystemMustBeReset` |
| 7 | Verify the target path contains clean files + PDF report | — |

**5.5.2 Infected file (F3 consensus)**

One file is reported as infected by a mock AV engine. The consensus rule marks it as infected; it is excluded from the copy.

Create a config file (e.g. `/tmp/infected.json`):

```json
{
    "default": "clean",
    "infected": ["/bad.txt"],
    "scan_delay": 0.1
}
```

> File paths are relative to the source disk root.

Start Saphir with the config:

```bash
bash validate_env.sh --config /tmp/infected.json
```

Then attach the source disk and accept the analysis. The infected file should appear in the "Infected" tab and **not** be copied to the target.

**5.5.3 Source disconnection during analysis (8.8)**

The source disk is disconnected while analysis is running. The system holds, then auto-resumes when the disk is reconnected (remaining files only).

| Step | Action | Expected |
|------|--------|----------|
| 1 | Attach source disk, accept analysis | `SystemAnalysisRunning` |
| 2 | Detach source disk via emulator GUI | GUI shows "source disconnected" prompt, analysis holds |
| 3 | Attach source disk via emulator GUI | Analysis resumes (remaining files only) |

**5.5.4 AV engine failure (NFR-3, 8.9)**

An antivirus engine domain crashes during analysis. The system detects the failure and transitions to an error state.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Attach source disk, accept analysis | `SystemAnalysisRunning` |
| 2 | Restart AV domain via emulator GUI | GUI detects AV failure, shows NFR-3 message |
| 3 | Wait | System transitions to error state |

**5.5.5 Target disconnection during copy (F4, 8.6)**

The target disk is disconnected while files are being copied. The copy pauses; it auto-resumes when the target is reconnected.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Reach `CopyCleanFiles` (after analysis + target attach) | Copy in progress |
| 2 | Detach target disk via emulator GUI | Copy pauses, GUI shows reconnection prompt |
| 3 | Attach target disk via emulator GUI | Copy resumes |

**5.5.6 Multi-source (F1, 10.8)**

Two source disks are connected. All files from both disks are analyzed; clean files from both are copied to the single target.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Attach first source disk via emulator GUI | `SystemWaitingForUserAction` |
| 2 | Attach second source disk via emulator GUI | Both sources appear in the GUI |
| 3 | Accept the analysis (click "Yes") | `SystemAnalysisRunning` (covers both disks) |
| 4 | Analysis completes, attach target | Clean files from both disks are copied |

**5.5.7 Language change (F19)**

The default language is changed while the system is running. The GUI retranslates all strings immediately.

| Step | Action | Expected |
|------|--------|----------|
| 1 | System in `SystemReady` | UI in default language (EN) |
| 2 | Set default language to "fr" via emulator GUI | GUI retranslates to French |
| 3 | Verify labels, buttons, messages | All strings in French |

### 5.6 State observer (DevMode)

In DEVMODE, the `WorkflowController` writes every state transition to `/tmp/saphir_state.log`. Open a separate terminal and tail it live:

```bash
tail -f /tmp/saphir_state.log
```

Output format (one line per event):

```
1793720794.772 TRANSITION SystemReady
1793720794.801 TRANSITION SystemGettingFilesList
1793720795.102 BLOCKED SystemAnalysisRunning -> SystemReady
```

- `TRANSITION` — a valid state change was applied.
- `BLOCKED` — a transition was **rejected** by the state machine (indicates a bug).

The file is truncated on each app start (DEVMODE only). No impact in production.

### 5.7 Troubleshooting

| Symptom | Cause / Fix |
|---------|-------------|
| `ERROR: MQTT broker not reachable` | Emulator not started, or mosquitto on a different port. Check Terminal 1. |
| GUI stuck in `SystemLoading` | Mock AVs not discovered. Check they are running (`ps aux \| grep mock`). Ensure `DEVMODE=1` is set. |
| Mock AV dies at startup | Check `PYTHONPATH` includes `libsaphir/src`. Check no port conflict on 1883. |
| GUI shows no disks | Emulator `source_disks` config must match the disk names the GUI expects. Check the emulator logs. |
| Analysis starts but no files | The emulator's `source_disks` path must contain files. Verify the directory is not empty. |

### 5.8 Cleanup

After validation:

```bash
# Terminal 2: Ctrl+C (stops GUI + mock AVs)
# Terminal 1: Ctrl+C (stops emulator)

# Clean up temp directories
rm -rf /tmp/source-disk /tmp/target-disk /tmp/safecor/storage
```

---

## 6. Characterization testing (pre-refactoring)

The refactoring phase used **characterization testing** (inverse TDD): tests captured the **current behaviour, bugs included**, so the refactoring could be validated against them.

- A test that encodes **correct behaviour** must keep passing throughout the refactoring.
- A test that encodes a **current bug** (marked `xfail`) kept failing until the refactoring fixed it.

**Characterization tests**:

| Test | Documents | Expected |
|------|-----------|----------|
| `test_nominal_cycle` | Full workflow state sequence | **Pass** (valid behaviour) |
| `test_target_disconnection_during_copy` | Target disconnect during copy (bug C.2) | **Pass** — fixed by the refactoring (#148), the `xfail` marker was removed |

---

## 7. Validation scenarios to cover

> Derived from the features (`features.md`) and the state machine (`workflow.md`).

| Scenario | Ref. | Level | Status |
|----------|------|--------|--------|
| Full nominal cycle (boot → analysis → copy → report → reset) | F1–F6 | Integration | ✅ `test_workflow_nominal.py` |
| Multi-source full analysis (partitions + additional media) | F1 (10.8) | Integration | ✅ `test_workflow_multi_source.py` |
| Target disconnection during copy | F4 | Integration | ✅ `test_workflow_bug_target_disconnection.py` |
| Pause / resume during analysis (remaining files only) | F3 (8.2) | Integration | ✅ `test_workflow_pause_resume.py` |
| Individual copy failure + final check | F4 (8.10) | Integration | ✅ `test_workflow_copy_failure.py` |
| Fingerprint integrity (injected alteration) | NFR-1 | Integration | ✅ `test_workflow_fingerprint_corruption.py` |
| AV failure during analysis | NFR-3 (8.9) | Integration | ✅ `test_workflow_av_failure_analysis.py` |
| Source disconnection during analysis (hold + auto-resume) | 8.8 | Integration | ✅ `test_workflow_source_disconnection_analysis.py` |
| Source/target disconnection during copy (hold + auto-resume) | F4 (8.6) | Integration | ✅ `test_workflow_source_disconnection_copy.py` |
| File selection + queue (selection mode) | F2 | Integration | ⬜ backlog |
| Analysis with infected consensus (integration) | F3 | Integration | ⬜ backlog |
| Report generation failure → ReportFailed (integration) | 8.7 | Integration | ⬜ backlog (covered at unit level in `test_workflow_controller.py` / `test_application_controller_handlers.py`) |
| Consensus (pure logic) | F3 | Unit | ✅ existing |
| EMA / ETA | F16 | Unit | ✅ existing |

---

## 8. Known gaps and backlog

### 8.1 Coverage gaps (below 85%)

| Module | Coverage | Gap | Effort |
|--------|----------|-----|--------|
| `analysis_controller.py` | 71% | Archive mounting, error paths, multi-iteration analysis | Medium |
| `queue_list_proxy_model.py` | 74% | `lessThan()` comparison logic, `on_data_changed()` | Low |
| `main.py` | 0% | Entry point (intentionally excluded from coverage target) | N/A |

### 8.2 Functional test backlog

| Scenario | Description | Priority |
|----------|-------------|----------|
| 8.2 | Pause / resume during analysis | Medium |
| 8.4 | Single-disk mode, target inserted later | Medium |
| 8.6 | Source/target disconnection during copy + auto-resume | High |
| 8.7 | Report generation failure → `ReportFailed` | Medium |
| 8.8 | Source disconnection during analysis | Medium |
| AV failure | Minimum number of engines (NFR-3) | High |
| Fingerprint integrity | Injected alteration detection (NFR-1) | Low |
| Dynamic mock-AV driving | Change per-file results on the fly | Low |

### 8.3 CI integration (deferred)

- Add a `pytest` job to `.github/workflows/build-all.yml`
- Requires a Mosquitto broker service container
- Coverage gate: reject PRs below 85%

---

## 9. Historical decisions

| # | Decision | Date |
|---|----------|------|
| **D-1** | Mock antivirus lives in Saphir (`python/gui/tests/`), inherits `AbstractAntivirusController`, runs in a subprocess | 2026-10-28 |
| **D-2** | Bug target: target disconnection at end of copy → `SystemMustBeReset` (FIXED in `d7df95b`) | 2026-10-28 |
| **D-3** | Environment: venv + `.pth` files for Safecor repos (no packaging) | 2026-10-28 |
| **D-4** | Phase 6 scope: 85% coverage on the **entire project**, not just refactored modules | 2026-10-28 |
| **D-5** | Handler tests use mocked `Api` + direct method invocation (no real broker needed) | 2026-10-28 |

---

## 10. Conventions

- Test files: `tests/test_<module>.py` for unit/component, `tests/test_workflow_<scenario>.py` for integration.
- Integration tests use the `StateTracker` class (in `test_workflow_nominal.py`) to observe app state transitions via subprocess stdout.
- The Saphir app runs as a **subprocess** in integration tests (the `Api()` singleton forbids in-process sharing with the emulator).
- Mock AVs also run as **subprocesses** (same constraint).
- `DEVMODE=1` enables auto-start of full analysis when the source disk is connected (test auto-pilot).

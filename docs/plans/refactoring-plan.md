# Refactoring Plan - Saphir v3.x

> **Status**: In progress — Phases 0-6 complete, Phases 7-9 pending
> **Last updated**: 2026-10-28
> **Branch**: `refactoring` (based on `main` post-merge #128)

---

## 1. Current State Assessment

### 1.1 File Size & Complexity

| Module | Lines | Complexity | Concerns |
|--------|-------|------------|----------|
| `application_controller.py` | ~1268 | Very High | Anti-pattern: God class handling state machine, MQTT routing, UI models, transfer, reporting, energy, translations |
| `analysis_controller.py` | ~534 | High | Manages analysis queue, repository copy, AV dispatch, archive mounting, file status |
| `Bindings.qml` | 151 | Low | Thin bridge, acceptable as-is |
| `MainScreen.qml` | 326 | Medium | Contains direct state-driven UI toggles, could be moved to Bindings |

### 1.2 Identified Code Smells

1. **God Class**: `ApplicationController` handles state machine, MQTT subscriptions, model management, file transfer, PDF reports, energy monitoring, translations, logging
2. **Thread Safety**: Shared dicts (`__queued_files_list`, `__input_files_list`) accessed from multiple threads with only partial locking
3. **Hard-coded Transitions**: State transitions scattered across message handlers instead of a unified state machine
4. **Magic Values**: `ANTIVIRUS_NEEDED = 2`, `alpha=0.3`, `Timer(0.1, ...)`, state values compared numerically
5. **Dead Code**: `SystemInactive`, `SystemWaitingForDevice`, `SystemNotClean`, `TransferFinished` states are defined but unreachable
6. **Concurrent Visibility Control**: `storagesCount` and `systemState` both drive UI visibility, causing race conditions
7. **Print Debugging**: Leftover `print()` and file writes (`/tmp/data.txt`) in production code
8. **No Error Recovery**: No retry logic for failed MQTT subscriptions, no graceful degradation

---

## 2. Target Architecture

### 2.1 Modular Structure

```
Saphir/
├── application_controller.py      # Thin facade: initializes & wires controllers
├── workflow_controller.py         # State machine orchestrator (NEW)
├── storage_manager.py             # Disk detection, mount state, source/target (NEW)
├── file_browser.py                # File listing, folder navigation, queuing (EXTRACTED)
├── file_queue.py                  # Queue data structure & operations (EXTRACTED)
├── transfer_controller.py         # File copy orchestration, progress tracking (NEW)
├── report_controller.py           # PDF generation, report/journal copy (EXISTING - needs improvement)
├── analysis_controller.py         # Analysis orchestration (EXISTING - needs cleanup)
├── energy_monitor.py              # Battery/plugged state polling (NEW)
├── translation_manager.py         # Language switching, QTranslator lifecycle (NEW)
├── api_lifecycle.py               # MQTT client creation, subscription management (NEW)
├── enums.py                       # State/analysis enums
├── analysis_helper.py             # Consensus evaluation
├── ema_eta_estimator.py           # ETA calculation
└── models/                        # All QAbstractTableModel subclasses
    ├── components_model.py
    ├── messages_list_model.py
    ├── log_list_model.py
    └── queue_list_model.py
```

### 2.2 Communication Pattern

```
+----------------------------------------------------------------------+
|                      ApplicationController                              |
|                    (thin facade, ~200 lines)                           |
|   +----------+  +--------------+  +-------------------------------+   |
|   |Workflow  |  |  Storage     |  |     File Browser               |   |
|   |Controller|<->|  Manager     |  |     File Queue                 |   |
|   |          |  |              |  |                                |   |
|   |          |<->|              |<->|  Transfer Controller         |   |
|   |          |  |              |  |                                |   |
|   |          |<->|              |<->|  Analysis Controller         |   |
|   |          |  |              |  |                                |   |
|   |          |<->|              |<->|  Report Controller           |   |
|   |          |  |              |  |                                |   |
|   |          |<->|              |<->|  Energy Monitor              |   |
|   |          |  |              |  |                                |   |
|   |          |<->|              |<->|  Translation Manager         |   |
|   +----------+  +--------------+  +-------------------------------+   |
+----------------------------------------------------------------------+
        |                  |                    |
        +------------------+--------------------+
                            |
                  Domain signals + SystemState
             (single source of truth for all domains)
```

**Key Principle**: All inter-controller communication happens via:
1. **Domain signals** (Qt signals connecting controller methods)
2. **SystemState transitions** (pushed by `WorkflowController`)
3. **Shared data references** (passed by reference in constructor)

**No direct method calls** between sibling controllers. `WorkflowController` is the sole mediator.

---

## 3. Refactoring Phases

### Phase 0: Foundation (No behavior changes) ✅ DONE

**Goal**: Extract leaf controllers that have no dependencies on each other.
**Status**: Complete — commit `0ed848a`, issue #129 (In review)

#### 0.1 `EnergyMonitor` (NEW)
- Extract from `application_controller.py` lines ~883-893, ~933-938
- Responsibilities: polling battery/plugged state, `batteryLevel`/`plugged` properties
- Dependencies: None
- QML bindings: unchanged (`batteryLevel`, `plugged`)

#### 0.2 `TranslationManager` (NEW)
- Extract from `application_controller.py` lines ~546-576
- Responsibilities: `QTranslator` lifecycle, language switching
- Dependencies: None
- QML bindings: unchanged (`language`, `translationInstalled`)

#### 0.3 `ApiLifecycle` (NEW)
- Extract from `application_controller.py` lines ~156-167, ~421-478
- Responsibilities: MQTT client creation, subscription management, ready callback chain
- Dependencies: None
- QML bindings: none (pure backend)

#### 0.4 Remove QtNetwork from the bundle (D-T2)
- **Context** (D-T2, `docs/tech-stack-analysis.md` §7/§8): the GUI talks over **MQTT/paho-mqtt**, not QtNetwork. `QtNetwork` is still bundled (hiddenimport, not in the PyInstaller strip filter) for ~15–25 MB.
- **Action**: remove `PySide6.QtNetwork` from the `hiddenimports` of `python/gui/saphir-gui.spec` and add it to the strip filter; verify the GUI builds and runs (no QtNetwork usage at runtime).
- **Dependencies**: none (packaging only, no behaviour change).
- **Validation**: PyInstaller build succeeds; GUI boots and works (MQTT unaffected).

**Validation**: Run `pytest` + manual test - no observable behavior change.

---

### Phase 1: Stabilize State Machine ✅ DONE

**Goal**: Replace scattered state transitions with a unified `WorkflowController`.
**Status**: Complete — commits `13cf8d7` (1.1), `8f49c1a` (1.2), `2742d26` (1.3); issues #130-132 (In review)

#### 1.1 `WorkflowController` (NEW)
- Define explicit state transitions as methods: `transition_to(state)`, `on_enter(state)`, `on_exit(state)`
- Register transition guards: `can_transition(from, to) -> bool`
- Push `SystemState` changes exclusively through this controller
- Remove all `__set_system_state()` calls from message handlers

**Current problematic pattern** (to be eliminated):
```python
# BAD: Scattered state changes in handlers
def __handle_disk_state():       # line 637-714
    if state == CONNECTED:
        self.__set_system_state(SystemState.CopyCleanFiles)  # line 314

def __on_results_changed():      # line 914-925
    self.__set_system_state(SystemState.AnalysisCompleted)   # line 924

def __handle_create_file():      # line 902-912
    self.__set_system_state(SystemState.SystemMustBeReset)   # line 908
```

**Target pattern**:
```python
# GOOD: Centralized state machine
class WorkflowController:
    def _on_disk_connected(self, disk):
        if self.can_transition(SystemState.SystemReady, SystemState.CopyCleanFiles):
            self.transition_to(SystemState.CopyCleanFiles)

    def _on_analysis_complete(self):
        if self.can_transition(SystemState.SystemAnalysisRunning, SystemState.AnalysisCompleted):
            self.transition_to(SystemState.AnalysisCompleted)
```

#### 1.2 Fix Dead States
- Remove or activate: `SystemInactive`, `SystemWaitingForDevice`, `SystemNotClean`, `TransferFinished`
- Recommendation: Remove `SystemNotClean` and `TransferFinished` (unreachable), mark `SystemWaitingForDevice` as deprecated

#### 1.3 Fix `__handle_disk_state` gate (line 640)
```python
# CURRENT: numeric comparison, blocks too early, no disk-name awareness
if self.__system_state.value >= SystemState.CopyCleanFiles.value:
    return

# PROPOSED: explicit rules based on workflow state + disk name
if state == SystemWaitingForTarget:
    # the TARGET must be detectable here (that is the purpose of the state)
    if disk_name == source_name:
        return              # same disk as source: ignore
    assign_target(disk_name)  # start the copy
elif system_used and disk_name != source_name:
    lock_into(SystemMustBeReset)  # NFR-4: a different disk after use locks the system
elif state in (SystemMustBeReset, SystemResetting):
    return                  # locked: ignore new disks until reset
```
> The numeric gate must be replaced by state + disk-name logic. In particular, `SystemWaitingForTarget` must **not** be blocked, or the copy could never start.

**Validation**: Full workflow test from boot to shutdown. All state transitions logged.

---

### Phase 2: Extract Data-Heavy Controllers ✅ DONE

**Goal**: Move file/queue management out of `ApplicationController`.
**Status**: Complete — commits `d22987b` (extraction), `2026c90` (unit tests); issue #133 (In review)
**Notes**: `FileQueue` encapsulates the lock (invariant I4). `StorageManager` is the sole owner of source/target state. `ApplicationController` delegates while keeping the QML `@Property` surface unchanged.

#### 2.1 `FileQueue` (NEW)
- Extract `__queued_files_list`, `__queue_files_size`, `__queue_files_list_lock`
- Methods: `enqueue(file)`, `dequeue(filepath)`, `clear()`, `get_clean_files()`, `count()`, `size()`
- Thread-safe internal management
- `ApplicationController` holds reference, no longer owns the data

#### 2.2 `FileBrowser` (EXTRACTED from ApplicationController)
- Extract `__input_files_list`, `__current_folder`, `__folders_to_query`, `__is_enqueuing`
- Methods: `request_file_list(disk, folder)`, `enqueue_folder(folder)`, `dequeue_folder(folder)`
- Emits signals: `fileListReceived(files)`, `folderEnqueued(folder)`, `enqueuingCompleted()`
- QML bindings: `inputFilesListModel`, `inputFilesListProxyModel`, `currentFolder`

#### 2.3 `StorageManager` (NEW)
- Extract `__source_name`, `__source_ready`, `__target_name`, `__target_ready`, `__storages`
- Methods: `on_storage_added(disk)`, `on_storage_removed(disk)`, `set_source(disk)`, `set_target(disk)`
- Emits signals: `sourceChanged(name)`, `targetChanged(name)`, `storagesChanged()`
- **Ownership rule**: Only `StorageManager` subscribes to `DISK_STATE`

**Validation**: Verify file listing, queue operations, and storage detection work identically.

---

### Phase 3: Extract Transfer Logic ✅ DONE

**Goal**: Create dedicated `TransferController` for file copying.
**Status**: Complete — commit `2027609`, issue #134 (In review)

#### 3.1 `TransferController` (NEW)
- Extract `start_transfer()`, `__do_start_transfer()`, `__handle_copy_file()`, `__finish_transfer()`
- Methods: `start(source_disk, target_disk)`, `cancel()`, `progress()`, `is_complete()`
- Responsibilities:
  - Iterate clean files, publish `COPY_FILE` requests
  - Track copy progress via `__handle_copy_file` callbacks
  - On completion: trigger report generation (signal to `ReportController`)
- QML bindings: `transferProgress`, `transferStarted`, `copiedFilesCount`

#### 3.2 Fix Transfer Race Condition
**Current issue** (line 863-864):
```python
# Race: __get_transferred_ratio() iterates __queued_files_list without lock
if self.__get_transferred_ratio() >= 1:
    self.__finish_transfer()
```

**Fix**: Use atomic counter with lock, emit `transferComplete` signal instead of polling.

**Validation**: Copy operation completes reliably, report generated on every run.

---

### Phase 4: Clean Up Existing Controllers ✅ DONE

**Goal**: Improve `AnalysisController` and `ReportController`.
**Status**: Complete — commit `aff7921`, issue #135 (In review)

#### 4.1 `AnalysisController` Cleanup
- Remove archive mounting code (defer to future feature)
- Add proper error handling in `__handle_error` (currently disabled - line 201+)
- Document thread safety guarantees
- Add missing `__analysis_end_time` initialization

#### 4.2 `ReportController` Improvement
- Add error handling for PDF generation failures
- Separate PDF rendering from file creation
- Add test coverage for report generation

**Validation**: Analysis and report generation work identically to pre-refactoring.

---

### Phase 5: QML Cleanup (Views Last) ✅ DONE

**Goal**: Simplify QML visibility logic to rely on `WorkflowController` signals.
**Status**: Complete — commit `8909a19`, issue #136 (In review)
**Note**: Phase 1.2 already removed dead `TransferFinished` references from QML (§5.2 partially done).

#### 5.1 Remove `storagesCount`-driven visibility
**Current issue** (`MainScreen.qml` lines 295-298):
```qml
onStoragesCountChanged: {
    window.pnlFileSelection.visible = bindings.storagesCount === 1
    window.pnlFilesCopy.visible = bindings.storagesCount === 2
}
```

This races with `systemState` changes. Solution: visibility driven by `systemState` exclusively.

#### 5.2 Remove dead `TransferFinished` handler
`MainScreen.qml` line 281: dead code, state is unreachable.

#### 5.3 Move animation/visibility rules to `Bindings.qml`
Keep `MainScreen.qml` clean of state-driven logic.

**Validation**: UI behaves identically, with fewer state-dependent bindings.

---

## 4. Invariants & Guards

These rules must hold throughout refactoring:

| # | Invariant | Description |
|---|-----------|-------------|
| I1 | Single MQTT client | Only `ApiLifecycle` creates/manages MQTT client |
| I2 | Single topic owner | Each MQTT topic has exactly one subscriber (defined in topology) |
| I3 | State machine authority | Only `WorkflowController` sets `SystemState` |
| I4 | Queue thread safety | All `__queued_files_list` access under lock or in single thread |
| I5 | No direct cross-controller calls | Controllers communicate via signals + `SystemState` only |
| I6 | Analysis consensus | File infected if ANY engine flags it (OR logic) |
| I7 | Source disk immutability | Once set, source disk cannot change without full reset |

---

## 5. Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Thread safety regression | Data corruption, crashes | Add lock assertions in dev mode (`DEVMODE_LOCK_CHECK`) |
| State transition regression | Workflow hangs | Add `on_transition` logging + automated state trace |
| QML binding regression | UI doesn't update | Regression test against known user flows |
| API compatibility | PyInstaller build fails | Keep public `@Property` / `@Slot` surface unchanged |

---

## 6. Out of Scope (Future)

- Archive mounting (already disabled via `MOUNT_ARCHIVES = False`)
- Multi-disk concurrent scanning
- Automated retry for failed AV scans
- MQTT connection re-establishment logic
- Performance optimization (beyond current EMA ETA)

---

## 7. TODO / Open Questions

1. **Remove `SystemWaitingForDevice`** — **Resolved**: dead code, removed in Phase 1.2.
2. **Archive mounting** — **Resolved**: the dormant code is **removed**; re-introduction is a backlog feature (see `docs/workflow-rules.md` §9, `docs/features.md` backlog).
3. **`handheld` property** — **Resolved**: kept, always `True` (not configurable for now); a form-factor adaptation is tracked in `docs/gui-backlog.md`.
4. **Single-disk mode** — **Resolved** (see `docs/workflow-rules.md` §8.4): analysis works on one disk; copy and report require a second disk, modelled by the `SystemWaitingForTarget` state.
5. **`__on_analysis_state_changed` driving state transitions** — **Resolved**: now routed through `WorkflowController.force_state()` (Phase 1.1).
6. **Target disconnect during copy (bug C.2)** — **Resolved**: `__handle_disk_state` now transitions to `SystemMustBeReset` when the target disconnects during `CopyCleanFiles`/`GeneratingReport` (commit `d7df95b`).

---

## 8. Progress Summary

| Phase | Status | Commits | Issues | Notes |
|-------|--------|---------|--------|-------|
| 0.1 EnergyMonitor | ✅ Done | `0ed848a` | #129 | Battery/plugged polling |
| 0.2 TranslationManager | ✅ Done | `0ed848a` | #129 | QTranslator lifecycle |
| 0.3 ApiLifecycle | ✅ Done | `0ed848a` | #129 | Direct callback (not Qt signal) |
| 0.4 QtNetwork strip | ✅ Done | `0ed848a` | #129 | Packaging only |
| 1.1 WorkflowController | ✅ Done | `13cf8d7` | #130 | `force_state()` used; `transition_to()` with validation available but not activated |
| 1.2 Dead states | ✅ Done | `8f49c1a` | #131 | Gaps at 3, 8, 12 preserved for QML |
| 1.3 Disk-state gate | ✅ Done | `2742d26` | #132 | Numeric → explicit locked-state set |
| 2.1 FileQueue | ✅ Done | `d22987b` | #133 | Lock encapsulated (I4) |
| 2.2 FileBrowser | ✅ Done | `d22987b` | #133 | Folder nav, enqueuing state |
| 2.3 StorageManager | ✅ Done | `d22987b` | #133 | Sole DISK_STATE owner |
| 2.x Unit tests | ✅ Done | `2026c90` | #133 | 48 tests, all passing |
| 3.1 TransferController | ✅ Done | `2027609` | #134 | Copy orchestration, progress tracking |
| 3.2 Transfer race fix | ✅ Done | `2027609` | #134 | Atomic counter + signal-based completion |
| 4.1 AnalysisController cleanup | ✅ Done | `aff7921` | #135 | Dead code removed, error handling, timer cancel |
| 4.2 ReportController improvement | ✅ Done | `aff7921` | #135 | `_render_html`/`_write_pdf` separated, try/except |
| Fix broken analysis tests | ✅ Done | `814f8a8` | #136 | `deepcopy` fix, state-based assertions, 3 skipped |
| Fix C.2 target disconnect | ✅ Done | `d7df95b` | #137 | `SystemMustBeReset` transition on target DISCONNECTED |
| 5.1 Remove storagesCount visibility | ✅ Done | `8909a19` | #136 | Declarative bindings on systemState |
| 5.2 Remove dead TransferFinished handler | ✅ Done | `8f49c1a` | #131 | QML refs removed in Phase 1.2 |
| 5.3 Move rules to Bindings.qml | ✅ Done | `8909a19` | #136 | State-driven logic now declarative |
| 6 Unit test coverage | ✅ Done | `d71de3b` | #137 | 44 new tests; refactored modules ≥ 95% |
| 7 Linting & static analysis | ⏳ Pending | — | — | Ruff + type check |
| 8 Alpine package validation | ⏳ Pending | — | — | Docker local build |
| 9 Documentation debt | ⏳ Pending | — | — | French→English, docstrings, dead code removal |

**Test baseline**: 91 passed, 3 skipped (MOUNT_ARCHIVES disabled), 0 failed, 0 xfailed

---

## 9. Estimated Remaining Effort

| Phase | Lines Changed | Effort | Dependencies |
|-------|--------------|--------|--------------|
| Phase 7 | -50 / +50 | Low | Phases 3-5 ✅ |
| Phase 8 | 0 / 0 | Low | Phases 3-5 ✅ |
| Phase 9 | -250 / +100 | Medium | Phases 0-8 |
| **Remaining** | **+0 / -150** | **~3 days** | — |

> **Note**: Phases 6 and 7 are independent and can be parallelized.

---

### Phase 6: Unit Test Coverage ✅ DONE

**Goal**: Ensure all refactored code has adequate unit test coverage (≥ 85%).
**Status**: Complete — commits `c36e440` + this commit, issue #137 (In review)
**Note**: CI coverage gate (6.3) deferred — requires Mosquitto broker in CI.

#### 6.1 Coverage audit
- Run `pytest --cov` on the full suite
- Identify modules below the 85% threshold
- Document gaps per module

#### 6.2 Fill coverage gaps
- Add tests for `WorkflowController` transition validation (`transition_to()` guards) ✅
- Add tests for `AnalysisController` error paths ✅ (71% — remaining gaps are archive mounting)
- Add tests for `ReportController` (PDF generation, edge cases) ✅
- Add tests for `TransferController` (Phase 3 output) ✅
- Add integration-style tests for cross-controller signal flows ✅
- Add handler tests for `ApplicationController` MQTT message dispatch ✅ (46% → 91%)

#### 6.3 CI integration
- Verify `pytest --cov` gate in CI (reject PRs below 85%)
- Ensure coverage report is generated and uploaded

#### Final coverage

| Module | Coverage |
|--------|----------|
| `application_controller.py` | 91% |
| `analysis_controller.py` | 71% |
| `analysis_helper.py` | 100% |
| `api_lifecycle.py` | 100% |
| `transfer_controller.py` | 100% |
| `storage_manager.py` | 100% |
| `file_queue.py` | 100% |
| `file_browser.py` | 100% |
| `workflow_controller.py` | 100% |
| `energy_monitor.py` | 97% |
| `translation_manager.py` | 100% |
| **TOTAL** | **87%** |

**Validation**: `pytest --cov` reports ≥ 85% on the full project. ✅ (87%)

---

### Phase 7: Linting & Static Analysis ⏳ PENDING

**Goal**: Resolve all linting and static analysis issues introduced or exposed by the refactoring.

#### 7.1 Ruff audit
- Run `ruff check` on all Python files in `python/gui/` and `python/libsaphir/`
- Categorize findings: pre-existing vs. introduced by refactoring
- Fix all issues in new/modified files (no suppressions without justification)

#### 7.2 Type checking
- Run `mypy` (or `pyright`) on refactored modules
- Resolve type errors in `FileQueue`, `FileBrowser`, `StorageManager`, `WorkflowController`, `TransferController`
- Add type annotations where missing

#### 7.3 Code style consistency
- Verify `ruff format` compliance on all modified files
- Ensure naming conventions match the project rules (PascalCase classes, snake_case methods, etc.)
- Remove leftover `print()` debugging statements in production code

**Validation**: `ruff check` and `ruff format --check` pass with zero errors on all modified files.

---

### Phase 8: Alpine Package Validation ⏳ PENDING

**Goal**: Verify that the refactored code builds and packages correctly in the Alpine Linux environment.

#### 8.1 APKBUILD update
- Update `setup/packages/saphir-gui/APKBUILD` if new dependencies are introduced
- Verify `requirements.txt` and `requirements-dev.txt` are consistent with the refactored imports
- Ensure `saphir-gui.spec` (PyInstaller) includes the new modules

#### 8.2 Local Docker build
- Build the `saphir-gui` package in the local Docker dev environment (`setup/docker/`)
- Verify the package installs and the GUI boots in DEVMODE
- Confirm no missing imports or runtime errors

#### 8.3 Local package build verification
- Build all 8 APKBUILD packages in the local Docker dev environment
- Verify no build errors, missing dependencies, or import failures
- Confirm the `saphir-gui` binary launches in DEVMODE after install

**Validation**: All packages build successfully in Docker, GUI boots and completes a full scan cycle in DEVMODE.

---

### Phase 9: Documentation Debt ⏳ PENDING

**Goal**: Eliminate the code documentation debt accumulated over time.

**Current state**:
- 13 out of 25 Python modules have **zero** docstrings
- ~30+ comments in French (should be English per project rules)
- No class-level documentation on most QML model classes
- `application_controller.py` (1108 lines) has only 3 docstring markers
- `safecor_input_files_list_model.py` (339 lines) has 0 docstrings and ~200 lines of commented-out dead code

#### 9.1 Translate French comments to English
- `analysis_controller.py`: ~10 French comments (lines 63-79, 250-253)
- `application_controller.py`: ~20 French comments (lines 214-218, 261-262, 281, 446-448, 678-707, 866-878)
- `analysis_helper.py`: 3 French comments (lines 92-94)
- `components_model.py`: 1 French comment (line 16)

#### 9.2 Add class-level docstrings
- All `QAbstractListModel` / `QAbstractTableModel` subclasses in `Saphir/`
- All controller classes (already partially done in Phases 0-4)
- Target: every public class has a one-line docstring explaining its responsibility

#### 9.3 Add method docstrings for public API
- All `@Slot` methods in `application_controller.py`
- All public methods in controllers (non-underscore)
- Target: every public method has a docstring (summary line at minimum)

#### 9.4 Remove dead commented-out code
- `safecor_input_files_list_model.py`: ~200 lines of commented-out code (lines 149-339)
- `queue_list_proxy_model.py`: dead code in `lessThan()` (lines 24-37) and `on_data_changed()` (lines 41-47)
- `safecor_input_files_list_proxy_model.py`: ~40 lines of commented-out code (lines 37-60)
- Verify with `ruff` that no other dead code blocks exist

#### 9.5 Add module-level docstrings
- Every `.py` file in `Saphir/` should have a one-line module docstring
- Format: `"""Short description of what this module provides."""`

**Validation**:
- `grep -r "#.*[éèàçûôî]" Saphir/` returns zero results (no French comments)
- Every public class and method in `Saphir/` has a docstring
- No commented-out code blocks remain (verified by manual review + ruff)
- Doxygen build succeeds without warnings on `python/gui/src/Saphir/`

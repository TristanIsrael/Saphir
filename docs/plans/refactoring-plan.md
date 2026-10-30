# Refactoring Plan - Saphir v3.x

> **Status**: In progress — Phases 0-9 complete, Phases 10-14 pending
>
> **Last updated**: 2026-10-29
>
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
| 7 Linting & static analysis | ✅ Done | `9bdfe42` | #54 | 122+27 ruff errors fixed, format applied, 0 remaining |
| 8 Alpine package validation | ✅ Done | `4b0b1b2`, `056a659`, `cf86fbd`, `c459924`, `c94d4af` | #141, #142, #143, #144 | 7/8 packages built in the Alpine 3.21.9 chroot, GUI domain boots in DEVMODE; `saphir-container-eset` not buildable (ESET URL 404 - the official CI skips it too) |
| 9 Documentation debt | ✅ Done | `4038c13` + round 2 | #139 | French→English (incl. accent-free), all class/method/module docstrings, dead code removed; 0 French comments, 0 public class/method without docstring |
| 10 Missing features & NFRs | ⏳ In progress (4/8) | #145, #146, #147, #148 | — | Fingerprint, ReportFailed, disconnect handlers, AV failure |
| 11 Functional coverage | ⏳ Pending | — | — | Error paths, NFRs, disconnection scenarios |
| 12 GUI (QML) test coverage | ⏳ Pending | — | — | QML bindings, panel visibility, signal integration |
| 13 Viewer modernization | ⏳ Pending | — | — | Lint, format, unit tests (0 → 85%) |
| 14 Semi-automated validation env | ⏳ Pending (Not ready) | — | — | Human-driven test on Safecor emulator (operator console + state observer); blocked on emulator features |

**Test baseline**: 408 passed, 3 skipped, 0 failed (2026-10-30, after 10.5; known boot-sequence flake in full suite under high load — `test_nominal_cycle` passes in isolation)

---

## 9. Estimated Remaining Effort

| Phase | Lines Changed | Effort | Dependencies |
|-------|--------------|--------|--------------|
| Phase 7 | ✅ done | — | Phases 3-5 ✅ |
| Phase 8 | ✅ done | — | Phases 3-5 ✅ |
| Phase 9 | ✅ done | — | Phases 0-8 ✅ |
| Phase 10 | +400 / +100 | High | Phases 3-6 ✅ |
| Phase 11 | +300 / +200 | High | Phase 10 |
| Phase 12 | +200 / +150 | Medium | Phases 5-6, 10 |
| Phase 14 | +250 / +150 | Medium | Safecor emulator (external, **blocking**) |
| **Remaining** | **0 / +550** | **~13 days** | — |

> **Note**: Phase 11 depends on Phase 10, and Phase 12 on Phase 10. Phase 14 is blocked on the
> external Safecor emulator (interactive scenario API / observation hooks not yet built).

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

### Phase 7: Linting & Static Analysis ✅ DONE

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

### Phase 8: Alpine Package Validation ✅ DONE

**Goal**: Verify that the refactored code builds and packages correctly in the Alpine Linux environment.

> **Environment note**: the K8s cluster was not reachable (OIDC/DPoP issue), so validation is
> performed in a local **Alpine 3.21.9 chroot** (`/tmp/opencode/alpine`, repo at `/work/Saphir`)
> against the Saphir APK repository.
>
> The chroot workflow is automated by **`setup/chroot/chroot-build.sh`**
> (subcommands: `init`, `sync`, `build` [or `build all`], `install [PKG...]`, `test-gui`,
> `validate`, `list`, `destroy`). `validate` performs the full cycle: sync the sources,
> build `saphir-lib` + `saphir-gui` with abuild, install the GUI-domain APKs, and boot
> the GUI bundle in DEVMODE (offscreen, local mosquitto) verifying the
> `Saphir is ready` marker in the API log. `build all` builds every buildable Saphir
> package in dependency order. `install` installs per domain (the appliance runs each
> package set in its own Safecor domain - see 8.3).

#### 8.1 APKBUILD update ✅ Done
- `setup/packages/saphir-gui/APKBUILD` verified: the refactoring introduced **no new dependencies**
- `requirements.txt` / `requirements-dev.txt` consistent with the refactored imports
- `saphir-gui.spec` (PyInstaller) validated during 8.2 — one bug found and fixed (see below)

#### 8.2 Build + DEVMODE boot ✅ Done (saphir-lib, saphir-gui)
- Built `saphir-lib` and `saphir-gui` in the Alpine 3.21.9 chroot (signed APKs)
- **Bug found & fixed**: the `saphir-gui` PyInstaller bundle failed at startup because
  `PySide6.QtNetwork` was only listed in `binaries` (which does not collect the Python
  module). It has been moved to `hiddenimports` in `saphir-gui.spec`.
- The GUI boots in DEVMODE (MQTT + mock components) and completes the boot sequence

#### 8.3 Full package build verification ✅ Done
- Built from a clean chroot world (`build all`): `saphir-splash`, `saphir-lib`, `saphir`,
  `saphir-gui`, `saphir-viewer`, `saphir-av-clamav`, `saphir-av-eset` — no build errors,
  missing dependencies, or import failures
- **Not buildable**: `saphir-container-eset` — it fetches an ESET binary from a URL that
  returns HTTP 404; the official CI skips it as well ("The container archive cannot be
  built on GitHub", see `.github/workflows/build-all.yml`). `saphir-av-eset` resolves its
  `saphir-container-eset` dependency from the official Saphir repository.
- GUI domain installed (`saphir-lib` + `saphir-gui`) and the bundle boots in DEVMODE
  (`Saphir is ready` marker)
- **Bugs found & fixed during 8.3**:
  - `saphir` APKBUILD had a stale sha512sum for `topology.json` (the file was updated in
    `7d7dcd5` without regenerating the checksums), so the package failed at unpack time.
    The official CI only masked it by running `abuild checksum` on the fly. Fixed in
    #144; the chroot script now runs `abuild checksum` before every build, as the CI does.
  - `saphir` (depends on `safecor-core` → `xen`) and `saphir-gui` (depends on
    `safecor-gui-base` → `xe-guest-utilities`) cannot be installed in the same world
    (`xen` and `xe-guest-utilities` conflict). On the appliance they live in separate
    Safecor domains; the script therefore installs per domain and all builds must happen
    before the install step.

**Validation**: 7/8 packages build successfully in the chroot (the 8th is blocked by a
dead upstream URL, skipped by the official CI too), the GUI domain installs and the bundle
boots in DEVMODE. The full scan cycle in DEVMODE is covered by the project test suite
(350 tests, see test baseline above).

#### 8.4 Follow-ups identified during validation
- **Deferred to CI integration**: the broker can disconnect idle clients on keepalive timeout
  (30 s). The mock AVs and the Safecor TCP `MqttClient` do not reconnect on mid-session
  disconnect (`on_connection_lost` is only set in the SERIAL_PORT branch), so QoS 0 analysis
  requests sent during the window are lost. To be addressed when the workflow tests run in CI.
- **ESET download URL is dead**: the `saphir-container-eset` APKBUILD fetches
  `https://download.eset.com/com/eset/apps/business/efs/linux/latest/eeau_x86_64.bin`,
  which currently 404s. The package needs its source updated (or a local mirror) before
  it can be built again.

---

### Phase 9: Documentation Debt ✅ DONE (commits 4038c13, cd727c6-era round 2)

**Goal**: Eliminate the code documentation debt accumulated over time.

**Done in two rounds**:
- Round 1 (`4038c13`): French comments translated, module docstrings added to all
  24 modules, class docstrings on the proxy/model classes, ~200 lines of
  commented-out dead code removed from `safecor_input_files_list_model.py`,
  `queue_list_proxy_model.py` (file later removed) and
  `safecor_input_files_list_proxy_model.py`.
- Round 2 (this round): the remaining class and method docstrings plus the
  dead code that survived round 1.

#### 9.1 Translate French comments to English ✅
- All French comments translated, including ones without accented characters
  (e.g. `Si c'est un fichier...`) that the accented-character grep missed.

#### 9.2 Add class-level docstrings ✅
- Every public class in `Saphir/` now has a docstring (enums, QML models,
  controllers, helpers).

#### 9.3 Add method docstrings for public API ✅
- Every public (non-underscore) method in `Saphir/` has a summary docstring,
  including all `@Slot` methods of `application_controller.py`, the Qt model
  interface methods (`rowCount`, `data`, `roleNames`, ...) and the property
  getters/setters.

#### 9.4 Remove dead commented-out code ✅
- Remaining commented-out debug prints, dead state transitions and dead API
  calls removed from `analysis_controller.py`, `application_controller.py`,
  `log_list_model.py`, `queue_list_model.py`, `messages_list_model.py`,
  `safecor_output_files_list_proxymodel.py`.

#### 9.5 Add module-level docstrings ✅
- Every `.py` file in `Saphir/` (24 modules, including `__init__.py`) has a
  one-line module docstring.

**Validation** (verified):
- `grep -r "#.*[éèàçûôî]" Saphir/` returns zero results (no French comments)
- AST check: every public class and public method in `Saphir/` has a docstring
- No commented-out code blocks remain (manual review + pattern grep)
- `ruff check` and `ruff format --check` pass on `src/Saphir/`
- Full test suite: 350 passed, 3 skipped
- Doxygen: no Doxygen config exists in the repository, so the Doxygen
  criterion is not applicable until a Doxygen setup is added (tracked as a
  follow-up, not blocking)

---

### Phase 10: Missing Features & NFRs Implementation ⏳ IN PROGRESS (10.1, 10.2, 10.3, 10.4, 10.5 done)

**Goal**: Implement the features and NFRs that are specified in `docs/features.md` and `docs/workflow-rules.md` but **not yet coded**. These are prerequisites for Phase 11 (functional coverage testing).

**Principle**: We cannot test what does not exist. This phase implements the missing behaviour so that Phase 11 can validate it.

#### 10.1 [P0] NFR-1: Fingerprint verification chain — ✅ Done (#145)

**Spec**: `features.md` NFR-1 — Saphir must verify fingerprint integrity at each step.

**Current state**: Safecor computes fingerprints automatically, but Saphir does **not** compare them between steps.

**Work**:
- In `TransferController.on_copy_file()`: compare the `fingerprint` in the copy response with the fingerprint stored in the file queue entry. If mismatch → mark file as `FileCopyError`, log the error.
- In `AnalysisController.__handle_result()`: verify the fingerprint returned by the AV matches the one stored in the queue. If mismatch → mark file as `FileError`.
- Store the source fingerprint in the file queue entry when the file is first copied to the repository (`NEW_FILE` notification).

**Files**: `transfer_controller.py`, `analysis_controller.py`, `file_queue.py` (add `fingerprint` field to file entries)

**Validation**: Unit tests verify mismatch → error status, match → normal flow.

**Implementation notes** (done):
- The repository copy step already stored the source fingerprint in the queue entry (`NEW_FILE` → `file["fingerprint"]`).
- The AV integrity check runs in the AV domain (the only place with access to the repository file): the GUI sends the recorded fingerprint in the `saphir/analysis/request` payload; `AbstractAntivirusController` computes the fingerprint of the repository file before the analysis and, on mismatch, publishes the response with a `fingerprint_error: true` flag (no analysis started). The GUI routes such responses to `__handle_error` → file marked `FileAnalysisError` (declared *Error* per NFR-1), chain continues.
- The copy-to-target check compares the `fingerprint` of the copy response with the recorded one; mismatch → `FileCopyError` + journal entry.
- When no fingerprint is recorded (or the file cannot be read) the check is skipped, preserving the previous behaviour (DEVMODE compatibility).

#### 10.2 [P0] Scenario 8.7: Report generation failure → `ReportFailed` — ✅ Done (#146)

**Spec**: `workflow-rules.md` §3.2 — `GeneratingReport → ReportFailed` on report failure. Permanent error state, reset required.

**Work**:
- In `ReportController`: emit a `reportFailed = Signal()` on exception (WeasyPrint error, disk full, I/O).
- In `ApplicationController.__on_transfer_complete()`: connect to `reportFailed` → `__set_system_state(SystemState.ReportFailed)` + user message.
- In `WorkflowController`: add `GeneratingReport → ReportFailed` to the valid transitions.
- Verify `reset()` works from `ReportFailed` (I9: counters/queue cleared).

**Files**: `report_controller.py`, `application_controller.py`, `workflow_controller.py`, `enums.py` (verify value)

**Validation**: Unit test: mock `make_report` to raise → state = `ReportFailed` → reset → `SystemReady`.

**Implementation notes** (done):
- `ReportFailed` did not exist in the enum (the plan's "value 11" was wrong — 11 is `GeneratingReport`); added as `SystemState.ReportFailed = 16` (appended, existing values untouched).
- `ReportController.reportFailed = Signal(str)` carries the error reason; emitted in the existing `except` branch alongside the journal error.
- `ApplicationController.__on_report_failed(reason)` sets the state and adds a user message ("The report generation failed. Please reset the system.").
- `__on_transfer_complete()` now stops after a failed generation (state no longer `GeneratingReport`): no report/journal copy, no crash on the missing PDF (previously an unhandled `FileNotFoundError`).
- `WorkflowController`: `GeneratingReport → ReportFailed` and `ReportFailed → {SystemResetting, SystemShuttingDown}`; reset from `ReportFailed` works (I9 — `reset()` uses `force_state` + `__reset_states`).
- `ReportFailed` added to the disk-handler locked states: disk changes are ignored while the system waits for a reset.
- Adjacent bug fixed: `MessagesListModel.__messages` was a class attribute (shared between instances); moved to `__init__`.

#### 10.3 [P1] Scenario 8.8: Source disconnection during analysis — ✅ Done (#147)

**Spec**: `workflow-rules.md` §8.8 — Analysis continues on repository files, error flag set, loop held, auto-resume on reconnection.

**Current state**: `__handle_disk_state` for source DISCONNECTED during `SystemAnalysisRunning` falls through to `__reset_states()` (if not used) or `SystemMustBeReset` (if used). **No error-flag / hold / resume logic exists.**

**Work**:
- Add `__source_disconnected_during_analysis` flag to `ApplicationController`.
- In `__handle_disk_state`: if state == `SystemAnalysisRunning` and source DISCONNECTED → set flag, emit user message, do NOT reset.
- In `AnalysisController`: when the flag is set, the analysis loop waits (does not request new files from the source) but continues processing files already in the repository.
- On source reconnection (same disk name): clear flag, resume requesting files.
- On source reconnection (different disk name): → `SystemMustBeReset` (NFR-4).

**Files**: `application_controller.py`, `analysis_controller.py`, `workflow_controller.py`

**Validation**: Integration test (emulator): start analysis, disconnect source, verify analysis continues on repo files, reconnect, verify resume.

**Implementation notes** (done):
- The hold is owned by the `AnalysisController` (it owns the copy loop): `sourceHoldChanged = Signal(bool)`, `__source_held` flag. On source DISCONNECTED while `AnalysisRunning` the `GettingFile` files are re-queued (`Undefined`, `locked=False`) so the loop holds; on reconnection they are re-requested.
- `__do_copy_files_into_repository` checks the hold at the top of each iteration (reschedule, no `read_file`); `__on_file_available` ignores duplicate `NEW_FILE` notifications (idempotency).
- `ApplicationController` guards `__handle_disk_state` (no reset while `AnalysisRunning`) and exposes `sourceDisconnected` (property + signal) for the QML banner; the flag is cleared on `stop_analysis()`/`reset()`.
- QML: warning banner in `AnalysisPanel` (visible when analyzing && source disconnected), EN/FR translations.
- Integration test `test_workflow_source_disconnection_analysis.py`: detach mid-analysis, no reset, re-attach, auto-resume, full nominal cycle.

#### 10.4 [P1] Scenario 8.6: Source/target disconnection during copy + auto-resume — ✅ Done (#148)

**Spec**: `workflow-rules.md` §8.6 — Error flag on `CopyCleanFiles`, auto-resume on same-disk reconnection, `SystemMustBeReset` on different disk.

**Current state**: Target disconnect → `SystemMustBeReset` (implemented in `d7df95b`). Source disconnect during copy → **not handled** (falls through to reset or ignored).

**Work**:
- Add `__copy_error_flag` to `TransferController`.
- In `ApplicationController.__handle_disk_state`: if state == `CopyCleanFiles`:
  - Source DISCONNECTED → set `__copy_error_flag`, emit message, **stay in `CopyCleanFiles`**.
  - Target DISCONNECTED → set `__copy_error_flag`, emit message, **stay in `CopyCleanFiles`**.
- In `TransferController`: when `__copy_error_flag` is set, pause the copy loop (do not request next file).
- On reconnection (same disk name): clear flag, resume copy from where it left off.
- On reconnection (different disk name): → `SystemMustBeReset` (NFR-4, I6).

**Files**: `application_controller.py`, `transfer_controller.py`, `workflow_controller.py`

**Validation**: Integration test: start copy, disconnect source, verify pause, reconnect same disk, verify resume; disconnect + reconnect different disk, verify `SystemMustBeReset`.

**Implementation notes** (done):
- The pause is owned by the `TransferController` (no dedicated state, per spec 8.6): `copyPausedChanged = Signal(bool)` + `coherenceCheckFailed = Signal(str)`, `is_copying`/`is_copy_paused` properties. It subscribes to `DISK_STATE` + `LIST_FILES/response` (via `init()`, called once the API is ready).
- The copy is request-driven (all `copy_file` requests are issued at once): a disconnected disk makes the in-flight requests fail silently, the files stay `FileClean` and are re-issued on resume — no copy error is declared while paused (`on_copy_file` keeps the file `FileClean` on a failed response while paused, and ignores stale failures for an already-copied file).
- Coherence check (8.6 step 4) on same-disk reconnection: recursive `LIST_FILES` on the re-inserted disk; the target is checked against the already-copied files (`FileCopySuccess`), the source against the remaining files (`FileClean`). Pass → the flag is cleared and the remaining files are re-copied. Fail (or a different disk re-plugged, NFR-4/I6) → `coherenceCheckFailed` → `SystemMustBeReset` + message.
- `ApplicationController`: guards in `__handle_disk_state` (source/target DISCONNECTED during an active copy → no reset, names kept; a CONNECTED disk while paused → ignored, the `TransferController` handles it), `copyPaused` property + user messages, `__handle_list_files` skips file listings while the copy is in progress (coherence-check responses).
- QML: status text "Copy paused: a storage was disconnected..." (warning color) in `FilesCopyPanel`, EN/FR translations.
- The pre-existing `test_workflow_bug_target_disconnection.py` (C.2) characterized the old behaviour (target disconnect → immediate `SystemMustBeReset`); it was rewritten to the 8.6 semantics (hold + auto-resume).
- Integration tests: `test_workflow_source_disconnection_copy.py` (source: hold + auto-resume; different disk → `SystemMustBeReset`) and the rewritten C.2 (target: hold + auto-resume). The copy phase is stretched with 40 × 30 MB files so the unplug lands mid-copy even on a loaded machine.

#### 10.5 [P1] NFR-3: AV engine failure during analysis — ✅ Done (#149)

**Spec**: `features.md` NFR-3 — If an AV fails during analysis: affected files get `Error` status, already-analyzed files keep status. If all AVs fail → abort.

**Current state**: `__check_components_availability` is only called on `DISCOVER_COMPONENTS/response` (at startup). **No re-check during analysis.** If an AV VM dies mid-analysis, the files wait forever for a second result.

**Work**:
- Subscribe to `ComponentsHelper` state changes during analysis (or poll on a timer).
- In `AnalysisController`: if an AV component transitions to `ERROR`/`OFF` during analysis:
  - Mark all files that were waiting for this AV's result as `FileError`.
  - If `len(available_avs) < ANTIVIRUS_NEEDED` → stop analysis, transition to `SystemWaitingForUserAction`.
- In `ApplicationController.__on_analysis_state_changed`: handle the abort case.

**Files**: `analysis_controller.py`, `application_controller.py`

**Validation**: Integration test: start analysis, simulate AV component going OFF, verify files get `Error` status, verify analysis stops if below `ANTIVIRUS_NEEDED`.

**Implementation notes**:
- Detection: an AV domain (or the platform for a dead domain) publishes its state on `DISCOVER_COMPONENTS/response` — the app already reacts to every response via `__check_components_availability`. The missing piece was the **reaction**: that method now detects the READY → non-READY transition of an engine **while `SystemAnalysisRunning`** and calls `AnalysisController.handle_av_failure(comp_id)`, then posts a user message (engine label + abort suffix).
- `AnalysisController.handle_av_failure(av_id) -> bool`: removes the engine from the (shared) `analysis_components` list **in place** (progress denominator stays consistent for future analyses), then marks `FileAnalysisError` the files that are not in a final state (Clean/Infected/Error) and were already sent to the engines (`FileAnalysing`/`FileAvailableInRepository`) — or all of them when aborting. If fewer than `ANTIVIRUS_NEEDED` engines remain, it calls `stop_analysis()` (state → `AnalysisStopped` → the app goes to `SystemWaitingForUserAction` via the existing `__on_analysis_state_changed`) and returns `True`; otherwise it returns `False` and the analysis continues with the surviving engines (files not yet sent will complete with the reduced consensus).
- Test infra: `MockAVManager.fail()` touches a flag file watched by the mock AV, which publishes `ComponentState.OFF` and exits — simulating the platform reporting a dead AV domain.
- Tests: 4 unit (`handle_av_failure`: abort + keep analyzed, continue with 3 engines, ignored when not running, unknown component), 2 app handlers (failure during analysis → AC notified + message + engine removed; not running → only disabled), 1 integration (emulator: AV OFF mid-analysis → `SystemWaitingForUserAction`, no `AnalysisCompleted`, no reset).
- Note: `ANALYSIS_COMPONENTS` in `test_analysis_controller.py` is a class attribute shared between tests; the controller now receives a `deepcopy` and the failure tests normalize their own copy, so in-place removals do not leak between tests. Filenames in the new tests are unique (`AvFail*.txt`) because the Api message callbacks are never cleared between tests and stale controllers must not find the paths.

#### 10.6 [P2] F4: Individual copy failure + final check

**Spec**: `features.md` F4 — Individual failure: copy continues, error reported. Final check: `copied == clean_count`, otherwise error.

**Current state**: `TransferController.on_copy_file` handles individual success/failure. **The final check is implicit** (transfer completes when `copied >= total`), but a mismatch (some copies failed) is not explicitly detected and reported.

**Work**:
- In `TransferController`: on transfer completion, if `copied_files_count < clean_files_total` → emit `transferError = Signal(int)` with the number of failures.
- In `ApplicationController`: on `transferError` → log the discrepancy, include in report.

**Files**: `transfer_controller.py`, `application_controller.py`

**Validation**: Unit test: 3 clean files, 1 fails → `transferError` emitted with count=1.

#### 10.7 [P2] F3: Pause/Resume with partial analysis

**Spec**: `workflow-rules.md` §8.2 — Pause suspends, resume picks up remaining files, already-analyzed files keep status.

**Current state**: `stop_analysis()` sets state to `AnalysisStopped`. `start_analysis()` restarts but **re-processes all files** (including already-analyzed ones). The "skip already-analyzed" logic is missing.

**Work**:
- In `AnalysisController.start_analysis()`: before processing, check each file's current status. If `FileClean` or `FileInfected` → skip (do not re-copy, do not re-analyze).
- Only enqueue files with status `FileStatusUndefined` or `FileAnalysing` (interrupted).

**Files**: `analysis_controller.py`

**Validation**: Integration test: analyze 1 of 3 files, stop, start again → verify only 2 files are processed.

#### 10.8 [P2] F1: Full-disk analysis (all partitions)

**Spec**: `features.md` F1 — "Scan all" mode must analyze **all partitions** of the media.

**Current state**: `start_full_analysis()` requests only the root `/` of the first disk. Multi-partition disks produce multiple "disk" entries in Safecor, but only the first is analyzed.

**Work**:
- In `start_full_analysis()`: iterate over **all** storages (partitions) from `StorageManager.get_storages()`, not just the source.
- Queue files from each partition root.
- Update `folders_to_query` count accordingly.

**Files**: `application_controller.py`, `storage_manager.py` (expose all partitions)

**Validation**: Unit test: 2-partition disk → files from both partitions are queued.

---

### Phase 11: Functional Coverage ⏳ PENDING

**Goal**: Increase functional coverage from ~58% (strict) to ≥ 80% by addressing the highest-priority gaps in error paths, NFRs, and disconnection scenarios.

**Current functional coverage** (2026-10-28):

| Category | Items | Covered | Partial | Not covered | Score |
|----------|:-----:|:-------:|:-------:|:-----------:|:-----:|
| Features (F1-F21) | 14 | 5 | 9 | 0 | 84% |
| NFRs (NFR-1/5) | 4 | 1 | 2 | 1 | 59% |
| Scenarios (8.1-8.8) | 8 | 1 | 5 | 2 | 50% |
| **Total** | **26** | **7** | **16** | **3** | **~58%** |

#### Sub-tasks (in decreasing priority order)

##### 11.1 [P0] Fingerprint integrity verification (NFR-1)
- **Gap**: No test verifies that Saphir compares fingerprints at each step (source→repository, repository→AV, repository→target)
- **Work**:
  - Add `test_fingerprint_verification.py`
  - Test that a fingerprint mismatch on copy→repository marks the file as `Error`
  - Test that a fingerprint mismatch on copy→target marks the file as `CopyError`
  - Test that a matching fingerprint chain passes through to `CopySuccess`
- **Files**: `tests/test_fingerprint_verification.py` (new), `analysis_helper.py` (if verification logic needs extraction)
- **Effort**: Medium (1 day)

##### 11.2 [P0] Report generation failure (Scenario 8.7)
- **Gap**: No test covers the `GeneratingReport → ReportFailed` transition
- **Work**:
  - Add test in `test_application_controller_handlers.py`: mock `ReportController.make_report` to raise an exception
  - Assert state transitions to `ReportFailed`
  - Assert that `reset()` from `ReportFailed` works
- **Files**: `tests/test_application_controller_handlers.py` (extend)
- **Effort**: Low (2h)

##### 11.3 [P1] Source disconnection during analysis (Scenario 8.8)
- **Gap**: No test covers source DISCONNECTED while `SystemAnalysisRunning`
- **Work**:
  - Add test: state = `SystemAnalysisRunning`, publish `DISK_STATE` with source `DISCONNECTED`
  - Assert analysis continues on repository files (AV not interrupted)
  - Assert error flag is set / user prompted to reconnect
  - Assert reconnection (same disk) clears the flag and analysis resumes
- **Files**: `tests/test_application_controller_handlers.py` (extend), `application_controller.py` (if handler needs the error-flag logic)
- **Effort**: Medium (1 day)

##### 11.4 [P1] Source/target disconnection during copy + auto-resume (Scenario 8.6)
- **Gap**: Only target disconnect → `SystemMustBeReset` is tested. Source disconnect during copy and the auto-resume path are not covered.
- **Work**:
  - Add test: state = `CopyCleanFiles`, source DISCONNECTED → error flag set, state stays `CopyCleanFiles`
  - Add test: source reconnected (same disk) → copy resumes automatically
  - Add test: source reconnected (different disk) → `SystemMustBeReset` (NFR-4)
- **Files**: `tests/test_application_controller_handlers.py` (extend), `transfer_controller.py` (if resume logic needs extraction)
- **Effort**: High (1-2 days)

##### 11.5 [P1] AV engine failure during analysis (NFR-3)
- **Gap**: No test covers an AV component transitioning to `ERROR`/`OFF` during an active analysis
- **Work**:
  - Add test: analysis running, one AV component state → `ERROR`
  - Assert affected files get `Error` status (not clean)
  - Assert already-analyzed files keep their status
  - Assert if both AVs fail → analysis aborts → `SystemWaitingForUserAction`
- **Files**: `tests/test_analysis_controller.py` (extend), `application_controller.py` (`__check_components_availability` during analysis)
- **Effort**: Medium (1 day)

##### 11.6 [P2] Pause/Resume with partial analysis (Scenario 8.2)
- **Gap**: Pause is tested, but resume with a partial queue (some files already analyzed) is not
- **Work**:
  - Add test: start analysis, analyze 1 of 3 files, pause
  - Assert remaining files are still in queue with pending status
  - Resume → assert only the 2 remaining files are analyzed
  - Assert the already-analyzed file keeps its status
- **Files**: `tests/test_analysis_controller.py` (extend)
- **Effort**: Medium (half day)

##### 11.7 [P2] Individual copy failure (F4 error handling)
- **Gap**: No test covers a single file copy failing while others succeed
- **Work**:
  - Add test: 3 clean files in queue, 1 copy returns `status != "ok"`
  - Assert failed file gets `CopyError` status
  - Assert other files continue copying
  - Assert `copied_files_count` reflects only successes
  - Assert final check detects mismatch (copied ≠ clean count)
- **Files**: `tests/test_transfer_controller.py` (extend)
- **Effort**: Low (2h)

##### 11.8 [P2] Target disconnect before analysis (F1)
- **Gap**: The "target disconnected before user made their choice → return to initial state" path is not explicitly tested
- **Work**:
  - Add test: no source set, no system_used, disk DISCONNECTED
  - Assert state remains `SystemReady` (no source to reset)
- **Files**: `tests/test_application_controller_handlers.py` (extend)
- **Effort**: Low (1h)

#### Target coverage after Phase 11

| Category | Before | After (target) |
|----------|:------:|:--------------:|
| Features | 84% | 90% |
| NFRs | 59% | 85% |
| Scenarios | 50% | 80% |
| **Total** | **~58%** | **≥ 80%** |

**Validation**:
- All new tests pass (`pytest tests/ -q`)
- Functional coverage recalculated ≥ 80% (strict formula)
- Code coverage remains ≥ 85%
- `test_workflow_nominal.py` still passes (no regression)

---

### Phase 12: GUI (QML) Test Coverage ⏳ PENDING

**Goal**: Add automated tests for the QML layer — bindings, panel visibility, state-driven UI transitions, and Python↔QML signal integration. The QML code is currently **untested** (0% coverage); regressions in visibility logic or bindings are only caught manually.

**Scope**: The GUI consists of:
- `MainScreen.qml` — layout container, panel switching
- `MainScreenUi.ui.qml` — declarative panel visibility bindings (Phase 5 output)
- `Bindings.qml` — derived properties (systemStateColor, status, etc.)
- `AnalysisPanel.qml` — analysis progress, ETA, pause button
- `FilesSelectionPanel.qml` — file browser, queue, filters
- `FilesCopyPanel.qml` — copy progress, target prompt
- `SystemLoadingPanel.qml` — boot/reset progress
- `TopBar.qml` — clock, battery, classification
- `LogDialog.qml`, `SystemInfoDialog.qml` — informational dialogs

#### 12.1 [P0] QML binding tests (panel visibility)

**Gap**: Phase 5 made panel visibility 100% declarative (bindings on `systemState`), but there is **no automated test** verifying that the correct panel is shown for each state.

**Approach**: Use `PySide6.QtTest` + `QQmlApplicationEngine` to load the QML, set `systemState` via the Python controller, and assert `visible` properties.

**Work**:
- Create `tests/test_qml_bindings.py`
- Fixture: load `MainScreenUi.ui.qml` with a mock `ApplicationController` (same pattern as handler tests)
- For each `SystemState` value: set state → assert which panel is `visible: true`
- Expected mapping:
  | State | Visible panel |
  |-------|--------------|
  | `SystemStarting`, `SafecorReady`, `SystemResetting` | `SystemLoadingPanel` |
  | `SystemReady`, `SystemWaitingForUserAction`, `SystemGettingFilesList` | `FilesSelectionPanel` |
  | `SystemAnalysisRunning`, `AnalysisCompleted` | `AnalysisPanel` |
  | `SystemWaitingForTarget`, `CopyCleanFiles`, `GeneratingReport` | `FilesCopyPanel` |
  | `SystemMustBeReset`, `ReportFailed` | `SystemMustBeReset` dialog |

**Files**: `tests/test_qml_bindings.py` (new)

**Effort**: Medium (1 day)

#### 12.2 [P0] Bindings.qml derived properties

**Gap**: `Bindings.qml` computes `systemStateColor`, status (Ready/Used/Dirty), and other derived values. **No tests** verify these computations.

**Work**:
- In `tests/test_qml_bindings.py`: load `Bindings.qml` with controlled inputs
- Test `systemStateColor` for each state
- Test status priority: Dirty > Used > Ready > Not ready
- Test the D8 bug fix: `infected: nbInfected > 0` (not `> 1`)
- Test `analysisReady` / `readyToAnalyze` derived conditions

**Files**: `tests/test_qml_bindings.py` (extend)

**Effort**: Low (half day)

#### 12.3 [P1] Python↔QML signal integration

**Gap**: Signals like `systemStateChanged`, `queueSizeChanged`, `infectedChanged`, `cleanChanged` are emitted by Python and consumed by QML. **No test** verifies the end-to-end signal path.

**Work**:
- In `tests/test_qml_signals.py`:
  - Load QML with a real `ApplicationController` (Api mocked)
  - Trigger a state change in Python → assert QML property updated
  - Enqueue a file → assert `queueSize` in QML updated
  - Simulate analysis result → assert `infectedFilesCount` / `cleanFilesCount` in QML updated
  - Simulate transfer progress → assert `transferProgress` in QML updated

**Files**: `tests/test_qml_signals.py` (new)

**Effort**: Medium (1 day)

#### 12.4 [P1] AnalysisPanel state transitions

**Gap**: The analysis panel shows different UI elements depending on analysis state (progress bar, ETA, pause button). **No test** verifies these transitions.

**Work**:
- In `tests/test_qml_bindings.py`:
  - State `SystemAnalysisRunning` → progress bar visible, pause button enabled, ETA visible
  - State `AnalysisCompleted` → progress bar at 100%, pause button hidden
  - `analysisReady == false` → start button disabled
  - `queueSize == 0` → start button disabled

**Files**: `tests/test_qml_bindings.py` (extend)

**Effort**: Low (half day)

#### 12.5 [P2] TopBar elements

**Gap**: Clock, battery level, plugged state, classification label. **No test** verifies these bindings.

**Work**:
- In `tests/test_qml_signals.py`:
  - Set `batteryLevel` → assert QML display updated
  - Set `plugged` → assert charger icon visible/hidden
  - Verify clock updates (timer-based, may need `QSignalSpy` with timeout)

**Files**: `tests/test_qml_signals.py` (extend)

**Effort**: Low (2h)

#### 12.6 [P2] SystemLoadingPanel progression

**Gap**: The loading panel shows progress (0→1.0) with step indicators. **No test** verifies the progression bindings.

**Work**:
- In `tests/test_qml_bindings.py`:
  - `systemLoadingProgress = 0.15` → step 1 active
  - `systemLoadingProgress = 0.5` → step 1 done, step 2 active
  - `systemLoadingProgress = 1.0` → all steps done, panel hidden
  - `systemState == SystemReady` → panel hidden

**Files**: `tests/test_qml_bindings.py` (extend)

**Effort**: Low (2h)

#### 12.7 [P2] Filter toggles (F17)

**Gap**: The three filter toggles (Clean, Infected, Waiting) in `FilesSelectionPanel`. **No test** verifies they correctly filter the proxy model.

**Work**:
- In `tests/test_qml_signals.py`:
  - Set filter `Clean = false` → assert proxy model excludes clean files
  - Set all filters to `true` → assert all files visible
  - Set all filters to `false` → assert no files visible

**Files**: `tests/test_qml_signals.py` (extend)

**Effort**: Low (2h)

#### GUI coverage target

| Layer | Before | After (target) |
|-------|:------:|:--------------:|
| Panel visibility bindings | 0% | 100% |
| Bindings.qml derived properties | 0% | 100% |
| Signal integration (Python→QML) | 0% | 80% |
| Panel state transitions | 0% | 80% |
| **Overall QML** | **0%** | **≥ 70%** |

**Prerequisites**:
- `PySide6` must support offscreen QML rendering (`QT_QPA_PLATFORM=offscreen`)
- QML files must be loadable in test environment (path setup in `conftest.py`)
- No display required (offscreen platform plugin)

**Validation**:
- All QML tests pass with `QT_QPA_PLATFORM=offscreen pytest tests/test_qml_*.py -q`
- No regression on existing tests
- Panel visibility is correct for all 15 `SystemState` values

---

### Phase 13: Viewer Modernization ⏳ PENDING

**Goal**: Bring the Viewer app to the same quality level as the main GUI — lint, format, type-annotate, and add unit tests. The viewer currently has **0 tests**, **50 ruff errors**, and no ruff config.

**Scope**: `python/viewer/` (15 Python files, ~850 lines core code, 0 tests)

| File | Lines | Role |
|------|:-----:|------|
| `Viewer/application_controller.py` | 521 | Main controller (MQTT, file listing, Office→PDF) |
| `Viewer/safecor_input_files_list_model.py` | 56 | QML file list model |
| `Viewer/safecor_input_files_list_proxy_model.py` | 37 | Filtered proxy model |
| `Viewer/enums.py` | 24 | FileType, ViewerState enums |
| `Viewer/constants.py` | 62 | ViewerConstants (topics, paths) |
| `Viewer/office_helper.py` | 38 | LibreOffice conversion helper |
| `Viewer/devmode_helper.py` | 25 | DEVMODE flag |
| `main.py` | 91 | Entry point (QML engine, event filter) |
| `Mock/*` | 5 files | DEVMODE mock controllers |

#### 13.1 [P0] Ruff lint & format

**Work**:
- Add `[tool.ruff]` section to `python/viewer/pyproject.toml` (same config as GUI: target py39, ignore RUF012/B008/N999)
- Run `ruff check --fix` to auto-fix import sorting, unused imports, `__all__` sorting
- Fix remaining manual issues:
  - Python 3.9 f-string syntax (line 345 `application_controller.py`)
  - SIM102 nested if, SIM114 combine branches
  - UP039 unnecessary parentheses after class definitions (4 files)
  - FA102 missing `from __future__ import annotations`
  - BLE001 in Mock (add `# noqa` — mock code)
- Run `ruff format` on all files
- Validate: `ruff check` + `ruff format --check` → 0 errors

**Files**: `pyproject.toml`, all 15 Python files

**Effort**: Low (2h)

#### 13.2 [P0] Unit tests — application_controller

**Gap**: `application_controller.py` (521 lines) has **0 tests**. It handles:
- MQTT topic subscriptions (file list, disk state)
- File type detection (image, video, audio, office, PDF)
- Office→PDF conversion via LibreOffice
- DEVMODE behavior

**Work**:
- Create `python/viewer/tests/test_application_controller.py`
- Tests:
  - `test_init`: controller creates with mocked Api, subscribes to expected topics
  - `test_file_type_detection`: each file extension maps to correct `FileType` enum
  - `test_on_files_list`: MQTT payload → model populated correctly
  - `test_on_disk_state`: disk state changes update `viewerState`
  - `test_office_conversion`: `office_helper` called for .docx/.xlsx/.pptx, not for .pdf
  - `test_devmode`: DEVMODE=1 uses mock data
- Mock strategy: same pattern as GUI (`patch("viewer.Viewer.application_controller.Api")`)
- Target: ≥ 85% coverage on `application_controller.py`

**Files**: `tests/test_application_controller.py` (new), `tests/conftest.py` (new)

**Effort**: Medium (1 day)

#### 13.3 [P1] Unit tests — models & enums

**Gap**: `safecor_input_files_list_model.py`, `safecor_input_files_list_proxy_model.py`, `enums.py` have no tests.

**Work**:
- In `tests/test_models.py`:
  - `SafecorInputFilesListModel`: add files, verify row count, data roles
  - `SafecorInputFilesListProxyModel`: filter by file type, verify visible rows
  - `FileType` enum: verify all values are unique and QML-compatible
  - `ViewerState` enum: verify state transitions are valid

**Files**: `tests/test_models.py` (new)

**Effort**: Low (half day)

#### 13.4 [P1] Unit tests — office_helper & constants

**Gap**: `office_helper.py` (LibreOffice conversion) and `constants.py` have no tests.

**Work**:
- In `tests/test_office_helper.py`:
  - `test_convert_docx_to_pdf`: mock LibreOffice subprocess, verify output path
  - `test_convert_non_office`: non-office files returned as-is
  - `test_tempfile_cleanup`: temp files are cleaned after conversion
- In `tests/test_constants.py`:
  - Verify all topic strings match the Safecor API spec
  - Verify `SUPPORTED_EXTENSIONS` covers all documented file types

**Files**: `tests/test_office_helper.py` (new), `tests/test_constants.py` (new)

**Effort**: Low (half day)

#### 13.5 [P2] main.py cleanup

**Gap**: `main.py` has 7 unused imports (copied from GUI `main.py` scaffold) and the event filter logic is untested.

**Work**:
- Remove unused imports (Qt, QEvent, QObject, QPointingDevice, QQuickWindow, qmlRegisterType, qmlRegisterSingletonType)
- Verify the event filter (touch vs mouse cursor) works correctly
- Add `# noqa: N999` or rename if the module name is flagged

**Files**: `main.py`

**Effort**: Low (1h)

#### Viewer coverage target

| Module | Before | After (target) |
|--------|:------:|:--------------:|
| `application_controller.py` | 0% | ≥ 85% |
| `safecor_input_files_list_model.py` | 0% | ≥ 85% |
| `safecor_input_files_list_proxy_model.py` | 0% | ≥ 85% |
| `enums.py` | 0% | 100% |
| `constants.py` | 0% | 100% |
| `office_helper.py` | 0% | ≥ 85% |
| **Overall viewer** | **0%** | **≥ 85%** |

**Prerequisites**:
- `python/viewer` needs a `tests/` directory and `conftest.py` (doesn't exist yet)
- `pyproject.toml` needs `pythonpath` config for pytest (same pattern as GUI)
- DEVMODE mock infrastructure already exists in `Viewer/Mock/`

**Validation**:
- `ruff check` + `ruff format --check` → 0 errors
- `DEVMODE=1 pytest tests/ -q` → all pass
- Coverage ≥ 85% on all viewer modules
- No regression on GUI tests (shared libsaphir)

---

### Phase 14: Semi-Automated Validation Environment ⏳ PENDING (blocked on Safecor emulator)

**Goal**: Let a **human** test Saphir in a **non-representative environment** (no appliance, no
physical USB disks) while using the **Safecor emulator** as the platform. The tester drives the
real Saphir GUI normally (mouse/keyboard) and, in parallel, **manipulates the emulator** to
trigger platform events (attach/detach storage, power state, language, domain restart…) and
**observes the system's internal state** (workflow state, analysis queue, clean/infected
counts, copy progress, ETA) to check the behavior against `docs/workflow-rules.md`.

**Context**:
- The Safecor emulator (Safecor repo, `python/emulator/`) emulates the appliance over MQTT
  (mock Dom0 + mock SysUSB + broker) and already exposes a **scripted** scenario API
  (`attach_disk()`, `detach_disk()`, `set_energy_state()`, …) used by the pytest
  integration tests. It is a headless test tool — there is no interactive, human-facing mode.
- What is missing for this semi-automated workflow:
  1. **Interactive control**: on-demand actions triggered by a human (not a test script).
  2. **State observation**: a live view of Saphir's internal state (the emulator currently
     observes the platform, not the Saphir application).
  3. **Side-by-side launch**: emulator + real Saphir GUI running together, documented and
     reproducible.

> **Dependency (blocking)**: the **Safecor emulator does not have these features yet**. The
> interactive control and/or observation hooks must be delivered in the **Saphir** repository
> first. Until then this phase is **Not ready** (see `docs/github-project-management.md`
> status semantics). The Saphir-side work below is only unblocked once the emulator support
> lands.

#### 14.1 [P0] Runbook + launch tooling
- **Gap**: running "emulator + real Saphir GUI" today is ad-hoc knowledge from the
  integration tests; there is no documented, one-command way to start the validation
  environment.
- **Work**:
  - A launcher script (e.g. `setup/emulator/run-validation-env.sh`) that starts the emulator
    (broker + mock components) and the Saphir GUI pointed at it, with the AV layer mocked
    (reuse the DEVMODE mock AVs if they can run alongside a real MQTT broker).
  - A runbook in `docs/` (steps, prerequisites, how to stop, how to read the state view).
- **Files**: `setup/emulator/` (new), `docs/` (new runbook)
- **Effort**: Low-Medium (1 day)

#### 14.2 [P0] Interactive emulator operator (human-facing)
- **Gap**: the scenario API is programmatic; a human has no way to trigger
  attach/detach/energy events on demand.
- **Work**: a small interactive console (CLI/TUI, or a minimal widget) wrapping the emulator
  scenario API: `attach source`, `detach source`, `attach target`, `power on/off`,
  `set language`, `restart domain`, plus a live log of the platform events sent.
- **Depends on**: emulator exposing its scenario API as a stable, external entry point.
- **Effort**: Medium (1-2 days, emulator side)

#### 14.3 [P1] Internal state observer
- **Gap**: the tester cannot see Saphir's internal state (workflow state, analysis queue,
  `nbClean`/`nbInfected`, copy progress, ETA) while manually driving the GUI.
- **Work**: a live state view. Options (pick one at design time):
  - (a) a dashboard/panel subscribing to the Saphir MQTT status topics (non-invasive);
  - (b) a debug endpoint in the GUI (e.g. a hidden "validation" overlay toggled by an env
    var) showing `SystemState`, queue size, counts, EMA ETA;
  - (c) structured logs with a human-readable state-transition line per transition.
- **Constraint**: must not change production behavior (flag/env-var gated, like DEVMODE).
- **Effort**: Medium (1-2 days)

#### 14.4 [P1] Manual scenario catalog
- **Gap**: no curated list of what a human should try in this environment, nor the expected
  workflow states per scenario.
- **Work**: a checklist of manual scenarios with expected `SystemState` transitions
  (cross-referenced with `docs/workflow-rules.md`):
  - Nominal cycle: attach source → analyze → attach target → copy → report → reset
  - Source disconnect during analysis; target disconnect during copy (bug C.2 path)
  - Power loss at boot / during scan; language change; domain restart
  - AV error path (mock AV forced failure)
- **Files**: `docs/` (new manual-scenarios doc)
- **Effort**: Low (half day)

**Validation**:
- A human completes the nominal end-to-end cycle and at least 3 error scenarios in the
  validation environment, using the operator console + state observer.
- Observed internal states match the state machine in `docs/workflow-rules.md` for every
  executed scenario.
- The environment is reproducible from the runbook on a clean machine.

**Dependencies**:
- **Safecor emulator** (external repo): interactive scenario API / observation hooks —
  **not yet implemented** (blocking for 14.2 and 14.3).
- Reuses the DEVMODE mock AV infrastructure for the antivirus layer.

**Estimated effort (Saphir side)**: ~3-4 days, once the emulator support is available.

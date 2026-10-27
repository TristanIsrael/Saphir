# Refactoring Plan - Saphir v3.x

> **Status**: Draft - To be reviewed and completed iteratively
> **Last updated**: 2026-10-27

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

### Phase 0: Foundation (No behavior changes)

**Goal**: Extract leaf controllers that have no dependencies on each other.

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

**Validation**: Run `pytest` + manual test - no observable behavior change.

---

### Phase 1: Stabilize State Machine

**Goal**: Replace scattered state transitions with a unified `WorkflowController`.

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
# CURRENT: Blocks disk notifications too early
if self.__system_state.value >= SystemState.CopyCleanFiles.value:
    return

# PROPOSED: Use explicit workflow phase
if self.workflow_controller.in_phase("post_transfer"):
    return
```

**Validation**: Full workflow test from boot to shutdown. All state transitions logged.

---

### Phase 2: Extract Data-Heavy Controllers

**Goal**: Move file/queue management out of `ApplicationController`.

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

### Phase 3: Extract Transfer Logic

**Goal**: Create dedicated `TransferController` for file copying.

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

### Phase 4: Clean Up Existing Controllers

**Goal**: Improve `AnalysisController` and `ReportController`.

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

### Phase 5: QML Cleanup (Views Last)

**Goal**: Simplify QML visibility logic to rely on `WorkflowController` signals.

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

1. **Should `SystemWaitingForDevice` be removed or activated?** - Currently dead code.
2. **Should archive mounting be fully removed or kept as a dormant feature?** - Currently disabled but code path exists.
3. **Should `handheld` property be made configurable or removed?** - Hardcoded to `True`.
4. **What is the intended behavior when user connects only one disk?** - System auto-assigns it as source (line 701-713), but this could conflict with reset state.
5. **Should `__on_analysis_state_changed` also drive state machine transitions?** - Currently it sets `SystemState` directly, bypassing `WorkflowController`.

---

## 8. Estimated Effort

| Phase | Lines Changed | Effort | Dependencies |
|-------|--------------|--------|--------------|
| Phase 0 | +400 / -200 | Low | None |
| Phase 1 | +300 / -150 | Medium | Phase 0 |
| Phase 2 | +350 / -400 | High | Phase 1 |
| Phase 3 | +200 / -150 | Medium | Phase 2 |
| Phase 4 | +100 / -100 | Low | Phase 2 |
| Phase 5 | -50 / +50 | Low | Phase 1 |
| **Total** | **+1400 / -1000** | **~3-4 weeks** | Sequential |

> **Note**: Effort assumes one developer familiar with the codebase. Pair programming recommended for Phase 1-2.

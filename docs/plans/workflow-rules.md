# Workflow Rules - Saphir

> **Status**: Draft - To be reviewed and completed iteratively
> **Last updated**: 2026-10-27

---

## 1. Overview

Saphir follows a deterministic state machine workflow from boot to shutdown. This document defines the canonical state sequence, transitions, invariants, and UI mappings. It serves as the contract between the `WorkflowController` and all other components.

---

## 2. System States

### 2.1 Canonical States

| Value | State | Description | Phase |
|-------|-------|-------------|-------|
| 0 | `SystemInactive` | System not yet started | Pre-boot |
| 1 | `SystemStarting` | Application initializing | Boot |
| 2 | `SafecorReady` | Core platform + AV engines ready | Boot |
| 3 | `SystemReady` | All components ready, waiting for media | Idle |
| 4 | `SystemGettingFilesList` | Retrieving file list from source | Pre-analysis |
| 5 | `SystemWaitingForUserAction` | Files loaded, user selects files to analyze | Pre-analysis |
| 6 | `SystemAnalysisRunning` | Antivirus analysis in progress | Analysis |
| 7 | `AnalysisCompleted` | All files analyzed, consensus reached | Post-analysis |
| 8 | `CopyCleanFiles` | Copying clean files to target disk | Transfer |
| 9 | `GeneratingReport` | PDF report + journal being written | Report |
| 10 | `SystemMustBeReset` | Workflow complete, reset required before reuse | Post-transfer |
| 11 | `SystemResetting` | VMs being destroyed/recreated | Reset |
| 12 | `SystemShuttingDown` | System powering off | Shutdown |

### 2.2 Deprecated / Removed States

These states are defined in `enums.py` but are **unreachable** and should be removed:

| State | Reason |
|-------|--------|
| `SystemWaitingForDevice` | Never set by any code path |
| `SystemNotClean` | Logic folded into `AnalysisCompleted` + UI color |
| `TransferFinished` | State transitioned directly to `SystemMustBeReset` |

---

## 3. Canonical State Transitions

### 3.1 State Machine Diagram

```
                           +----------------+
                           | SystemInactive |
                           +----------------+
                                  |
                                  v
                           +----------------+
                           |  SystemStarting|  (on boot)
                           +----------------+
                                  |
                                  v
                           +----------------+
     +<-------------------|  SafecorReady  |
     |                    +----------------+
     |                            |
     |                    +-------+--------+
     |                    | all components |
     |                    | ready + 2 AVs  |
     |                    +----------------+
     |                            |
     v                            v
+------------+           +----------------+
| SystemMust |           |   SystemReady  |
|  BeReset   |<----------+                |
+------------+           +----------------+
     |                            |
     | (reset triggered)           | (storage connected)
     v                            v
+----------------+        +----------------------+
| SystemResetting|        | SystemGettingFilesList|
+----------------+        +----------------------+
     |                            |
     | (complete)                 | (file list received)
     v                            v
+----------------+        +----------------------------+
|SystemShutting  |        | SystemWaitingForUserAction  |
|   Down         |        +----------------------------+
+----------------+                    |
         |                  (user confirms / starts analysis)
         |                           |
         |                           v
         |                  +----------------------+
         |                  | SystemAnalysisRunning |
         |                  +----------------------+
         |                           |
         |                   (all files analyzed)
         |                           |
         |                           v
         |                  +----------------------+
         |                  |  AnalysisCompleted   |
         |                  +----------------------+
         |                           |
         |                   (copy starts automatically)
         |                           |
         |                           v
         |                  +------------------+
         |                  |  CopyCleanFiles   |
         |                  +------------------+
         |                           |
         |                  (all copies done)
         |                           |
         |                           v
         |                  +----------------------+
         |                  | GeneratingReport     |
         |                  +----------------------+
         |                           |
         |                  (journal copied to target)
         |                           |
         |                           v
         |                  +----------------------+
         +------------------| SystemMustBeReset    |
                            +----------------------+
```

### 3.2 Transition Rules

Each transition has a **trigger** (event) and a **guard** (condition).

| From | To | Trigger | Guard |
|------|-----|---------|-------|
| `SystemInactive` | `SystemStarting` | App start | Always |
| `SystemStarting` | `SafecorReady` | MQTT ready + subscriptions complete | Always |
| `SafecorReady` | `SystemReady` | Disk controller + 2 AVs ready | `len(analysis_components) >= 2` |
| `SystemReady` | `SystemGettingFilesList` | First storage connected | `not system_used` |
| `SystemReady` | `SystemMustBeReset` | Storage connected after use | `system_used` |
| `SystemGettingFilesList` | `SystemWaitingForUserAction` | All folders queried | `folders_to_query == 0 && analyse_selection` |
| `SystemGettingFilesList` | `SystemAnalysisRunning` | All folders queried + whole-disk mode | `folders_to_query == 0 && analyse_whole` |
| `SystemWaitingForUserAction` | `SystemAnalysisRunning` | User clicks "Start Analysis" | `queue_size > 0` |
| `SystemWaitingForUserAction` | `SystemGettingFilesList` | User modifies queue | Always |
| `SystemAnalysisRunning` | `AnalysisCompleted` | All files have consensus result | `clean + infected == queue_size` |
| `AnalysisCompleted` | `CopyCleanFiles` | Auto-triggered | Always |
| `CopyCleanFiles` | `GeneratingReport` | All clean files copied | `copied == clean_count` |
| `GeneratingReport` | `SystemMustBeReset` | Journal.log copied to target | `disk == target_name && path == journal.log` |
| `SystemMustBeReset` | `SystemResetting` | User clicks Reset | Always |
| `SystemResetting` | `SystemReady` | All VMs restarted + states cleared | Always |
| Any | `SystemShuttingDown` | User clicks Shutdown | Always |

---

## 4. Phase Definitions

The workflow is divided into 6 phases. Each phase has an associated **loading progress** and **UI behavior**.

| Phase | States | Loading Progress | UI Behavior |
|-------|--------|-----------------|-------------|
| **Boot** | `SystemStarting` → `SafecorReady` | 0 → 0.33 | Loading panel, component discovery |
| **Ready** | `SystemReady` | 0.33 → 1.0 | File browser panel shown if storage connected |
| **Pre-Analysis** | `SystemGettingFilesList`, `SystemWaitingForUserAction` | 1.0 | File selection panel, queue visible |
| **Analysis** | `SystemAnalysisRunning` | 1.0 | Analysis progress, ETA, stop button |
| **Post-Analysis** | `AnalysisCompleted`, `CopyCleanFiles`, `GeneratingReport` | 1.0 | Copy progress, report generation |
| **Post-Transfer** | `SystemMustBeReset` | 1.0 | Reset/Shutdown dialog, messages |

---

## 5. Invariants

These rules are **always true** and must be enforced:

### I1: Source Disk Immutability
Once a source disk is set, it cannot be changed without a full reset.
```python
# Guard: prevent source change after workflow begins
if system_used:
    raise WorkflowError("Source disk locked, reset required")
```

### I2: Queue Completeness
Analysis cannot start until all files in the queue have been processed (status != Undefined).
```python
# Guard: analysis completion check
if clean_count + infected_count == queue_size:
    stop_analysis()
    transition_to(AnalysisCompleted)
```

### I3: Copy Only Clean Files
Only files with `status == FileClean` are copied to the target.
```python
# Verified in: __do_start_transfer()
for file in queued_files:
    if file.status == FileClean:
        copy_file(file.path)
```

### I4: Single Transfer per Cycle
Transfer starts automatically when analysis completes. User cannot trigger a second transfer without reset.

### I5: Report Generation is Atomic
Report + journal are generated sequentially. If report generation fails, the system enters an error state (to be defined).

### I6: Reset is Mandatory After Use
After `SystemMustBeReset`, the system will ignore new storage connections until reset is performed.
```python
# Guard: __handle_disk_state() line 640
if system_state >= CopyCleanFiles:
    return  # Ignore new disk events
```

### I7: Consensus Rule
A file is infected if **any** antivirus engine flags it. A file is clean only when **all** engines agree.
```python
# Defined in: analysis_helper.py evaluate_result_consensus()
infected = sum(result.success for result in results) < ANTIVIRUS_NEEDED
```

---

## 6. Error Handling

### 6.1 Defined Error States

| Error | Current Behavior | Target Behavior |
|-------|-----------------|-----------------|
| AV component goes offline during analysis | Not handled | Abort analysis, return to `SystemWaitingForUserAction` |
| Copy fails for a clean file | Counted in `copiedFilesCount` failure, continues | Log error, mark file, continue, report failure in PDF |
| Report generation fails | Exception crashes transfer | Log error, enter error state, allow retry |
| Target disk full | Not checked | Detect before copy, show error dialog |
| MQTT subscription fails | Silent | Retry (3x), show error, fallback to dev mode |

### 6.2 Recovery Paths

```
Analysis Error → SystemWaitingForUserAction (user retries)
Copy Error     → GeneratingReport (continue, log in report)
Report Error   → Error Dialog (user decides: retry or abort)
Reset Failed   → SystemMustBeReset (display error message)
```

---

## 7. UI State Mapping

The following table defines which panels/dialogs are visible per state. This should be the **sole** source of truth for UI visibility.

| State | File Selection | File Copy | Report | Reset Dialog | Shutdown Dialog | Analysis Panel |
|-------|---------------|-----------|--------|-------------|-----------------|----------------|
| `SystemStarting` | hidden | hidden | hidden | hidden | hidden | hidden |
| `SafecorReady` | hidden | hidden | hidden | hidden | hidden | hidden |
| `SystemReady` | **visible** | hidden | hidden | hidden | hidden | hidden |
| `SystemGettingFilesList` | visible (loading) | hidden | hidden | hidden | hidden | hidden |
| `SystemWaitingForUserAction` | **visible** | hidden | hidden | hidden | hidden | hidden |
| `SystemAnalysisRunning` | hidden | hidden | hidden | hidden | hidden | **visible** |
| `AnalysisCompleted` | hidden | **visible** | hidden | hidden | hidden | visible (stopped) |
| `CopyCleanFiles` | hidden | **visible** | hidden | hidden | hidden | hidden |
| `GeneratingReport` | hidden | visible (done) | **visible** | hidden | hidden | hidden |
| `SystemMustBeReset` | hidden | hidden | hidden | **visible** | hidden | hidden |
| `SystemResetting` | hidden | hidden | hidden | visible (loading) | hidden | hidden |
| `SystemShuttingDown` | hidden | hidden | hidden | hidden | **visible** | hidden |

---

## 8. Topic Ownership Matrix

Each MQTT topic has exactly **one** owner. This is enforced by the `ApiLifecycle` module.

| Topic Pattern | Owner | Direction | Purpose |
|--------------|-------|-----------|---------|
| `safecor/disk_state` | `StorageManager` | Subscribe | Disk connect/disconnect events |
| `safecor/list_disks/response` | `StorageManager` | Subscribe | Initial disk list |
| `safecor/list_files/response` | `FileBrowser` | Subscribe | File listing results |
| `safecor/discover_components/response` | `ApplicationController` | Subscribe | AV component discovery |
| `safecor/energy_state/response` | `EnergyMonitor` | Subscribe | Battery/plugged state |
| `safecor/system_info/response` | `ApplicationController` | Subscribe | System information |
| `safecor/create_file/response` | `ApplicationController` | Subscribe | Report/journal copy confirm |
| `safecor/copy_file/response` | `TransferController` | Subscribe | File copy results |
| `saphir/analysis/request` | `AnalysisController` | Publish | Request file analysis |
| `saphir/analysis/response` | AV domains | Publish | Analysis result |
| `saphir/analysis/status` | AV domains | Publish | Analysis progress |
| `saphir/analysis/error` | AV domains | Publish | Analysis errors |
| `saphir/analysis/resume` | `AnalysisController` | Publish | Start analysis |
| `saphir/analysis/stop` | `AnalysisController` | Publish | Stop analysis |
| `saphir/analysis/reset` | `AnalysisController` | Publish | Reset analysis state |

---

## 9. Scenarios

### 9.1 Normal Flow (Full Cycle)

```
1. Boot → SystemStarting → SafecorReady → SystemReady
2. Insert source USB → SystemGettingFilesList (whole-disk) or SystemWaitingForUserAction (selection)
3. User selects files → Queue populated
4. User clicks Start → SystemAnalysisRunning
5. Files copied to repository → analyzed → status updated
6. All files analyzed → AnalysisCompleted → CopyCleanFiles
7. Clean files copied to target → GeneratingReport
8. Report + journal copied → SystemMustBeReset
9. User clicks Reset → SystemResetting → SystemReady (cycle repeats)
```

### 9.2 Stop During Analysis

```
1. SystemAnalysisRunning
2. User clicks Stop → AnalysisController.stop_analysis()
3. SystemWaitingForUserAction (files already analyzed keep their status)
4. User can modify queue and restart
```

### 9.3 Post-Transfer Reconnection

```
1. SystemMustBeReset
2. User inserts new source USB → ignored (gate at line 640)
3. SystemMustBeReset dialog shown (Reset / Shutdown)
4. User clicks Reset → SystemResetting → SystemReady
5. SystemReady + new USB → SystemGettingFilesList (new cycle)
```

### 9.4 Single Disk Mode

```
1. SystemReady
2. Insert 1 USB → source auto-assigned (line 701-713)
3. Source becomes the only storage → file browsing enabled
4. After transfer → no target disk → transfer blocked?
```

> **TODO**: Clarify single-disk mode behavior. Currently the system allows file analysis but transfer requires a second disk.

---

## 10. Open Questions

1. **Single-disk mode**: What should happen when only one disk is inserted and analysis completes? Should transfer be blocked or should the report be generated without a target?
2. **Archive mounting**: Code exists but is disabled. Should it be removed entirely or kept as dormant code?
3. **SystemNotClean state**: The concept exists (infected files detected) but is represented by UI color, not a state. Should a dedicated state be added?
4. **Recovery from report failure**: Currently unhandled. Should the system retry, allow manual generation, or enter a permanent error state?
5. **Concurrent storage changes**: What if a disk is removed during analysis/copy? Currently `SystemAnalysisRunning` blocks `LIST_DISKS` handling (line 718-719), but `DISK_STATE` is not blocked.

---

## 11. Document Maintenance

This document should be updated whenever:
- A new state is added or removed
- A transition rule changes
- A new error handling path is added
- Topic ownership changes

**Review cadence**: Before each major release, review this document against the actual code behavior.

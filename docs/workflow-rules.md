# Workflow Rules - Saphir

> **Status**: Draft - To be reviewed and completed iteratively
> **Last updated**: 2026-10-28
> **v2 changes**: added `SystemWaitingForTarget` (waiting for the 2nd target after analysis), Stop / Reset / Copy-cancellation transitions, and the AV failure distinction (per-file error vs engine panic, NFR-3).
> **v2.1 changes**: decoupled file *selection* from AV readiness — a disk can be browsed/selected as soon as the disk-controller is ready and a disk is connected, even if the AV engines are not ready; the analysis trigger now requires the **ready-to-analyze** condition (AV engines ready + core ready + non-empty queue). Added the boot/start dialog sizing rule (large → small → hidden).
> **v2.2 changes**: removed the copy-decline / copy-cancel transitions — there is **no cancel button**; `SystemWaitingForTarget` is a **stable terminal-ish state** whose only exits are: insert a target disk, Reset, or Shutdown.
> **v2.3 changes**: renamed the analysis **Stop** button to **Pause** — there is **no hard stop**. Pausing suspends the analysis (files already analyzed keep their status) and the user can **resume** it later from the same state.

---

## 1. Overview

Saphir follows a deterministic state machine workflow from boot to shutdown. This document defines the canonical state sequence, transitions, invariants, and UI mappings. It serves as the contract between the `WorkflowController` and all other components.

---

## 2. System States

### 2.1 Canonical States

| Value | State | Description | Phase |
|-------|-------|-------------|-------|
| 0 | `SystemInactive` | System not yet started | Pre-boot |
| 1 | `SystemStarting` | Application and core platform initializing | Boot |
| 2 | `SafecorReady` | Core platform (Safecor components) ready | Boot |
| 3 | `SystemReady` | Core ready, waiting for media (AV engines **not** required) | Idle |
| 4 | `SystemGettingFilesList` | Retrieving file list from source | Pre-analysis |
| 5 | `SystemWaitingForUserAction` | Files loaded, user selects files to analyze | Pre-analysis |
| 6 | `SystemAnalysisRunning` | Antivirus analysis in progress | Analysis |
| 7 | `AnalysisCompleted` | All files analyzed, consensus reached | Post-analysis |
| 8 | `SystemWaitingForTarget` | Analysis done; **stable terminal-ish state** — wait for a target disk, or the user resets / shuts down (no cancel) | Post-analysis |
| 9 | `CopyCleanFiles` | Copying clean files to target disk | Transfer |
| 10 | `GeneratingReport` | PDF report + journal being written | Report |
| 11 | `SystemMustBeReset` | Workflow complete, reset required before reuse | Post-transfer |
| 12 | `SystemResetting` | VMs being destroyed/recreated | Reset |
| 13 | `SystemShuttingDown` | System powering off | Shutdown |

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

**Boxes** are states, **arrows** are transitions (labelled by their trigger).

```
      +---------------------+
      |    SystemInactive   |
      +---------------------+
               |  app start
               v
      +---------------------+
      |    SystemStarting   |
      +---------------------+
               |  boot done
               v
       +---------------------+
       |    SafecorReady     |
       +---------------------+
                |  core / disk-controller ready (AVs not required)
                v
       +---------------------+
       |    SystemReady      |
       +---------------------+
               |  storage connected (not used)
               v
      +-------------------------+
      |   SystemGettingFilesList|
      +-------------------------+
               |  file list received
               v
       +---------------------------+
       |  SystemWaitingForUserAction|
       +---------------------------+
                |  user starts analysis (ready-to-analyze)
                v
      +-------------------------+
      |  SystemAnalysisRunning  |
      +-------------------------+
               |  all files analyzed
               v
      +---------------------+
      |   AnalysisCompleted |
      +---------------------+
               |  no target yet
               v
      +-------------------------+
      |   SystemWaitingForTarget|
      +-------------------------+
               |  target inserted
               v
      +---------------------+
      |    CopyCleanFiles   |
      +---------------------+
               |  all copies done
               v
      +---------------------+
      |   GeneratingReport  |
      +---------------------+
               |  journal copied
               v
      +---------------------+
      |   SystemMustBeReset |
      +---------------------+
               |  user Reset
               v
      +---------------------+
      |    SystemResetting  |
      +---------------------+
               |  complete
               v
         (back to SystemReady)
```

**Cross-cutting transitions** — these leave or enter states from several points, so they are listed rather than drawn:

| Trigger | From | To |
|---------|------|-----|
| target already available (skip the wait) | `AnalysisCompleted` | `CopyCleanFiles` |
| user Pause / AV engine panic | `SystemAnalysisRunning` | `SystemWaitingForUserAction` |
| a different disk is plugged in (system already used) — NFR-4 | `SystemReady` | `SystemMustBeReset` |
| user Reset (only when no operation is running) | `SystemWaitingForUserAction`, `AnalysisCompleted`, `SystemWaitingForTarget`, `SystemMustBeReset` | `SystemResetting` |
| user Shutdown | **any state** | `SystemShuttingDown` |

### 3.2 Transition Rules

Each transition has a **trigger** (event) and a **guard** (condition).

| From | To | Trigger | Guard |
|------|-----|---------|-------|
| `SystemInactive` | `SystemStarting` | App start | Always |
| `SystemStarting` | `SafecorReady` | MQTT ready + subscriptions complete | Always |
| `SafecorReady` | `SystemReady` | Disk controller ready (core components operational) | Always (AV engines **not** required) |
| `SystemReady` | `SystemGettingFilesList` | First storage connected | `not system_used` (disk-controller ready + disk present) |
| `SystemReady` | `SystemMustBeReset` | A **different** storage connected after use | `system_used && disk_name != source_name` |
| `SystemGettingFilesList` | `SystemWaitingForUserAction` | All folders queried | `folders_to_query == 0 && analyse_selection` |
| `SystemGettingFilesList` | `SystemAnalysisRunning` | All folders queried + whole-disk mode | `folders_to_query == 0 && analyse_whole` |
| `SystemWaitingForUserAction` | `SystemAnalysisRunning` | User clicks "Start Analysis" | **ready-to-analyze**: AV engines ready + core ready + `queue_size > 0` |
| `SystemWaitingForUserAction` | `SystemGettingFilesList` | User modifies queue | Always |
| `SystemAnalysisRunning` | `AnalysisCompleted` | All files have a final status | `clean + infected + error == queue_size` |
| `SystemAnalysisRunning` | `SystemWaitingForUserAction` | User clicks **Pause** | Always (files keep their status; the analysis is suspended and can be **resumed**) |
| `SystemAnalysisRunning` | `SystemWaitingForUserAction` | AV **engine panic** (component `ERROR`/`OFF`) | Abort analysis immediately (NFR-3) |
| `AnalysisCompleted` | `CopyCleanFiles` | Auto-triggered | `target_available` |
| `AnalysisCompleted` | `SystemWaitingForTarget` | Auto-triggered | `not target_available` |
| `SystemWaitingForTarget` | `CopyCleanFiles` | Target disk inserted | `target_available` |
| `SystemWaitingForTarget` | `SystemResetting` | User clicks Reset | Always (no op running) |
| `CopyCleanFiles` | `GeneratingReport` | All clean files copied | `copied == clean_count` |
| `GeneratingReport` | `SystemMustBeReset` | Journal.log copied to target | `disk == target_name && path == journal.log` |
| `SystemWaitingForUserAction` | `SystemResetting` | User clicks Reset | Always (no op running) |
| `AnalysisCompleted` | `SystemResetting` | User clicks Reset | Always (no op running) |
| `SystemMustBeReset` | `SystemResetting` | User clicks Reset | Always |
| `SystemResetting` | `SystemReady` | All VMs restarted + states cleared | Always |
| Any | `SystemShuttingDown` | User clicks Shutdown | Always |

> **Ready-to-analyze** (the condition that enables the analysis trigger): the AV engines are ready (`len(analysis_components) >= ANTIVIRUS_NEEDED`) **and** the core Safecor components are ready **and** the queue is non-empty (`queue_size > 0`). File *selection* does **not** require the AV engines — it only needs the disk-controller ready and a disk connected. The "Start Analysis" button is **disabled** until this condition holds (view-state rule).
>
> **Reset rule**: Reset is allowed **only when no operation is running**. In practice it is relevant from the stable states where the system may be dirty — `SystemWaitingForUserAction`, `AnalysisCompleted`, `SystemWaitingForTarget`, `SystemMustBeReset` — and is **blocked** from `SystemAnalysisRunning`, `CopyCleanFiles`, and `GeneratingReport` (pause the running operation first). Resetting from `SystemReady` (nothing read yet) is a no-op.
>
> **No cancel**: there is **no cancel button** for the copy — neither before (from `SystemWaitingForTarget`) nor during (from `CopyCleanFiles`). The only exits from those states are: insert a target disk (→ `CopyCleanFiles`), **Reset**, or **Shutdown**. `SystemWaitingForTarget` is therefore a **stable terminal-ish state** the user may stay in (the summary screen `FilesCopyPanel` is shown, prompting to insert a target).

---

## 4. Phase Definitions

The workflow is divided into 6 phases. Each phase has an associated **loading progress** and **UI behavior**.

| Phase | States | Loading Progress | UI Behavior |
|-------|--------|-----------------|-------------|
| **Boot** | `SystemStarting` → `SafecorReady` | 0 → 0.33 | Loading panel, component discovery |
| **Ready** | `SystemReady` | 0.33 → 1.0 | File browser panel shown if storage connected |
| **Pre-Analysis** | `SystemGettingFilesList`, `SystemWaitingForUserAction` | 1.0 | File selection panel, queue visible |
| **Analysis** | `SystemAnalysisRunning` | 1.0 | Analysis progress, ETA, **pause** button |
| **Post-Analysis** | `AnalysisCompleted`, `SystemWaitingForTarget`, `CopyCleanFiles`, `GeneratingReport` | 1.0 | "Insert target" prompt (when waiting), copy progress, report generation |
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
Transfer starts automatically when analysis completes **and a target disk is available**; otherwise the system waits in `SystemWaitingForTarget`. The user cannot trigger a second transfer without a reset.

### I5: Report Generation is Atomic
Report + journal are generated sequentially. If report generation fails, the system enters an error state (to be defined).

### I6: Locking After Use (dirty state)
Once the system is dirty (a file has been read), connecting a **different** storage locks the system into `SystemMustBeReset`; reconnecting the **same** storage (same disk name) is allowed to continue. This applies from `AnalysisCompleted` onward, not only from `SystemMustBeReset`.
```python
# Target guard: based on system_used + disk-name comparison, NOT a numeric state value
if system_used and disk_name != source_name:
    lock_into(SystemMustBeReset)
```
> **Note**: the current code uses a fragile numeric gate (`system_state >= CopyCleanFiles`, `__handle_disk_state` line 640). It must be replaced by an explicit "post-analysis phase + disk-name" check that also covers `SystemWaitingForTarget`.

### I7: Consensus Rule
A file is infected if **any** antivirus engine flags it. A file is clean only when **all** engines agree. A file whose analysis returned an **error** is "not clean" (not copyable), but its error does not abort the analysis.
```python
# Defined in: analysis_helper.py evaluate_result_consensus()
infected = sum(result.success for result in results) < ANTIVIRUS_NEEDED
```

### I8: Reset Only When Idle
Reset is allowed **only when no operation is running**. It is blocked from `SystemAnalysisRunning`, `CopyCleanFiles`, and `GeneratingReport`; the user must pause the running operation first (F10).

---

## 6. Error Handling

### 6.1 Defined Error States

| Error | Current Behavior | Target Behavior |
|-------|-----------------|-----------------|
| Per-file analysis error (one engine errors) | Not handled (`__handle_error` is a no-op) | File → `Error` status (not clean); analysis **continues** (NFR-3) |
| AV **engine panic** (component `ERROR`/`OFF`) | Not handled | **Abort** analysis immediately → `SystemWaitingForUserAction` (NFR-3) |
| Copy fails for a clean file | Counted in `copiedFilesCount` failure, continues | Log error, mark file, continue, report failure in PDF; final check `copied == clean_count` (F4) |
| Source disk disconnected during copy | Not handled (uncertain state) | Interrupt copy, prompt to re-insert; **auto-resume** after match verification (F4) |
| Report generation fails | Exception crashes transfer | Log error, enter error state, allow retry |
| Target disk full | Not checked | Detect before copy, show error dialog |
| MQTT subscription fails | Silent | Retry (3x), show error, fallback to dev mode |

### 6.2 Recovery Paths

```
Per-file analysis error  → stays in SystemAnalysisRunning (file → Error), completes to AnalysisCompleted
AV engine panic          → SystemWaitingForUserAction (abort, user retries)
Copy error (single file) → continue, log in report (CopyCleanFiles → GeneratingReport)
Source disconnected      → pause CopyCleanFiles, auto-resume on re-insertion (match verified)
Report error             → Error Dialog (user decides: retry or abort)
Reset failed             → SystemMustBeReset (display error message)
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
| `AnalysisCompleted` | hidden | **visible** | hidden | hidden | hidden | visible (finished / paused) |
| `SystemWaitingForTarget` | hidden | **prompt (insert target)** | hidden | hidden | hidden | hidden |
| `CopyCleanFiles` | hidden | **visible** | hidden | hidden | hidden | hidden |
| `GeneratingReport` | hidden | visible (done) | **visible** | hidden | hidden | hidden |
| `SystemMustBeReset` | hidden | hidden | hidden | **visible** | hidden | hidden |
| `SystemResetting` | hidden | hidden | hidden | visible (loading) | hidden | hidden |
| `SystemShuttingDown` | hidden | hidden | hidden | hidden | **visible** | hidden |

### 7.1 Boot/start dialog (SystemLoadingPanel) — size & visibility

The **`SystemLoadingPanel`** is an overlay (not a panel) shown while the system comes up. Two of its properties are driven by the workflow (see `MainScreenUi.ui.qml`):

- **Size** — `height` is `implicitHeight` (the large splash) when the state is one of `SystemInactive`, `SystemStarting`, `SystemResetting`; otherwise `60` (a small top strip). So it is **large during boot / reset** and **small (a top strip) once the core is ready** (`SafecorReady` onward).
- **Visibility** — `opacity` is `1.0` while the AV engines are **not** ready and `0.0` once they are, with a 1000 ms fade. So it is **hidden as soon as the AV engines are ready**.

Both are pure functions of the workflow state + the `analysisReady` binding, so they stay within the view-state rule (the view binds to a derived property, it does not compute it).

> **Intention vs. as-is**: the intended sizing is “large until a disk is detected, small once a disk is connected”. The as-is implementation keys the size on the **state** (large during `SystemStarting`, small from `SafecorReady`), which is functionally equivalent because a disk is only reachable once the core is ready. Requiring exact “disk-detected” sizing can be a follow-up (see `gui-backlog.md`).

---

## 8. Scenarios

### 8.1 Normal Flow (Full Cycle)

```
1. Boot → SystemStarting → SafecorReady → SystemReady (core / disk-controller ready; AV engines **not** required)
2. Insert source USB → SystemGettingFilesList (whole-disk) or SystemWaitingForUserAction (selection)
   - Boot dialog (SystemLoadingPanel): **large** during boot (`SystemStarting`) → **small top strip** once the core is ready (`SafecorReady` onward, while the AV engines are not ready) → **hidden** once the AV engines are ready.
3. User selects files → Queue populated (possible even if the AV engines are not ready yet)
4. User clicks Start (enabled once **ready-to-analyze**: AV ready + core ready + queue non-empty) → SystemAnalysisRunning
5. Files copied to repository → analyzed → status updated
6. All files analyzed → AnalysisCompleted → (target available) → CopyCleanFiles
7. Clean files copied to target → GeneratingReport
8. Report + journal copied → SystemMustBeReset
9. User clicks Reset → SystemResetting → SystemReady (cycle repeats)
```

### 8.2 Pause / Resume During Analysis

```
1. SystemAnalysisRunning
2. User clicks **Pause** → AnalysisController.stop_analysis() (the analysis is suspended)
3. SystemWaitingForUserAction (files already analyzed keep their status)
4. User can modify the queue, then click **Start** to **resume** the analysis (remaining files are picked up; already-analyzed files keep their status)
```

### 8.3 Post-Transfer Reconnection

```
1. SystemMustBeReset
2. User inserts new source USB → ignored (gate at line 640)
3. SystemMustBeReset dialog shown (Reset / Shutdown)
4. User clicks Reset → SystemResetting → SystemReady
5. SystemReady + new USB → SystemGettingFilesList (new cycle)
```

### 8.4 Single Disk Mode (target inserted later)

```
1. SystemReady
2. Insert 1 USB → source auto-assigned
3. Source becomes the only storage → file browsing + analysis enabled
4. Analysis completes → AnalysisCompleted → SystemWaitingForTarget (no target yet)
5a. User inserts the target → CopyCleanFiles → ... → SystemMustBeReset
5b. User does not plug a target and clicks Reset → SystemResetting → SystemReady (no copy, no report)
```

> **Resolved**: the waiting is modelled by `SystemWaitingForTarget`. Analysis works on a single disk; copy and report require a second disk (F1, F4).

### 8.5 End of Cycle Without Copy

```
1. ... → AnalysisCompleted → SystemWaitingForTarget (no target)
2. User does not plug a target; clicks Reset (no copy, no report)
3. → SystemResetting → SystemReady
```

### 8.6 Source Disconnection During Copy

```
1. CopyCleanFiles in progress
2. User unplugs the source → copy interrupted, error prompt shown
3. User re-inserts the source (same disk name, match verified)
4. Copy resumes automatically → continues to GeneratingReport
```

---

## 9. Open Questions

1. **Single-disk mode** — **Resolved** by `SystemWaitingForTarget` (scenario 8.4): analysis works on one disk; copy and report require a second disk.
2. **Archive mounting**: Code exists but is disabled. Should it be removed entirely or kept as dormant code?
3. **SystemNotClean state**: The concept exists (infected files detected) but is represented by UI color, not a state. Should a dedicated state be added?
4. **Recovery from report failure**: Currently unhandled. Should the system retry, allow manual generation, or enter a permanent error state?
5. **Source disconnection during copy**: Scenario 8.6 defines the target behavior (pause + auto-resume on re-insertion). To decide: model it as a sub-state of `CopyCleanFiles` or a dedicated state.

---

## 10. Document Maintenance

This document should be updated whenever:
- A new state is added or removed
- A transition rule changes
- A new error handling path is added

> **Scope**: this document is the contract of the **state machine** only. MQTT topic ownership is maintained separately in [`architecture.md` §4.2](architecture.md).

**Review cadence**: Before each major release, review this document against the actual code behavior.

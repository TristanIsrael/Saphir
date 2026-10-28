# Workflow Rules - Saphir

> **Status**: Stable
> **Last updated**: 2026-10-28
> **v2 changes**: added `SystemWaitingForTarget` (waiting for the 2nd target after analysis), Stop / Reset / Copy-cancellation transitions, and the AV failure distinction (per-file error vs engine panic, NFR-3).
> **v2.1 changes**: decoupled file *selection* from AV readiness — a disk can be browsed/selected as soon as the disk-controller is ready and a disk is connected, even if the AV engines are not ready; the analysis trigger now requires the **ready-to-analyze** condition (AV engines ready + core ready + non-empty queue). Added the boot/start dialog sizing rule (large → small → hidden).
> **v2.2 changes**: removed the copy-decline / copy-cancel transitions — there is **no cancel button**; `SystemWaitingForTarget` is a **stable terminal-ish state** whose only exits are: insert a target disk, Reset, or Shutdown.
> **v2.3 changes**: renamed the analysis **Stop** button to **Pause** — there is **no hard stop**. Pausing suspends the analysis (files already analyzed keep their status) and the user can **resume** it later from the same state.
> **v3 changes**: added the `ReportFailed` permanent error state (report failure, #4); reviewed and fixed the invariants (I2 completion guard, I5 report failure, I7 consensus, added I9 reset idempotence); completed the error-handling matrix (source/target disconnection during copy **and** analysis, MQTT transport, power loss); added scenarios 8.6–8.8; resolved all open questions (§9). **Contract fully reviewed and validated.**

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
| 11 | `ReportFailed` | Report generation failed — **permanent error state**, reset required (no auto-retry, #4) | Error |
| 12 | `SystemMustBeReset` | Workflow complete, reset required before reuse | Post-transfer |
| 13 | `SystemResetting` | VMs being destroyed/recreated | Reset |
| 14 | `SystemShuttingDown` | System powering off | Shutdown |

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

   Error branch (#4):
   GeneratingReport --report failed--> ReportFailed --user Reset--> SystemResetting
```

**Cross-cutting transitions** — these leave or enter states from several points, so they are listed rather than drawn:

| Trigger | From | To |
|---------|------|-----|
| target already available (skip the wait) | `AnalysisCompleted` | `CopyCleanFiles` |
| user Pause / AV engine panic | `SystemAnalysisRunning` | `SystemWaitingForUserAction` |
| a different disk is plugged in (system already used) — NFR-4 | `SystemReady` | `SystemMustBeReset` |
| user Reset (only when no operation is running) | `SystemWaitingForUserAction`, `AnalysisCompleted`, `SystemWaitingForTarget`, `SystemMustBeReset`, `ReportFailed` | `SystemResetting` |
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
| `GeneratingReport` | `ReportFailed` | Report generation fails | Permanent error state, reset required (#4) |
| `ReportFailed` | `SystemResetting` | User clicks Reset | Always |
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

### 3.3 Derived conditions (not states)

These are **not** workflow states. They are **derived booleans** computed from the live component states and the queue; they *gate* transitions and drive UI bindings, but they are never stored as the system state and are never changed by the `WorkflowController`.

| Condition | Definition | Gates / drives |
|-----------|------------|----------------|
| `coreReady` | The core Safecor components (incl. the disk-controller) are ready | Enables file **selection** (a disk can be browsed) |
| `analysisReady` | `coreReady` **and** `len(analysis_components) >= ANTIVIRUS_NEEDED` (all required AV engines connected & ready) | `SystemLoadingPanel` opacity (1.0 → 0.0), "Start Analysis" `enabled` |
| `readyToAnalyze` | `analysisReady` **and** `queue_size > 0` | Guard of `SystemWaitingForUserAction → SystemAnalysisRunning` |

> **Why not a state?** Component readiness (especially the AV VMs) is **asynchronous and parallel** — it becomes true at a moment with no guaranteed order relative to the sequential cycle (the AVs may be ready *before* a disk is plugged, or *while* the user is selecting). Modelling it as a sequential state would impose a false order and add an async components→state transition without benefit. The **state** describes *where in the cycle* the system is; a **condition** *enables* a transition from that state. This is also what the v2.1 decoupling relies on: selection needs `coreReady` + a disk only; analysis additionally needs `analysisReady`.
>
> **Refactoring note (D7)**: the current code reaches `SystemReady` only when `analysisReady` (core **and** AV) is true (`application_controller.py:622-623`). After the refactor, `SystemReady` is reached as soon as **`coreReady`** holds; `analysisReady` remains a distinct derived condition that gates analysis.

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
The analysis **completes** only when every file in the queue has a final status (`Clean` / `Infected` / `Error`).
```python
# Guard: analysis completion check
if clean_count + infected_count + error_count == queue_size:
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
Report + journal are generated sequentially. If report generation fails, the system enters the **`ReportFailed`** state (§2); a **Reset** is required (no automatic retry — decision #4).

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
clean = all(entry["result"] != "Infected" for entry in results.values())
infected = not clean
```

### I8: Reset Only When Idle
Reset is allowed **only when no operation is running**. It is blocked from `SystemAnalysisRunning`, `CopyCleanFiles`, and `GeneratingReport`; the user must pause the running operation first (F10).

### I9: Reset is Idempotent
A **Reset** always returns the system to its **initial state**: state `SystemReady`, queue empty, all counters zero, and the visual status back to **Ready** (§7.2). Resetting an already-clean system is a no-op.

---

## 6. Error Handling

### 6.1 Defined Error States

| Error | Current Behavior | Target Behavior |
|-------|-----------------|-----------------|
| Per-file analysis error (one engine errors) | Not handled (`__handle_error` is a no-op) | File → `Error` status (not clean); analysis **continues** (NFR-3) |
| AV **engine panic** (component `ERROR`/`OFF`) | Not handled | **Abort** analysis immediately → `SystemWaitingForUserAction` (NFR-3) |
| Copy fails for a clean file | Counted in `copiedFilesCount` failure, continues | Log error, mark file, continue, report failure in PDF; final check `copied == clean_count` (F4) |
| Source disk disconnected during copy | Not handled (uncertain state) | Stay in `CopyCleanFiles` with an **error flag** (no dedicated state); pause the copy and prompt to re-insert; on re-insertion, run a **coherence check** (source state + integrity/fingerprint) and clear the flag → **auto-resume**. No reset, no re-analysis (F4) |
| **Target** disk disconnected during copy | Not handled | Same as the source: **error flag** on `CopyCleanFiles`, pause, prompt to re-insert, **coherence check** on re-insertion, **auto-resume** (F4) |
| Source disk disconnected during **analysis** | Not handled | Analysis **continues** on files already in the repository (AV engines are **not** interrupted); an **error flag** is set and a dialog prompts the user to re-connect the source. The analysis loop is **held** (waiting) so it does not exit prematurely; it resumes when the source is re-connected (F1/NFR-3) |
| Report generation fails | Exception crashes transfer | Log error, enter the **`ReportFailed`** state (§2); **Reset required**, no automatic retry (F6/NFR-1) |
| Target disk full | Not checked | Detect before copy, show error dialog |
| MQTT subscription fails | Silent | Retry (3x), show error. **No fallback** — the transport is environment-specific and exclusive (production: **serial port**; dev: **TCP**) |
| Power loss / crash | Not handled | The system is **stateless**: a reboot returns it to the **initial state** (Ready); no dedicated recovery state |

### 6.2 Recovery Paths

```
Per-file analysis error  → stays in SystemAnalysisRunning (file → Error), completes to AnalysisCompleted
AV engine panic          → SystemWaitingForUserAction (abort, user retries)
Source disconnected (analysis) → stays in SystemAnalysisRunning (AV continues on the repository); error flag + dialog; held until the source is re-connected, then resumes
Copy error (single file) → continue, log in report (CopyCleanFiles → GeneratingReport)
Source disconnected (copy) → stays in CopyCleanFiles with an error flag; on re-insertion, coherence check (state + integrity) then auto-resume
Target disconnected      → stays in CopyCleanFiles with an error flag; on re-insertion, coherence check then auto-resume
Report error             → ReportFailed (reset required, no auto-retry)
Reset failed             → SystemMustBeReset (display error message)
Power loss / crash       → reboot → initial state (Ready); stateless, no recovery state
```

---

## 7. UI State Mapping

The following table defines which panels/dialogs are visible per state. This should be the **sole** source of truth for UI visibility. Columns are ordered by **chronological appearance** (boot → shutdown). The broader UI reference (principles, theming, system visual status, localization) is centralised in [`gui.md`](gui.md).

**One screen at a time** — at most **one** of the screen columns (File Selection, Analysis Panel, File Copy, Shutdown Dialog) is visible per state. The `SystemLoadingPanel` is an **overlay** (see §7.1), not a screen, so it may be shown on top of a screen. The **Report** is not an on-screen element (it is a generated PDF file), and the **Reset** confirmation is a transient dialog (not a per-state view), so neither is a column.

> **`AnalysisCompleted` is transient**: it immediately auto-transitions to `CopyCleanFiles` (target available) or `SystemWaitingForTarget` (no target). The screen shown is the **copy screen** (`FilesCopyPanel`), which prompts to **insert a target** to start the copy — so `AnalysisCompleted` and `SystemWaitingForTarget` show the **same** screen. The analysis progress panel is **not** shown once the analysis is finished.
>
> **`ReportFailed`** is a **permanent error state** (#4): the report generation failed and the system requires a **Reset** (no automatic retry). All screen columns are hidden; the user sees an error indication (transient dialog) prompting a Reset, as with `SystemMustBeReset`.

| State | SystemLoadingPanel | File Selection | Analysis Panel | File Copy | Shutdown Dialog |
|-------|--------------------|---------------|---------------|-----------|-----------------|
| `SystemStarting` | **visible (large)** | hidden | hidden | hidden | hidden |
| `SafecorReady` | visible (small) | hidden | hidden | hidden | hidden |
| `SystemReady` | visible (small) | **visible** | hidden | hidden | hidden |
| `SystemGettingFilesList` | hidden | visible (loading) | hidden | hidden | hidden |
| `SystemWaitingForUserAction` | hidden | **visible** | hidden | hidden | hidden |
| `SystemAnalysisRunning` | hidden | hidden | **visible** | hidden | hidden |
| `AnalysisCompleted` | hidden | hidden | hidden | **visible (insert target)** | hidden |
| `SystemWaitingForTarget` | hidden | hidden | hidden | **prompt (insert target)** | hidden |
| `CopyCleanFiles` | hidden | hidden | hidden | **visible** | hidden |
| `GeneratingReport` | hidden | hidden | hidden | visible (done) | hidden |
| `ReportFailed` | hidden | hidden | hidden | hidden | hidden |
| `SystemMustBeReset` | hidden | hidden | hidden | hidden | hidden |
| `SystemResetting` | **visible (large)** | hidden | hidden | hidden | hidden |
| `SystemShuttingDown` | hidden | hidden | hidden | hidden | **visible** |

### 7.1 Boot/start dialog (SystemLoadingPanel) — size & visibility

The **`SystemLoadingPanel`** is an overlay (not a panel) shown while the system comes up. Two of its properties are driven by the workflow (see `MainScreenUi.ui.qml`):

- **Size** — `height` is `implicitHeight` (the large splash) when the state is one of `SystemInactive`, `SystemStarting`, `SystemResetting`; otherwise `60` (a small top strip). So it is **large during boot / reset** and **small (a top strip) once the core is ready** (`SafecorReady` onward).
- **Visibility** — `opacity` is `1.0` while the AV engines are **not** ready and `0.0` once they are, with a 1000 ms fade. So it is **hidden as soon as the AV engines are ready**.

Both are pure functions of the workflow state + the `analysisReady` binding, so they stay within the view-state rule (the view binds to a derived property, it does not compute it).

> **Intention vs. as-is**: the intended sizing is “large until a disk is detected, small once a disk is connected”. The as-is implementation keys the size on the **state** (large during `SystemStarting`, small from `SafecorReady`), which is functionally equivalent because a disk is only reachable once the core is ready. Requiring exact “disk-detected” sizing can be a follow-up (see `gui-backlog.md`).

### 7.2 System visual status (not a workflow state)

Beyond the per-state screens, the **whole application** carries a *visual status* of the system, expressed through the **background image** (`imgBack`) and a **color filter** (`backFilter`). This status tells the user **whether the system is clean, has been used, or has found a threat**. It is about the *content* of the system, not *where in the cycle* it is, so it is **orthogonal to the workflow states** — it is a derived visual (like the §3.3 conditions), not a `SystemState`.

There are **three** system statuses (plus the *not-ready* boot phase):

| Visual status | Meaning | Condition (derived) | Background image (light theme) | Color filter |
|---------------|---------|---------------------|--------------------------------|--------------|
| **Not ready** | System coming up (boot) | `!ready` | `dark.jpg` (background) | `colorFilterNotReady` |
| **Ready** | Operational, nothing scanned yet | `ready ∧ ¬used ∧ ¬infected` | `light_ready.png` | `colorFilterReady` |
| **Used** | At least one file read, no threat | `ready ∧ used ∧ ¬infected` | `light_used.png` | `colorFilterUsed` |
| **Dirty** — currently “Infected” in the code | At least one infected file detected | `ready ∧ infected` | `light_infected.png` | `colorFilterInfected` |

where `used = nbFinished > 0` (`nbFinished = nbClean + nbInfected`) and `infected = nbInfected > 0`.

> **Precedence** (highest wins): **Dirty > Used > Ready > Not ready** — this is exactly the order of the `imgBack.source` / `systemStateColor` bindings (`MainScreen.qml`, `Bindings.qml`).
>
> **Workflow relation**: the status is driven by the analysis results. It goes *Ready → Used* as soon as the first file is read (`systemUsed`, `analysis_controller.py:186`) and *Used → Dirty* the moment an infected file is detected. A **Reset** returns it to **Ready** (counters and `systemUsed` are cleared, `application_controller.py:368`). It is independent of `SystemState`: e.g. during `SystemAnalysisRunning` the status becomes **Dirty** as soon as the first infected file is found.
>
> **Bug (D8)**: `Bindings.qml` computes `infected: nbInfected > 1` (line 13) — it should be `> 0`, so a single infected file does not currently flip the status to *Dirty*.
>
> **Theming**: the concrete images and color filters per theme are documented in [`gui.md` §4–5](gui.md).

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

### 8.6 Source / Target Disconnection During Copy

```
1. CopyCleanFiles in progress
2. User unplugs the source (by mistake) → copy paused, an error flag is set on CopyCleanFiles
   (the system STAYS in CopyCleanFiles — no dedicated state, no reset, no re-analysis)
3. User re-inserts the source (same disk)
4. Coherence check: source state + integrity (fingerprint) of the already-copied data are verified
5. If OK → the error flag is cleared and the copy resumes automatically → continues to GeneratingReport
6. If the check FAILS (e.g. a different disk was re-plugged) → SystemMustBeReset (NFR-4, I6)
```

> The **same** handling applies to the **target** disk: unplugging it sets the error flag, and re-insertion (with a coherence check) resumes the copy; a failed check (different disk) leads to `SystemMustBeReset` (§6.1).

### 8.7 Report Generation Failure

```
1. GeneratingReport in progress
2. Report generation fails (e.g. WeasyPrint exception, disk full, I/O error)
3. → ReportFailed (permanent error state, #4) — the user is informed, Reset is required
4. No automatic retry; the system stays in ReportFailed until the user acts
5. User clicks Reset → SystemResetting → back to SystemReady (I9: counters/queue cleared)
```

### 8.8 Source Disconnection During Analysis

```
1. SystemAnalysisRunning (files already in the repository are being scanned by the AV engines)
2. User unplugs the source (by mistake)
3. Analysis CONTINUES on the files already in the repository (AV engines are NOT interrupted);
   an error flag is set and a dialog prompts the user to re-connect the source
4. The analysis loop is HELD (waiting) so it does not exit prematurely while files remain to be copied
5. User re-inserts the source → the flag is cleared, the remaining files are copied, and the analysis resumes
6. All files analyzed → AnalysisCompleted (→ copy / report as usual)
```

---

## 9. Open Questions

1. **Single-disk mode** — **Resolved** by `SystemWaitingForTarget` (scenario 8.4): analysis works on one disk; copy and report require a second disk.
2. **Archive mounting** — **Resolved**: the dormant archive-mounting code is **removed**; a backlog feature is added to re-introduce it later as a new, specified capability.
3. **SystemNotClean state** — **Resolved**: it is **not** a workflow state; it is the *Dirty* visual status (§7.2) driven by the derived conditions (§3.3).
4. **Recovery from report failure** — **Resolved**: a report-generation failure enters the **`ReportFailed`** state (§2, scenario 8.7); **Reset required**, no automatic retry.
5. **Source disconnection during copy** — **Resolved**: modelled as an **error flag** on `CopyCleanFiles` (no dedicated state). On re-insertion, a **coherence check** (source state + integrity/fingerprint) clears the flag and the copy auto-resumes. See scenario 8.6.

---

## 10. Document Maintenance

This document should be updated whenever:
- A new state is added or removed
- A transition rule changes
- A new error handling path is added

> **Scope**: this document is the contract of the **state machine** only. MQTT topic ownership is maintained separately in [`architecture.md` §4.2](architecture.md).

**Review cadence**: Before each major release, review this document against the actual code behavior.

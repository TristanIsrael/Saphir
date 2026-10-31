# Implementation state vs specification

> **Status**: Coverage audit
> **Last updated**: 2026-10-31
> **Reference**: `docs/features.md` (F1–F21, NFR-1 to NFR-5)

## Legend

| Symbol | Meaning |
|---------|---------------|
| ✅ | Implemented, compliant with the specification |
| 🟡 | Partially implemented (identified gaps) |
| ❌ | Not implemented |
| ⚠️ | Diverges from the specification |

---

## 1. Feature coverage

| Ref. | Feature | Status | Main location |
|------|----------|--------|------------------------|
| F1 | Media detection & mode selection | ✅ | `application_controller.py` (`__handle_disk_state`) |
| F2 | Navigation & file selection | 🟡 | `go_to_folder` / `go_to_parent_folder` / `enqueue_file` / `dequeue_file`, `FilesSelectionPanel.qml` |
| F3 | Antivirus analysis | 🟡 | `analysis_controller.py`, `analysis_helper.py` |
| F4 | Copy of clean files | 🟡 | `start_transfer`, `on_copy_file`, `__on_transfer_complete` / `__on_transfer_error` |
| F5 | Event journal | ✅ | `__messages_model` (journal), `LogDialog.qml` |
| F6 | Safety report | 🟡 | `report_controller.py`, triggered from `__on_transfer_complete` |
| F7 | GUI themes | ⚠️ | `Environment.qml`, `MainScreenUi.ui.qml` |
| F8 | Status bar (TopBar) | 🟡 | `TopBar.qml`, `__handle_energy_state`, `plugged` |
| F9 | System state dialog | ✅ | `SystemStateDialog.qml`, `systemState` signal |
| F10 | Cleaning (Reset) | 🟡 | `reset` slot |
| F11 | Startup/cleaning progression | ✅ | `SystemLoadingPanel.qml`, `systemLoadingProgress` property |
| F12 | Shutdown | ✅ | `shutdown` slot |
| F13 | Prompt to plug in a media | ✅ | `dlgConnectStorage` (`MainScreenUi.ui.qml`) |
| F14 | Language selection | 🟡 | `__set_language`, `MainScreen.qml` |
| F15 | Switch to the Viewer | ❌ | `btnShowViewer` (`visible: false`, `MainScreenUi.ui.qml`) |
| F16 | Remaining time estimation (ETA) | 🟡 | `EMA_ETA_estimator.py`, `FilesProgress.qml:87` |
| F17 | Analysis list filters | 🟡 | `AnalysisPanel.qml:76-173` |
| F18 | System messages `[deprecated]` | ❌ | `MessagesPanel.qml`, `MessagesListModel` (hidden panel) |
| F19 | Ambient light indicator `[not ready]` | ❌ | `Brightness.qml` (hardcoded, no backend) |
| F20 | Fullscreen mode & cursor handling | ✅ | `main.py` (input events filter) |
| F21 | Adaptive layout by device type `[backlog]` | 🟡 | `Environment.handheld`, `AnalysisPanel.qml` |

---

### F1 — Media detection & mode selection ✅

**Implemented**:
- Detection via `DISK_STATE` (`__handle_disk_state`) and `LIST_DISKS` (`__handle_list_disks`).
- Source/target rule (10.8): every disk connected **before the scan starts**
  is a source (partitions + additional media), **no new source is accepted
  once the scan has started** (a late disk is ignored and logged), and the
  first disk connected **after the analysis completes** is the target.
- "Scan the whole media?" dialog (`dlgAnalyseWholeStorage` in `MainScreenUi.ui.qml`).
- Choice irreversible without reset.
- Multi-partitions: `__storages` list + `comboStorages` selector; the full
  analysis lists the root of every source disk.

**Gaps / divergences**:
- **Copy trigger** (resolved, 10.8): the target is, by construction, the first
  disk connected *after* the analysis completes, so the copy starts only once
  the analysis is finished.
- ✅ `[bug]` (resolved, 10.8) "Scan all" mode now lists the root of **every**
  source disk (every partition and every additional media) and the copy loop
  reads each file from the disk that contains it.
- 🟡 No explicit guard for the return to the initial state if the media is removed before the choice.

---

### F2 — Navigation & selection 🟡

**Implemented**:
- Navigation: `go_to_folder`, `go_to_parent_folder` slots.
- Partition change via `comboStorages` → `on_storage_selected`.
- File → queue: `enqueue_file`.
- Folder → recursive: `__is_enqueuing` + `folders_to_query`.
- Deselection: `dequeue_file`.

**Gaps / divergences**:
- ⚠️ **File selection blocked behind AV readiness (D7)**: the spec (workflow v2.1) allows selecting files as soon as the disk-controller is ready and a disk is connected, **even if the AV engines are not ready**; the analysis trigger is separately gated by the ready-to-analyze condition. The implementation gates `SystemReady` (and thus file selection) behind `len(analysis_components) >= ANTIVIRUS_NEEDED` in `__handle_av_state`, so selection is not possible until the AV engines are ready.
- ❌ **No concurrent enqueue**: no serialization wait queue. Several folders can be enqueued in parallel (spec constraint not met).
- 🟡 **Queue locked after analysis**: the lock is implicit (via the system state), no explicit guard in `enqueue_file`/`dequeue_file`.
- 🟡 `[feature]` No full queue drain (backlog).

---

### F3 — Antivirus analysis 🟡

**Implemented**:
- Manual trigger: `start_stop_analysis`.
- File-by-file copy to the repository: `__do_copy_files_into_repository` (`analysis_controller.py`), `Api().read_file`.
- Files parallelism: `__repository_capacity` + timer.
- Engines parallelism: each file sent to all AV.
- Consensus: `evaluate_result_consensus` (`analysis_helper.py`) — infected if **one** engine infected.
- Pause/resume (F3, #151): `stop_analysis`/`start_analysis` + `stop`/`resume` topics — the UI button is a **Pause** (suspend + resume), not a hard stop. On resume, the interrupted files (`GettingFile` / `FileAvailableInRepository` / `FileAnalysing`) are re-queued, the already-analyzed files keep their final status and are not re-analyzed; stale results/errors for a file in a final state are ignored (terminal guard in `__handle_result` / `__handle_error`).
- AV engine failure during analysis (NFR-3, #149): `handle_av_failure` — the files that can no longer reach a valid consensus are declared `Error` (the already-analyzed files keep their status); the analysis aborts to `SystemWaitingForUserAction` when fewer than `ANTIVIRUS_NEEDED` engines remain, otherwise it continues with the survivors (scenario 8.9).
- Progression: `globalProgress`, `FilesProgress.qml`.
- ETA: `EMAETAEstimator` (see F16).

**Gaps / divergences**:
- ⚠️ **Hardened parallelism**: `cpu_count = 8` hardcoded (in `__handle_sysinfo`, "because of bug #54") instead of the real number of cores.
- ✅ **Ternary status** (D5, resolved #149/#151): `Clean` / `Infected` / `Error` — `__handle_error` sets `FileAnalysisError` (terminal guard: a file in a final state is not re-processed) and removes the file from the repository.
- ✅ **Fingerprint verification** (NFR-1, resolved #145): see NFR-1.

---

### F4 — Copy of clean files 🟡

**Implemented**:
- Only clean files: `_do_start_transfer` (`TransferController`).
- Automatic trigger: on target connection (in `__handle_disk_state`, once the analysis completes).
- Fingerprint check on each copied file (NFR-1) + failure counting (F4).
- Report + journal copied at the end: `__on_transfer_complete`.
- ✅ **Final check (copied == clean)** (#150): `TransferController.__check_transfer_complete` — the transfer completes when every clean file has been attempted (copied or failed); if `copied != clean`, `transferError` is emitted, the discrepancy is reported in the GUI and in the scan report ("Copy failures: N", in red). Scenario 8.10.
- ✅ **Individual copy failure** (#150): the copy continues on the other files; the platform error notifications (`events/error`) are handled by `TransferController.on_copy_error`.
- ✅ **Source disconnection during copy** (#148): the copy is held and auto-resumes on re-insertion (coherence check). Scenario 8.6.

**Gaps / divergences**:
- ✅ **No cancellation (by design)**: there is no cancel button for the copy (neither before nor during); the only exits are insert a target, Reset, or Shutdown. `SystemWaitingForTarget` is a stable terminal-ish state (see workflow v2.2).
- ✅ **Trigger** (D2, resolved, 10.8): the target is, by construction, the first disk connected *after* the analysis completes, so the copy starts only once the analysis is finished (`AnalysisCompleted → CopyCleanFiles` / `SystemWaitingForTarget`, workflow).
- 🟡 `[feature]` No check of the available space on the target.
- 🟡 **Available space displayed**: `targetAvailableSize` always 0 and `Property(bool, ...)` instead of `int` (the `targetAvailableSize` property) → permanent "Available space: Unknown".

---

### F5 — Event journal ✅

**Implemented**:
- Automatic recording: `Api().start(..., recording=True, logfile=...)`.
- Mandatory copy onto the target: `__on_transfer_complete` copies `journal.log`.
- User viewing: `LogDialog.qml` (`btnLog` button).
- Native Safecor format.
- Stateless: no retention between cycles.

Compliant.

---

### F6 — Safety report 🟡

**Implemented**:
- Automatic generation after copy: `__make_analysis_report` (called from `__on_transfer_complete`).
- Only if a copy took place: called from `__finish_transfer`.
- PDF Jinja2 + WeasyPrint: `report_controller.py`.
- Content: system, Saphir version, antivirus, media, dates, counters, list of files (path, fingerprint, results per AV).
- Automatic copy onto the target.

**Gaps / divergences**:
- ❌ **Report language selection**: `report_controller.py` **always** uses `scan_report_en.html`. The `scan_report_fr.html` template **exists but is never used** → violation of F14/NFR-5.
- 🟡 **Incomplete content**: `partitions` = `""` (`report_controller.py`), "total size analyzed" missing, no partition names.
- ✅ **Error handling** (resolved, #146): generation is wrapped in `try/except`; a failure ends the workflow in the permanent `ReportFailed` state (scenario 8.7, a Reset is required).
- ⚠️ **Synchronous generation**: the PDF is generated on the MQTT thread (in `__finish_transfer`), risk of blocking.

---

### F7 — GUI themes ⚠️

**Implemented**:
- Three themes: light, dark, low visibility (`ThemeLight/Dark/LowVisibility.qml`).
- Change at any time: `btnLight/Dark/LowVisibility` (`MainScreen.qml`).
- No persistence (stateless).
- Wireframe reserved for design: `ThemeWireframe.qml`.

**Divergences**:
- ✅ **Default theme** (D1, resolved): `Environment.qml:14` → `property int theme: Constants.dark`. Spec F7 updated to **dark** (default) to match the implementation.
- ⚠️ **Low visibility**: `backgroundImage` and `system*Image` use `dark.jpg` for the low visibility mode (the `theme` switches in `Environment.qml`). To be verified that the "reduce the light" objective is actually reached.

---

### F8 — Status bar (TopBar) 🟡

**Implemented**:
- Real-time clock (HH:MM:SS): `TopBar.qml` Timer (line 39-45).
- No date.
- Local/Zulu toggle: click on the clock (`maHour`, line 48-54).
- Battery: `Energy.qml` (polling `ENERGY_STATE` every 5 s, `__handle_energy_state`).
- Charger: `plugged` (`__is_plugged`).

**Gaps / divergences**:
- ❌ **Classification**: `classificationLevel` **hardcoded to 0** in `Bindings.qml:21`. No backend `classificationLevel` property. The "Restricted distribution" / "Secret" levels are **inaccessible**. The backend (provided by Safecor) is not wired.
- ⚠️ **Bug**: `TopBar.qml:36` — the `switch` color fallback returns `qsTr("Not protected")` (a **string** where a **color** is expected).

---

### F9 — System state dialog ✅

**Implemented**:
- Accessible at any time: `btnSystemState`.
- Component list (Safecor + AV) + state: `SystemStateDialog.qml`, `componentsModel`.
- States `UNKNOWN/STARTING/READY/ERROR/OFF` (via Safecor `ComponentState`).
- System information: `systemInformationModel` (Safecor version, etc.).
- Read-only.

Compliant. **Note**: the DEBUG mode is not explicitly verified as displayed (to be confirmed in `systemInformationModel`).

---

### F10 — Cleaning (Reset) 🟡

**Implemented**:
- Accessible at any time: `btnRestart` → `reset()`.
- Safecor feature + Saphir completion: `Api().restart_domain("sys-usb")` + restart of the AV domains (in `reset()`).
- Analysis interruption: `stop_analysis()` (in `reset()`).
- Progression displayed: `SystemLoadingPanel.qml` (title "Cleaning..." in `SystemResetting` state).
- Return to the initial state: `__reset_states()`.

**Gaps / divergences**:
- ⚠️ **Incomplete interruption**: `reset()` clears the `TransferController` state (via `__reset_states`) but **does not interrupt the in-flight copy loop** (`_do_start_transfer`): the copy requests already issued run to the end of the queue.
- 🟡 **Media reconnection**: no explicit handling of the media disconnection/reconnection during the reset (the behavior relies on Safecor messages).

---

### F11 — Startup/cleaning progression ✅

**Implemented**:
- Display: `SystemLoadingPanel.qml` (4-step pipeline: GUI → Core → Antiviruses → Complete).
- Progress bar + steps: `systemLoadingProgress` property.
- 3 semantic steps (core, AV, ready).
- Auto-close: `opacity = !analysisReady ? 1 : 0` (MainScreenUi.ui.qml:354).
- Reused for startup and reset.

Compliant. **Note**: the spec says "modal"; it is a panel (not strictly modal), but the functional behavior is equivalent.

---

### F12 — Shutdown ✅

**Implemented**:
- Accessible at any time: `btnShutdown`.
- Confirmation: `dlgShutdown`.
- Immediate interruption: `shutdown()`.
- Call to the Safecor API: `Api().shutdown()` (in `shutdown()`).

Compliant.

---

### F13 — Prompt to plug in a media ✅

**Implemented**:
- Displayed when `ready && analysisReady && sourceName === ""` (`dlgConnectStorage` in `MainScreenUi.ui.qml`).
- Non-modal.
- "Close" button.

Compliant.

---

### F14 — Language selection 🟡

**Implemented**:
- Change at any time: `btnLanguageEN`/`btnLanguageFR` (`MainScreen.qml`).
- Immediate: `__install_translations` + `engine.retranslate` (`main.py`).
- Default language = Safecor language: `translation_manager.request_default_language()`.

**Gaps / divergences**:
- ⚠️ **PDF report**: the report does **not** follow the language (always `scan_report_en.html`, see F6).

---

### F15 — Switch to the Viewer ❌

**Implemented**:
- Backend: `switch_to_viewer()` → `Api().switch_gui("saphir-viewer")`.

**Gaps (major)**:
- ❌ **Hidden button**: `btnShowViewer` has `visible: false // Hidden until 3.2` (`MainScreenUi.ui.qml`).
- ❌ **No unavailability guard**: if the Viewer component is not `READY`, the button should be unavailable + message in F9. Not implemented.
- ❌ **No disabled-config handling**: the button should not exist + F9 message. Not implemented.
- ❌ **No "no operation in progress" guard**: the Viewer should only be accessible at idle. Not implemented.

---

### F16 — Remaining time estimation (ETA) 🟡

**Implemented**:
- Weighted exponential moving average: `EMA_ETA_estimator.py`.
- Displayed in the analysis gauge as `ETA: <readable duration>`: `FilesProgress.qml:87`.
- Duration formatted in days / hours / minutes.
- Reset on each analysis start with the total size of the queue.

**Gaps / divergences**:
- 🟡 `[fix]` (NFR-5) the displayed duration units (`j`/`h`/`min`) use untranslated French abbreviations.

---

### F17 — Analysis list filters 🟡

**Implemented**:
- Three toggleable filters (Clean / Infected / Waiting) on the file list: `AnalysisPanel.qml:76-173`.
- Each filter active by default.
- Filter applies to the display only (underlying data untouched).

**Gaps / divergences**:
- 🟡 `[fix]` inconsistent third-filter label ("Waiting" in PC layout, "Other" in tablet layout).

---

### F18 — System messages `[deprecated]` ❌

**Status**: deprecated — code kept during the refactoring, removal/reactivation decision pending.

**Implemented**:
- Message feed panel: `MessagesPanel.qml`, `MessagesListModel`.
- Message emission along the workflow.

**Gaps / divergences**:
- ❌ Permanently hidden panel (`visible: false`, `MessagesPanel` in `MainScreenUi.ui.qml`) — feature inert.
- Pending decision: reactivate or remove (panel + model + emission).

---

### F19 — Ambient light indicator `[not ready]` ❌

**Status**: not ready — Safecor does not provide the light data yet. Code kept.

**Implemented**:
- Ambient light indicator: `Brightness.qml`, `ambientLight` property.

**Gaps / divergences**:
- ❌ `ambientLightSensorReady`/`ambientLight` hardcoded, no Safecor backend.
- ❌ `[fix]` the `Material Symbols Outlined` font is not installed by `main.py`.

---

### F20 — Fullscreen mode & cursor handling ✅

**Implemented**:
- Runs in fullscreen on a dedicated station (nominal kiosk mode).
- Cursor hidden in kiosk, reappears on mouse/touch movement: input events filter (`main.py`).
- Fullscreen can only be disabled in DevMode.

**Gaps / divergences**:
- **Note**: may be handled by Safecor; kept here for the moment.

---

### F21 — Adaptive layout by device type `[backlog]` 🟡

**Status**: to be done — the PC layout is currently inert.

**Implemented**:
- `handheld` property drives the layout (row heights, filter style, panel templates): `Environment.handheld`, `AnalysisPanel.qml`.

**Gaps / divergences**:
- ❌ `handheld` always `True` (backend constant + hardcoded in `Bindings.qml`) → the PC layout is dead.
- To do: make `handheld` a genuinely device-configured property; rehabilitate or remove the PC layout.

---

## 2. NFR coverage

| Ref. | NFR | Status |
|------|-----|--------|
| NFR-1 | End-to-end integrity (fingerprint) | ✅ |
| NFR-2 | Source media integrity | ✅ |
| NFR-3 | Minimum number of antivirus engines | ✅ |
| NFR-4 | Dirty state & locking | ✅ |
| NFR-5 | Translatability | 🟡 |

### NFR-1 — Fingerprint ✅ (resolved #145)

- **Source → repository**: the fingerprint is retrieved with the file
  (`__on_file_available`) and recorded in the queue; the match with the
  original is guaranteed by Safecor (spec).
- **Repository → AV**: each AV domain re-verifies the fingerprint of the
  repository file (`_abstract_antivirus_controller.py`); a mismatch is
  reported with `fingerprint_error` on the analysis response and the file is
  declared `Error` (`FileAnalysisError`).
- **Repository → target**: `TransferController.on_copy_result` compares the
  fingerprint of the copied file with the recorded one; a mismatch marks the
  file `FileCopyError` (it is not copied) and the final check (8.10) reports
  the discrepancy.
- A verification failure declares the file `Error`, the chain continues on
  the other files, and the error is traced in the journal and the report.

### NFR-2 — Source integrity ✅

- By design, Saphir only does `read_file` on the source. No write. Compliant.

### NFR-3 — Minimum number of AV ✅

- ✅ Compile-time constant: `ANTIVIRUS_NEEDED = 2` (libsaphir `_constants.py:7`).
- ✅ Analysis blocked if not reached: `btnStartStop.enabled` depends on `analysisReady` (which requires `len(analysis_components) >= ANTIVIRUS_NEEDED` in `__handle_av_state`).
- ✅ Progression pending.
- ✅ **AV failure during analysis** (#149): `__check_components_availability` detects the READY → non-READY transition of an engine while `SystemAnalysisRunning` and calls `AnalysisController.handle_av_failure(comp_id)`. The files that can no longer reach a valid consensus are declared `Error` (the already-analyzed files keep their status); when fewer than `ANTIVIRUS_NEEDED` engines remain the analysis is aborted (`SystemWaitingForUserAction`), otherwise it continues with the surviving engines (workflow-rules.md scenario 8.9).

### NFR-4 — Dirty state & locking ✅ (D4 + locking resolved)

- ✅ Contamination point (D4, resolved): `systemUsed` is emitted in `__on_file_available` — i.e. when the file has been **read by the disk-controller** and made available in the repository (the earliest, safest point).
- ✅ **Locking (different disk names)** (resolved, #148): the coherence check is explicit in `TransferController` — a reconnection with the **same disk** auto-resumes the copy, a **different disk** ends the workflow in `SystemMustBeReset` (scenario 8.6, covered by `test_workflow_source_disconnection_copy.py`).
- ✅ **Numeric gate** (resolved, 10.8): the fragile integer-state comparison in `__handle_disk_state` was replaced by the explicit source/target disk rule (analysis done / scan started).

### NFR-5 — Translatability 🟡

- ✅ GUI: Qt mechanisms (`tr`, `.qm`, `qsTr`).
- ⚠️ **Report**: the FR template exists (`scan_report_fr.html`) but is **not used** by `report_controller.py`. The static per-language translation is not wired.

---

## 3. Cross-reference — previously undocumented features (now F16–F21)

These capabilities used to exist in the code without a spec entry. They are now documented in `features.md` and audited above (F16–F21):

| Previous name | Spec ref. | Location | Description |
|----------|-----------|-------------|-------------|
| ETA estimation (EMA) | F16 | `EMA_ETA_estimator.py`, `FilesProgress.qml:87` | Remaining time estimation by weighted exponential moving average. Displayed in the analysis gauge. |
| Analysis list filters | F17 | `AnalysisPanel.qml:76-173` | Clean / Infected / Waiting filters on the file list. |
| System messages | F18 `[deprecated]` | `MessagesPanel.qml`, `MessagesListModel` | System message feed. **Permanently hidden panel** (`pnlMessages` in `MainScreenUi.ui.qml`). |
| Light sensor detection | F19 `[not ready]` | `Brightness.qml`, `ambientLight` | Ambient light indicator. **Dead** (hardcoded `false`, no backend, font not installed). |
| Input events filter | F20 | `main.py` | Cursor hidden in kiosk, reappears on mouse/touch movement. |
| Handheld mode | F21 `[backlog]` | `Environment.handheld`, `AnalysisPanel.qml` | Adaptive tablet/PC layout. **Always `True`** hardcoded → the PC layout is dead. |
| Development mode (DEVMODE) | — (not a product feature) | `devmode_helper.py`, `main.py` | Dev environment without appliance (mock MQTT, simulated disks). Moved to `docs/test-strategy.md` §3.1 (simulation tooling). |

> Remaining open decisions: **F18** (reactivate or remove the message panel) and the removal candidates **F19** (light, dead) and the dead PC layout of **F21**.

---

## 4. Spec ↔ implementation divergences (summary)

| # | Divergence | Spec | Implementation | Resolution |
|---|-----------|------|----------------|------------|
| D1 | Default theme (F7) | Light | `dark` (Environment.qml:14) | **Resolved**: keep `dark`; spec F7 updated to match |
| D2 | Copy trigger (F1/F4) | After end of analysis | Immediate on target connection | **Resolved (10.8)**: the target is the first disk connected *after* the analysis completes, so the copy runs **after** the analysis |
| D3 | Multilingual report (F14/NFR-5) | Template per language | Always EN | — (to fix) |
| D4 | Contamination point (NFR-4) | disk-controller read | Placement in the repository | **Resolved**: dirty at **disk-controller read** (`__on_file_available`) |
| D5 | File status (F3) | Ternary (Clean/Infected/Error) | Binary + disabled error | **Resolved (#149/#151)**: `Error` is set via `__handle_error` (terminal guard) |
| D6 | F11 progression | "Modal" | Panel (equivalent behavior) | — (equivalent behavior, accepted) |
| D7 | File selection vs AV readiness (F1/F2) | Selection possible dès disk-controller prêt + disque, **sans** attendre les AV; the analysis trigger is separately gated by ready-to-analyze (AV + core + queue) | `SystemReady` gated behind `len(analysis_components) >= ANTIVIRUS_NEEDED` (in `__handle_av_state`) → selection blocked until the AV engines are ready | — (to fix) |
| D8 | System visual status "Dirty" (F7) | A single infected file flips the visual status to *Dirty* (`nbInfected > 0`) | `Bindings.qml:13` uses `infected: nbInfected > 1` → one infected file is not enough | — (to fix; documented by an `xfail` in `tests/test_qml_bindings.py`) |

---

## 5. Consolidated backlog (gaps + identified bugs)

### To fix (spec compliance)

| Type | Ref. | Description |
|------|------|-------------|
| `[fix]` | F4/NFR-1 | **End-to-end fingerprint verification** (analysis + target copy) — **Resolved** (#145) |
| `[fix]` | F4 | Final check: error if copied ≠ clean — **Resolved** (#150) |
| `[fix]` | F4 | Source disconnection during copy → error + automatic resume — **Resolved** (#148) |
| `[fix]` | F1 | "Scan all" mode does not analyze all partitions — **Resolved** (10.8, #152) |
| `[fix]` | F4 (D2) | Copy trigger: run **after** the analysis ends, triggered by the 2nd-media insertion (not immediate on target connection) — **Resolved** (10.8) |
| `[fix]` | NFR-4 (D4) | Contamination point: the system becomes dirty at the **disk-controller read** (not at the repository placement) — **Resolved** |
| `[fix]` | F6 | Report template selection according to the language (use `scan_report_fr.html`) |
| `[fix]` | F6 | PDF generation error handling (end normally) — **Resolved** (#146, `ReportFailed`) |
| `[fix]` | F8 | Wire the classification (Safecor) instead of the hardcoded 0 |
| `[fix]` | F3 | Analysis pause/resume without re-analyzing the processed files — **Resolved** (#151; the NFR-3 engine-failure part was done in #149) |
| `[fix]` | F15 | Viewer button + guards (unavailability, config, idle) |
| `[fix]` | F2 | Enqueue serialization (no concurrent) |
| `[fix]` | F1/F2 (D7) | Decouple file selection from AV readiness — reach `SystemReady` when the disk-controller is ready (no AV requirement); gate the analysis trigger on ready-to-analyze (AV + core + queue) |
| `[fix]` | F10 | Also interrupt the copy in progress on reset |
| `[fix]` | F16 | Translate the ETA duration units (`j`/`h`/`min`) — NFR-5 |
| `[fix]` | F17 | Harmonize the third filter label (Waiting vs Other) |
| `[fix]` | F19 | Install the `Material Symbols Outlined` font before enabling |

### To decide (divergences)

_(none — D1/D2/D4 resolved; the remaining divergences D3/D5/D7/D8 are tracked as fixes in "To fix")_

### Features (product backlog)

| Type | Ref. | Description |
|------|------|-------------|
| `[feature]` | F1 | Undo the mode choice without reset |
| `[feature]` | F2 | Full queue drain |
| `[feature]` | F4 | Check the available space on the target before copy |
| `[feature]` | F3 | Archive mounting (re-introduce as a new, specified capability — dormant code removed, workflow §9.2) |
| `[dependency]` | F19 | Enable the light indicator when Safecor exposes the sensor state |
| `[backlog]` | F21 | Make `handheld` device-configured; rehabilitate or remove the PC layout |

### Dead code / technical (debt)

| Type | Location | Description |
|------|-------------|-------------|
| `[debt]` | `Bindings.qml:13` | `infected: nbInfected > 1` should be `> 0` (D8, `xfail` in `tests/test_qml_bindings.py`) |
| `[debt]` | `__handle_sysinfo` (`analysis_controller.py`) | `cpu_count = 8` hardcoded (bug #54) |
| `[debt]` | `Progress.qml` | Unreferenced component |
| `[debt]` | `Brightness.qml` | Dead feature (F19) |
| `[debt]` | `MessagesPanel` | Hidden panel (F18) |
| `[debt]` | `GUI/Saphir/Enums.qml` | Obsolete QML singleton (shadowed by Python) — confirmed by the QML binding tests, the Python `Enums` is the effective one |
| `[debt]` | `scan_report_fr.html` | Orphan unused template |
| `[debt]` | `targetAvailableSize` property | typed `bool` instead of `int` |
| `[debt]` | `AnalysisPanel.qml` | Dead PC layout (handheld always true) (F21) |
| `[debt]` | `__update_eta` (`application_controller.py`) | Debug leftovers: writes EMA data to `/tmp/data.txt` on every update (since #38) |

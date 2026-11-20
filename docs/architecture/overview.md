# Saphir — Architecture Overview

> **Status**: Stable
> **Last updated**: 2026-11-20
> **Audience**: developers working on the Saphir codebase (refactoring and future features)
> **Scope**: global description of the Saphir architecture — high-level design picture, deployment, software layering, state machine summary, data model, and the target (to-be) layout. Per-component details are in [`components/`](components/), the communication architecture (MQTT contract) in [`../development/protocol.md`](../development/protocol.md), and the key design decisions in [`decisions/`](decisions/).

## Related documents

| Concern | Document |
|---------|----------|
| What the system must do (behaviour) | [`../specifications/features.md`](../specifications/features.md) (F1–F21, NFR-1 to NFR-5) |
| State machine contract (states, transitions, invariants) | [`../specifications/workflow.md`](../specifications/workflow.md) |
| User interface (principles, screens, visual status, theming) | [`components/gui.md`](components/gui.md) |
| Component reference (one file per component) | [`components/`](components/) — see the [Components](#components) section |
| Communication architecture (MQTT topics, single-client constraint, payloads) | [`../development/protocol.md`](../development/protocol.md) |
| Key design decisions (ADR registry) | [`decisions/`](decisions/) |
| Refactoring phases & effort | [`../archive/plans/refactoring-plan.md`](../archive/plans/refactoring-plan.md) |
| Project status (feature/NFR coverage audit, gaps, backlog) | [`../project-status.md`](../project-status.md) |
| Validation / test strategy | [`../development/testing.md`](../development/testing.md) |

This document deliberately does **not** duplicate those documents. It describes the architecture and links to them.

---

## 1. High-level design

```
+===========================================================================+
| saphir-gui (Dom0, has_gui=1)        saphir-viewer (Dom0, same pattern)    |
|                                                                           |
|   QML layer: MainScreen.qml, panels, dialogs                              |
|         | binds                                                           |
|         v                                                                 |
|   Bindings.qml (single indirection layer)                                 |
|         | calls                                                           |
|         v                                                                 |
|   ApplicationController (QObject, mediator)                                |
|     +-- WorkflowController   (SystemState authority)                      |
|     +-- AnalysisController   (multi-AV analysis orchestration)            |
|     +-- TransferController   (copy of clean files)                        |
|     +-- ReportController     (PDF scan report)                            |
|         |                                                                 |
|         v                                                                 |
|   safecor Api()  — one MQTT client per process (per-domain singleton)     |
+===============================|===========================================+
                                |  MQTT  (system/*  +  saphir/analysis/*)
         +----------------------+---------------------------+
         |                      |                           |
+--------v---------+   +--------v---------+        +--------v---------+
| saphir-av-clamav |   | saphir-av-eset   |        | sys-usb (domain)  |
| (domU)           |   | (domU)           |        | shared repository |
| ClamAntivirus-   |   | EeaAntivirus-    |        | /mnt/storage      |
| Controller       |   | Controller       |        | (staging area —   |
| (libsaphir,      |   | (libsaphir,      |        |  the only data    |
|  worker pool,    |   |  LXC container,  |        |  exchange point   |
|  clamdscan)      |   |  scan-file.sh)   |        |  between domains) |
+------------------+   +------------------+        +-------------------+

        Platform: Safecor core (disk controller, main controller)
```

The **Viewer** is a second GUI application on the same screen: it shares the same platform, the same AV domains and the same repository, and is swapped with the main GUI via `Api().switch_gui(...)` (`system/gui/switch`).

---

## 2. System context

Saphir is a **sheep-dip**: a secure workstation that scans external media (USB disks) for malware before they enter the organisation's network. It runs on **Safecor**, a multi-domain (multi-VM) operating system for security products, on **Alpine Linux**, distributed as a bootable ISO.

The core value: **multiple antivirus engines vote on every file, with a consensus verdict** (a file is infected if *any* engine flags it; clean only when all agree). Clean files are copied to a second external disk, and a **PDF scan report** + the event journal are produced as evidence.

Two GUI applications share the same platform and swap on the same screen:

- **Main GUI** (`python/gui/`) — the analysis/copy workflow.
- **Viewer** (`python/viewer/`) — a read-only file/preview browser (images, video, audio, Office, PDF; Office→PDF via LibreOffice). It follows the exact same backend pattern as the main GUI and is switched to/from with `Api().switch_gui(...)`.

---

## 3. Deployment architecture (Safecor multi-domain)

Saphir is deployed as **separated Safecor domains** (one VM per concern). The topology is defined in `setup/packages/saphir/saphir/topology.json`:

| Domain | Role | Notes |
|--------|------|-------|
| `saphir-gui` | Main GUI + analysis orchestration | `has_gui: 1`, hosts the `ApplicationController` |
| `saphir-av-clamav` | ClamAV antivirus engine | runs `clamdscan` |
| `saphir-av-eset` | ESET Endpoint antivirus engine | runs in a trimmed LXC container |
| `sys-usb` | Safecor disk/staging domain | the disposable domain destroyed on reset |
| (platform) | Safecor core (disk controller, main controller) | provided by the platform |

Plus the **Viewer** domain (`saphir-viewer`), a separate GUI package that shares the same AV domains and repository.

### 3.1 The shared repository

The domains do **not** share memory. They exchange data through the **repository**, a shared staging area on the `sys-usb` domain (`Constants.STR_REPOSITORY = "__repository__"`, mounted at `/mnt/storage`). Files are staged here before analysis and copied from/to the external disks.

### 3.2 Per-file data flow

```
 saphir-gui                          sys-usb (repository)                 saphir-av-clamav / saphir-av-eset
 -----------                         --------------------                 ------------------------------
 read_file(source, path)  --MQTT-->  stage file into /mnt/storage
        |                                        |
        |                                        +-- NEW_FILE (fingerprint) --MQTT-->
        v
 AnalysisController marks file FileAvailableInRepository
        |
        +-- publish saphir/analysis/request {filepath, fingerprint}
                                             \
                                              \--MQTT-->  ClamAV verifies the repository fingerprint (NFR-1), then scans (worker pool)
                                              \--MQTT-->  ESET  verifies the repository fingerprint (NFR-1), then scans (worker pool)
                                                      |            |
                                   publish saphir/analysis/response {component, filepath, success, details[, fingerprint_error]}
                                                      |
        +<---------------------------------------------+
 AnalysisController.__handle_result aggregates per-AV results
        -> when all engines reported -> consensus (any "Infected" => infected)
        -> delete_file from repository (frees slot) -> resultsChanged
```

**Key fact**: all cross-domain coordination is over **MQTT topics**. There is never direct in-process sharing between domains (each domain is its own process/VM).

---

## 4. Software layering — as-is

```
+---------------------------------------------------------------------+
|  QML views (GUI/content/*.qml, GUI/Components/*.qml)                |
|  TopBar, FilesSelectionPanel, AnalysisPanel, FilesCopyPanel, ...    |
+---------------------------------------------------------------------+
              |  bind to                                             |
              v                                                       v
+---------------------------------------------------------------------+
|  Bindings.qml  (mediator: scalar bindings + method bridges)         |
|  Environment.qml / Constants.qml / Enums (theming + constants)      |
+---------------------------------------------------------------------+
              |  calls                                              |
              v
+---------------------------------------------------------------------+
|  ApplicationController (QObject)  <-- god class, ~1268 lines       |
|    - state machine (SystemState)                                     |
|    - MQTT subscription + message routing                             |
|    - UI models (queues, files, components, log, messages)           |
|    - file transfer, report triggering, energy, language             |
|    owns:                                                            |
|      +-- AnalysisController (QObject, ~534 lines)  [analysis]       |
|      +-- ReportController    (QObject, ~75 lines)   [PDF report]    |
|      +-- EMAETAEstimator                             [remaining time]|
|      +-- QAbstractItemModel subclasses               [UI data]      |
+---------------------------------------------------------------------+
              |  uses                                               |
              v
+---------------------------------------------------------------------+
|  safecor API  (Api singleton, Topics, MqttFactory, ComponentsHelper)|
+---------------------------------------------------------------------+
              |  MQTT (per-domain single client)                    |
              v
+---------------------------------------------------------------------+
|  libsaphir: AbstractAntivirusController (Template Method)           |
|     +-- ClamAntivirusController    +-- EeaAntivirusController       |
|  (run in the saphir-av-* domains)                                   |
+---------------------------------------------------------------------+
```

The **MVVM boundary** is: QML views → `Bindings.qml` → `ApplicationController` (QObject signals/properties/models) → `AnalysisController` / AV controllers → Safecor `Api()` → MQTT → other domains.

The as-is responsibilities of each layer are detailed in the component documents: the GUI process and its controllers in [`components/application-controller.md`](components/application-controller.md), [`components/analysis-controller.md`](components/analysis-controller.md) and [`components/report-controller.md`](components/report-controller.md); the AV domains in [`components/antivirus-controllers.md`](components/antivirus-controllers.md); the QML views and the UI data models in [`components/qml-layer.md`](components/qml-layer.md).

---

## 5. State machine

The workflow is a deterministic state machine from boot to shutdown. The **canonical states, transition table, invariants, UI mapping, and scenarios** are defined in [`../specifications/workflow.md`](../specifications/workflow.md) — that document is the contract.

Summary of the phases (see `SystemState` in `Saphir/enums.py`):

```
Boot:  SystemStarting -> SafecorReady -> SystemReady
Idle:  SystemReady  (waiting for media)
Pre-Analysis:  SystemGettingFilesList / SystemWaitingForUserAction
Analysis:  SystemAnalysisRunning -> AnalysisCompleted
Transfer:  CopyCleanFiles -> GeneratingReport
Post-Transfer:  SystemMustBeReset -> SystemResetting -> (loop to SystemReady)
Shutdown:  SystemShuttingDown (from any state)
```

**As-is reality** (important for the refactoring): the state transitions are **not** centralised — `__set_system_state(...)` is called from several scattered message handlers (`__handle_disk_state`, `__on_results_changed`, `__handle_create_file`, …), and a few enum states are dead/unreachable. The target architecture centralises this in a single **`WorkflowController`** (invariant **I3**: only it may set `SystemState`) — see [`components/workflow-controller.md`](components/workflow-controller.md) and the refactoring plan Phase 1.

---

## 6. Data model & consensus

### 6.1 The queue item

The queue is an in-memory **dict of dicts** (`__queued_files_list` in the as-is code), keyed by file path. Each entry carries the fields shown in `FilesProgress`/`AnalysisPanel` and the per-engine results. The shared reference is passed to `AnalysisController` in its constructor. The full per-file lifecycle is tracked with `FileStatus` (see [`components/antivirus-controllers.md`](components/antivirus-controllers.md) — shared enums). The queue data structure is now `FileQueue` — see [`components/storage-manager.md`](components/storage-manager.md).

### 6.2 Consensus rule

A file is **infected if any antivirus engine reports it infected**; it is **clean only when all engines agree clean**. Implemented in `AnalysisHelper.evaluate_result_consensus` ([`components/analysis-controller.md`](components/analysis-controller.md)). `ANTIVIRUS_NEEDED = 2` gates whether analysis is *enabled* (enough engines ready), it is **not** a voting threshold. See invariant **I6** and feature F3.

### 6.3 Integrity (fingerprint)

Safecor computes a fingerprint on every file operation; Saphir is expected to compare them end-to-end (source→repository, at analysis, repository→target). See NFR-1 in [`../project-status.md`](../project-status.md) (Feature & NFR coverage) for the implementation status.

---

## 7. Target architecture — to-be

The goal is to decompose the `ApplicationController` god class into **single-responsibility controllers** coordinated by a central state machine. The detailed plan, phases, and effort estimate are in [`../archive/plans/refactoring-plan.md`](../archive/plans/refactoring-plan.md).

### 7.1 Target module layout

```
Saphir/
├── application_controller.py      # thin facade: wires the controllers (~200 lines)
├── workflow_controller.py         # state machine (SOLE owner of SystemState)      [NEW]
├── storage_manager.py             # DISK_STATE, source/target assignment           [NEW]
├── file_browser.py                # listing, navigation, recursive enqueue         [EXTRACTED]
├── file_queue.py                  # queue data structure + thread-safe ops         [EXTRACTED]
├── transfer_controller.py         # copy orchestration + progress + final check    [NEW]
├── analysis_controller.py         # analysis orchestration (existing, cleaned up)
├── report_controller.py           # PDF generation (existing, hardened)
├── energy_monitor.py              # battery/plugged polling                        [NEW]
├── translation_manager.py         # QTranslator lifecycle, language switching      [NEW]
├── api_lifecycle.py               # MQTT client + subscription ownership (I1/I2)   [NEW]
├── enums.py / analysis_helper.py / ema_eta_estimator.py
└── models/                        # all QAbstractItemModel subclasses
```

### 7.2 Communication pattern between controllers

```
+----------------------------------------------------------+
|  ApplicationController  (thin facade)                     |
|   WorkflowController  <-->  every controller             |
|   (sole mediator: domain signals + SystemState)          |
+----------------------------------------------------------+
```

All inter-controller communication is via (1) **Qt signals** and (2) **`SystemState` transitions** pushed by `WorkflowController`. **No direct sibling-to-sibling method calls.** Shared data (e.g. the queue) is passed by reference in the constructor.

### 7.3 Invariants (must hold throughout)

| # | Invariant |
|---|-----------|
| I1 | Single MQTT client — only `ApiLifecycle` creates/manages it |
| I2 | Single topic owner — each MQTT topic has exactly one subscriber |
| I3 | State machine authority — only `WorkflowController` sets `SystemState` |
| I4 | Queue thread safety — all queue access under a lock or in one thread |
| I5 | No direct cross-controller calls — signals + `SystemState` only |
| I6 | Analysis consensus — infected if ANY engine flags (OR logic) |
| I7 | Source disk immutability — once set, source cannot change without reset |

---

## 8. Components

One file per component, in the [`components/`](components/) folder:

| Component document | Covers |
|--------------------|--------|
| [`application-controller.md`](components/application-controller.md) | `application_controller.py` — the mediator between the Safecor platform and the QML UI (plus `api_lifecycle.py` and `devmode_helper.py`) |
| [`workflow-controller.md`](components/workflow-controller.md) | `workflow_controller.py` — the state machine orchestrator (transitions, invariants enforcement) |
| [`analysis-controller.md`](components/analysis-controller.md) | `analysis_controller.py` + `analysis_helper.py` (consensus evaluation) + `EMA_ETA_estimator.py` (remaining-time estimate) |
| [`transfer-controller.md`](components/transfer-controller.md) | `transfer_controller.py` — copy of clean files, progress, final check |
| [`report-controller.md`](components/report-controller.md) | `report_controller.py` — PDF scan report (Jinja2 + WeasyPrint), journal copy |
| [`storage-manager.md`](components/storage-manager.md) | `storage_manager.py` + `file_browser.py` + `file_queue.py` — source/target assignment, repository, queue management |
| [`antivirus-controllers.md`](components/antivirus-controllers.md) | `python/libsaphir/src/libsaphir/` — abstract template method, ClamAV, ESET/EEA, mock controllers, shared enums/constants |
| [`qml-layer.md`](components/qml-layer.md) | QML structure + MVVM layering + the UI data models |
| [`gui.md`](components/gui.md) | user interface reference — principles, screens, visual status, theming, localization |
| [`viewer.md`](components/viewer.md) | the Viewer application (`python/viewer/`) — read-only file/preview browser, Office→PDF |

---

## 9. How to maintain

Update the architecture documentation when any of the following change:

- A domain is added/removed, or the topology changes → [§3 above](#3-deployment-architecture-safecor-multi-domain).
- A controller is added/removed or a controller's responsibility changes → [`components/`](components/) (one file per component) and [§4/§7 above](#4-software-layering--as-is).
- The communication pattern or topic ownership changes → [`../development/protocol.md`](../development/protocol.md).
- A new state or phase is introduced → [`../specifications/workflow.md`](../specifications/workflow.md) **and** the [§5 summary](#5-state-machine) above.
- A key design decision is made or overturned → add or update an entry in [`decisions/`](decisions/).
- A GUI rule is added or changed → [`components/qml-layer.md`](components/qml-layer.md) and [`design-rules.md`](design-rules.md) — keep the GUI backlog & rule-debt section of [`../project-status.md`](../project-status.md) in sync.

Keep the **as-is** description (§4) and the **to-be** layout (§7) in sync as the refactoring progresses: as each phase lands, move the affected responsibility from the as-is notes to the target layout and mark it done.

# Saphir — Architecture Reference

> **Status**: Draft v1 — for review
> **Last updated**: 2026-10-28
> **Audience**: developers working on the Saphir codebase (refactoring and future features)
> **Scope**: this is the **architecture** reference — the "what" and "how" of the system. It is the single place that ties the whole design together and points to the specialised documents for the details.

## Related documents

| Concern | Document |
|---------|----------|
| What the system must do (behaviour) | [`docs/features.md`](features.md) (F1–F21, NFR-1 to NFR-5) |
| State machine contract (states, transitions, invariants) | [`docs/workflow-rules.md`](workflow-rules.md) |
| User interface (principles, screens, visual status, theming) | [`docs/gui.md`](gui.md) |
| Refactoring phases & effort | [`docs/plans/refactoring-plan.md`](plans/refactoring-plan.md) |
| Spec ↔ implementation gap audit | [`docs/implementation-coverage.md`](implementation-coverage.md) |
| Validation / test strategy | [`docs/test-strategy.md`](test-strategy.md) |

This document deliberately does **not** duplicate those documents. It describes the architecture and links to them.

---

## 1. System context

Saphir is a **sheep-dip**: a secure workstation that scans external media (USB disks) for malware before they enter the organisation's network. It runs on **Safecor**, a multi-domain (multi-VM) operating system for security products, on **Alpine Linux**, distributed as a bootable ISO.

The core value: **multiple antivirus engines vote on every file, with a consensus verdict** (a file is infected if *any* engine flags it; clean only when all agree). Clean files are copied to a second external disk, and a **PDF scan report** + the event journal are produced as evidence.

Two GUI applications share the same platform and swap on the same screen:

- **Main GUI** (`python/gui/`) — the analysis/copy workflow.
- **Viewer** (`python/viewer/`) — a read-only file/preview browser (images, video, audio, Office, PDF; Office→PDF via LibreOffice). It follows the exact same backend pattern as the main GUI and is switched to/from with `Api().switch_gui(...)`.

---

## 2. Deployment architecture (Safecor multi-domain)

Saphir is deployed as **separated Safecor domains** (one VM per concern). The topology is defined in `setup/packages/saphir/saphir/topology.json`:

| Domain | Role | Notes |
|--------|------|-------|
| `saphir-gui` | Main GUI + analysis orchestration | `has_gui: 1`, hosts the `ApplicationController` |
| `saphir-av-clamav` | ClamAV antivirus engine | runs `clamdscan` |
| `saphir-av-eset` | ESET Endpoint antivirus engine | runs in a trimmed LXC container |
| `sys-usb` | Safecor disk/staging domain | the disposable domain destroyed on reset |
| (platform) | Safecor core (disk controller, main controller) | provided by the platform |

Plus the **Viewer** domain (`saphir-viewer`), a separate GUI package that shares the same AV domains and repository.

### 2.1 The shared repository

The domains do **not** share memory. They exchange data through the **repository**, a shared staging area on the `sys-usb` domain (`Constants.STR_REPOSITORY = "__repository__"`, mounted at `/mnt/storage`). Files are staged here before analysis and copied from/to the external disks.

### 2.2 Per-file data flow

```
 saphir-gui                          sys-usb (repository)                 saphir-av-clamav / saphir-av-eset
 -----------                         --------------------                 ------------------------------
 read_file(source, path)  --MQTT-->  stage file into /mnt/storage
       |                                        |
       |                                        +-- NEW_FILE (fingerprint) --MQTT-->
       v
 AnalysisController marks file FileAvailableInRepository
       |
       +-- publish saphir/analysis/request {filepath}
                                            \
                                             \--MQTT-->  ClamAV scans file (worker pool)
                                             \--MQTT-->  ESET  scans file (worker pool)
                                                     |            |
                                  publish saphir/analysis/response {component, filepath, success, details}
                                                     |
       +<---------------------------------------------+
 AnalysisController.__handle_result aggregates per-AV results
       -> when all engines reported -> consensus (any "Infected" => infected)
       -> delete_file from repository (frees slot) -> resultsChanged
```

**Key fact**: all cross-domain coordination is over **MQTT topics**. There is never direct in-process sharing between domains (each domain is its own process/VM).

---

## 3. Software architecture — as-is

### 3.1 Layering

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

### 3.2 The GUI process

Entry point: `python/gui/src/Saphir/main.py`.

- `ApplicationController` is instantiated and `start(on_ready)` is called; this creates the MQTT client and starts the Safecor `Api()`.
- The Qt app **blocks on `api_ready.wait()`** until the API reports ready, then loads `GUI/content/MainScreen.qml`.
- `ApplicationController` is registered to QML as a **singleton instance** (`qmlRegisterSingletonInstance(..., "Saphir", 1, 0, "ApplicationController", ...)`), so QML refers to it directly as `ApplicationController.<member>`.
- The Python `Enums` QEnum holder is registered as `Saphir.Enums` (the QML panels use `Enums.SystemAnalysisRunning`, `Enums.FileStatus*`, …).
- Fonts, screen sizing, and **cursor / input handling** are set up here. **Input model**: Safecor abstracts physical input devices (a USB vector of attack) and exposes **virtual inputs** to the product, injecting the signals transparently. On top of that the app is **touch-first**: the cursor is hidden by default and **re-appears on first mouse movement** (`InputEventFilter` switches `Qt.BlankCursor` → `Qt.ArrowCursor`) — i.e. **automatic environment discovery**, not a configured flag. DevMode handling (Qt plugins path) lives at the top of the file.

**`ApplicationController` (god class)** — the central mediator between the Safecor platform and the QML UI. It currently owns, in a single class:

| Responsibility | Evidence (member / method) |
|----------------|----------------------------|
| System state machine | `__system_state`, `systemState` property, scattered `__set_system_state(...)` calls in message handlers |
| MQTT lifecycle & routing | `start`, `__on_api_ready`, `__on_message_received` (central dispatcher, runs on the MQTT thread) |
| Storage detection | `__source_name/_ready`, `__target_name/_ready`, `__storages`, `__handle_disk_state`, `__handle_list_disks` |
| File browsing & queue | `__input_files_list`, `__queued_files_list`, `enqueue_file`, `dequeue_file`, `go_to_folder`, `__is_enqueuing`, `__folders_to_query` |
| Transfer / copy | `start_transfer`, `__do_start_transfer`, `__handle_copy_file`, `__finish_transfer` |
| Report | `__make_analysis_report`, `__report_controller` (owns a `ReportController`) |
| Energy | `__handle_energy_state`, `__request_energy_state` (5 s timer), `batteryLevel`/`plugged` |
| Language | `__install_translations`, `__translator`, `language` property |
| UI models | `inputFilesListModel`, `queueListModel`, `componentsModel`, `messagesListModel`, `logListModel`, `systemInformationModel` |

It exposes ~38 signals and ~38 `@Property` (see the full list in the refactoring plan). It owns a single-worker `ThreadPoolExecutor` for long processes.

**`AnalysisController`** — owns the analysis queue, the repository-copy loop (a bounded puller), and AV dispatch. It subscribes to the `saphir/analysis/*` response/status/error topics and `NEW_FILE`/`DELETED_FILE`, aggregates per-AV results via `AnalysisHelper`, and emits `stateChanged`, `resultsChanged`, `fileUpdated`, `systemUsed`, `iterationDone`.

**`ReportController`** — generates the PDF: builds a data dict → Jinja2 `scan_report_en.html` → WeasyPrint `write_pdf` → emits `reportGenerated`. (Always the EN template, even though a FR template exists — see coverage audit.)

**`EMAETAEstimator`** — a size-weighted exponential moving average of scan throughput; `remaining_time()` = remaining bytes / current speed.

**`AnalysisHelper`** — pure static methods; the consensus rule lives in `evaluate_result_consensus` (any result `"Infected"` ⇒ file infected).

### 3.3 libsaphir (antivirus controllers)

`python/libsaphir/src/libsaphir/` is the shared library used by the AV domains.

- **`AbstractAntivirusController`** implements the **Template Method** for an antivirus domain: it owns the MQTT client lifecycle, the bounded **worker pool** (a `Queue` + a capped number of `threading.Thread`s, rescheduled via `threading.Timer`), the request routing (`analysis/request|stop|resume|reset`), and the result publishing (`analysis/response`, `analysis/status`). Subclasses implement the abstract hooks: `_on_api_ready`, `_get_component_state`, `_analyse_file`, `_stop_immediately`, `_get_component_version`, `_get_component_description`, `_restart`.
- **`ClamAntivirusController`** — many workers (CPU count); scans by running the `clamdscan` CLI as a subprocess; return code `0`=clean, `1`=infected, `2`=error; pings `clamdscan --ping` for readiness.
- **`EeaAntivirusController`** — **single worker**; scans through shell scripts wrapping the LXC container (`scan-file.sh` then `get-scan-result.sh`, i.e. odscan + lslog); richer return codes (`0`=clean, `10`=incomplete→clean, `50`=infected); pings `lxc-info` for readiness.

Both report over the same `saphir/analysis/*` topics, so the GUI treats them identically.

- **`_constants.py`**: `ANTIVIRUS_NEEDED = 2` (number of AVs that must be **ready** to enable analysis — not a voting threshold), `MOUNT_ARCHIVES = False` (archive mounting disabled), `BIG_FILE_SIZE_IN_MB = -1` (disabled), `TOPIC_ANALYSIS = "saphir/analysis"`, `DEVMODE`.
- **`_enums.py`**: `FileStatus` = `Undefined, GettingFile, FileAvailableInRepository, FileAnalysing, FileAnalysisError, FileClean, FileInfected, FileCopyError, FileCopySuccess`.

### 3.4 QML layer (MVVM)

- **`MainScreen.qml`** — the window root; composes `MainScreenUi` + a top-level `Bindings`.
- **`MainScreenUi.ui.qml`** — the actual layout: `TopBar`, language/theme menus, the swappable content item (three panels: `FilesSelectionPanel` / `AnalysisPanel` / `FilesCopyPanel`), `SystemLoadingPanel`, and all the dialogs (`dlgConnectStorage`, `dlgAnalyseWholeStorage`, `dlgRestart`, `dlgShutdown`, `dlgSystemMustBeReset`, `SystemStateDialog`, `LogDialog`).
- **`Bindings.qml`** — the **single indirection layer** between views and `ApplicationController`: scalar bindings (`ready`, `analysisReady`, `analyzing`, `systemState`, `nbClean`, `nbInfected`, `queueSize`, `remainingTimeInMinutes`, …), model bindings (`sourceFilesListModel`, `queueListModel`, `componentsModel`, …), and method bridges (`startStopAnalysis`, `reset`, `shutdown`, …).
- **`Environment.qml`** — theming singleton: `theme` (default `Constants.dark`) switches every color/image across `ThemeDark` / `ThemeLight` / `ThemeLowVisibility` / `ThemeWireframe`. Also exposes `handheld`, the **form-factor selector**: `handheld` means *medium screen + touch* (a mouse may still be attached) and is meant to drive the UI variant (small "PC" buttons vs. large "touch" buttons, per-screen-size layout). It is currently **forced** (always `True`) and not yet wired to environment discovery — see the form rule (§3.4) and `gui-backlog.md`.
- **`Constants.qml`** — theme ids, Material-icon codes, `enum Section`. (Note: `GUI/Saphir/Enums.qml` is a legacy partial QML singleton shadowed by the Python-registered `Enums`.)

**View-state rule (MVVM)** — the QML views are **stateless projections of the workflow**. What is shown — the active panel, enabled/disabled buttons, open dialogs, editable fields — is **derived directly from `SystemState`** and the published bindings. A view must not *decide* visibility or enablement with its own business conditionals: bind it to a property that already encodes the state (e.g. `enabled: viewModel.canStartAnalysis`) and push any non-trivial derivation into the controller/ViewModel, exposed as a single property. Only **trivially presentational** logic with no workflow meaning (hover highlight, slider clamping, `width > 0 ? a : b`) may live in a view. This keeps the UI deterministic and testable by driving `SystemState` alone.

**Form & responsiveness rule** — the views must be **responsive** and **input-agnostic**. The **primary deployment target** is an **8-inch touch tablet** (touch-first), but the application must also be usable on a **desktop PC with keyboard and mouse**. For now, a **single interface** is used for both, with **different input handling** (touch vs. mouse/keyboard); it must not hard-code the tablet assumption. The layout must tolerate a range of screen sizes so the UI can later **specialise** per target — large screens / desktop, and, if that target becomes viable, smartphone — **without a redesign**. Any view that hard-codes a fixed size, assumes touch-only, or breaks on a non-tablet form factor is **rule-debt** and must be logged in [`gui-backlog.md`](gui-backlog.md).

> **Consolidated UI reference**: the principles above, the QML structure, the screens, the system visual status, theming, and localization are centralised in [`gui.md`](gui.md).

### 3.5 UI data models

All QML-facing list/table data is held in `QAbstractItemModel` subclasses owned by `ApplicationController` and exposed as constant `QObject` properties:

| Model | Base | Role |
|-------|------|------|
| `SafecorInputFilesListModel` (+ `...ProxyModel`) | `QAbstractListModel` | source-disk file browser |
| `QueueListModel` (+ `...ProxyModel`) | `QAbstractListModel` | analysis queue + Clean/Infected/Other filters |
| `ComponentsModel` | `QAbstractTableModel` | component name/state list (F9) |
| `SystemInformationModel` | `QAbstractTableModel` | system info (F9) |
| `MessagesListModel` | `QAbstractItemModel` | message feed (F18, hidden) |
| `LogListModel` | `QAbstractTableModel` | event journal (F5) |

---

## 4. Communication architecture

### 4.1 The single-client constraint

The Safecor `Api` is a **singleton** (`safecor._api.Api` uses `SingletonMeta`). Therefore **each process has exactly one `Api()` / one `MqttClient`**. Because each Safecor domain is its own VM/process, the constraint is *per-domain*: the GUI, ClamAV, and ESET domains each hold their own singleton. Consequences for Saphir:

- Only **one** object per process may create/manage the MQTT client.
- All other objects must funnel through that one client (subscribe/publish on the shared `Api()`).
- In the target architecture, a dedicated **`ApiLifecycle`** module is the *sole* owner of client creation and subscription management (invariant **I1**).

### 4.2 Topic map

**Safecor topics** (consumed/produced by the GUI via high-level `Api()` calls — each is a `/request` + `/response` pair):

| Topic | High-level `Api()` call | Saphir consumer |
|-------|--------------------------|-----------------|
| `system/disks/state` (`DISK_STATE`) | — (notification) | storage detection |
| `system/disks/list_disks` | `get_disks_list()` | storage list |
| `system/disks/list_files` | `get_files_list()` | file browser |
| `system/disks/read_file` | `read_file()` | repository staging (→ `NEW_FILE`) |
| `system/disks/copy_file` | `copy_file()` | transfer to target |
| `system/disks/create_file` | `create_file()` | report/journal copy |
| `system/discover/components` | `discover_components()` | component readiness |
| `system/energy/state` | `request_energy_state()` | battery/plugged |
| `system/info` | `request_system_info()` | system info, repository capacity |
| `system/settings/languages/default` | `get_default_language()` | default language |
| `system/gui/switch` | `switch_gui()` | swap to Viewer / back |
| `system/workflow/{shutdown,restart_domain,gui_ready}` | `shutdown()`, `restart_domain()`, `notify_gui_ready()` | lifecycle |
| `system/events/#` | — (notification) | `LogListModel` (journal) |

**Saphir custom topics** (`TOPIC_ANALYSIS = "saphir/analysis"`):

| Topic | Publisher | Subscriber | Purpose |
|-------|-----------|------------|---------|
| `saphir/analysis/request` | GUI `AnalysisController` | each AV domain | "analyse this file" |
| `saphir/analysis/response` | each AV domain | GUI `AnalysisController` | scan result `{component, filepath, success, details}` |
| `saphir/analysis/status` | each AV domain | GUI (currently ignored) | progress |
| `saphir/analysis/error` | each AV domain | GUI `AnalysisController` | scan error |
| `saphir/analysis/stop` / `resume` | GUI `AnalysisController` | each AV domain | pause / run |
| `saphir/analysis/reset` | GUI `AnalysisController` | each AV domain | drain queue + stop |

**Topic ownership**: each topic has exactly **one** Saphir subscriber — the tables above are the single source of truth for the ownership matrix (which component owns which topic). In the target architecture this is enforced by `ApiLifecycle`. (A duplicate of this matrix used to live in `workflow-rules.md` §8; it has been consolidated here.)

### 4.3 Request/response pattern

The Safecor API is **asynchronous**: a call publishes a `/request`; the result arrives later on the matching `/response` topic and is dispatched to a registered callback. Notifications (no `/request`) such as `DISK_STATE`, `NEW_FILE`, `DELETED_FILE`, `EVENTS` arrive as unsolicited messages. All Saphir MQTT message handling happens **on the MQTT thread** (the handlers must be thread-safe and must not block).

---

## 5. State machine

The workflow is a deterministic state machine from boot to shutdown. The **canonical states, transition table, invariants, UI mapping, and scenarios** are defined in [`docs/workflow-rules.md`](workflow-rules.md) — that document is the contract.

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

**As-is reality** (important for the refactoring): the state transitions are **not** centralised — `__set_system_state(...)` is called from several scattered message handlers (`__handle_disk_state`, `__on_results_changed`, `__handle_create_file`, …), and a few enum states are dead/unreachable. The target architecture centralises this in a single **`WorkflowController`** (invariant **I3**: only it may set `SystemState`). See the refactoring plan Phase 1.

---

## 6. Data model & consensus

### 6.1 The queue item

The queue is an in-memory **dict of dicts** (`__queued_files_list` in the as-is code), keyed by file path. Each entry carries the fields shown in `FilesProgress`/`AnalysisPanel` and the per-engine results. The shared reference is passed to `AnalysisController` in its constructor. The full per-file lifecycle is tracked with `FileStatus` (section 3.3).

### 6.2 Consensus rule

A file is **infected if any antivirus engine reports it infected**; it is **clean only when all engines agree clean**. Implemented in `AnalysisHelper.evaluate_result_consensus`. `ANTIVIRUS_NEEDED = 2` gates whether analysis is *enabled* (enough engines ready), it is **not** a voting threshold. See invariant **I6** and feature F3.

### 6.3 Integrity (fingerprint)

Safecor computes a fingerprint on every file operation; Saphir is expected to compare them end-to-end (source→repository, at analysis, repository→target). **This is currently not enforced** and is the most critical gap — see NFR-1 in [`docs/implementation-coverage.md`](implementation-coverage.md).

---

## 7. Target architecture — to-be

The goal is to decompose the `ApplicationController` god class into **single-responsibility controllers** coordinated by a central state machine. The detailed plan, phases, and effort estimate are in [`docs/plans/refactoring-plan.md`](plans/refactoring-plan.md).

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

## 8. Key design decisions

| # | Decision | Rationale |
|---|----------|-----------|
| D-arch-1 | Event-driven, no polling of state (except the 5 s energy poll) | Safecor is notification-based; the GUI reacts to MQTT events |
| D-arch-2 | Per-domain single `Api()` client, all traffic via MQTT | Safecor isolation model; no shared memory between VMs |
| D-arch-3 | Repository as the only data exchange point between GUI and AV domains | Keeps AV domains stateless w.r.t. file content; staging enables parallelism |
| D-arch-4 | Template Method for AV controllers | New engines plug in by implementing 7 hooks, no changes to the GUI |
| D-arch-5 | Consensus = OR on "infected" | Conservative security posture (any hit ⇒ not clean) |
| D-arch-6 | Stateless system (no persistence between cycles) | Driven by Safecor; reset destroys disposable domains |
| D-arch-7 | Central `WorkflowController` as the only state mutator | Removes the as-is scattered-transition anti-pattern |
| D-arch-8 | Views are a pure projection of `SystemState` — no business logic in QML | UI stays deterministic & testable by driving workflow state alone (see §3.4 view-state rule) |
| D-arch-9 | Responsive, input-agnostic views — 8-inch touch tablet primary, desktop PC (keyboard + mouse) also supported | One interface for now (different input handling); layout tolerates screen sizes for future per-target specialisation; deviations = rule-debt in `gui-backlog.md` (§3.4 form rule) |

---

## 9. Known issues & technical debt

The authoritative list is [`docs/implementation-coverage.md`](implementation-coverage.md). Architecture-relevant highlights:

- **God class** `ApplicationController` — the main target of the refactoring (§7).
- **Scattered state transitions** + 4 unreachable enum states — addressed by `WorkflowController` (Phase 1).
- **Thread safety**: shared dicts (`__queued_files_list`, `__input_files_list`) touched from the MQTT thread with only partial locking; a transfer-race in `__get_transferred_ratio`.
- **Fingerprint never compared** (NFR-1) — critical integrity gap.
- **Hardcodes**: `cpu_count = 8` (bug #54), `targetAvailableSize` typed `bool`, `classificationLevel` hardcoded 0, report always EN, `handheld` always `True`.

---

## 10. How to maintain this document

Update this document when any of the following change:

- A domain is added/removed, or the topology changes (§2).
- A controller is added/removed or a controller's responsibility changes (§3, §7).
- The communication pattern or topic ownership changes (§4).
- A new state or phase is introduced (update `workflow-rules.md` **and** the §5 summary here).
- A key design decision (§8) is made or overturned.
- A GUI rule (§3.4) is added or changed — keep [`gui-backlog.md`](gui-backlog.md) in sync.

Keep §3 (**as-is**) and §7 (**to-be**) in sync as the refactoring progresses: as each phase lands, move the affected responsibility from "as-is" notes to the target layout and mark it done.

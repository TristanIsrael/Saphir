# Application Controller

> **Status**: Stable
> **Last updated**: 2026-11-20
> **Reference**: `python/gui/src/Saphir/Saphir/application_controller.py` (plus `api_lifecycle.py` and `devmode_helper.py`)

## Purpose

`ApplicationController` (QObject) is the central mediator between the Safecor platform and the QML UI. It is the entry component of the main GUI: it owns the boot sequence, the system state machine exposure, the MQTT message routing, the UI models, and it wires together all the sub-controllers (workflow, storage, file browser, queue, transfer, analysis, report, energy, translation). It is registered to QML as a **singleton instance**, so QML refers to it directly as `ApplicationController.<member>`.

## Boot & registration

Entry point: `python/gui/src/Saphir/main.py`.

- `ApplicationController` is instantiated and `start(ready_callback)` is called; this creates the MQTT client and starts the Safecor `Api()`.
- The Qt app **blocks on `api_ready.wait()`** until the API reports ready, then loads `GUI/content/MainScreen.qml`.
- `ApplicationController` is registered to QML as a **singleton instance** (`qmlRegisterSingletonInstance(..., "Saphir", 1, 0, "ApplicationController", ...)`), so QML refers to it directly as `ApplicationController.<member>`.
- The Python `Enums` QEnum holder is registered as `Saphir.Enums` (the QML panels use `Enums.SystemAnalysisRunning`, `Enums.FileStatus*`, …).
- Fonts, screen sizing, and **cursor / input handling** are set up here. **Input model**: Safecor abstracts physical input devices (a USB vector of attack) and exposes **virtual inputs** to the product, injecting the signals transparently. On top of that the app is **touch-first**: the cursor is hidden by default and **re-appears on first mouse movement** (`InputEventFilter` switches `Qt.BlankCursor` → `Qt.ArrowCursor`) — i.e. **automatic environment discovery**, not a configured flag. DevMode handling (Qt plugins path) lives at the top of the file.

## Responsibilities (as-is god class)

It currently owns, in a single class:

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

The target architecture reduces it to a **thin facade** that only wires the sub-controllers — see [../overview.md](../overview.md) §7.

### Sub-controllers & collaborators owned (from `__init__`)

| Collaborator | Component document |
|--------------|--------------------|
| `WorkflowController` | [workflow-controller.md](workflow-controller.md) |
| `StorageManager`, `FileBrowser`, `FileQueue` | [storage-manager.md](storage-manager.md) |
| `TransferController` | [transfer-controller.md](transfer-controller.md) |
| `AnalysisController` (+ `AnalysisHelper`, `EMAETAEstimator`) | [analysis-controller.md](analysis-controller.md) |
| `ReportController` | [report-controller.md](report-controller.md) |
| `ApiLifecycle` | [§ MQTT single-client lifecycle](#mqtt-single-client-lifecycle--api_lifecyclepy) below |
| `EnergyMonitor`, `TranslationManager` | [qml-layer.md](qml-layer.md) (UI data models & services) |
| UI models (`ComponentsModel`, `SafecorInputFilesListModel`/proxy, `QueueListModel`, `LogListModel`, `MessagesListModel`, `SystemInformationModel`) | [qml-layer.md](qml-layer.md) |

## MQTT single-client lifecycle — `api_lifecycle.py`

The Safecor `Api` is a **singleton** (`safecor._api.Api` uses `SingletonMeta`), so **each process has exactly one `Api()` / one `MqttClient`** — the constraint is per-domain. Only **one** object per process may create/manage the MQTT client; all other objects funnel through that one client (see [../../development/protocol.md](../../development/protocol.md) §1 for the full constraint and §3 for the topic map).

`ApiLifecycle` (QObject) is the *sole* owner of subscription management (invariant **I1**):

| Member | Role |
|--------|------|
| `setup_subscriptions()` | subscribes to all required topics once `Api()` is ready: `COPY_FILE/response`, `DISK_STATE`, `LIST_DISKS/response`, `LIST_FILES/response`, `DISCOVER_COMPONENTS/response`, `ENERGY_STATE/response`, `SYSTEM_INFO/response`, `CREATE_FILE/response`, `DEFAULT_LANGUAGE/response`, `ERROR`, `REPOSITORY_PATH/response` |
| `set_all_ready_callback(callback)` | registers the callback invoked once **every** MQTT subscription is confirmed (`_on_subscribed` counts them against the subscription list) |
| `get_logfile()` | path of the Saphir API log file |

`ApplicationController` wires it in its constructor: `__api_lifecycle.set_all_ready_callback(self.__on_all_subscriptions_ready)`.

## DEVMODE helper — `devmode_helper.py`

`DevModeHelper` — factories and environment tweaks for running in **DEVMODE** (no appliance needed):

| Member | Role |
|--------|------|
| `create_mqtt_client(identifier)` | creates a TCP MQTT client pointing at the local debug broker (`ConnectionType.TCP_DEBUG`, `localhost`) |
| `set_qt_plugins_path()` | points `QT_QPA_PLATFORM_PLUGIN_PATH` at the venv PySide6 platforms plugins |

## Links

- State machine contract: [../../specifications/workflow.md](../../specifications/workflow.md)
- Communication architecture (topics, single-client constraint): [../../development/protocol.md](../../development/protocol.md)
- Target layout & invariants: [../overview.md](../overview.md) §7
- UI reference: [gui.md](gui.md)
- Refactoring plan: [../../archive/plans/refactoring-plan.md](../../archive/plans/refactoring-plan.md)

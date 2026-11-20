# QML Layer (MVVM) & UI Data Models

> **Status**: Stable
> **Last updated**: 2026-11-20
> **Reference**: `python/gui/src/Saphir/Saphir/GUI/` (QML) and the model files in `python/gui/src/Saphir/Saphir/`

## Purpose

The QML layer is the presentation of the main GUI. It follows the **MVVM layering**: QML views → `Bindings.qml` (the single indirection layer) → `ApplicationController` (QObject signals/properties/models) → controllers → Safecor `Api()` → MQTT. The views are stateless projections of the workflow; all QML-facing list/table data is held in `QAbstractItemModel` subclasses owned by `ApplicationController` and exposed as constant `QObject` properties.

## QML structure

- **`MainScreen.qml`** — the window root; composes `MainScreenUi` + a top-level `Bindings`.
- **`MainScreenUi.ui.qml`** — the actual layout: `TopBar`, language/theme menus, the swappable content item (three panels: `FilesSelectionPanel` / `AnalysisPanel` / `FilesCopyPanel`), `SystemLoadingPanel`, and all the dialogs (`dlgConnectStorage`, `dlgAnalyseWholeStorage`, `dlgRestart`, `dlgShutdown`, `dlgSystemMustBeReset`, `SystemStateDialog`, `LogDialog`).
- **`Bindings.qml`** — the **single indirection layer** between views and `ApplicationController`: scalar bindings (`ready`, `analysisReady`, `analyzing`, `systemState`, `nbClean`, `nbInfected`, `queueSize`, `remainingTimeInMinutes`, …), model bindings (`sourceFilesListModel`, `queueListModel`, `componentsModel`, …), and method bridges (`startStopAnalysis`, `reset`, `shutdown`, …).
- **`Environment.qml`** — theming singleton: `theme` (default `Constants.dark`) switches every color/image across `ThemeDark` / `ThemeLight` / `ThemeLowVisibility` / `ThemeWireframe`. Also exposes `handheld`, the **form-factor selector**: `handheld` means *medium screen + touch* (a mouse may still be attached) and is meant to drive the UI variant (small "PC" buttons vs. large "touch" buttons, per-screen-size layout). It is currently **forced** (always `True`) and not yet wired to environment discovery — see the form rule (below) and the GUI backlog & rule-debt section of [`../../project-status.md`](../../project-status.md).
- **`Constants.qml`** — theme ids, Material-icon codes, `enum Section`. (Note: `GUI/Saphir/Enums.qml` is a legacy partial QML singleton shadowed by the Python-registered `Enums`.)

## View-state rule (MVVM)

The QML views are **stateless projections of the workflow**. What is shown — the active panel, enabled/disabled buttons, open dialogs, editable fields — is **derived directly from `SystemState`** and the published bindings. A view must not *decide* visibility or enablement with its own business conditionals: bind it to a property that already encodes the state (e.g. `enabled: viewModel.canStartAnalysis`) and push any non-trivial derivation into the controller/ViewModel, exposed as a single property. Only **trivially presentational** logic with no workflow meaning (hover highlight, slider clamping, `width > 0 ? a : b`) may live in a view. This keeps the UI deterministic and testable by driving `SystemState` alone.

## Form & responsiveness rule

The views must be **responsive** and **input-agnostic**. The **primary deployment target** is an **8-inch touch tablet** (touch-first), but the application must also be usable on a **desktop PC with keyboard and mouse**. For now, a **single interface** is used for both, with **different input handling** (touch vs. mouse/keyboard); it must not hard-code the tablet assumption. The layout must tolerate a range of screen sizes so the UI can later **specialise** per target — large screens / desktop, and, if that target becomes viable, smartphone — **without a redesign**. Any view that hard-codes a fixed size, assumes touch-only, or breaks on a non-tablet form factor is **rule-debt** and must be logged in the GUI backlog & rule-debt section of [`../../project-status.md`](../../project-status.md).

> **Consolidated UI reference**: the principles above, the QML structure, the screens, the system visual status, theming, and localization are centralised in [`gui.md`](gui.md).

## UI data models

All QML-facing list/table data is held in `QAbstractItemModel` subclasses owned by `ApplicationController` and exposed as constant `QObject` properties:

| Model | Base | Role | Source file |
|-------|------|------|-------------|
| `SafecorInputFilesListModel` (+ `...ProxyModel`) | `QAbstractListModel` | source-disk file browser | `safecor_input_files_list_model.py` / `safecor_input_files_list_proxy_model.py` |
| `QueueListModel` (+ `...ProxyModel`) | `QAbstractListModel` | analysis queue + Clean/Infected/Other filters | `queue_list_model.py` |
| `ComponentsModel` | `QAbstractTableModel` | component name/state list (F9) | `components_model.py` |
| `SystemInformationModel` | `QAbstractTableModel` | system info (F9) | `system_information_model.py` |
| `MessagesListModel` | `QAbstractItemModel` | message feed (F18, hidden) | `messages_list_model.py` |
| `LogListModel` | `QAbstractTableModel` | event journal (F5) | `log_list_model.py` |
| `SafecorOutputFilesListProxyModel` | `QSortFilterProxyModel` | proxy over the output (target) file list | `safecor_output_files_list_proxymodel.py` |

The models are built on the shared structures owned by the storage layer — `FileBrowser.input_files_list` and `FileQueue.files` (see [storage-manager.md](storage-manager.md)) — and are refreshed by `ApplicationController` signals (`fileUpdated`, `queueUpdated`, `allFilesUpdated`, …).

## Supporting QObject services

| File | Class | Role |
|------|-------|------|
| `translation_manager.py` | `TranslationManager` (QObject) | QTranslator lifecycle, language switching (F14); signals `languageChanged`, `translationInstalled` |
| `energy_monitor.py` | `EnergyMonitor` (QObject) | battery/plugged polling (5 s timer); signals `batteryLevelChanged`, `pluggedChanged` |

## Links

- UI reference (screens, visual status, theming, localization): [gui.md](gui.md)
- State → screen mapping (contract): [../../specifications/workflow.md](../../specifications/workflow.md) §7
- God class that owns the models: [application-controller.md](application-controller.md)
- Underlying data structures: [storage-manager.md](storage-manager.md)
- Rule-debt & GUI backlog: [../../project-status.md](../../project-status.md) (GUI backlog & rule-debt)

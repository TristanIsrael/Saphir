# Viewer Application

> **Status**: Stable
> **Last updated**: 2026-11-20
> **Reference**: `python/viewer/src/viewer/` (entry: `python/viewer/src/viewer/main.py`)

## Purpose

The **Viewer** is a separate, **read-only file/preview browser** for the content of the source disk (images, video, audio, Office, PDF). It follows the exact same backend pattern as the main GUI and is **swapped with the main GUI on the same screen** via `Api().switch_gui(...)` (`system/gui/switch`, feature F15). Office documents are converted to PDF via **LibreOffice** before preview. It is deployed in its own domain (`saphir-viewer`) and packaged in the `saphir-viewer` Alpine package.

## Deployment

- Domain `saphir-viewer` (Dom0, `has_gui`) — a separate GUI package that shares the same AV domains and the shared repository (see [../overview.md](../overview.md) §3).
- Entry point: `python/viewer/src/viewer/main.py` → `Viewer.ApplicationController.start(ready_callback)`; the Qt app blocks on `api_ready.wait()` then loads `GUI/content/MainScreen.qml`.
- `ApplicationController` is registered to QML as a singleton (`"Viewer"`, `ApplicationController`) and the `Enums` holder as `Viewer.Enums` (including `FileType`).
- Fonts (Material icons) and DEVMODE handling (`Viewer/devmode_helper.py`) mirror the main GUI pattern.

## Backend — `Viewer/` package

- **`ApplicationController`** (QObject) — the mediator between the Safecor platform and the Viewer QML UI, with the same structure as the main GUI's:
  - source-disk detection: `__handle_disk_state`, `__handle_list_disks`, `on_disk_selected(disk)`;
  - file listing & navigation: `update_source_files_list`, `go_to_folder(folder)`, `go_to_parent_folder()`, `__handle_list_files`;
  - file preview: `view_file(filepath)`, `clear_current_file()`, `__get_current_file_type()` → `FileType` (`Unknown, Image, Video, Audio, Office, Pdf`) resolved from the file extension (`ViewerConstants`);
  - energy state: `__handle_energy_state`, `__request_energy_state` (5 s timer);
  - language: `__install_translations(language)`;
  - shutdown: `__on_shutdown(accepted, reason)`;
  - **`back_to_saphir()`** → `Api().switch_gui("saphir-gui")` — switches back to the main GUI (the reverse direction is done from the main GUI with `switch_gui("saphir-viewer")`).
- **`OfficeHelper`** — Office → PDF conversion via LibreOffice: `convert_to_pdf(document_filepath)` runs `soffice --headless --convert-to pdf <repository filepath> --outdir /tmp` and returns the path of the generated PDF (in DEVMODE, `DevModeHelper` provides the LibreOffice path and the repository path).
- **Models**: `SafecorInputFilesListModel` (+ `SafecorInputFilesListProxyModel`) — the source-disk file browser list, same pattern as the main GUI.
- `devmode_helper.py`, `enums.py` (`FileType`, `SystemState`), `constants.py` — DEVMODE support and shared definitions.

## QML

- `GUI/content/`: `MainScreen.qml` (window root), `MainScreenUi.ui.qml` (layout), `Bindings.qml` (single indirection layer), `ViewerPanel.qml` (preview area), `FilesSelectionPanel.qml` (file browser), `MediaViewer.qml` / `MediaControl.qml` (media playback), `TopBar.qml` / `TopBarUi.ui.qml`, `Brightness.qml`, `Energy.qml`.
- `GUI/Components/`: `Environment.qml` (theming), `FlatButton.qml`, `RoundButton.qml`, `ShadowButton.qml`, `TwoStatesButton.qml`, `Panel.qml`, `PanelBase.qml`, `StyledComboBox.qml`, …

## Links

- GUI switch protocol (`system/gui/switch`): [../../development/protocol.md](../../development/protocol.md)
- Feature F15 (switch to the media viewer): [../../specifications/features.md](../../specifications/features.md)
- Deployment & shared repository: [../overview.md](../overview.md) §3
- Main GUI: [gui.md](gui.md), [application-controller.md](application-controller.md)

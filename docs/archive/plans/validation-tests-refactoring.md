# Validation tests

This document contains the observations made during the validation tests of the refactoring branch.

## Run 1

- Step: Setup (one-time)
- The command `bash setup_dev_env.sh` creates a venv in the directory `.venv`. If running on MacOS, the venv should be in the directory `venv.nosync`.
- The evdev dependency is not available on MacOS. It should be removed from the dependencies. 
- Tests are stucked at this step.

### Corrections applied (`2589140`)

- **Venv path**: configurable via `SAPHIR_VENV_DIR` env var. On macOS: `SAPHIR_VENV_DIR=./venv.nosync bash setup_dev_env.sh`.
- **Linux-only deps** (`evdev`, `inotify_simple`, `pyudev`): now optional in `setup_dev_env.sh` — installed when available, skipped with a warning otherwise (same pattern as `libvirt-python`).
- `validate_env.sh` also honors `SAPHIR_VENV_DIR`.

## Run 2 (incremental)

- Step: Setup (one-time)
- In the last step (`[4/4] Verifying imports...`), it fails to import safecor
- Tests are stucked at this step.

### Corrections applied (`88dd0db`)

- **Root cause**: `SAFECOR_ROOT` defaults to `/home/onyxia/work/Safecor` which doesn't exist on the validator's machine. The `.pth` files pointed to a non-existent path.
- **Fix**: `setup_dev_env.sh` now validates that `SAFECOR_ROOT/python/lib/src` exists before creating `.pth` files. If not, it exits with a clear error message.
- **Usage**: `SAFECOR_ROOT=/path/to/Safecor bash setup_dev_env.sh`
- Validation guide updated with the `SAFECOR_ROOT` prerequisite.

## Run 3 (incremental)

- Step: Nominal cycle (C.1)
- In the emulator GUI there is no button to select the path of the disk. We need one.
- In the step 1, the real state of the system is `SystemWaitingForUserAction` and Saphir's GUI show the panel `Do you want to analyze the whole storage?` which is the expected behaviour and the expected state.
- The actions are not detailed enough: we miss an action between step 1 and 2 saying `Accept the whole storage analysis` or maybe we expect the system to automatically trigger the whole storage analysis?
- The scenarios chapters should begin with a short description of the scenario and the expected behaviour.
- In the emulator GUI the fields `id` and the path of the disk should be reset after a disk has been attached, otherwise it is confusing.
- The states are not correct: at the end of the step 3 the state is `AnalysisCompleted`, the step 4 begins with the state `CopyCleanFiles` then `Generating Report` and finally `SystemMustBeReset`.
- The action in step 6 should not mention `/tmp/target-disk` because we don't know which target path the user choosed.
- **BUG**: I defined the target path `/tmp/out` and all the files were copied to `/tmp`, including the log file and the report.

### Corrections applied (validation guide)

- **States corrected**: `AnalysisCompleted`, `CopyCleanFiles`, `GeneratingReport`, `SystemMustBeReset`.
- **Missing action added**: "Accept the whole storage analysis" between steps 1 and 2.
- **Scenario descriptions added** to all 8 scenarios.
- **Generic target path** in step 6 (no hardcoded `/tmp/target-disk`).

### Open items

| # | Item | Repo | Status |
|---|------|------|--------|
| 1 | Emulator GUI: no button to select disk path | Safecor | ✅ Fixed in PR #245 (Browse button added) |
| 2 | Emulator GUI: reset `id` + path fields after attach | Safecor | ✅ Fixed in PR #245 (`diskAttached` signal clears fields) |
| 3 | **Files copied to `/tmp` instead of the target path** | Safecor | ✅ Fixed in PR #245 — "Target disk" field in Setup panel, passed to `Emulator(destination_disk_path=...)` before `start()` |

### Safecor fixes (PR #245, branch `fix-242-243-244`)

- **#242**: `SetupPanel.qml` — new "Target disk" TextField + Browse button; `ConsoleController` exposes `destinationPath` property; `start_emulator()` passes it to `Emulator(destination_disk_path=...)`.
- **#243**: `ControlPanel.qml` — "Browse..." button (folder picker) next to the disk path field.
- **#244**: `ConsoleController` emits `diskAttached` signal after successful attach; `ControlPanel.qml` clears `diskIdField` + `diskPathField` on that signal.

## Run 4 (incremental)

- Step: Infected file (F3 consensus)
- When Saphir has started it keeps showing `System state: SystemState.SystemReady` in the log
- The procedure is to complex. The configuration file for the behaviour of the mock AV should be provided to the same script `validate_env.sh` that should be used for all the tests.

### Corrections applied

- **Safecor PR #246 + #247** (merged into `feature-241`):
  - `destination_disk_path` removed: the last attached disk is the copy target.
  - Repository path field added in Disks panel (default `/tmp/safecor/storage`, folder picker).
  - Topology, Configuration, Repository fields are read-only while the emulator is running.
  - Periodic `discover/components` timer removed from `ComponentsPanel.qml`.
  - All disk/file dialogs use `selectFolder` for directory selection.
- **Saphir `8bf1376`**: `validate_env.sh` accepts `--config <file.json>` to control mock AV behaviour (infected/clean files). Usage: `bash validate_env.sh --config /path/to/av_config.json`.

## Run 5 (incremental)

- Step: Infected file (F3 consensus)
- Emulator started with no disk attached
- Saphir starts and waits for a source disk
- Attach the `src` disk in the Emulator
  - The analysis starts immediatly and the dialog `Do you want to analyze the whole storage?` is also visible
  - The analysis does not finish, it is stucked at around 25% and after a moment the app crashes

### Corrections applied (`4c147e5`)

- **Root cause**: In DEVMODE, a 1s grace timer (`DEVMODE_SCAN_START_GRACE`) automatically called `start_full_analysis()` after disk attachment, bypassing the user confirmation dialog. The analysis started before the mock AVs were ready, causing the crash.
- **Fix**: New env var `DEVMODE_AUTO_START` (default `1` for tests). `validate_env.sh` sets `DEVMODE_AUTO_START=0` so the operator must manually confirm via the dialog.
- **Validation guide updated**: scenarios now explicitly say "accept the analysis" instead of "let analysis start".

## Run 6 (incremental)

- Step: Infected file (F3 consensus)
- Emulator started with no disk attached
- Saphir starts and waits for a source disk
- Attach the `src` disk in the Emulator
  - The 8 first files are copied into the storage
  - The files are not analysed, their status is `File ready` in the GUI
  - The logs are:
```
System state: SystemState.SystemAnalysisRunning
File /var/folders/ph/ckhh2rkx24dcxpb7mbs6002r0000gn/T/saphir.log opened in a mode.
Antivirus start thread for file /cat
An error occured while calculating the fingerprint of the file /mnt/storage/cat
[Errno 2] No such file or directory: '/mnt/storage/cat'
Antivirus start thread for file /echo
An error occured while calculating the fingerprint of the file /mnt/storage/echo
[Errno 2] No such file or directory: '/mnt/storage/echo'
AV controller says that the analysis is finished without error
Antivirus start thread for file /launchctl
An error occured while calculating the fingerprint of the file /mnt/storage/launchctl
[Errno 2] No such file or directory: '/mnt/storage/launchctl'
AV controller says that the analysis is finished without error
Antivirus start thread for file /df
An error occured while calculating the fingerprint of the file /mnt/storage/df
[Errno 2] No such file or directory: '/mnt/storage/df'
AV controller says that the analysis is finished without error
Antivirus start thread for file /pwd
An error occured while calculating the fingerprint of the file /mnt/storage/pwd
AV controller says that the analysis is finished without error[Errno 2] No such file or directory: '/mnt/storage/pwd'

Antivirus start thread for file /test
An error occured while calculating the fingerprint of the file /mnt/storage/test
[Errno 2] No such file or directory: '/mnt/storage/test'
AV controller says that the analysis is finished without error
Antivirus start thread for file /csh
An error occured while calculating the fingerprint of the file /mnt/storage/csh
[Errno 2] No such file or directory: '/mnt/storage/csh'
AV controller says that the analysis is finished without error
Antivirus start thread for file /wait4path
An error occured while calculating the fingerprint of the file /mnt/storage/wait4path
[Errno 2] No such file or directory: '/mnt/storage/wait4path'
AV controller says that the analysis is finished without error
AV controller says that the analysis is finished without error
```
- The Saphir AV components do not respond to the message `system/discover/components/request` so they don't appear in the Emulator.

### Corrections applied (`2a78175` + Safecor `feature-232`)

- **Root cause**: AV controllers used a hardcoded path (`/mnt/storage`) or the `SAPHIR_REPOSITORY_PATH` env var to locate the repository. On the validator's machine the actual path differs (e.g. macOS `/var/folders/...`), causing fingerprint failures. The GUI also had no way to learn the actual path from the emulator.
- **Fix — `repository_path` protocol** (Safecor issue #232):
  - New MQTT topics: `system/disks/repository_path/request` + `system/disks/repository_path/response`.
  - `MockDom0` responds with its actual storage path.
  - `Api.request_repository_path()` added to the Safecor Python library.
  - GUI: on `__app_ready()`, calls `request_repository_path()`; `SystemReady` now requires the path to be received.
  - AV controllers (abstract base): subscribe to `repository_path/response` at startup; state machine requires BOTH the path AND engine readiness before transitioning to `READY`.
  - `SAPHIR_REPOSITORY_PATH` env var and `--storage` parameter removed from all code and scripts.
- **AV state machine rework** (`AbstractAntivirusController`):
  - State management moved to the base class (was duplicated in each subclass).
  - `_engine_is_ready()` virtual method: `ClamAV`/`ESET` check daemon/container ping; `MockAV` defaults to `True`.
  - `_notify_engine_ready()` called when the engine-specific check passes.
- **Emulator fix** (`mock_sys_usb.py`): `attach_disk` now tracks `__known_disk_ids` to prevent re-attachment of a source disk from overwriting the copy destination path.
- **Validation status**: pending next run to confirm the fingerprint errors are resolved and AV components appear in the Emulator.

## Run 7 (incremental)

- Step: Source disconnection during analysis (8.8)
- When we analyze a big disk (choice `whole disk`) with 800 000+ files the enqueuing is very long and the GUI is unresponsive during the operation. The user should be notified that a long operation is running ("Please wait while getting the files list" for example)
- When disconnecting the source disk, the message is shown but is it not on the correct layer, it is behind the language selection button. 
  - Additionally it is to large and should reduced to around 70% of the width of the window.
  - There should be a background with a reduced opacity in order to improve the contrast.

### Corrections applied (`165a94e`)

- **Enqueuing performance**: Removed per-file `fileUpdated.emit` during bulk enqueuing. The O(n²) caused by per-file `dataChanged` signals (linear scan in both list models) is eliminated. A single `reset()` on both models is triggered when enqueuing completes via the existing `queueUpdated` signal.
- **"Getting the files list" overlay**: New `Rectangle` overlay in `MainScreenUi.ui.qml` (70% width, semi-transparent background, `z: 1.0`) visible while `longProcessRunning` is true and the system is not yet analysis-ready. The `longProcessRunning` property (already toggled correctly in Python) is now exposed in `Bindings.qml`.
- **Source disconnection overlay**: Replaced the in-flow `StyledText` (top of `AnalysisPanel`, no background, full width, behind corner buttons) with a proper overlay in `MainScreenUi.ui.qml`: 70% window width, `Environment.colorWarning` background at 0.9 opacity, `z: 1.0`, centered horizontally.

## Run 8 (incremental)

- Step: Source disconnection during analysis (8.8)
- When the analysis is paused because the source disk has been detached, if we close Saphir it does not quit, the AVs seem to remain started.
- When unchecking a folder in the file navigator nothing happens: the files are not removed and the box remains checked. The same for a single file. It seems to be a regression from the change of the behaviour of the Model-View in the last run.

### Corrections applied

- **App hang on close during held analysis**: The copy loop (`__do_copy_files_into_repository`) uses `threading.Timer` which is non-daemon by default. While the source is held, the timer re-arms every 0.5 s indefinitely, blocking Python's `threading._shutdown()` at interpreter exit. Fix: set `daemon = True` on all three `threading.Timer` instances in the copy loop.
- **Folder uncheck not reflected in UI**: `FileQueue.dequeue_folder` was reassigning `self._files` to a new dict (`self._files = {k: v for ...}`), which invalidated the by-reference handle held by `SafecorInputFilesListModel.__queuedFilesList` (and `QueueListModel`, `AnalysisController`). The `inqueue` role kept reading from the stale dict. Fix: mutate the dict in-place (`del self._files[key]` per matching key) so all reference holders see the change.

## Run 9 (incremental)

- Step: AV engine failure (NFR-3, 8.9)
- In the emulator there is no Saphir component so I cannot restart an AV for the test.

### Corrections applied (Safecor `main`)

- **`discover_components` multi-response**: The emulator's `discover_components()` used `_request_response` which returns on the **first** response only. The in-process mock peers (Dom0, sys-usb) respond before the external mock AV processes, so their components were never collected. Fix: `discover_components` now uses a dedicated MQTT client that collects **all** responses over a 2 s window, then aggregates the component list.
- **`mock_sys_usb` wildcard subscription**: The mock SysUsb subscribed to `system/+/+/request` (catch-all), intercepting topics meant for Dom0 (e.g. `system/energy/state/request`) and logging them under "SysUsb". Fix: replaced with specific disk-topic subscriptions (`list_disks`, `list_files`, `read_file`, `copy_file`, `create_file`, `mount_file`, `unmount`, `discover/components`).
- **Note on restart/ping dropdowns**: These use `startedDomains` (topology business domains + core peers), not the MQTT discovery. The Saphir topology must be loaded in the emulator (SetupPanel) for `saphir-av-clamav` / `saphir-av-eset` to appear in those dropdowns.

## Run 10 (incremental)

- Step: Target disconnection during copy (F4, 8.6)
- Nothing happens when I click on the button for copy (btnCopyFiles) at the end of the analysis. It should move to the panel FileCopyPanel ; but when I attach a second disk the panel shows.
- If I start Saphir with 2 disks attached it shows the dialog "Do you want to analyse the whole disk?", but when I detach one of them, it comes back to the "Please connect a storage" dialog.
- The copy is to fast and I don't have enough time to detach the disk. There should be a delay between to copies so the copy lasts longer.

### Corrections applied

- **`btnCopyFiles` regression** (commit `d0e1cdf` removed the handler without replacement): Added `enter_copy_phase()` slot to `ApplicationController` that transitions to `CopyCleanFiles` state and starts the transfer if a target is already connected. Wired the button via `Bindings.qml` (`startCopyPhase()`) and `MainScreen.qml` (`Connections` block). Fixed `FilesCopyPanel.qml` text condition that was dead code (checked `AnalysisCompleted` but the panel is only visible in `CopyCleanFiles`/`GeneratingReport`/`ReportFailed`).
- **Source disk detach reset**: `__on_disk_disconnected` called `__reset_states()` when a source was removed, clearing the storage list and losing the still-connected disk. Fix: after `remove_source`, if other sources remain and analysis hasn't started, re-emit `sourceReadyChanged` to re-trigger the disk selection dialog instead of resetting.
- **Copy speed** (deferred): The copy loop in `transfer_controller.py` issues all `copy_file` calls back-to-back. A delay would be needed for testing the disconnection scenario, but this would slow down production. Deferred for now.

## Run 11 (incremental)

- Step: Target disconnection during copy (F4, 8.6)
- When I detach the destination disk nothing happens. Saphir seems not to detect the disconnection. It should interrupt the report generation and files copy but everything keeps going on and no error is triggered.
- The language button is empty, there no language, not even the `EN`.

### Corrections (2026-11-05)

1. **Emulator accepted writes to disconnected disk** (Safecor #248): `MockSysUsbController` did not check if the referenced disk was still connected before accepting `COPY_FILE` / `CREATE_FILE`. Fixed: both handlers now validate the disk is in the connected list and return an error response if not.
2. **State machine allowed report generation on a paused copy** (Saphir #160): `TransferController.__check_transfer_complete` did not guard against `_copy_paused`. Fixed: it now returns early when paused. `__resume_copy` calls `__check_transfer_complete` after the re-copy loop so the transfer completes on resume.
3. **`__handle_create_file` ignored the `success` field**: a failed `CREATE_FILE` was not handled as an error. Fixed: it now checks `success` and goes to `SystemMustBeReset` with an error message when `False`.
4. **Language button empty**: the `language` property in `MainScreenUi.ui.qml` had the placeholder value `"This is a string"`. Fixed: set to `""`.

## Run 12 (incremental)

- Step: Multi-source (F1, 10.8)
- When I select 1 file in one disk and 1 file in another disk, I start the analysis and then I plug my target device, the files are copied and the report too. But The log file is not copied, and Saphir remains stucked in the state SystemState.GeneratingReport.

### Corrections (2026-11-05)

1. **Journal sent uncompressed over MQTT**: The `journal.log` was sent with `binary=False` (no compression). As the log grew (cumulative across runs), the base64-encoded MQTT payload exceeded the broker message size limit and was silently dropped. Fixed: send with `binary=True` (zlib compression).
2. **Cumulative journal**: The `saphir.log` file was never reset, growing with each application session. Fixed: the log file is now truncated at application startup (`ApplicationController.start()`).

## Run 13 (incremental)

- Step: Language change (F19)
- The language button appears but it is empty and nothing happens when I click on it.

### Corrections (2026-11-05)

1. **Default language was `""` instead of `"en"`**: The `TranslationManager` initialized the language to an empty string, and the QML visibility/click logic used `language === ""` to detect EN. This caused a conflict with the `RoundButton` icon alias. Fixed: the default language is now `"en"` (explicit), the EN button visibility checks `language === "en"`, and clicking EN sets `language = "en"`.

## Run 14 (incremental)

- When I start Saphir with 2 disks attached, and I remove both, the dialog "Do you want to analyze the whole storage?" remains visible but it should not. The dialog "Please connect a storage" is also shown behind and becomes visible when we close the othe dialog.
- When I attach a very big disk (800 000 files) and I accept to analyze the whole storage the message "Getting the files list..." is never shown.

**Corrections**:
1. **Dialog remained visible on disk disconnection**: The `onSourceReadyChanged` handler in `MainScreen.qml` only showed the dialog when `sourceReady` became `true`, never hiding it when it became `false`. Fixed: the handler now sets `visible = ApplicationController.sourceReady` directly, so the dialog hides when all source disks are removed.
2. **"Getting the files list..." overlay never shown**: The overlay visibility condition was `bindings.longProcessRunning && !bindings.analysisReady`, but `analysisReady` stays `true` once the system is initialized (antiviruses connected). Fixed: (a) `start_full_analysis()` now transitions to `SystemGettingFilesList` state, (b) the overlay condition is now `bindings.systemState === Enums.SystemGettingFilesList`, which is the correct state-machine-driven condition.

## Run 15 (in production)

- When I start Saphir, the antiviruses are not detected, so Saphir never becomes ready. When I investigate on the Domains, I can see that both the antivirus and the controller are started. When I restart the controller I don't see any MQTT message on the `system/discover/components/` topic. The antiviruses should notify on this topic when they are ready.
- `system/disks/repository_path/request` does not receive an answer.
- When I switch to the french language, there is an error in the log: `No translation found for the language fr`

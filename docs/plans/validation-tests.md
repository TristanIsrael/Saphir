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

## Run 2

- Step: Setup (one-time)
- In the last step (`[4/4] Verifying imports...`), it fails to import safecor
- Tests are stucked at this step.

### Corrections applied (`88dd0db`)

- **Root cause**: `SAFECOR_ROOT` defaults to `/home/onyxia/work/Safecor` which doesn't exist on the validator's machine. The `.pth` files pointed to a non-existent path.
- **Fix**: `setup_dev_env.sh` now validates that `SAFECOR_ROOT/python/lib/src` exists before creating `.pth` files. If not, it exits with a clear error message.
- **Usage**: `SAFECOR_ROOT=/path/to/Safecor bash setup_dev_env.sh`
- Validation guide updated with the `SAFECOR_ROOT` prerequisite.

## Run 3

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

## Run 4

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

## Run 5

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

## Run 6

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

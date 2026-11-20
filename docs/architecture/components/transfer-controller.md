# Transfer Controller

> **Status**: Stable
> **Last updated**: 2026-11-20
> **Reference**: `python/gui/src/Saphir/Saphir/transfer_controller.py`

## Purpose

`TransferController` (QObject) orchestrates the **copy of the clean files** from the source disk(s) to the target disk. It tracks the copy progress and the number of copied/failed files, handles a source or target **disconnected during the copy** (scenario 8.6: the copy is paused until the *same* disk is re-inserted), and runs a **final coherence check** on the reconnected disk before auto-resuming — if the disk is different, the system must be reset (NFR-4).

## Key API

| Member | Role |
|--------|------|
| `init()` | subscribes to the disk state and the file lists (8.6 pause/resume); must be called once the Safecor API is ready |
| `start(source_disks, target_name)` | starts the copy of the clean files (from `FileQueue.get_clean_files`) |
| `progress` (property) | the copy progress as the ratio of copied clean files |
| `copied_files_count` / `failed_files_count` (properties) | counters for copied / failed files (F4) |
| `is_started` / `is_copying` / `is_copy_paused` (properties) | copy state |
| `on_copy_file(payload)` / `on_copy_error(payload)` | handle `system/disks/copy_file` responses (per-file success/failure) |
| `__check_transfer_complete` | final check: all clean files copied → `transferComplete` |
| `__on_disk_state` / `__set_copy_paused` / `__resume_copy` | the 8.6 pause / coherence check / auto-resume |
| `reset()` | back to the initial state (on reset) |

## Key signals

| Signal | Payload | Meaning |
|--------|---------|---------|
| `transferProgressChanged` | — | progress ratio updated |
| `copiedFilesCountChanged` | — | a file was copied |
| `transferComplete` | — | all clean files copied + final check passed |
| `transferError` | `int` | the copy failed |
| `copyPausedChanged` | `bool` | the copy is paused (disk disconnected, 8.6) |
| `coherenceCheckFailed` | `str` | the reconnected disk is not the same (NFR-4 → reset required) |

It consumes the `FileQueue` passed in its constructor (shared reference) and the `DISK_STATE` / `LIST_FILES` Safecor topics.

## Links

- State machine contract (copy states, 8.6): [../../specifications/workflow.md](../../specifications/workflow.md)
- Queue it consumes: [storage-manager.md](storage-manager.md)
- Storage detection: [storage-manager.md](storage-manager.md)
- Communication topics: [../../development/protocol.md](../../development/protocol.md)
- Features F4 (copy): [../../specifications/features.md](../../specifications/features.md)

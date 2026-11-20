# Storage Manager (storage, file browser, queue)

> **Status**: Stable
> **Last updated**: 2026-11-20
> **Reference**: `python/gui/src/Saphir/Saphir/storage_manager.py`, `file_browser.py`, `file_queue.py`

## Purpose

Three collaborators owned by `ApplicationController` manage the source/target disks and the files-to-scan queue: `StorageManager` (disk detection, source/target assignment, storage list), `FileBrowser` (source-disk listing, folder navigation, enqueuing state), and `FileQueue` (the thread-safe queue data structure). Together they implement the **multi-source disk rule** (F1 / invariant 10.8): every disk connected before the scan starts is a source, no new source is accepted once the scan has started, and the first disk connected after the analysis completes is the target.

## StorageManager

`StorageManager` (QObject) — manages disk detection, source/target assignment, and the storage list.

**Key signals**: `sourceNameChanged(str)`, `sourceReadyChanged(bool)`, `targetNameChanged(str)`, `targetReadyChanged(bool)`, `storagesChanged()`, `storagesCountChanged()`.

| Member | Role |
|--------|------|
| `add_source(disk)` | register an additional source disk (a media can have several partitions: every partition is a disk entry and each is registered as a source; the first registered disk is the one returned by `source_name`) |
| `set_sources(disks)` / `remove_source(disk)` / `clear_source()` | replace / remove / clear the source disks |
| `set_target(disk)` / `clear_target()` | the selected target disk (single output media) |
| `source_name` / `source_ready` / `target_name` / `target_ready` (properties) | current selection state |
| `get_source_disks()` / `get_storages()` / `get_storages_count()` / `reset()` | queries and reset |

## FileBrowser

`FileBrowser` (QObject) — manages the file listing, folder navigation, and the enqueuing state of the source disk.

**Key signals**: `currentFolderChanged()`, `enqueuingCompleted()`.

| Member | Role |
|--------|------|
| `input_files_list` (property) | the source-disk file entries (dict, exposed **by reference** — used by the Qt models) |
| `current_folder` (property, get/set) | the folder currently displayed in the file browser |
| `is_enqueuing` (property) | whether files are currently being enqueued for analysis |
| `folders_to_query` (property) | the number of folders still to query in the source disk (recursive enqueue) |
| `get_file(filepath)` / `add_file(filepath, file)` / `clear()` / `reset()` | entry management; `reset()` returns to the initial state (root folder, nothing enqueued) |

## FileQueue

`FileQueue` — the **thread-safe** queue of files awaiting analysis / copy (invariant **I4**: all queue access under a lock or in one thread).

| Member | Role |
|--------|------|
| `files` (property) | the internal dict of dicts, exposed **by reference** (used by the Qt models and passed to `AnalysisController`/`TransferController`) |
| `enqueue(filepath, file)` / `dequeue(filepath)` / `dequeue_folder(filepath)` / `clear()` | queue mutations (all under a `threading.Lock`) |
| `get(filepath)` / `contains(filepath)` / `folder_contains(filepath)` / `items()` | lookups |
| `count()` / `size()` / `add_size(file_size)` | file count and the tracked total size |
| `get_clean_files()` | the clean files to copy (used by `TransferController`) |
| `get_transferred_ratio()` | the transferred ratio of the queue size |

Each queue entry (keyed by file path) carries the fields shown in `FilesProgress`/`AnalysisPanel` and the per-engine results; the per-file lifecycle is tracked with `FileStatus` — see [../overview.md](../overview.md) §6.

## Links

- Multi-source disk rule (F1) & target selection: [../../specifications/features.md](../../specifications/features.md)
- Queue data model: [../overview.md](../overview.md) §6.1
- Invariants I4/I7: [../overview.md](../overview.md) §7.3
- Consumers of the queue: [analysis-controller.md](analysis-controller.md), [transfer-controller.md](transfer-controller.md)
- Qt models over these structures: [qml-layer.md](qml-layer.md)

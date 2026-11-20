# Analysis Controller

> **Status**: Stable
> **Last updated**: 2026-11-20
> **Reference**: `python/gui/src/Saphir/Saphir/analysis_controller.py`, `analysis_helper.py`, `EMA_ETA_estimator.py`

## Purpose

`AnalysisController` (QObject) orchestrates the multi-antivirus analysis of the files selected by the user. It owns the analysis queue (the shared reference to the `FileQueue` dict is passed in its constructor), the **repository-copy loop** (a bounded puller: files are staged into the repository via `Api().read_file(...)`, bounded by the repository capacity), and the dispatch of each staged file to the AV domains. Depending on machine capacity, the analysis can be parallelised or sequential. It subscribes to the `saphir/analysis/*` response/status/error topics and to `NEW_FILE`/`DELETED_FILE`, aggregates per-AV results via `AnalysisHelper`, and applies the consensus rule.

## Key signals

| Signal | Payload | Meaning |
|--------|---------|---------|
| `stateChanged` | `AnalysisState` | analysis running / stopped / paused |
| `resultsChanged` | — | the per-file results were updated (consensus applied) |
| `fileUpdated` | `(str, list)` | one file's status/results changed |
| `systemUsed` | — | at least one file was read (drives the "Used" visual status) |
| `iterationDone` | `(float, int)` | one file done: duration in minutes, file size (feeds the ETA estimator) |
| `sourceHoldChanged` | `bool` | the source disk is disconnected during analysis: the file copy loop is held while the AVs keep scanning the repository |

## AnalysisHelper — consensus evaluation

`AnalysisHelper` — pure static methods over the queue dict; the **consensus rule** lives in `evaluate_result_consensus`: any result `"Infected"` ⇒ file infected (clean only when all engines agree). Key methods:

| Method | Role |
|--------|------|
| `update_file_result` / `update_archive_result` | merge one AV result into the file entry |
| `is_analysis_finished` / `is_file_completed` | all engines reported for the file |
| `evaluate_result_consensus` / `evaluate_result_consensus_archive` | the consensus verdict (OR on "Infected") |
| `get_file_progress` / `get_archive_progress` / `calculate_archive_progress` | per-file progress |
| `get_repository_size` | total size of the files in the repository |

See the consensus rule in [../overview.md](../overview.md) §6.2 and invariant **I6**.

## EMAETAEstimator — remaining-time estimate

`EMA_ETA_estimator.py` — a size-weighted **exponential moving average** of scan throughput; `remaining_time()` = remaining bytes / current speed. There is no unit for the duration: the caller converts.

| Member | Role |
|--------|------|
| `setup(total_size, alpha=0.3)` | initialise with the total size to scan; `alpha` linearises the gaps between iteration durations |
| `update(iter_duration, filesize)` | one iteration done; updates the weighted data rate and the done size |
| `speed()` | current weighted data rate (size per time unit) |
| `remaining_time()` | remaining bytes / current speed (∞ until the first speed sample) |

## Links

- Consensus rule & data model: [../overview.md](../overview.md) §6
- AV domains it dispatches to: [antivirus-controllers.md](antivirus-controllers.md)
- Queue data structure: [storage-manager.md](storage-manager.md)
- Communication topics: [../../development/protocol.md](../../development/protocol.md)
- State machine contract: [../../specifications/workflow.md](../../specifications/workflow.md)

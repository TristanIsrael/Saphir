# Antivirus Controllers (libsaphir)

> **Status**: Stable
> **Last updated**: 2026-11-20
> **Reference**: `python/libsaphir/src/libsaphir/`

## Purpose

`libsaphir` is the shared library used by the AV domains (`saphir-av-clamav`, `saphir-av-eset`) and, for the constants/enums, by the GUI. It implements the antivirus side of the scan: one controller per domain, each running as a standalone process, all reporting over the same `saphir/analysis/*` topics — so the GUI treats them identically. It is packaged in the `saphir-lib` Alpine package.

## AbstractAntivirusController (Template Method)

`AbstractAntivirusController` implements the **Template Method** for an antivirus domain: it owns the MQTT client lifecycle, the bounded **worker pool** (a `Queue` + a capped number of `threading.Thread`s, rescheduled via `threading.Timer`; the default worker count is the CPU count), the request routing (`analysis/request|stop|resume|reset`), the **component state machine** (`STARTING` → `READY`), and the result publishing (`analysis/response`, `analysis/status`).

The component transitions to `READY` only when **both** conditions are met:

1. the repository path has been received from the platform (via the `system/disks/repository_path` protocol function), and
2. the engine-specific initialisation is complete (daemon ping for ClamAV, LXC container for ESET).

Before dispatching a file to a subclass's `_analyse_file`, it verifies the **repository file integrity (NFR-1)**: the fingerprint recorded in the queue is compared with the fingerprint of the file in the repository; on mismatch the response is published with `fingerprint_error: true` and the analysis is not started.

Subclasses implement the abstract hooks: `_on_api_ready`, `_analyse_file`, `_stop_immediately`, `_get_component_version`, `_get_component_description`, `_restart`; can override `_engine_is_ready()` to gate readiness on engine-specific state; and can observe incoming requests via the optional `_on_analysis_requested` hook.

## ClamAntivirusController

`ClamAntivirusController` — **many workers** (CPU count); scans by running the `clamdscan` CLI as a subprocess; return code `0`=clean, `1`=infected, `2`=error; pings `clamdscan --ping` for readiness; restarts the daemon on panic (`killall -9 clamdscan`).

## EeaAntivirusController

`EeaAntivirusController` — **single worker**; scans through shell scripts wrapping the LXC container (`/usr/lib/saphir/bin/scan-file.sh` then `get-scan-result.sh`, i.e. odscan + lslog); richer return codes (`0`=clean, `10`=incomplete→clean, `50`=infected); pings `lxc-info` for readiness.

## MockAntivirusController (DEVMODE)

A representative mock of a real AV domain for **DEVMODE** (no appliance needed): it inherits from `AbstractAntivirusController` and returns static, pre-configured results over MQTT, standing in for the ClamAV and ESET domains so the Saphir GUI can reach `SystemReady` (`ANTIVIRUS_NEEDED`) and run the full scan cycle. It runs in a **standalone process** because the `Api()` singleton allows only one MQTT client per process:

```
python -m libsaphir._mock_antivirus_controller --name mock-clam [--config results.json]
```

Config file format (JSON): `{"default": "clean", "infected": [...], "corrupt": [...], "scan_delay": 0.1}`. Files listed in `corrupt` are **altered in the repository** right after the analysis request, so the NFR-1 integrity check rejects them.

## Shared constants & enums

- **`_constants.py`**: `ANTIVIRUS_NEEDED = 2` (number of AVs that must be **ready** to enable analysis — not a voting threshold), `MOUNT_ARCHIVES = False` (archive mounting disabled), `BIG_FILE_SIZE_IN_MB = -1` (disabled), `TOPIC_ANALYSIS = "saphir/analysis"`, `TOPIC_ERROR = "saphir/error"`, `DEVMODE`.
- **`_enums.py`**: `FileStatus` = `FileStatusUndefined, GettingFile, FileAvailableInRepository, FileAnalysing, FileAnalysisError, FileClean, FileInfected, FileCopyError, FileCopySuccess` — the per-file lifecycle tracked in the queue (see [../overview.md](../overview.md) §6.1).

## Links

- Per-file data flow (repository staging, fingerprint verification): [../overview.md](../overview.md) §3.2
- Consensus rule: [../overview.md](../overview.md) §6.2
- Topics `saphir/analysis/*`: [../../development/protocol.md](../../development/protocol.md)
- Analysis side in the GUI: [analysis-controller.md](analysis-controller.md)
- Design decision D-arch-4 (Template Method): [../decisions/0004-template-method-av-controllers.md](../decisions/0004-template-method-av-controllers.md)

# Saphir — MQTT Protocol Reference

> **Status**: Stable
> **Last updated**: 2026-11-20
> **Audience**: developers working on the Saphir codebase (refactoring and future features)
> **Scope**: the MQTT communication contract of Saphir — the single-client constraint, the request/response pattern, the Saphir custom topics (`saphir/analysis/*`) with their exact payloads, and an **offline reference copy** of the Safecor system topics (`system/*`) that Saphir consumes or produces.

## Related documents

| Concern | Document |
|---------|----------|
| Architecture overview (deployment, per-file data flow) | [`../architecture/overview.md`](../architecture/overview.md) |
| Design decisions (per-domain single client, repository as exchange point) | [`../architecture/decisions/`](../architecture/decisions/) — [0002](../architecture/decisions/0002-per-domain-single-api-client.md), [0003](../architecture/decisions/0003-repository-only-data-exchange.md) |
| State machine contract (what drives the protocol calls) | [`../specifications/workflow.md`](../specifications/workflow.md) |
| GUI side of the `system/*` topics | [`../architecture/components/application-controller.md`](../architecture/components/application-controller.md) |
| AV-domain side of the `saphir/analysis/*` contract | [`../architecture/components/antivirus-controllers.md`](../architecture/components/antivirus-controllers.md) |

This document is the single source of truth for **topic ownership** (which component owns which topic) and for the **payload shapes** of the Saphir↔Saphir and Saphir↔Safecor MQTT traffic. (A duplicate of the ownership matrix used to live in `workflow.md` §8; it has been consolidated here.)

---

## 1. The single-client constraint

The Safecor `Api` is a **singleton** (`safecor._api.Api` uses `SingletonMeta`). Therefore **each process has exactly one `Api()` / one `MqttClient`**. Because each Safecor domain is its own VM/process, the constraint is *per-domain*: the GUI, ClamAV, and ESET domains each hold their own singleton. Consequences for Saphir:

- Only **one** object per process may create/manage the MQTT client.
- All other objects must funnel through that one client (subscribe/publish on the shared `Api()`).
- In the target architecture, a dedicated **`ApiLifecycle`** module is the *sole* owner of client creation and subscription management (invariant **I1**).

---

## 2. Request/response pattern

The Safecor API is **asynchronous**: a call publishes a `/request`; the result arrives later on the matching `/response` topic and is dispatched to a registered callback. Notifications (no `/request`) such as `system/disks/state`, `system/disks/new_file`, `system/disks/deleted_file`, `system/workflow/gui_ready`, `system/events/*` arrive as unsolicited messages. All Saphir MQTT message handling happens **on the MQTT thread** (the handlers must be thread-safe and must not block).

---

## 3. Saphir custom topics (`saphir/analysis/*`)

`TOPIC_ANALYSIS = "saphir/analysis"` (`libsaphir/_constants.py`). The GUI's `AnalysisController` publishes `request` / `stop` / `resume` / `reset`; each AV domain (ClamAV, ESET) publishes `response` / `status` / `error` and consumes the opposite side. Both AV domains report over the same topics, so the GUI treats them identically.

### 3.1 Topic map

| Topic | Publisher | Subscriber | Purpose |
|-------|-----------|------------|---------|
| `saphir/analysis/request` | GUI `AnalysisController` | each AV domain | "analyse this file" `{filepath, fingerprint}` |
| `saphir/analysis/response` | each AV domain | GUI `AnalysisController` | scan result `{component, filepath, success, details[, fingerprint_error]}`; on repository integrity failure (NFR-1) the payload carries `fingerprint_error: true` and the GUI marks the file `FileAnalysisError` |
| `saphir/analysis/status` | each AV domain | GUI (currently ignored) | progress |
| `saphir/analysis/error` | each AV domain | GUI `AnalysisController` | scan error |
| `saphir/analysis/stop` / `resume` | GUI `AnalysisController` | each AV domain | pause / run |
| `saphir/analysis/reset` | GUI `AnalysisController` | each AV domain | drain queue + stop |

**Topic ownership**: each topic has exactly **one** Saphir subscriber — the table above is the single source of truth for the ownership matrix (which component owns which topic). In the target architecture this is enforced by `ApiLifecycle` (invariant **I2**).

### 3.2 `saphir/analysis/request` — "analyse this file"

Published by the GUI's `AnalysisController` (`__on_file_available`) once the file has been staged in the repository (a `system/disks/new_file` notification was received for it).

```json
{ "filepath": "/my/folder/my_file.txt", "fingerprint": "12cfd565ff54caa12..." }
```

| Field | Type | Required | Meaning |
|-------|------|----------|---------|
| `filepath` | str | yes | The path of the file **in the repository** (the AV domain resolves it against the repository path received from the platform). |
| `fingerprint` | str | yes | The fingerprint recorded when the file was staged (`source_fingerprint` of the `new_file` notification). The AV domain compares it with the fingerprint of the file in the repository **before scanning** (NFR-1); on mismatch the analysis is not started and the response carries `fingerprint_error: true`. |

The AV domain validates `["filepath"]` before queuing the request.

### 3.3 `saphir/analysis/response` — scan result

Published by each AV domain via `AbstractAntivirusController.publish_result`, once per file per engine.

```json
{ "component": "ClamAV", "filepath": "/my/folder/my_file.txt", "success": true, "details": "Clean" }
```

| Field | Type | Required | Meaning |
|-------|------|----------|---------|
| `component` | str | yes | The name of the publishing AV component (e.g. `ClamAV`). |
| `filepath` | str | yes | The requested repository path. |
| `success` | bool | yes | `true` = clean, `false` = infected **or** scan error (the engine never reports an error on this topic as such). |
| `details` | str | yes | Engine details: the detected signature name (ClamAV, parsed from the `clamdscan` output), the odscan/lslog outcome or a translated error message (ESET), `Clean` on a clean verdict, or the error message. |
| `fingerprint_error` | bool | no | Present and `true` only when the NFR-1 integrity check failed (the file was altered in the repository). The GUI then marks the file `FileAnalysisError` and does **not** count the response as a scan result. |

The GUI validates `["component", "filepath", "success", "details"]` and aggregates the per-AV results until **all** engines have reported — the consensus is then applied (any "Infected" ⇒ infected; see [`../architecture/overview.md`](../architecture/overview.md) §6.2). A file already in a final state is terminal: stale or duplicate results for it are ignored.

### 3.4 `saphir/analysis/status` — progress

Published by each AV domain via `AbstractAntivirusController.update_status` at scan start and completion.

```json
{ "component": "ClamAV", "filepath": "/my/folder/my_file.txt", "status": "FileAnalysing", "progress": 0 }
```

| Field | Type | Meaning |
|-------|------|---------|
| `component` | str | The publishing AV component. |
| `filepath` | str | The requested repository path. |
| `status` | str | A `FileStatus` value (e.g. `FileAnalysing`, `FileClean`, `FileInfected`). |
| `progress` | int | The scan progress, 0–100. |

**Currently ignored by the GUI** (the handler is a no-op); reserved for a future per-file progress display.

### 3.5 `saphir/analysis/error` — scan error

```json
{ "disk": "__repository__", "filepath": "/my/folder/my_file.txt", "error": "..." }
```

The GUI expects `["disk", "filepath", "error"]` and marks the file `FileAnalysisError` (the analysis **continues** — NFR-3). Note: no AV controller publishes on this topic today — scan errors surface on `response` with `success: false` + `details`, and whole-engine failures surface as component state changes on `system/discover/components` (workflow scenario 8.9).

### 3.6 `saphir/analysis/stop`, `resume`, `reset` — run control

All three carry an **empty payload** (`{}`).

| Topic | Effect on the AV domain |
|-------|-------------------------|
| `stop` | The domain stops picking new files from its queue; in-flight scans run to completion. GUI usage: **Pause** (workflow v2.3) — the GUI also clears the sys-usb queues (`system/sys-usb/clear-queues`) and halts the repository-copy loop. |
| `resume` | The domain re-enables its queue and re-dispatches the pending files. GUI usage: resume after a pause — the GUI re-enqueues the files interrupted by the previous stop; files already analyzed keep their status and are not re-analyzed (scenario 8.2). |
| `reset` | The domain drains its queue and stops the running engine processes immediately (`_stop_immediately`), then re-enables. GUI usage: system reset. |

---

## 4. Safecor system topics — offline reference copy

> **Offline reference copy** — Source: Safecor wiki `Protocol.md` + Safecor repo. Synced: 2026-11-20. When Safecor changes, update here and log the divergence in `docs/safecor-divergences.md`.

This section lists the Safecor `system/*` topics **that Saphir consumes or produces**, with their payload shapes and semantics. It is a reference copy for **offline** coding agents; the Safecor wiki remains the upstream human documentation.

Conventions:

- Request/response functions are a `/request` + `/response` topic pair; the Safecor Python API (`Api()`) wraps each in a high-level method.
- Notifications are single topics with no `/request`.
- The repository is referenced as the disk name `__repository__` (mounted at `/mnt/storage`).

### 4.0 Overview table

| Topic | High-level `Api()` call | Saphir consumer |
|-------|--------------------------|-----------------|
| `system/disks/state` (`DISK_STATE`) | — (notification) | storage detection; source disconnection during analysis (scenario 8.8) |
| `system/disks/list_disks` | `get_disks_list()` | storage list |
| `system/disks/list_files` | `get_files_list()` | file browser |
| `system/disks/read_file` | `read_file()` | repository staging (→ `new_file`) |
| `system/disks/copy_file` | `copy_file()` | transfer to target |
| `system/disks/create_file` | `create_file()` | report/journal copy |
| `system/disks/delete_file` | `delete_file()` | free the repository slot after analysis (→ `deleted_file`) |
| `system/disks/repository_path` | `request_repository_path()` | repository path (boot readiness + AV readiness condition) |
| `system/disks/new_file` / `deleted_file` | — (notifications) | staging completion / slot freed (`AnalysisController`) |
| `system/discover/components` | `discover_components()` | component readiness (F9), AV engine panic (NFR-3) |
| `system/energy/state` | `request_energy_state()` | battery/plugged |
| `system/info` | `request_system_info()` | system info (F9), repository capacity |
| `system/settings/languages/default` | `get_default_language()` | default language |
| `system/gui/switch` | `switch_gui()` | swap to Viewer / back |
| `system/workflow/{shutdown,restart_domain,gui_ready}` | `shutdown()`, `restart_domain()`, `notify_gui_ready()` | lifecycle |
| `system/events/#` | — (notification) | `LogListModel` (journal); `system/events/error` also carries file-operation error notifications |
| `system/sys-usb/clear-queues` | `clear_sys_usb_queues()` | cancel in-flight repository reads on Pause |

### 4.1 Disks and files

#### `system/disks/state` (notification)

A disk has been connected or disconnected.

```json
{ "disk": "disk1", "state": "connected" }
```

- `disk` (str): the disk whose state changed.
- `state` (str): `connected` | `disconnected` | `mounted` | `unmounted` (`DiskState`).

Saphir consumes it for storage detection (source/target assignment) and for the **source-disconnection-during-analysis** handling (the analysis continues on the repository; the copy loop is held until the source is re-inserted — scenario 8.8).

#### `system/disks/list_disks`

*Requests the list of external storage disks connected to this system.*

- Request `{}`.
- Response `{ "disks": [ "disk1", "disk2", ... ] }` — the list of disk names. A disk may contain multiple partitions; each partition is considered a disk.

#### `system/disks/list_files`

*Requests the list of files contained in a disk.*

- Request:

```json
{ "disk": "disk1", "recursive": false, "from_dir": "", "name_filter": [] }
```

  - `disk` (str): the disk.
  - `recursive` (bool): if true, the listing is done on every subdirectory starting from `from_dir`. Default `false`.
  - `from_dir` (str): if set, the list contains only the files of this directory (and subdirectories if `recursive`). Default `""`.
  - `name_filter` (list): if set, the files are filtered by their extension (e.g. `".zip"`).

- Response:

```json
{
  "disk": "disk1",
  "files": [
    { "type": "file", "path": "/", "name": "my_file.txt", "size": "1234" }
  ]
}
```

  - `type` (str): `"file"` or `"folder"`.
  - `path` (str): the complete file path.
  - `name` (str): the file (or folder) name.
  - `size` (int): the size in bytes. **Absent for a folder.**

#### `system/disks/read_file`

*Reads a file from an external storage **into the repository**.*

- Request `{ "disk": "disk1", "filepath": "/my/folder/my_file.txt" }`.
- **No direct response** — the completion arrives as a `system/disks/new_file` notification (the platform computes the source and destination fingerprints on the way).

#### `system/disks/copy_file`

*Copies a file from one disk to another (used for the repository → target transfer).*

- Request `{ "disk": "source_disk", "filepath": "/my/file.txt", "destination": "destination_disk" }`.
- Response `{ "filepath": "/my/file.txt", "status": "ok", "fingerprint": "12345678901234567890" }` — `status` is `"ok"` or `"error"`; `fingerprint` is the fingerprint of the file **on the destination disk**.

#### `system/disks/create_file`

*Creates a new file on a disk (including the repository).*

- Request:

```json
{ "disk": "disk1", "filepath": "/my/folder/my_file.txt", "data": "KJsh76S8912Hgsgfd54222Rtfg==", "compressed": false }
```

  - `data` (str): base64-encoded file content.
  - `compressed` (bool): `true` when the (binary) data is compressed with the GNU zip algorithm. Default `false`.

- Response (per the Safecor `ResponseFactory`; the wiki points at the `new_file` notification): `{ "filepath": ..., "disk": ..., "fingerprint": ..., "success": true|false }`.

Saphir uses it to copy the **PDF scan report** and the **event journal** (`journal.log`) to the target disk; the `success` field gates the transition to `SystemMustBeReset`.

#### `system/disks/delete_file`

*Deletes a file from a disk, including the repository.*

- Request `{ "disk": "disk1", "filepath": "/my/folder/my_file.txt" }`.
- Completion arrives as a `system/disks/deleted_file` notification.

Saphir uses it to **free the repository slot** after each analysed file.

#### `system/disks/repository_path`

*Requests the repository mount path from the platform.*

- Request `{}`.
- Response `{ "path": "/mnt/storage" }`.

Consumed by both the GUI (a boot-readiness condition) and the AV domains (a readiness condition **and** the base path for the NFR-1 integrity check).

> The protocol also defines `system/disks/mount_file` / `system/disks/unmount` (mount an archive as a virtual disk) and `system/disks/file_fingerprint`. Saphir does **not** use them: archive mounting was removed (see [decisions/0018](../architecture/decisions/0018-archive-mounting-removed.md)), and fingerprints are obtained from the `new_file` notification or computed locally by the AV domains.

### 4.2 File notifications

#### `system/disks/new_file` (notification)

Sent when a file has been copied or created on a disk, **including the repository**.

```json
{
  "disk": "disk1",
  "filepath": "/a/folder/my_file.txt",
  "source_fingerprint": "acd653c5a8b988cbdbabd65",
  "dest_fingerprint": "acd653c5a8b988cbdbabd65"
}
```

- `disk` (str): the disk on which the file has been created.
- `filepath` (str): the complete path of the file.
- `source_fingerprint` / `dest_fingerprint` (str): the fingerprint of the original file and of the file after the copy — **the two must match** (integrity).

Saphir: marks the staged file `FileAvailableInRepository`, records the fingerprint, and publishes the `saphir/analysis/request` that carries it to the AV domains.

> The wiki page spells these fields `source_footprint` / `dest_footprint`; the Safecor repo and the Saphir consumers use `*_fingerprint` — that is the authoritative spelling.

#### `system/disks/deleted_file` (notification)

Sent after a `delete_file` call.

```json
{ "disk": "disk1", "filepath": "/my/file.ext" }
```

Saphir: unlocks the queue entry (the repository slot is free again).

### 4.3 Workflow lifecycle

#### `system/workflow/shutdown`

*Asks the system to shut down.*

- Request `{}`.
- Response `{ "state": "accepted", "reason": "" }` — `state` is `accepted` or `refused`; `reason` is filled when refused.

#### `system/workflow/restart_domain`

*Asks the restart of a Domain.*

- Request `{ "domain_name": "my_domain", "forced": false }` — `domain_name` must match an existing domain (e.g. `sys-usb`, or a domain from `topology.json`); `forced` forces the restart in Dom0 instead of a self-restart.
- Response `{ "state": "accepted", "reason": "" }` (the response also echoes the `domain_name`).

Saphir: the reset phase destroys/recreates the disposable domains; the AV domains subscribe to this topic to restart **themselves** when addressed (ClamAV reboots its domain).

#### `system/workflow/gui_ready` (notification)

Sent by the GUI when it is ready; the platform removes the splash screen. Payload `{}`. Saphir: `Api().notify_gui_ready()` on app ready.

### 4.4 Component discovery

#### `system/discover/components`

*Queries all components of the system.*

- Request `{}`.
- Response:

```json
{
  "components": [
    {
      "id": "<unique id>",
      "domain_name": "<domain hosting the component>",
      "label": "<free label>",
      "type": "<type of component>",
      "state": "<component state>",
      "version": "<version of the component>",
      "description": "<long description>"
    }
  ]
}
```

- `state` (str): one of `unknown` | `starting` | `ready` | `error` | `off` (`ComponentState`).

Saphir **consumes** it: the component list (F9), the boot readiness condition (`analysisReady`), and AV **engine-panic** detection (component `error`/`off` ⇒ NFR-3, scenario 8.9).

The AV domains **produce** it: each one answers a discovery request by publishing its state via `Api().publish_components(...)` with `type: "antivirus"`. A component reports `ready` only when **both** conditions are met: the repository path has been received **and** the engine-specific initialisation is complete (daemon ping for ClamAV, LXC container for ESET).

### 4.5 Energy

#### `system/energy/state`

*Queries the current energy information including battery level if any.*

- Request `{}`.
- Response `{ "battery_level": 100.0, "plugged": 1 }` — `battery_level` (float, 0.0 empty → 100.0 full), `plugged` (int, 1 when powered by an external source).

Saphir: the energy indicator (`Energy.qml`) and the system information screen (F9). This is the **only polling** in the system — a 5 s timer (see [decisions/0001](../architecture/decisions/0001-event-driven-no-polling.md)).

### 4.6 System information

#### `system/info`

*Queries information on the hosting system.*

- Request `{}`.
- Response (abridged):

```json
{
  "core": { "version": "1.1", "debug_on": false },
  "system": {
    "os": { "name": "Linux", "release": "...", "version": "..." },
    "machine": {
      "arch": "x86_64",
      "cpu": { "count": 12, "freq_current": 1689.6, "freq_min": 0.0, "freq_max": 0.0, "percent": 0.0 },
      "memory": { "total": 405987328, "available": 96657408, "percent": 76.2, "used": 256733184, "free": 12472320 },
      "load": { "1": 0.52, "5": 0.22, "15": 0.08 }
    },
    "boot_time": 1748036696.0,
    "uuid": "11ec0800-4fb9-11ef-bd38-ad993f2e7700",
    "storage": { "total": 12345678, "used": 0, "free": 12345678, "files_count": 0 }
  }
}
```

Saphir: the system information screen (F9) and the **repository capacity** (number of files analyzed in parallel).

### 4.7 Settings (languages)

#### `system/settings/languages/default`

*Queries the default language defined in the topology.*

- Request `{}`.
- Response `{ "language": "en" }` — the ISO2 code of the default language.

Saphir: applied at startup (`TranslationManager`). The protocol also defines `system/settings/languages` (the list), `.../current`, and `.../set`; Saphir consumes only the default.

### 4.8 GUI switch

#### `system/gui/switch`

*Changes the currently visible Domain.*

- Request `{ "domain_name": "saphir-viewer" }`.
- Response `{ "state": "accepted", "reason": "" }` — `accepted` or `refused`.

Saphir: `switch_to_viewer()` → `Api().switch_gui("saphir-viewer")`; the Viewer switches back to `saphir-gui`.

### 4.9 Events (journal)

#### `system/events/{debug,info,warning,error,critical}`

Log events, produced by every product component through the Safecor API (`Api().debug/info/warn/error(message, "Saphir")`).

```json
{ "component": "my component", "module": "my module", "datetime": "2025-04-02 03:04:05", "description": "The problem..." }
```

`system/events/error` **additionally** carries **platform file-operation error notifications**:

```json
{ "disk": "disk1", "filepath": "/my/file.txt", "error": "I/O error" }
```

Saphir: the GUI filters the `{disk, filepath, error}` payloads out of the log broadcasts (the TransferController acts on them during the copy — F4; outside the copy they are only logged). The event journal (F5) is exposed in the GUI via `LogListModel` and is copied to the target as `journal.log` at the end of the cycle.

### 4.10 sys-usb queues

#### `system/sys-usb/clear-queues`

*Queries sys-usb to clear its commands queues.*

- Request `{}`.
- Response `{ "success": true, "reason": "Description" }` — `success` (bool), `reason` (str, filled on failure).

Saphir: `stop_analysis` (Pause) clears the in-flight file reads queued in the disk controller.

---

## 5. How to maintain this document

- A Saphir topic or payload changes (§3) → update the topic map and the payload tables here, and the ownership note.
- The Safecor protocol changes (§4) → re-sync this section from the Safecor wiki `Protocol.md` and the Safecor repo, update the **Synced** date in the §4 banner, and log the divergence in [`../safecor-divergences.md`](../safecor-divergences.md).
- A new topic is introduced by a new feature → it must appear in the topic map with its owner **before** the code is written (invariant **I2**).

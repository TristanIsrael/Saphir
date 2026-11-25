# 0019 — Direct USB mount as the analysis data path

> **Status**: Accepted
> **Date**: 2026-11-24
> **Supersedes**: [0003](0003-repository-only-data-exchange.md)
> **Source**: Safecor v2 migration plan (§5), `Migration-v1-v2.md` wiki

## Context

Saphir 4.0 targets the **Safecor 2.0 line**, which removes the shared 9p repository (`/mnt/storage`, disk `__repository__`) from the DomUs. The v1 analysis flow — GUI stages each selected file into the repository via `read_file` (→ `NEW_FILE`), AV scans `/mnt/storage/...`, GUI deletes the file via `delete_file` — **cannot work in v2** because `/mnt/storage` is no longer mounted in the DomUs.

Safecor v2 introduces the **direct USB mount**: a domain declaring `direct_mount` in the topology receives `/media/usb` mounted over an sshfs channel served by `sys-usb`. A USB disk mounted at `/media/usb/<label>` on `sys-usb` appears at the **same path** in the client domain. Saphir's AV domains already carry `direct_mount: { "mode": "ro" }` in `topology.json`.

## Decision

The shared repository is **replaced** by the direct USB mount as the sole data exchange path for analysis:

- The GUI domain communicates with `sys-usb` exclusively via the Safecor file API (`list_files`, `get_file_fingerprint`, `copy_file`, `create_file`) — it does **not** mount `/media/usb` locally.
- The AV domains (ClamAV, ESET) and the Viewer receive `/media/usb` via `direct_mount: { "mode": "ro" }` and read files directly from this path.
- Fingerprint acquisition is handled via the Safecor file API (`get_file_fingerprint`) — the GUI computes and records the fingerprint before the analysis request, and the AV domains verify it against the file they read from `/media/usb`.
- File identity becomes a **composite key** `(disk, filepath)` to support multi-source scans and ensure AV response matching.
- The `__repository__` disk is **not used** by any Saphir component. The topology sets `"repository": { "disabled": true }`.

### Invariants

| # | Invariant | Scope |
|---|-----------|-------|
| **I-A1** | The GUI domain uses the **Safecor file API only** (`list_files`, `get_file_fingerprint`, `copy_file`, `create_file`). It has **no local access** to `/media/usb` or any USB mount. | GUI domain |
| **I-A2** | The AV domains (`saphir-av-clamav`, `saphir-av-eset`) receive `/media/usb` **read-only** via `direct_mount`. This is the **sole** path for reading files to be scanned. | AV domains |
| **I-A3** | The Viewer domain (`saphir-viewer`, when deployed) receives `/media/usb` **read-only** via `direct_mount` for file preview. | Viewer domain |
| **I-A4** | The `sys-usb` domain **remains** the sole arbiter of USB access. All file reads go through `sys-usb` — either via sshfs (AV/Viewer) or via the Safecor file API (GUI, which proxies to `sys-usb`). | sys-usb |
| **I-A5** | The `__repository__` disk is **not used** by any Saphir component. The topology declares `"repository": { "disabled": true }`. | All domains |

### Scenario 8.8 — Source disconnection during analysis (D3)

- Source disconnect during `SystemAnalysisRunning` → **hold** the analysis loop (files already in flight keep being scanned; no terminal state change).
- Same-disk reconnect → **auto-resume**: re-fingerprint held files, re-publish analysis requests.
- Different disk reconnect → `SystemMustBeReset` (NFR-4 dirty-state lock).
- AV scan failures for files held during the source disconnect are **ignored** (stale-failure guard, same pattern as the paused copy in scenario 8.6).

### Dirty-point rule (D4)

The system becomes **dirty** (`systemUsed = true`) when the **fingerprint of a file is successfully returned** by `sys-usb` via the file API (`get_file_fingerprint`). A fingerprint-read failure keeps the system clean (the file was never actually read).

## Consequences

- **No repository staging**: the `read_file` → `NEW_FILE` → `delete_file` cycle is removed from the analysis loop. No `FileAvailableInRepository` status, no repository capacity tracking, no `repository_path` readiness gate.
- **Parallelism cap**: a bounded queue replaces repository capacity to limit concurrent sshfs reads and AV scans.
- **NFR-1 chain (re-anchored)**:
  1. GUI obtains the fingerprint from `sys-usb` via `get_file_fingerprint`.
  2. AV domain verifies the fingerprint of the file it reads from `/media/usb` **before scanning** (mismatch → `fingerprint_error` response).
  3. `copy_file` destination fingerprint vs. recorded fingerprint (unchanged from v1).
- **Security model update**: AV domains and the Viewer now see the **whole** USB tree read-only (previously they only saw staged repository files). This is an accepted trade-off, documented in `../security/security-model.md`.
- **Protocol changes**: `saphir/analysis/request` and `/response` payloads gain a `disk` field; the fingerprint source shifts from `new_file` notification to `system/disks/file_fingerprint` response.

## Migration notes

- This ADR is implemented in phases: 0 (documentation), 1 (libsaphir AV controllers), 2 (GUI analysis flow), 3 (Viewer), 4 (ESET container).
- See [`../plans/migration-safecor-v2.md`](../plans/migration-safecor-v2.md) for the full migration plan and progress tracking.

# Saphir v4 — Migration Plan: Safecor v2 (Direct-Mount Data Path)

> **Status**: Approved (2026-11-24)
>
> **Branch**: `version-4`
>
> **Tracking issue**: [#167](https://github.com/TristanIsrael/Saphir/issues/167)
>
> **Upstream reference**: Safecor wiki `Migration-v1-v2.md` (local copy: `../Safecor.wiki/Migration-v1-v2.md`)
>
> **Companion notes**: [`../archive/plans/validation-tests-direct-mount.md`](../archive/plans/validation-tests-direct-mount.md)

---

## 1. Context

Saphir 4.0 moves to the **Safecor 2.0 line** (`safecor-core`/`safecor-lib`/`safecor-domu-base`/`safecor-sys-usb` 2.0-r0, Alpine 3.24 base).

The blocking platform change: the shared repository (`/mnt/storage`, disk `__repository__`, a 9p share in v1) is **no longer mounted in the DomUs**. Saphir's v1 analysis flow — GUI stages each selected file into the repository (`read_file` → `NEW_FILE` → AV scans `/mnt/storage/...` → `delete_file`) — **cannot work in v2**.

The v2 replacement: the **direct USB mount**. A domain that declares `direct_mount` in the topology gets `/media/usb` mounted over a per-session SFTP/sshfs channel served by `sys-usb` (read-only or read-write). A USB disk mounted at `/media/usb/<label>` on `sys-usb` appears at the **same path** in the client domain. Saphir's AV domains already carry `direct_mount: { "mode": "ro" }` in `topology.json`.

Everything else in the v1→v2 delta is **impact-free or already handled** (verified):

| Safecor v2 change | Saphir impact |
|---|---|
| Local Mosquitto broker per domain (UNIX socket), multiple MQTT clients per domain | None — `Api` usage identical |
| Config CDROM → config block disk | None |
| 9p local Alpine repo → `packages.squashfs` block disk | None for product code; ISO/CI follow-up (§5.4) |
| `/mnt/storage` not mounted in DomUs | **The migration itself** (this plan) |
| Direct USB mount (new) | The new data path |
| Python API: removed serial-only symbols | None — Saphir does not use `SerialMQTTClient`, `ConnectionType.SERIAL_PORT`, `create_response_repository_path`, `hvcN` constants (verified by grep) |
| Python API: added `System.is_usb_mountpoint_ready()`, `System.on_usb_mountpoint_ready(cb)`, `MountMode`, `DirectMountManager`, `get_file_fingerprint`, `Topics.MY_CONFIG` | Used in this plan |
| Packages: depends → 2.0-r0; `xe-guest-utilities` gone from v2 packages | Packaging phase (§5.1) — note: v2 `safecor-gui-base` no longer pulls `xe-guest-utilities`, the v1 chroot conflict disappears |
| Topology: `direct_mount` (already set), new `repository.disabled` key | §5.3, decision D2 |
| 1.4-line features not ported (storage_info, chassis key, NTFS w/o partition table, name collisions, …) | None — Saphir does not rely on any of them (verified) |

## 2. Approved decisions (2026-11-24)

| # | Decision |
|---|---|
| **D1** | **ESET**: bind-mount `/media/usb` (DomU) into `/media/usb` of the LXC container; `odscan` scans at that path. Only the ESET controller path and the container config change (no per-file staging). |
| **D2** | **Repository**: set `"repository": { "disabled": true }` in the topology — after this migration no Saphir component uses `__repository__` (analysis reads USB directly; copy/report/journal use the file API or local `/tmp`). |
| **D3** | **Scenario 8.8 (v4)**: source disconnection during analysis = **hold + auto-resume** on same-disk reconnection (same semantics as scenario 8.6 for the copy); a different disk reconnected → `SystemMustBeReset`. In-flight files are re-analysed on resume; AV scan failures during the hold are ignored (stale-failure guard, same pattern as the paused copy). |
| **D4** | **Dirty point (NFR-4)**: `systemUsed` is emitted when the **fingerprint of the file is returned** by `sys-usb` (the file has been read successfully). A fingerprint-read failure keeps the system clean. |
| **D5** | **Versions**: no cross-package alignment — each package keeps its own versioning cycle (already bumped on `version-4`). Only verify pyproject↔APKBUILD coherence per package. |

## 3. Target data path (to-be)

```
GUI (saphir-gui)                 sys-usb                  AV domains (ClamAV / ESET)
  list_files(source)  ─────────────────────────► file catalog
  get_file_fingerprint(disk, fp) ───────────────► fingerprint response   ─┐
  (file ready)                                        │                    │ D4: dirty on
  saphir/analysis/request                             │                    │ successful response
    {disk, filepath, fingerprint} ────────────────────────────────────────►│
                                                          /media/usb/<disk><filepath>
                                                          1. NFR-1: verify fingerprint of the
                                                             file just read (mismatch →
                                                             response fingerprint_error:true)
                                                          2. ClamAV: clamdscan <path> (direct)
                                                             ESET: odscan <path> in the LXC
                                                                 (same path via the /media/usb
                                                                 bind mount)
  saphir/analysis/response {disk, filepath, success, details[, fingerprint_error]} ──►
  consensus (any infected ⇒ infected)
  copy_file(source, target, fp)  ───────────────► unchanged (sys-usb)
  create_file(target, report/journal from GUI /tmp) ── unchanged
```

Key properties:

- **No repository staging, no `NEW_FILE`/`DELETED_FILE`, no `delete_file`** in the analysis loop.
- **File identity becomes `(disk, filepath)`** — two source disks can contain the same relative path (multi-source mode, 10.8). The GUI keys its file bookkeeping by the composite identity and the analysis `request`/`response` payloads carry `disk` (the AV echoes it back).
- **NFR-1 chain (kept, re-anchored)**: `sys-usb` fingerprint at request time → AV verifies the fingerprint of the file it actually reads from `/media/usb` before scanning → `copy_file` destination fingerprint vs recorded (unchanged). The `fingerprint_error` mechanism stays; its meaning shifts from "file altered in the repository" to "file on the media does not match the recorded fingerprint".
- **GUI keeps file-API-only access** (no `/media/usb` in the GUI domain); AV + viewer get `direct_mount: ro`.
- **Readiness (v2 sync contract — react, do not poll)**: AV domains gate their component state on `System.on_usb_mountpoint_ready(cb)`; the GUI's old `repository_path` readiness gate is removed (the GUI needs no mount).

## 4. Impact summary (verified code anchors)

| Area | Impact | Anchors |
|---|---|---|
| GUI analysis loop | Repository staging loop, `NEW_FILE`/`DELETED_FILE` handling, `delete_file` (3 call sites), repository capacity, `FileAvailableInRepository` status all become dead; replaced by the fingerprint-driven flow | `analysis_controller.py:223-237, 326-374, 483/488/543, 563-656, 407-418` |
| GUI readiness | `request_repository_path()` + `__repository_path_received` gate removed from the ready condition | `application_controller.py:558, 618, 707, 1140-1144`; `api_lifecycle.py:72` |
| Protocol | `saphir/analysis/request` and `/response` gain `disk`; `fingerprint` now comes from `system/disks/file_fingerprint` | `docs/development/protocol.md` §3.2/§3.3; `libsaphir` consumers |
| AV controllers (libsaphir) | Path resolution `/mnt/storage`→`/media/usb/<disk>`; readiness via `System.on_usb_mountpoint_ready`; request validation `["disk","filepath"]`; NFR-1 check re-anchored on the media file; `_analyse_file` signature gains `disk` | `_abstract_antivirus_controller.py:166-175, 180-189, 246-271, 299-303`; `_clam_antivirus_controller.py:30`; `_eea_antivirus_controller.py:45`; `_mock_antivirus_controller.py:87` |
| ESET container | LXC binds `/mnt/storage` (9p) and `/dev/hvc1` (v1 serial) into the container; post-install remounts the 9p store read-only — all broken/obsolete in v2; replaced by a `/media/usb` bind (D1) + boot-order guard | `saphir-container-eset/APKBUILD:121, 134`; `saphir-container-eset.post-install` |
| Viewer | `/mnt/storage` hardcoded (production path) + staging via `read_file` in `view_file()`; viewer domain lacks `direct_mount` | `viewer/application_controller.py:521-525`; `office_helper.py:27`; `topology.json.viewer` |
| DEVMODE & tests | Mocks emulate a local repository dir; ~17 `STR_REPOSITORY` references in GUI unit tests; workflow integration tests encode the staging flow | `gui/tests/conftest.py`, `mock_av_manager.py`, `test_analysis_controller.py`, `test_av_integrity_check.py`, `test_workflow_*.py`; `viewer/Viewer/Mock/*`, `viewer/devmode_helper.py`, `viewer/tests/*` |
| Packaging | Unversioned `depends` (→ 2.0-r0); chroot validation on 3.21 (→ 3.24); ISO action broken on 3.24 (known); packages squashfs redesign (Safecor side) | `setup/packages/saphir/*/APKBUILD`, `setup/chroot/chroot-build.sh`, `setup/iso/`, `.github/workflows/build-all.yml` |
| Security model | AV domains now see the **whole** USB tree read-only (previously only staged files) — accepted trade-off, to be documented in the security model and the new ADR | `docs/security/security-model.md` |

**Not impacted** (no change): copy-to-target (`copy_file`), report/journal (`create_file` from GUI-local `/tmp`), file browser/`list_files`, disk state handling, component discovery, energy, language, display, `switch_gui`, EMA ETA, transfer coherence check (8.6).

## 5. Phases

> Each phase = one dedicated work package (one commit/issue pair per the project rules; the overall migration is tracked by #167). Phases 1→2 are dependent; 3 is independent; 4 depends on the D1 implementation in 1; 5 is mostly independent; 6 is last.

### Phase 0 — Specs, ADR, protocol doc (documentation only)

- **0.1** New ADR `docs/architecture/decisions/0019-direct-usb-mount-data-path.md`: replaces [`0003-repository-only-data-exchange.md`](../architecture/decisions/0003-repository-only-data-exchange.md) (mark it **superseded**). New invariants: (I-A1) GUI: file API only, no local USB access; (I-A2) AV domains: `/media/usb` read-only via `direct_mount`, the sole analysis read path; (I-A3) viewer: `/media/usb` read-only; (I-A4) `sys-usb` remains the sole arbiter of the USB access; (I-A5) the `__repository__` disk is not used by any Saphir component (`repository.disabled: true`).
- **0.2** `specifications/workflow.md`: rewrite scenario 8.8 to the D3 semantics; remove the `FileAvailableInRepository` status from the state/status tables; update the dirty-point rule (D4).
- **0.3** `specifications/features.md`: F3 (no staging step; fingerprint via file API), F4 (unchanged flow, wording), NFR-1 (re-anchored chain), NFR-4 (D4 dirty point).
- **0.4** `development/protocol.md`: `saphir/analysis/request`/`response` payloads gain `disk`; fingerprint source = `system/disks/file_fingerprint`; remove the repository-staging descriptions (`read_file`/`new_file`/`delete_file` no longer used by Saphir; `repository_path` no longer a readiness input); resync the §4 Safecor reference copy (v2 topics) and bump the *Synced* date.
- **0.5** `specifications/topology.md` §2/§7: `repository.disabled: true`, direct-mount as the analysis read path; `specifications/python-api.md`: same resync.
- **Acceptance**: docs consistent with §3; no code change; `0003` marked superseded with a pointer to `0019`.

### Phase 1 — libsaphir: AV controllers on the direct mount

- **1.1** `_abstract_antivirus_controller.py`:
  - Remove the `REPOSITORY_PATH` subscribe/publish and `__repository_path_received`; gate readiness on `System.on_usb_mountpoint_ready(cb)` (+ `is_usb_mountpoint_ready()` at start) AND `_engine_is_ready()`.
  - `saphir/analysis/request` handler: validate `["disk", "filepath"]`; queue `(disk, filepath, fingerprint)`.
  - `__analyse_with_integrity_check(disk, filepath, fingerprint)`: NFR-1 check against `f"/media/usb/{disk}{filepath}"` (kept, see §3); on mismatch → `fingerprint_error` response (unchanged mechanism, updated message).
  - Abstract `_analyse_file(disk, filepath)`; `publish_result`/`update_status` payloads echo `disk`.
- **1.2** `_clam_antivirus_controller.py`: scan `clamdscan /media/usb/<disk><filepath>` (direct, no staging).
- **1.3** `_eea_antivirus_controller.py`: same path (the LXC sees it via the bind mount — the container change lands in Phase 4); keep the odscan/lslog flow.
- **1.4** `_mock_antivirus_controller.py` (DEVMODE) + `_constants.py`: drop `DOMU_REPOSITORY_PATH`; add the `/media/usb` mount-point constant (verify whether the safecor lib already exposes one, otherwise define locally).
- **1.5** Unit tests for: readiness gating (mount not ready → not READY; ready → READY), NFR-1 mismatch on the media path, request validation, result payload with `disk`. `ruff check`/`ruff format` clean; coverage ≥ 85 % on modified modules.
- **Acceptance**: libsaphir unit suite green; a mock AV (DEVMODE) scans a file given `(disk, filepath)` and resolves it under a fake `/media/usb/<disk>` tree.

### Phase 2 — GUI: analysis flow rewrite

- **2.1** `analysis_controller.py`:
  - Remove: staging loop (`__do_copy_files_into_repository`, `__get_repository_free_slots`), `NEW_FILE`/`DELETED_FILE` handlers, the three `delete_file` calls, repository capacity/size properties, `FileAvailableInRepository`.
  - New flow per selected file: `Api().get_file_fingerprint(filepath, disk)` → on success: record fingerprint, **emit `systemUsed` (D4)**, publish `saphir/analysis/request {disk, filepath, fingerprint}`; on read failure: file → `FileAnalysisError`, chain continues (message logged).
  - Keep a parallelism cap (rename repository capacity → analysis capacity, same behaviour) so N sshfs reads/scans stay bounded.
  - **File identity `(disk, filepath)`**: key `__files`, `FileQueue`, `QueueListModel`, transfer and report details by the composite identity (display `<disk><filepath>`); this also hardens multi-source mode against path collisions.
  - Scenario 8.8 (D3): hold + auto-resume on same-disk reconnection; AV errors for held files ignored while held; re-fingerprint + re-request on resume; different disk → `SystemMustBeReset`.
  - AV response handling: match on `(disk, filepath)`; terminal-guard unchanged.
- **2.2** `application_controller.py` + `api_lifecycle.py`: remove the `repository_path` readiness gate and the `REPOSITORY_PATH/response` subscription.
- **2.3** `enums.py`: drop `FileAvailableInRepository` (preserve enum values/gaps used by QML — audit `Bindings.qml`/`QueueListModel` first).
- **2.4** DEVMODE & tests: mocks build a fake `/media/usb/<label>/` tree (GUI `conftest.py`, `mock_av_manager.py`; viewer mocks in Phase 3); rewrite `test_analysis_controller.py` (17+ `STR_REPOSITORY` refs), `test_av_integrity_check.py` (corruption now on the media tree), `test_workflow_*` (nominal, source-disconnection-analysis → D3 semantics, fingerprint-corruption); re-baseline the characterization list in `development/testing.md` §6.
- **Acceptance**: full GUI test suite green (DEVMODE) including the rewritten workflow scenarios; no `__repository__` reference left in `python/gui` (production code).

### Phase 3 — Viewer on the direct mount

- **3.1** `topology.json.viewer`: add `direct_mount: { "mode": "ro" }` to `saphir-viewer`.
- **3.2** `viewer/application_controller.py`: `repositoryPath` → per-disk `/media/usb/<disk>` (property becomes non-constant); `view_file()` opens the file directly from the media (no `read_file` staging); readiness via `System.on_usb_mountpoint_ready(cb)` before browsing.
- **3.3** `office_helper.py`: LibreOffice conversion from the media path.
- **3.4** Mocks + tests: `Viewer/Mock/*` (`mock_dom0_controller`, `mock_clam/eea`, `start_mocks_system`), `devmode_helper.get_repository_path` → fake media tree; `test_application_controller.py:453`, `test_office_helper.py:44`.
- **Acceptance**: viewer unit suite green; DEVMODE viewer opens a file from the fake `/media/usb/<disk>` tree.

### Phase 4 — ESET container package (decision D1)

- **4.1** `saphir-container-eset/APKBUILD`: container config — replace the `/mnt/storage` bind entry with `lxc.mount.entry = /media/usb media/usb none bind,optional,create=dir,noexec,nodev,nosuid`; drop the obsolete `/dev/hvc1` bind (v1 serial remnant); keep the `/tmp` bind.
- **4.2** `saphir-container-eset.post-install`: remove the 9p read-only remount (`mount -o remount,ro,trans=xen,version=9p2000.L ... storage /mnt/storage`); before `lxc-start`, wait (bounded, e.g. 60 s) for `/media/usb` to be mounted in the DomU (the `direct-mount` service brings it up at boot, before app-package install; the guard makes the order deterministic so the bind entry is not silently skipped).
- **4.3** `saphir-av-eset` initd/scripts: no change beyond what the controller (Phase 1.3) requires.
- **4.4** Rebuild the container package and validate an ESET scan end-to-end on a real disk (the dead ESET download URL is a known upstream issue — build against the official repository artifact).
- **Acceptance**: container starts only when the mount is ready; odscan reports `Scanned targets: /media/usb/<disk>/...`; one clean + one infected (EICAR) file scanned correctly.

### Phase 5 — Packaging & platform

- **5.1** APKBUILDs: pin `depends` to the 2.0-r0 line (`safecor-core`, `safecor-lib`, `safecor-domu-base`, `safecor-gui-base`); no `xe-guest-utilities` anywhere (v2 `safecor-gui-base` no longer pulls it — verify on the Safecor repo at build time). Per-package pyproject↔APKBUILD version coherence check (D5: no cross-package alignment).
- **5.2** Chroot validation → Alpine **3.24** (`setup/chroot/chroot-build.sh` + docker files); re-test the per-domain install worlds (the v1 xen/xe-guest-utilities conflict is gone in v2 — the GUI and core packages may now share a world, verify).
- **5.3** `topology.json`: add `"repository": { "disabled": true }` (D2) to both variants; regenerate the `saphir` APKBUILD checksums (`abuild checksum`).
- **5.4** ISO & local repository: fix `build-and-publish-iso` on Alpine 3.24 and adapt `setup/iso` + `setup/infrastructure` to the `packages.squashfs` local repository (Safecor-side redesign, `validation-tests-direct-mount.md` §"Packages repository redesign") — track as a follow-up item, may land in a separate issue when the Safecor side is final.
- **Acceptance**: all buildable Saphir packages build on the 3.24 chroot; GUI domain boots in DEVMODE.

### Phase 6 — Integration validation & docs wrap-up

- **6.1** Appliance/emulator run: boot, component states, `safecor_direct_mount` READY, full cycle (select → analyse → copy → report → reset), scenarios 8.6/8.8 (D3)/8.9, viewer switch, language.
- **6.2** Performance: sshfs read throughput vs 9p (ClamAV direct, ESET in the container); validate the parallelism cap; adjust if needed.
- **6.3** Security docs: `security/security-model.md` — NFR-1 re-anchored chain + the accepted trade-off (AV/viewer see the whole USB tree read-only; `sys-usb` sandbox remains the arbiter; repository disabled).
- **6.4** `project-status.md` + `validation-tests-direct-mount.md` updated; plan marked complete and moved to `docs/archive/plans/`.
- **Acceptance**: validation report appended; no open blocker from 6.1/6.2.

## 6. Protocol changes (summary)

| Topic | v1 payload | v4 payload |
|---|---|---|
| `saphir/analysis/request` | `{filepath, fingerprint}` | `{disk, filepath, fingerprint}` — `disk` = USB disk label (the `/media/usb/<disk>` component); `fingerprint` = `sys-usb`-computed (file API `file_fingerprint`) |
| `saphir/analysis/response` | `{component, filepath, success, details[, fingerprint_error]}` | `{component, disk, filepath, success, details[, fingerprint_error]}` |
| `saphir/analysis/status` / `error` | `{component/disk, filepath, ...}` | gain `disk` for consistency (error topic already carries `disk`) |
| GUI consumes (new) | — | `system/disks/file_fingerprint/response` |
| GUI stops consuming | `system/disks/new_file`, `system/disks/deleted_file` (repository), `system/disks/repository_path/response` | — |

## 7. Risks & mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| LXC bind evaluated at container start; if `/media/usb` not mounted yet the `optional` bind is silently skipped | High (boot) | Phase 4.2 bounded wait before `lxc-start`; fail loudly if the mount never comes up |
| sshfs performance (option `max_read=131072`) on deep scans | Medium | Phase 6.2 benchmark; keep the parallelism cap; ESET reads the same file via the bind (no extra copy) |
| NFR-1 TOCTOU (fingerprint computed by `sys-usb`, file read later by the AV) | Medium | AV-side verification kept (mismatch → `fingerprint_error`); residual window documented in the security model |
| File-identity collision across source disks | High (correctness) | `(disk, filepath)` composite keying in the GUI (Phase 2.1) |
| Workflow test re-baseline (staging-encoded tests) | Medium | Phase 2.4 targeted rewrites; characterization list re-audited |
| Attack surface: AV/viewer read the whole USB tree (ro) | Medium (accepted) | Documented (Phase 0.1, 6.3); ro + `sys-usb` bubblewrap sandbox; repository disabled |
| ISO build broken on 3.24 / squashfs redesign (Safecor side) | Medium | Tracked separately (Phase 5.4) |
| v2 local broker unauthenticated (dev line) | Low | Logged in `docs/safecor-divergences.md` (Safecor-side hardening) |

## 8. Out of scope

- Feature backlog items unrelated to the migration (F15 guards, F6 report language, D7/D8 GUI divergences, …) — stay in `project-status.md`.
- Safecor-side work (squashfs repository, broker hardening) — tracked via `docs/safecor-divergences.md`.
- Reintroducing archive mounting (ADR 0018).

## 9. Progress log

| Phase | Status | Issue | Notes |
|---|---|---|---|
| 0 Specs & ADR | ✅ done | — | ADR 0019 created; 0003 superseded; workflow/features/protocol/topology/python-api all updated |
| 1 libsaphir AV controllers | ✅ done | — | All 5 controllers rewritten: no staging, direct `/media/usb/<disk><filepath>` paths, `Constants.USB_MOUNT_POINT` used; DEVMODE readiness gate on `System.on_usb_mountpoint_ready` (G7) |
| 2 GUI analysis flow | ✅ done | — | Phase 2.1–2.4 all done: `analysis_controller.py` rewritten with `_find_file()` (bare keys + `disk` field for G1/G2), stale-failure guard (G3), `resetRequired` signal + handler (G4), disk field validation (G5), NFR-1 wording + `disk` param on `update_status` (G6), mock AV injectable `usb_mount` (G8). Round-2 integrity failure (see log 2026-11-25): v2 sources were restored by the coordinator and re-verified end to end |
| 3 Viewer | ⬜ pending | — | |
| 4 ESET container | ⬜ pending | — | |
| 5 Packaging & platform | ⬜ pending | — | |
| 6 Integration validation | ⬜ pending | — | |

### 2026-11-25 — Phase 1/2 verification, integrity incident, test-infra hardening

- **Round-2 integrity failure (rejected):** a delegated round reverted the v2 production
  sources to the v1 state with fabricated justifications. All v2 sources
  (`analysis_controller.py`, `application_controller.py`, `api_lifecycle.py`,
  libsaphir AV controllers) were restored by the coordinator and re-verified
  independently: ruff check/format clean, boot smoke PASS (`SystemReady`),
  E2E smoke PASS (disk hot-plug → file list → 3 real SHA-512 fingerprints
  computed by the emulator → analysis → consensus → `AnalysisCompleted`).
- **Safecor emulator (cross-repo, user validation pending):** `mock_sys_usb.py`
  now emulates `system/disks/file_fingerprint/{request,response}` (real SHA-512
  of `{disk_root}{filepath}`; missing file → empty fingerprint, mirroring
  production). Ruff error count identical to HEAD (all pre-existing).
- **DEVMODE broker self-sufficiency:** the safecor DEVMODE clients hard-code
  `localhost:1883`; the GUI suite silently depended on a broker left over on the
  dev machine. `python/gui/tests/conftest.py` now provides a session-scoped
  autouse `_mqtt_broker` fixture (reuse if reachable, else start and own a
  `MosquittoBroker`, stopped at session end).
- **Workflow flake root cause (2026-11-25):**
  `test_source_disconnection_during_analysis_holds_and_resumes` stalled in
  `SystemAnalysisRunning` intermittently. Root cause: two **zombie mock AV
  subprocesses** from a crashed session (client IDs `mock-clam`/`mock-eset`,
  paho auto-reconnect) fought the new session's AVs for the same fixed MQTT
  client IDs; the broker repeatedly disconnected one side or the other,
  in-flight responses were lost and files stayed `FileAnalysing` until timeout.
  A delegated diagnosis blaming a "stale Mosquitto broker PID" was rejected
  (no live broker existed). Fix: zombies killed + session-scoped autouse
  `_kill_stale_test_processes` fixture in `conftest.py` (pkills stale
  `libsaphir._mock_antivirus_controller` and `test_app_entry.py` subprocesses
  at session start). The test then passed 3/3 consecutive runs.
- **D3 unit-test coverage gap:** the sub-agent's unit tests covered the hold
  (DISCONNECTED) branch only; the CONNECTED resume branch was exercised solely
  by workflow tests (subprocesses, not counted for coverage), leaving
  `analysis_controller.py` at 84 % (below the 85 % gate). Three in-process
  unit tests were added to `test_analysis_controller.py` (same-disk resume,
  different-disk `resetRequired`, AV failure ignored while held).
- **Final verification (2026-11-25):** full GUI suite
  **538 passed / 4 failed / 1 xfailed** in 270 s — the 4 failures are exactly
  the pre-existing, out-of-scope translation failures
  (`test_translation_manager` ×3, `test_application_controller::test_language_initial`).
  Coverage (`--cov=src/Saphir/Saphir`): `api_lifecycle` 100 %,
  `application_controller` 92 %, `analysis_controller` **91 %**, TOTAL **94 %**
  (gate ≥ 85 % satisfied). libsaphir in-process coverage (39 %) is a
  pre-existing structural property (concrete AV controllers run in separate
  VMs in production / subprocesses in tests; the same in-process
  `test_av_integrity_check.py` pattern existed on HEAD).
- **User validation & commit (2026-11-25):** the cross-repo Safecor emulator
  change (`mock_sys_usb.py` FILE_FINGERPRINT handler) and the GUI test-infra
  fixtures (`conftest.py`) were validated by the user. Phases 0–2 committed on
  `version-4` (refs #167); Phase 3 (viewer) paused by the user. The Safecor
  emulator change remains uncommitted in the Safecor repository. Note:
  `python/gui/.coverage` is tracked in the repository (pre-existing); it must
  be untracked + gitignored in a separate cleanup.

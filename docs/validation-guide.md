# Saphir Validation Environment Guide

> **Status**: Active
>
> **Last updated**: 2026-11-03
>
> **Reference**: `docs/test-strategy.md` §3–4, `docs/workflow-rules.md`

This guide describes how to set up and use the **semi-automated validation
environment** for Saphir. It allows a developer or QA operator to manually
drive user scenarios (attach/detach disks, trigger analysis, observe the GUI)
without a Safecor appliance.

---

## 1. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Host machine                                                   │
│                                                                 │
│  ┌────────────────────┐    MQTT (localhost:1883)   ┌────────┐  │
│  │  Safecor Emulator  │ ◄─────────────────────────► │  GUI   │  │
│  │  (GUI app:         │                             │ (Qt,   │  │
│  │   mosquitto +      │ ◄─────────────────────────► │ on-    │  │
│  │   mock Dom0 +      │                             │ screen)│  │
│  │   mock SysUSB +    │                             └────────┘  │
│  │   operator panel)  │                                         │
│  └────────────────────┘                                         │
│           ▲                                                     │
│           │ MQTT                                                 │
│  ┌────────┴────────┐  ┌──────────────────┐                      │
│  │  mock-clam      │  │  mock-eset       │                      │
│  │  (subprocess)   │  │  (subprocess)    │                      │
│  └─────────────────┘  └──────────────────┘                      │
└─────────────────────────────────────────────────────────────────┘
```

Three components must be running simultaneously:

| # | Component | Role | Started by |
|---|-----------|------|------------|
| 1 | **Emulator GUI** | Mosquitto broker + mock Dom0 + mock SysUSB + operator controls | Operator (prerequisite) |
| 2 | **mock-clam / mock-eset** | Mock antivirus engines | `validate_env.sh` |
| 3 | **Saphir GUI** | The application under test (on-screen) | `validate_env.sh` |

The **operator console** (a separate terminal) is used to drive the scenario.

---

## 2. Prerequisites

| Requirement | Check |
|-------------|-------|
| Saphir dev environment | `bash python/gui/setup_dev_env.sh` (venv + Safecor `.pth` links) |
| Safecor repository checkout | A local clone of the Safecor repo (path set via `SAFECOR_ROOT`) |
| A local directory emulating the source disk | e.g. `/tmp/source-disk/` with a few files |
| A local directory emulating the target disk | e.g. `/tmp/target-disk/` (empty) |
| Mosquitto broker | Auto-started by the emulator on port 1883 |

---

## 3. Setup (one-time)

```bash
cd /path/to/Saphir/python/gui
SAFECOR_ROOT=/path/to/Safecor bash setup_dev_env.sh
source .venv/bin/activate   # or venv.nosync/bin/activate on macOS
```

`SAFECOR_ROOT` must point to the root of your Safecor repository checkout
(the directory containing `python/lib/src` and `python/emulator/src`).

> **macOS**: the venv is created in `venv.nosync` by default (Time Machine
> friendly). Linux-only dependencies (`evdev`, `inotify_simple`, `pyudev`) are
> skipped automatically with a warning. Override with `SAPHIR_VENV_DIR`.

Verify the emulator is importable:

```bash
python -c "from safecor_emulator import Emulator, default_profile; print('OK')"
```

---

## 4. Running the validation environment

### Terminal 1 — Emulator (GUI)

Launch the Safecor emulator GUI:

```bash
python -m safecor_emulator.cli
```

The GUI provides:
- Configuration of source disks, storage path, and target disk
- Starting/stopping the emulator (mosquitto broker + mock Dom0 + mock SysUSB)
- Interactive controls: attach/detach disks, set energy state, restart domains,
  set language

Use the GUI to configure the scenario (source disk path, target disk path,
storage path) before starting the emulator.

### Terminal 2 — Saphir (GUI + mock AVs)

```bash
cd /path/to/Saphir/python/gui
bash validate_env.sh
```

The script:
1. Verifies the broker is reachable on `localhost:1883`.
2. Starts `mock-clam` and `mock-eset` as background subprocesses.
3. Launches the Saphir GUI **on-screen** (native platform, kiosk layout).

Stop everything with **Ctrl+C** in Terminal 3 (mock AVs are cleaned up
automatically).

---

## 5. Validation scenarios

Each scenario below starts from a fresh boot (restart the GUI to reset).
Use the operator console (Terminal 2) to drive events.

### 5.1 Nominal cycle (C.1)

| Step | Action | Expected GUI state |
|------|--------|--------------------|
| 1 | Emulator running, source disk attached at boot | `SystemLoading` → `SystemReady` |
| 2 | Wait for auto-analysis (DEVMODE auto-pilot) | `SystemAnalysisRunning` |
| 3 | Analysis completes | `SystemAnalysisFinished` |
| 4 | Attach target disk via emulator GUI | Copy starts → `SystemCopyRunning` |
| 5 | Copy completes | `SystemReportGeneration` → `SystemMustBeReset` |
| 6 | Verify `/tmp/target-disk/` contains clean files + PDF report | — |

### 5.2 Infected file (F3 consensus)

Pre-configure one of the mock AVs to report a file as infected. This requires
a custom config file:

```json
{
    "default": "clean",
    "infected": ["/tmp/source-disk/bad.txt"],
    "scan_delay": 0.1
}
```

Start the mock with:
```bash
DEVMODE=1 python -m libsaphir._mock_antivirus_controller --name mock-clam --config /tmp/infected.json
```

Then run `validate_env.sh` but skip the `mock-clam` startup (edit the script
or start only `mock-eset`). The infected file should appear in the "Infected"
tab and **not** be copied to the target.

### 5.3 Source disconnection during analysis (8.8)

| Step | Action | Expected |
|------|--------|----------|
| 1 | Let analysis start | `SystemAnalysisRunning` |
| 2 | Detach source disk via emulator GUI | GUI shows "source disconnected" prompt, analysis holds |
| 3 | Attach source disk via emulator GUI | Analysis resumes (remaining files only) |

### 5.4 AV engine failure (NFR-3, 8.9)

| Step | Action | Expected |
|------|--------|----------|
| 1 | Let analysis start | `SystemAnalysisRunning` |
| 2 | Restart AV domain via emulator GUI | GUI detects AV failure, shows NFR-3 message |
| 3 | Wait | System transitions to error state |

### 5.5 Target disconnection during copy (F4, 8.6)

| Step | Action | Expected |
|------|--------|----------|
| 1 | Reach `SystemCopyRunning` | Copy in progress |
| 2 | Detach target disk via emulator GUI | Copy pauses, GUI shows reconnection prompt |
| 3 | Attach target disk via emulator GUI | Copy resumes |

### 5.6 Multi-source (F1, 10.8)

| Step | Action | Expected |
|------|--------|----------|
| 1 | Boot with one source | Analysis starts on disk0 |
| 2 | Attach second source via emulator GUI | Second source appears in the GUI |
| 3 | Analysis covers both disks | All clean files from both disks are copied |

### 5.7 Power loss during scan (NFR-5)

| Step | Action | Expected |
|------|--------|----------|
| 1 | Let analysis start | `SystemAnalysisRunning` |
| 2 | Set energy state to "off" via emulator GUI | GUI shows low-power / shutdown message |
| 3 | System transitions to shutdown | `SystemShuttingDown` in state log |

### 5.8 Language change (F19)

| Step | Action | Expected |
|------|--------|----------|
| 1 | System in `SystemReady` | UI in default language (EN) |
| 2 | Set default language to "fr" via emulator GUI | GUI retranslates to French |
| 3 | Verify labels, buttons, messages | All strings in French |

---

## 6. State observer (DevMode)

In DEVMODE, the `WorkflowController` writes every state transition to
`/tmp/saphir_state.log`. Open a separate terminal and tail it live:

```bash
tail -f /tmp/saphir_state.log
```

Output format (one line per event):

```
1793720794.772 TRANSITION SystemReady
1793720794.801 TRANSITION SystemGettingFilesList
1793720795.102 BLOCKED SystemAnalysisRunning -> SystemReady
```

- `TRANSITION` — a valid state change was applied.
- `BLOCKED` — a transition was **rejected** by the state machine (indicates a bug).

The file is truncated on each app start (DEVMODE only). No impact in production.

---

## 7. Troubleshooting

| Symptom | Cause / Fix |
|---------|-------------|
| `ERROR: MQTT broker not reachable` | Emulator not started, or mosquitto on a different port. Check Terminal 1. |
| GUI stuck in `SystemLoading` | Mock AVs not discovered. Check they are running (`ps aux \| grep mock`). Ensure `DEVMODE=1` is set. |
| Mock AV dies at startup | Check `PYTHONPATH` includes `libsaphir/src`. Check no port conflict on 1883. |
| GUI shows no disks | Emulator `source_disks` config must match the disk names the GUI expects. Check the emulator logs. |
| Analysis starts but no files | The emulator's `source_disks` path must contain files. Verify the directory is not empty. |

---

## 8. Cleanup

After validation:

```bash
# Terminal 3: Ctrl+C (stops GUI + mock AVs)
# Terminal 1: Ctrl+C (stops emulator)
# Terminal 2: exit (closes operator console)

# Clean up temp directories
rm -rf /tmp/source-disk /tmp/target-disk /tmp/repo
```

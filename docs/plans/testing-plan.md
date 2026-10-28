# Testing Plan — Saphir (pre-refactoring phase)

> **Status**: Done — all phases A–D complete (PR Saphir #128, PR Safecor #231)
> **Branch**: `pre-refactoring`
> **Last updated**: 2026-10-28
> **Reference**: `docs/test-strategy.md`, `docs/workflow-rules.md` (scenarios §8), `docs/plans/refactoring-plan.md`

---

## 1. Objective

Build a **safety net** of integration / functional tests (**characterization**) **before** the refactoring. The tests capture the **current behaviour, bugs included**, so that the refactoring can be validated against them: a test that encodes a current bug keeps failing until the refactoring fixes it; a test that encodes correct behaviour must keep passing throughout the refactoring.

Scope: **no new unit tests** for the sub-modules to be extracted (they would be partly useless after the refactor). The focus is on **end-to-end workflow** driven through the **Safecor emulator**.

---

## 2. Decisions (2026-10-28)

| # | Decision |
|---|----------|
| **D-1** | **Mock antivirus** lives in **Saphir** (`python/gui/tests/`), **not** in the Safecor emulator (AV analysis is a Saphir feature, not a Safecor one). It **inherits `AbstractAntivirusController`**, runs in a **subprocess** (the `Api()` singleton forbids in-process sharing with the GUI), and is driven **statically** (results fixed at launch). Dynamic driving → backlog. |
| **D-2** | **Bug target** of the first functional test: **target disconnection at the end of the copy** → the GUI goes to an **incoherent waiting state** instead of `SystemMustBeReset`. Root cause: `SystemMustBeReset` is only emitted in `__handle_create_file` (when `journal.log` is copied); a target disconnect is handled by `__handle_disk_state` which does **not** emit it. |
| **D-3** | **Environment**: a venv is **created** for Saphir (none exists yet). `safecor` + `safecor-emulator` are exposed via **`.pth` files** pointing at the local Safecor repos (no packaging — their transitive dependencies are already in Saphir's `requirements.txt`). `pytest` is added to `requirements-dev.txt`. |

---

## 3. Phases

### Phase A — Extend the Safecor emulator (`safecor_emulator`, **Safecor repo**)

Add only the **generic** Safecor capabilities that Saphir consumes and that the emulator does not yet provide.

- **A.1. Mock Dom0 extension** (`peers/mock_dom0.py`):
  - `ENERGY_STATE/response` — `set_energy(battery_level, plugged)`.
  - `DEFAULT_LANGUAGE/response` — `set_default_language(lang)`.
  - `RESTART_DOMAIN/response` — `restart_domain(domain_name)`.
- **A.2. Scenario API** (extension of `emulator.py`):
  - `em.set_energy(battery_level, plugged)`
  - `em.set_default_language(lang)`
  - `em.restart_domain(domain_name)`
  - (`attach_disk` / `detach_disk` already exist.)
- **A.3. Pytest plugin** (`pytest_plugin.py`): keep the `emulator` fixture; document the new scenario methods.

> The **mock AV is NOT part of Phase A** (see D-1) — it belongs to Phase B (Saphir).

### Phase B — Saphir: mock AV + remove local mocks

- **B.1. Mock antivirus** (`python/gui/tests/`):
  - `MockAntivirusController(AbstractAntivirusController)` — implements the abstract hooks; **pilotable** (a `filepath → result` map, a default result, a delay).
  - Runs in a **subprocess** (its own `Api()` singleton), launched with the driving config (args / JSON file).
  - Test-side driver: launch/stop the subprocesses, pass the config.
- **B.2. Remove local mocks**: delete `python/gui/src/Saphir/Mock/` (all files); clean imports.
- **B.3. `devmode_helper.py`**: make the hardcoded macOS paths portable (or simplify, the emulator now owns the disks).

### Phase C — Saphir: functional tests (`python/gui/tests/`)

- **`conftest.py`**: `pytest_plugins = ["safecor_emulator.pytest_plugin"]` + fixtures (emulator, mock-AV driver, GUI harness).
- **`test_workflow_nominal.py`** — scenario **8.1** (full cycle):
  boot + 2 AV ready → `attach_disk(source)` → LIST_FILES → selection → analysis (2 AV, all clean) → `AnalysisCompleted` → `attach_disk(target)` → `CopyCleanFiles` → `GeneratingReport` → report+journal copied → `SystemMustBeReset` → reset → `SystemReady`.
- **`test_workflow_bug_target_disconnection.py`** — **bug target (D-2)**:
  nominal cycle up to `CopyCleanFiles` (copy running) → `detach_disk(target)` (user removes the target) → **assert state == `SystemMustBeReset`** → **the test FAILS** (current incoherent state) → documents the bug, will be validated by the refactoring.

### Phase D — Config

- **`requirements-dev.txt`**: add `pytest` (and note the `.pth` requirement).
- **`setup_dev_env.sh`**: create the venv, install `requirements.txt` + `requirements-dev.txt`, create the two `.pth` files pointing at `/home/onyxia/work/Safecor/python/lib/src` and `/home/onyxia/work/Safecor/python/emulator/src`.
- **pytest config** (`pyproject.toml` `[tool.pytest.ini_options]`): `addopts = "-p safecor_emulator.pytest_plugin"`, `testpaths = tests`.

---

## 4. Milestones (execution order)

1. **A.1 + A.2** → a minimal test (boot + energy) passes.
2. **B.1** → the mock AV works (an analysis test passes with it).
3. **B.2 + B.3** → no reference to the local mocks.
4. **C.1** → the nominal cycle passes.
5. **C.2** → the bug test **fails** (documents the bug).
6. **D** → `pytest` runs cleanly from a fresh venv.

---

## 5. Test backlog (future increments)

- **Dynamic mock-AV driving** (change per-file results on the fly; needed for "one AV flags a file").
- Scenario **8.2** (pause / resume during analysis).
- Scenario **8.4** (single-disk mode, target inserted later).
- Scenario **8.6** (source/target disconnection **during** copy + auto-resume — blocked by the `>= CopyCleanFiles` gate).
- Scenario **8.7** (report generation failure → `ReportFailed`).
- Scenario **8.8** (source disconnection during analysis).
- AV failure (NFR-3 — minimum number of engines).
- Fingerprint integrity (NFR-1 — injected alteration).
- `storagesCount` / `systemState` visibility race (plan §1.2).
- Thread-safety checks (plan §1.2).

---

## 6. Notes

- All work that **modifies existing code** is done on the **`pre-refactoring`** branch.
- The emulator extension (Phase A) is done in the **Safecor** repo (separate branch there if needed).
- The bug test (C.2) is expected to **fail** on the current code — that is intentional (characterization). It must be tracked and only pass once the refactoring (or a targeted fix) addresses D-2.

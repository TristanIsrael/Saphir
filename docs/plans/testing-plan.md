# Testing Plan — Saphir

> **Status**: Active — refactoring Phases 0-6 complete, testing validates the refactored architecture
> **Branch**: `refactoring`
> **Last updated**: 2026-10-28
> **Reference**: `docs/plans/refactoring-plan.md`, `docs/test-strategy.md`

---

## 1. Objective

Validate the refactored architecture through a layered test strategy:
- **Unit tests** — cover individual modules in isolation (mocked dependencies)
- **Handler tests** — invoke MQTT message handlers directly with crafted payloads
- **Integration tests** — full workflow cycles driven through the Safecor emulator + real MQTT

Quality gate: **≥ 85% code coverage** on the full `Saphir` package.

---

## 2. Current State (2026-10-28)

### 2.1 Coverage

| Module | Coverage |
|--------|----------|
| `application_controller.py` | 91% |
| `analysis_controller.py` | 71% |
| `analysis_helper.py` | 100% |
| `api_lifecycle.py` | 100% |
| `transfer_controller.py` | 100% |
| `storage_manager.py` | 100% |
| `file_queue.py` | 100% |
| `file_browser.py` | 100% |
| `workflow_controller.py` | 100% |
| `energy_monitor.py` | 97% |
| `translation_manager.py` | 100% |
| `report_controller.py` | 95% |
| `queue_list_model.py` | 92% |
| `safecor_input_files_list_model.py` | 91% |
| `queue_list_proxy_model.py` | 74% |
| **TOTAL** | **87%** ✅ |

### 2.2 Test inventory (350 tests, 3 skipped)

| File | Tests | Scope |
|------|-------|-------|
| `test_workflow_controller.py` | 18 | State machine transitions, guards |
| `test_energy_monitor.py` | 8 | Battery/plugged state polling |
| `test_translation_manager.py` | 7 | Language switching, QTranslator |
| `test_api_lifecycle.py` | 11 | Subscription tracking, all-ready callback |
| `test_file_queue.py` | 12 | Queue data structure, enqueue/dequeue |
| `test_file_browser.py` | 10 | Folder navigation, file listing |
| `test_storage_manager.py` | 14 | Source/target management, storages |
| `test_transfer_controller.py` | 12 | Copy orchestration, progress, completion |
| `test_analysis_controller.py` | 28 | Full analysis cycle via MQTT (integration) |
| `test_analysis_helper.py` | 16 | Consensus rule, file classification |
| `test_report_controller.py` | 8 | Report generation, file operations |
| `test_ema_eta_estimator.py` | 10 | ETA calculation, exponential moving average |
| `test_application_controller.py` | 51 | Property getters, slots, state management |
| `test_application_controller_handlers.py` | 76 | MQTT message handlers (disk state, list files/disks, components, copy, energy, system info, create file, results, transfer, reset, shutdown) |
| `test_models.py` | 74 | All QML models (QueueList, Components, SystemInfo, LogList, MessagesList, InputFilesList, proxy models, DevModeHelper) |
| `test_workflow_nominal.py` | 1 | Full nominal cycle via Safecor emulator (integration) |

### 2.3 Resolved bugs (validated by tests)

| Bug | Fix commit | Validating test |
|-----|-----------|-----------------|
| Target disconnection during copy → incoherent state | `d7df95b` | `test_handle_disk_state_disconnected_target_during_copy` |
| Broken analysis controller tests (deepcopy, state assertions) | `814f8a8` | `test_analysis_controller.py` (full suite) |

---

## 3. Test Architecture

### 3.1 Layers

```
┌─────────────────────────────────────────────────────────┐
│  Integration (emulator + real MQTT)                     │
│  test_workflow_nominal.py, test_analysis_controller.py │
├─────────────────────────────────────────────────────────┤
│  Handler (mocked Api, direct method invocation)         │
│  test_application_controller_handlers.py               │
├─────────────────────────────────────────────────────────┤
│  Unit (mocked dependencies, isolated modules)           │
│  test_workflow_controller.py, test_file_queue.py, etc. │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Key patterns

- **Api mocking**: `patch("Saphir.<module>.Api")` — each module that imports `Api` must be patched separately.
- **Mock AnalysisController**: `_make_mock_analysis_controller()` provides the interface without a real MQTT subscription.
- **Emulator integration**: `safecor_emulator.pytest_plugin` provides the `emulator` fixture with a real Mosquitto broker + mock peers.
- **DEVMODE**: set via environment variable (`DEVMODE=1`) to activate the dev MQTT client path.

### 3.3 Running tests

```bash
cd python/gui
DEVMODE=1 .venv/bin/python -m pytest tests/ -v

# Coverage
DEVMODE=1 .venv/bin/coverage run --source=src/Saphir -m pytest tests/ -q
.venv/bin/coverage report
```

---

## 4. Remaining Gaps & Backlog

### 4.1 Coverage gaps (below 85%)

| Module | Coverage | Gap | Effort |
|--------|----------|-----|--------|
| `analysis_controller.py` | 71% | Archive mounting, error paths, multi-iteration analysis | Medium |
| `queue_list_proxy_model.py` | 74% | `lessThan()` comparison logic, `on_data_changed()` | Low |
| `main.py` | 0% | Entry point (intentionally excluded from coverage target) | N/A |

### 4.2 Functional test backlog

| Scenario | Description | Priority |
|----------|-------------|----------|
| 8.2 | Pause / resume during analysis | Medium |
| 8.4 | Single-disk mode, target inserted later | Medium |
| 8.6 | Source/target disconnection during copy + auto-resume | High |
| 8.7 | Report generation failure → `ReportFailed` | Medium |
| 8.8 | Source disconnection during analysis | Medium |
| AV failure | Minimum number of engines (NFR-3) | High |
| Fingerprint integrity | Injected alteration detection (NFR-1) | Low |
| Dynamic mock-AV driving | Change per-file results on the fly | Low |

### 4.3 CI integration (deferred)

- Add a `pytest` job to `.github/workflows/build-all.yml`
- Requires a Mosquitto broker service container
- Coverage gate: reject PRs below 85%

---

## 5. Decisions (historical)

| # | Decision | Date |
|---|----------|------|
| **D-1** | Mock antivirus lives in Saphir (`python/gui/tests/`), inherits `AbstractAntivirusController`, runs in a subprocess | 2026-10-28 |
| **D-2** | Bug target: target disconnection at end of copy → `SystemMustBeReset` (FIXED in `d7df95b`) | 2026-10-28 |
| **D-3** | Environment: venv + `.pth` files for Safecor repos (no packaging) | 2026-10-28 |
| **D-4** | Phase 6 scope: 85% coverage on the **entire project**, not just refactored modules | 2026-10-28 |
| **D-5** | Handler tests use mocked `Api` + direct method invocation (no real broker needed) | 2026-10-28 |

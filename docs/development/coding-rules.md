# Saphir — Coding Rules

> **Status**: Stable
> **Last updated**: 2026-11-20
> **Audience**: developers (human and AI agents) writing or modifying Saphir code
> **Scope**: the coding standards, naming conventions, and linting/static-analysis rules for the Saphir codebase (Python and QML).

> **Source of truth**: `AGENTS.md` (repository root) is the authoritative source for these rules. This file is an intentional **standalone offline copy** so that offline coding agents have the standards at hand without the rest of `AGENTS.md`. When the two disagree, `AGENTS.md` wins.

## Related documents

| Concern | Document |
|---------|----------|
| Project overview, tech stack, repository layout | [`../../AGENTS.md`](../../AGENTS.md) |
| MQTT protocol contract (topics & payloads) | [`protocol.md`](protocol.md) |
| Build & packaging rules | [`building.md`](building.md) / [`packaging.md`](packaging.md) |
| Test conventions (test file naming, coverage gate) | [`testing.md`](testing.md) |

---

## 1. General rules

- Follow the **existing naming conventions**. The codebase is the reference; when in doubt, match the surrounding code.
- Use **`ruff format`** to format Python code consistently.
- Do **not** introduce unrelated formatting changes.
- Comments, documentation and commits are written in **English**.

---

## 2. Naming conventions

| Domain | Convention | Examples |
|---|---|---|
| Python — classes | `PascalCase` | `ApplicationController`, `EMAETAEstimator` |
| Python — methods / variables | `snake_case` | `start_transfer`, `remaining_time` |
| Python — private methods | double-underscore (name mangling) | `__set_system_state`, `__handle_disk_state` |
| Python — constants | `UPPER_SNAKE` | `ANTIVIRUS_NEEDED`, `TOPIC_ANALYSIS`, `DEVMODE` |
| Python — enums | `PascalCase` (no underscores) | `SystemAnalysisRunning`, `FileClean` |
| QML — components | `PascalCase` | `AnalysisPanel`, `FilesSelectionPanel` |
| QML — properties / bindings | `camelCase` | `systemState`, `queueSize`, `nbClean` |
| MQTT topics | `saphir/analysis/{request,response,status,error,stop,resume,reset}`; `system/...` | — |

---

## 3. Linting and static analysis

- Use **`ruff check`** to detect linting issues, potential bugs, and violations of coding conventions.
- Run static analysis on **all modified Python files**, including newly added files.
- Do **not** suppress linting rules unless there is a clear justification.
- Use **type checking** and resolve any new type errors introduced by the changes.

The project's `ruff` configuration lives in `python/gui/pyproject.toml` (`[tool.ruff]`, `target-version = "py39"`) and ignores a small set of Qt-idiom rules (`RUF012`, `B008`, `N999`). Match the surrounding code and do not add new suppressions without justification.

---

## 4. Python dependency placement

These placement rules keep production and development dependencies separated (see also [`building.md`](building.md)):

- Dependencies used **only** in development and tests must lie in `requirements-dev.txt`.
- Dependencies used in **production, development and tests** must lie in `requirements.txt`.

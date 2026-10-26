---
name: Feature
about: Propose a new feature for Saphir. Fill in the template so the feature can be implemented and tested.
title: "[Feature] "
labels: feature
---

## Objective

<!-- ONE sentence: the observable end state. This is your "definition of done". -->
<!-- Ex: "The user can select multiple files in one action and send them to analysis; the queue shows a selection count." -->

## Context / Problem

<!-- 2-5 sentences: why, what problem, what the current behavior is. -->
<!-- No undefined jargon. If it's a bug/limitation, describe what happens today. -->

## Use case

- As a <role>, I want to <action>, so that <benefit>.

## Functional requirements

<!-- Precise, TESTABLE behaviors, Given/When/Then format. Each RF maps 1:1 to a test. -->

1. **RF-1**: <behavior>
   - Given <precondition>
   - When <action>
   - Then <observable result>
2. **RF-2**: …

## Out of scope (non-goals)

<!-- Mandatory: bounds the work, prevents over-interpretation. -->

- We are NOT doing <X> here.
- <Y> will be handled in a separate issue.

## Technical constraints & conventions

<!-- What the implementation MUST follow to stay consistent with the codebase. -->

- Affected files/modules: e.g. `python/gui/src/Saphir/Saphir/analysis_controller.py`
- Patterns to respect: e.g. new QObject signal (MVVM), AV controller Template Method, new `FileStatus` enum value
- Allowed / forbidden dependencies
- EN/FR bilingualism: add i18n keys (`i18n/fr.ts` + `.ts`)

## Interface / Contract (if changed)

<!-- The exact contract — ambiguity here breaks auto-implementation. -->

- MQTT: exact new topics/payloads, e.g. `saphir/analysis/…`
- Python API: signatures, e.g. `def enqueue_files(paths: list[str]) -> int`
- QML exposed: new `Property`/`Signal`/slots
- Config/CLI: new keys/options
- Enums/states: new values + transitions (e.g. `SystemState`)

## Edge cases & error handling

- If <condition> → <expected behavior>
- Exact error message + where it shows (dialog / log / QML)

## Data / State changes

<!-- New persisted values, state transitions, new QML models. -->

## Required tests

<!-- Framework: pytest, in `python/gui/tests/`. Describe each test + expected assertion. -->

- `test_<name>`: covers <RF-n>, asserts <…>
- Edge cases to cover: <…>
- `DEVMODE` / mocks (`Saphir/Mock/`) needed? yes/no + which ones

## Verification (how to validate)

<!-- EXACT commands + what can be validated locally vs on the appliance. -->

- Tests: `pytest python/gui/tests/<file> -v`
- Lint / typecheck: <repo command>
- Reproducible manual scenario (DEVMODE): <steps 1-2-3>
- Cannot be validated without the appliance: <…>

## Likely files touched

<!-- Hint for locating — does not lock the implementation choice. -->

- <path 1>, <path 2>

## Definition of Done

- [ ] RF-1..N satisfied
- [ ] Tests added and green
- [ ] Lint / typecheck OK
- [ ] Docs updated: `/docs` + Doxygen (implementation files) + `README.md` & `README.fr.md` + `docs/manual.md` (if user-visible)
- [ ] EN/FR bilingual
- [ ] No commit without approval

## References

- Related issue/PR: <#…>
- Doc: <docs/…>
- Code: <path:line>

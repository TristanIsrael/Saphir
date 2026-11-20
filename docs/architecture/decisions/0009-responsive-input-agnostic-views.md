# 0009 — Responsive, input-agnostic views

> **Status**: Accepted
> **Source**: architecture.md §8 — D-arch-9 (and §3.4 form & responsiveness rule)

## Context

The **primary deployment target** is an **8-inch touch tablet** (touch-first), but the application must also be usable on a **desktop PC with keyboard and mouse**. Safecor abstracts the physical input devices and exposes virtual inputs, so the app is not tied to one hardware input.

## Decision

The views must be **responsive** and **input-agnostic**. For now a **single interface** is used for both targets, with **different input handling** (touch vs. mouse/keyboard); the tablet assumption must not be hard-coded. The layout must tolerate a range of screen sizes so the UI can later **specialise** per target — large screens / desktop, and, if that target becomes viable, smartphone — **without a redesign**. The `Environment.qml` `handheld` property is the form-factor selector meant to drive the UI variant.

## Consequences

- Any view that hard-codes a fixed size, assumes touch-only, or breaks on a non-tablet form factor is **rule-debt** and must be logged in the GUI backlog & rule-debt section of [`../../project-status.md`](../../project-status.md).
- The cursor is hidden by default and re-appears on first mouse movement (touch-first behaviour without a configured flag).

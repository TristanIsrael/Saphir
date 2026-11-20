# 0001 — Event-driven, no polling

> **Status**: Accepted
> **Source**: architecture.md §8 — D-arch-1

## Context

Safecor is notification-based: disk state changes, file availability, component readiness, and log events all arrive as MQTT messages. A GUI that polls the platform would add latency, load, and races on top of a protocol that already delivers every change.

## Decision

The system is **event-driven**: Saphir components never poll platform state — they subscribe to the relevant topics and react to the messages. The **sole exception** is the 5 s energy poll (`system/energy/state`), because the energy state is otherwise only refreshed on user action.

## Consequences

- Every state change arrives **on the MQTT thread**: handlers must be thread-safe and must not block.
- The battery level is at most ~5 s stale.
- No component may introduce a polling loop over `system/*` topics without a new ADR.

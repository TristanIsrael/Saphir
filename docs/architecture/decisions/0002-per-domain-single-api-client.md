# 0002 — Per-domain single API client

> **Status**: Accepted
> **Source**: architecture.md §8 — D-arch-2 (and §4.1)

## Context

The Safecor `Api` is a **singleton** (`safecor._api.Api` uses `SingletonMeta`). Each Safecor domain is its own VM/process and the isolation model does not allow shared memory between VMs.

## Decision

Each domain holds **exactly one** `Api()` / `MqttClient`, and **all** traffic between domains goes over MQTT. Only one object per process may create and manage the client; all other objects funnel through that one client. In the target architecture the dedicated **`ApiLifecycle`** module is the *sole* owner of client creation and subscription management (invariant **I1**).

## Consequences

- A process cannot create a second MQTT client — which is why the mock AV controllers run in **standalone processes** in DEVMODE.
- All subscriptions are centralised in one place (`ApiLifecycle`), which is what makes the topic-ownership matrix ([protocol.md](../../development/protocol.md)) enforceable (invariant **I2**).

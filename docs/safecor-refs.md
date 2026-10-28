# Safecor references

> Purpose: point to the **Safecor sources of truth** used during Saphir's analysis and
> refactoring. Keep this file up to date as Safecor evolves.
>
> The Safecor repo and wiki live in **sibling directories** of the Saphir repository
> (current machine layout: `/home/onyxia/work/` → `Saphir/` = repo, `Saphir.wiki/` = wiki).

## Sources

| Source | Path (sibling of Saphir) | Role |
|---|---|---|
| **Safecor repo** (code) | `Saphir/` | **Source of truth** for the current Python API and platform behaviour. |
| **Safecor wiki** | `Saphir.wiki/` | Platform context: protocol, topology, emulator, design rules. Complementary. |

## Safecor wiki — pages to rely on

| Page | Use during refactoring |
|---|---|
| `Protocol.md` | MQTT topics + payloads (system topics). **Verified coherent** with `safecor/_topics.py`. |
| `Topology.md` | Multi-domain topology (dom0 / domU). |
| `Architecture.md` | Platform architecture. |
| `Saphir-core.md` | Core behaviours (boot, reset, restart). |
| `Emulator.md` | Emulator — useful for DevMode / local tests. |
| `Design-rules.md` | Platform design rules. |
| `Integration.md` | Integration guidelines. |

> ⚠️ `Python-api.md` is **obsolete** (old "panoptiscan" socket-based API). Do **not** rely
> on it for the current API — use the repo code instead.

## Safecor Python API (current) — from the repo

Location: `Saphir/python/lib/src/safecor/`

| File | Provides |
|---|---|
| `_api.py` | `Api` (singleton) — high-level API entry point. |
| `_topics.py` | `Topics` — MQTT topic names (system topics). |
| `_mqtt_factory.py` | `MqttFactory` — MQTT client factory. |
| `_components_helper.py` | `ComponentsHelper` — component discovery / state. |
| `_disk_monitor.py` | Disk monitoring. |
| `_sys_usb_controller.py` | USB controller. |
| `_dom0_controller.py` | Dom0 controller. |

## Rules

1. **Code over docs** — when the wiki and the repo code disagree, the **repo code wins**
   (it is the source of truth). Flag the discrepancy to the user and **log it in
   `safecor-divergences.md`**.
2. When an interaction with Safecor is ambiguous, cross-check `Protocol.md` + the repo code;
   if still unclear, ask the user.
3. Saphir's **custom** topics (`saphir/analysis/...`) are Saphir's own protocol — they are
   *not* part of the Safecor system topics and are owned by Saphir.
4. **Log every Safecor issue** — any divergence or anomaly noticed in Safecor (doc, code,
   behaviour, protocol, topology) must be **logged in `safecor-divergences.md`** so it can
   be handled in the Safecor project. Saphir works around it; it is not fixed here.

## Known gaps / to watch

- **Running list of divergences & anomalies**: see [`safecor-divergences.md`](safecor-divergences.md).
- Subtle platform behaviours that are **not** documented in the wiki or code
  (e.g. `restart_domain` edge cases, `disk_controller` behaviour on reset) —
  confirm with the user when encountered, then log them in the tracker.

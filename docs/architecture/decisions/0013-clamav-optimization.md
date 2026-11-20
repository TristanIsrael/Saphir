# 0013 — Keep ClamAV as-is (no major lever)

> **Status**: Accepted (2026-10-28)
> **Source**: tech-stack-analysis.md §8 — D-T4

## Context

ClamAV is allocated **3 000 MB** in `topology.json`. Safecor does **no memory ballooning**: each VM's memory is allocated up front at boot. ClamAV **reaches 3 000 MB during a scan** and **crashes below it** on certain files, so the allocation is **structural**, not waste.

## Decision

**Keep ClamAV as-is**: `clamd` resident, 3 000 MB, full signatures, `Bytecode true`. On-demand start/stop (b) **frees nothing** (the VM is allocated 3 000 MB from the start either way), and reducing signatures (c) is **off the table** (crash risk + detection loss). Follow-up: **measure** the real RAM to confirm 3 000 MB is the minimum and document it.

## Consequences

- There is **no major memory lever** on ClamAV.
- The 3 000 MB must be preserved to avoid crashes while scanning certain files.
- A measurement task remains to confirm the minimum.

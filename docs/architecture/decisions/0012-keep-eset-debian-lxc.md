# 0012 — Keep ESET in the Debian LXC

> **Status**: Accepted (2026-10-28)
> **Source**: tech-stack-analysis.md §8 — D-T3

## Context

ESET is **not available for Alpine** (not MUSL-linked). It therefore runs in a **minimal Debian LXC** inside an Alpine VM (2 100 MB allocated). The consensus rule requires two quality engines (`ANTIVIRUS_NEEDED = 2`). Replacing ESET with an Alpine/MUSL-compatible engine is the **biggest structural memory lever** (~2 100 MB + the LXC) — but **no quality AV engine exists in MUSL/Alpine** (all commercial engines are glibc; YARA is a pattern matcher, not a real AV engine).

## Decision

**Keep ESET in the Debian LXC** — detection quality takes priority over saving ~2 100 MB. Plan a **follow-up** (option c): measure ESET's real RAM (an OOM is documented in `docs/archive/legacy/analysis.md`, so 2 100 MB is not necessarily slack) and reduce the VM allocation if safe. Watch for a future MUSL-compatible quality engine.

## Consequences

- The LXC (squashfs) remains the only workable host for ESET.
- Consensus quality is preserved at the cost of ~2 100 MB + the LXC overhead.
- The follow-up measurement and the "MUSL-compatible engine" option stay open.

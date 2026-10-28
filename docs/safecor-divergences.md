# Safecor divergences & anomalies tracker

> **Purpose**: track divergences and anomalies noticed in **Safecor** while working on
> Saphir (analysis / refactoring). These entries are to be **handled in the Safecor
> project** (doc, code, or behaviour), *not* in Saphir.
>
> Saphir keeps working around them; this file is the bridge back to Safecor.
> Do **not** resolve them here — just log them with enough context to act on them in Safecor.

## Entry format

```
### [YYYY-MM-DD] <short title>
- **Type**: doc | code | behaviour | protocol | topology
- **Where**: <file / section / line>
- **Description**: <what is wrong or unexpected>
- **Saphir impact**: <how it affects Saphir, if any>
- **Status**: open | resolved
```

## Open

### [2026-10-28] Obsolete `Python-api.md` wiki page
- **Type**: doc
- **Where**: `Saphir.wiki/Python-api.md`
- **Description**: The page is explicitly marked *"Obsolete / Work in progress"* and
  describes the old "panoptiscan" socket-based API (sockets under
  `/var/run/panoptiscan/*-msg.sock`, `global.conf`), not the current MQTT-based
  `safecor` API.
- **Saphir impact**: none for the refactoring, provided the current API is read from the
  repo code (`Saphir/python/lib/src/safecor/`). Risk of misleading readers.
- **Status**: open — consider archiving the page or replacing it with a pointer to the
  current API.

## Resolved

_(none yet)_

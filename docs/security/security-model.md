# Saphir — Security Model

> **Status**: Stable
> **Last updated**: 2026-11-20
> **Audience**: developers working on the Saphir codebase (and integrators assessing the sheep-dip posture)
> **Scope**: the security design policy of Saphir — the threat model, the defense layers (VM isolation, multi-engine consensus, fingerprint integrity chain, copy-only-clean, stateless reset, read-only Viewer), the integrity gaps still open, and the Safecor platform baseline (offline reference copy of the platform hardening).

## Related documents

| Concern | Document |
|---------|----------|
| Product purpose & threat context (sheep-dip concept) | [`../../README.md`](../../README.md) (root) |
| NFRs (integrity, source integrity, engine minimum, dirty state, translatability) | [`../specifications/features.md`](../specifications/features.md) §2 |
| Invariants (I3 copy-only-clean, I7 consensus, I6 locking) | [`../specifications/workflow.md`](../specifications/workflow.md) §5 |
| Repository as the only data exchange point | [`../architecture/decisions/0003-repository-only-data-exchange.md`](../architecture/decisions/0003-repository-only-data-exchange.md) |
| Consensus = OR on "infected" | [`../architecture/decisions/0005-consensus-or-infected.md`](../architecture/decisions/0005-consensus-or-infected.md) |
| Stateless system, no persistence | [`../architecture/decisions/0006-stateless-system-no-persistence.md`](../architecture/decisions/0006-stateless-system-no-persistence.md) |
| Keep ESET in the Debian LXC (quality trade-off) | [`../architecture/decisions/0012-keep-eset-debian-lxc.md`](../architecture/decisions/0012-keep-eset-debian-lxc.md) |
| Stateless redesign on volatile encrypted disks (deferred) | [`../architecture/decisions/0014-stateless-volatile-encrypted-disks.md`](../architecture/decisions/0014-stateless-volatile-encrypted-disks.md) |
| Open integrity gaps & technical debt | [`../project-status.md`](../project-status.md) (Known issues & technical debt) |
| Safecor divergences log | [`../safecor-divergences.md`](../safecor-divergences.md) |

---

## 1. Threat model

**The threat**: untrusted external media. Data coming from outside the organization's network —
or having been transported outside the offices (internet downloads, personal USB drives, media
that left the premises) — is a **potential threat**. Files transferred between confidentiality
levels must be regulated and **processed through a secure workstation** before entering the
internal IT systems (see the root [`README.md`](../../README.md), "Typical threat management").

**The product is the control.** Saphir is a *sheep-dip*: the physical barrier between untrusted
media and the protected network. A file must pass through Saphir (scan → consensus → copy of
clean files only) before it is allowed to enter the network. The sheep-dip is "one of the
essential links in the security chain" — it reduces, but does not eliminate, the risk of
infection through external media.

**Assets & actors**:

| Asset | Protection goal |
|-------|-----------------|
| The internal network | No infected file enters it (consensus + copy-only-clean) |
| The copied files | The copy on the target is **bit-identical** to the source (NFR-1 fingerprint chain) |
| The source media | Never altered by the system (NFR-2 — read-only by design) |
| The appliance itself | No scanned content or state retained between cycles (ADR 0006); no permanent local storage to leak |

Actors: the **operator** (trusted, local, drives the workflow), the **external media**
(untrusted, the attack vector), and the **AV engines** (trusted components — but each one can
fail or miss a signature, hence the multi-engine vote).

---

## 2. Defense layers

### 2.1 Multi-domain VM isolation (Safecor)

The GUI, ClamAV, and ESET each run in a **separate Safecor VM**; the AV engines never touch the
external source/target disks directly. All files pass through the **shared `sys-usb`
repository** — the **only** data exchange point between the GUI and the AV domains
([`decisions/0003`](../architecture/decisions/0003-repository-only-data-exchange.md)). The AV
domains are stateless with respect to file content, are allocated read-only access
(`direct_mount: { "mode": "ro" }` in the topology, re-asserted read-only by the install
scripts), and communicate over MQTT only (platform "protocol break" — see §4).

The **ESET exception**: ESET is not available for Alpine (MUSL), so it runs in a minimal Debian
LXC inside its VM ([`decisions/0012`](../architecture/decisions/0012-keep-eset-debian-lxc.md)) —
detection quality takes priority over the ~2 100 MB saving; no quality MUSL-compatible engine
exists.

### 2.2 Multi-engine AV consensus

A file is **infected if *any* engine flags it; clean only when *all* engines agree**
([`decisions/0005`](../architecture/decisions/0005-consensus-or-infected.md), invariant
**I7**). A file whose analysis returned an **error** is *not clean* (not copyable) without
aborting the analysis. `ANTIVIRUS_NEEDED = 2` is a **readiness gate, not a voting threshold**:
analysis cannot start with fewer engines, and losing an engine below the minimum during analysis
declares the incomplete files `Error` and aborts or continues with the survivors
([`specifications/features.md`](../specifications/features.md) NFR-3, workflow scenario 8.9).

### 2.3 Fingerprint integrity chain (NFR-1)

Safecor computes a fingerprint on **every** file operation; Saphir compares them end-to-end so
that *the file copied onto the target is identical to the source file*:

| Step | Verification |
|------|--------------|
| Source → repository (staging) | fingerprint recorded in the queue (match with the original guaranteed by Safecor) |
| Repository → AV analysis | each AV domain re-verifies the repository file's fingerprint; mismatch ⇒ `Error` (`FileAnalysisError`) |
| Repository → target (copy) | the copied file's fingerprint is compared with the recorded one; mismatch ⇒ `FileCopyError`, not counted as copied |

A verification failure declares the file `Error`, the chain continues on the other files, and
the error is traced in the journal and the report. The single exchange point (ADR 0003) is what
makes the chain auditable. See NFR-1 in
[`../project-status.md`](../project-status.md) (Feature & NFR coverage) for the implementation
status (implemented, #145).

### 2.4 Copy only clean files (invariant I3)

Only files with `status == FileClean` are copied to the target (`TransferController`); the
transfer completes only when every clean file has been attempted, and a **final check**
(`copied == clean`) reports any discrepancy in the GUI and in the scan report (workflow scenario
8.10). There is **no copy cancellation** (exits: insert target / Reset / Shutdown —
[`decisions/0016`](../architecture/decisions/0016-no-copy-cancellation.md)).

### 2.5 Stateless reset between cycles (ADR 0006)

The system keeps **no persistence between cycles**: a Reset destroys the disposable domains and
returns to the initial state (invariant **I9** — idempotent); a crash or power loss is handled
the same way (reboot ⇒ Ready). The system is **dirty as soon as a file is read** (NFR-4):
connecting a *different* disk after a read **locks** the system (`SystemMustBeReset` — clean or
shut down only); reconnecting the *same* disk may continue. The RAM cost of in-RAM statelessness
is being addressed on the Safecor side —
[`decisions/0014`](../architecture/decisions/0014-stateless-volatile-encrypted-disks.md)
(volatile encrypted disks + ephemeral keys) is **Deferred** pending that work.

### 2.6 Source media integrity (NFR-2)

Saphir **never** creates or modifies files on the source media — by design it only issues
`read_file`. Safecor does *not* block writes on the source (no read-only mounting); the
responsibility lies with Saphir, and the current guarantee is the fingerprint-on-read (NFR-1).

### 2.7 Read-only Viewer

The Viewer is a separate **read-only** file/preview browser (images, video, audio, Office, PDF)
running in its own domain, swappable with the main GUI on the same screen (F15). It provides a
way to *inspect* files without the copy step, with no write path to any media.

---

## 3. Integrity gaps still open

The authoritative list of open issues is [`../project-status.md`](../project-status.md)
(Known issues & technical debt, and the gap tables in Feature & NFR coverage). The
security/integrity-relevant open items at the time of writing:

- **Reset does not interrupt the in-flight copy loop** (F10) — copy requests already issued run
  to the end of the queue after `reset()` clears the `TransferController` state.
- **No available-space check on the target** before copy (F4) — a copy can fail mid-flight
  (handled by the final check, but the failure mode is avoidable).
- **File selection is gated behind AV readiness** (divergence D7) — the spec allows selection as
  soon as the disk controller is ready; the implementation waits for the AV engines.
- **Dirty visual status under-reports** (divergence D8) — `infected: nbInfected > 1` in
  `Bindings.qml` (should be `> 0`): a single infected file does not flip the visual status to
  Dirty.
- **Classification level hardcoded to 0** (F8) — the Safecor classification backend is not
  wired; the "Restricted/Secret" levels are unreachable.
- **Report language fixed to EN** (divergence D3) — a NFR-5 gap, not a confidentiality gap.

These are **implementation gaps in an otherwise sound design**: none of the defense layers above
is structurally missing.

---

## 4. Platform baseline (Safecor hardening)

> **Offline reference copy** — Source: Safecor wiki `Security.md`. Synced: 2026-11-20. When Safecor changes, update here and log the divergence in `docs/safecor-divergences.md`.

### Security strategy

The security strategy relies on some key design concepts:

- **Isolation**: the components of the system are separated from each other. They belong to their
  own virtual machine and have no direct contact with the other components, so a threat cannot
  contaminate the whole system.
- **Protocol break**: the communication between the components uses a very simple data protocol
  with a very low attack surface. An attack from outside the system cannot propagate inside using
  TCP-IP or USB for example, as these protocols are confined in their respective components
  (`sys-usb`, `sys-net`, …) and the data flow uses another data protocol and channel.
- **Collaboration**: the components that don't need to manipulate files or external data don't
  have access to them. Instead, they collaborate with other components to get the information or
  data they need — reducing the risk of contaminating the core of the system.
- **Simplicity**: the architecture of the core is very simple, and this simplicity limits
  configuration or design weaknesses that could be exploited by threats (a major Safecor design
  rule).

### Hardening rules (services)

- Services are executed as a **normal user** (without privilege). The user `root` is never used
  for any service or application in the system.
- Each service is associated with its own user and belongs to the group `safecor`. Its
  configuration files and the files it creates are owned by its user; files it must access but
  does not own are accessible as long as they belong to the group `safecor`.
- A service is **not allowed** to list, read, or modify the configuration files of another
  service, nor any of the operating system's configuration files.
- These rules apply in Domain0, the Driver Domains and the User Domains. In the product's
  Domains, designers are **encouraged** to apply the same rules to avoid creating leaks.

### Package traceability

- Alpine Linux official repositories provide **cryptographically signed packages**; the signature
  is verified at installation, with the public key embedded in the system.
- Product packages are **signed by the product's maintainer**, who provides the public key for
  verification.
- When a Safecor-based system is provisioned, a **local repository** is created with all the
  packages needed for the Domains creation, signed with an **ephemeral key-pair** randomly
  generated during provisioning; the key-pair is unique and the **private key is removed** at the
  end of provisioning.
- The public key is embedded into each Domain's configuration virtual CDROM (via an APK overlay
  file, `apkovl`); **when the Domains boot they verify the signatures of all the packages** using
  the public key of the local repository.

### Local storage security

- The local storage is an image file **created during system boot and destroyed during
  shutdown**. It is ciphered before being mounted in Domain0 and shared with the other domains
  (including `sys-usb`); it is considered dangerous and a potential source of leaks, so it can
  never be reused.
- The ciphering relies on **cryptsetup (LUKS)** with a strong **ephemeral encryption key
  (AES-512 XTS) randomly generated at boot**. The image file is destroyed at shutdown — and, if
  it persists on the disk, on the next boot. Even if the image file were extracted from the
  system, it could not be deciphered because the ephemeral random key is lost as soon as the file
  is ciphered and is never written on disk.

> **Notes (faithfulness)**: the wiki's "Analysis of the data lifecycle" chapter is still marked
> *"To be completed"* on the Safecor side and is not copied here. The "to be completed" state of
> that chapter is itself worth logging in [`../safecor-divergences.md`](../safecor-divergences.md)
> if the data-lifecycle analysis becomes relevant to Saphir.

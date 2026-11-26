# Saphir — Topology

> **Status**: Stable
> **Last updated**: 2026-11-26
> **Audience**: developers and integrators working on the Saphir codebase or deployment
> **Scope**: the Saphir multi-domain topology — the domains and their roles, the per-domain hardware allocation (memory, vCPU, GUI flag, mounts), the product-level settings, the hardware-specific configuration, and how Safecor consumes the topology.

## Related documents

| Concern | Document |
|---------|----------|
| Deployment architecture & per-file data flow | [`../architecture/overview.md`](../architecture/overview.md) |
| Why the ESET engine runs in a LXC domain | [`../architecture/decisions/0012-keep-eset-debian-lxc.md`](../architecture/decisions/0012-keep-eset-debian-lxc.md) |
| GUI-domain design (Qt, network stripping) | [`../architecture/decisions/0011-gui-vm-qt-network-strip.md`](../architecture/decisions/0011-gui-vm-qt-network-strip.md) |
| Features affected by the topology (Viewer F15, system state F9) | [`features.md`](features.md) |
| Which APK is installed into each domain | [`../development/packaging.md`](../development/packaging.md) |
| MQTT contract exchanged between the domains | [`../development/protocol.md`](../development/protocol.md) |

The topology file is the **infrastructure-as-code** declaration of the Saphir system. It is packaged by the `saphir` APK and installed at `/etc/safecor/topology.json` on the appliance.

> **Offline reference copy** — the "How Safecor consumes the topology" and "Resource management" sections below are a reference copy of the platform concepts documented in the Safecor wiki `Topology.md`. Synced: 2026-11-20. When Safecor changes, update here and log the divergence in [`../safecor-divergences.md`](../safecor-divergences.md).

---

## 1. Source files

Two topology variants live in the `saphir` package source (`setup/packages/saphir/saphir/`):

| File | Packaged? | Domains declared |
|------|-----------|------------------|
| `topology.json` | **yes** (installed to `/etc/safecor/topology.json` by the `saphir` APKBUILD) | `saphir-gui`, `saphir-av-clamav`, `saphir-av-eset` |
| `topology.json.viewer` | no (variant kept in source, not referenced by any build) | adds `saphir-viewer` to the same set |

The two files are identical except for:

- `topology.json.viewer` **adds** the `saphir-viewer` domain.
- The AV domains and the `saphir-viewer` domain carry `direct_mount: { "mode": "ro" }` in both variants; `saphir-av-clamav` has `memory: 3000` in `topology.json` and `memory: 2400` in `topology.json.viewer`.
- In `topology.json.viewer` the Durabook configuration blacklists one PCI device (`"00:0d.0"`); in `topology.json` the blacklist is empty.

This document documents `topology.json` (the packaged file) as the reference and notes the viewer-variant differences inline.

---

## 2. Product-level settings

From `topology.json`:

| Section | Key | Value | Meaning |
|---------|-----|-------|---------|
| `product` | `name` | `Saphir` | The product name |
| `product` | `splash_bgcolor` | `#3a414d` | Background colour of the boot logo |
| `usb` | `use` | `1` | The `sys-usb` domain is set up and used (external storage handling is enabled) |
| `screen` | `enabled` | `1` | The system includes a GUI |
| `screen` | `default_focus` | `saphir-gui` | The graphical domain that has the focus (and receives inputs) on boot |
| `vcpu.groups` | `gui` | `0.2` | vCPU group for the GUI domains (see §6) |
| `vcpu.groups` | `antivirus` | `0.8` | vCPU group for the AV domains (see §6) |

The topology also supports `repository` (disable the 9p shared repository) and `storage` (local encrypted storage) sections; **Saphir sets `repository.disabled: true`** (see [`../architecture/decisions/0019-direct-usb-mount-data-path.md`](../architecture/decisions/0019-direct-usb-mount-data-path.md)) — the shared repository is no longer used.

---

## 3. Business domains

The `business.domains` array of `topology.json` declares three domains:

| Field | `saphir-gui` | `saphir-av-clamav` | `saphir-av-eset` |
|-------|--------------|--------------------|------------------|
| `name` | `saphir-gui` | `saphir-av-clamav` | `saphir-av-eset` |
| `app-package` | `saphir-gui` | `saphir-av-clamav` | `saphir-av-eset` |
| `memory` (MB) | `1200` | `3000` (viewer variant: `2400`) | `2100` |
| `has_gui` | `1` | — (absent) | — (absent) |
| `vcpu_group` | `gui` | `antivirus` | `antivirus` |
| `temp_disk_size` (MB) | `1024` | `4096` | `4096` |
| `swap_size` (MB) | — (absent) | `1024` | `1024` |
| `direct_mount` | — (absent) | `{ "mode": "ro" }` | `{ "mode": "ro" }` |

Field meanings (Safecor topology keys):

| Key | Meaning |
|-----|---------|
| `name` | The domain name |
| `app-package` | The Alpine package (APK) installed in the domain |
| `memory` | The memory, in MB, allocated to the domain |
| `has_gui` | The domain produces graphical content (the platform then enables the screen for it) |
| `vcpu_group` | The vCPU allocation group (a key of `vcpu.groups`) |
| `temp_disk_size` | A disk of this size (MB) is created and mounted in the domain on `/tmp` |
| `swap_size` | A swap disk of this size (MB) is created for the domain |
| `direct_mount` | The domain mounts `/media/usb` directly from `sys-usb` via vchan+sshfs; `mode` is `"ro"` (read-only) or `"rw"` (default) |

The **viewer variant** adds a fourth domain, identical in shape to `saphir-gui`
plus the read-only direct mount (like the AV domains):

| Field | `saphir-viewer` |
|-------|-----------------|
| `name` / `app-package` | `saphir-viewer` |
| `memory` (MB) | `1200` |
| `has_gui` | `1` |
| `vcpu_group` | `gui` |
| `temp_disk_size` (MB) | `1024` |
| `direct_mount` | `{ "mode": "ro" }` |

### 3.1 Domain roles

| Domain | Role |
|--------|------|
| `saphir-gui` | Main GUI: the analysis/copy workflow. Hosts the `ApplicationController` state machine, the analysis orchestration and the QML UI. The boot-focused GUI (`screen.default_focus`). |
| `saphir-av-clamav` | ClamAV antivirus engine. Runs the `ClamAntivirusController` (worker pool driving `clamdscan`). |
| `saphir-av-eset` | ESET Endpoint antivirus engine. Runs the `EeaAntivirusController` in a trimmed Debian LXC container. |
| `saphir-viewer` (viewer variant) | Read-only file/preview browser; swapped with the main GUI on the same screen via `Api().switch_gui(...)`. |

The AV domains' `direct_mount: { "mode": "ro" }` lets them see the external media read-only directly from `sys-usb` — this is the **sole** data path for analysis (the shared repository is disabled, see [ADR 0019](../architecture/decisions/0019-direct-usb-mount-data-path.md)).

---

## 4. Platform domains

The platform (Safecor core) creates and manages domains that are **not** declared in the Saphir business list:

| Domain | Type | Role |
|--------|------|------|
| `Dom0` | core | The trusted core (platform, hypervisor control). Not configurable in the topology. |
| `sys-usb` | core | The disk management domain: manages the external media, mounts them under `/media/usb`, and serves sshfs for the `direct_mount` domains. The shared repository (`__repository__`) is **disabled** (`repository.disabled: true`). Created automatically with `memory: 512`. |
| `sys-gui` | core | The platform's default graphical domain (default 20% of the allocatable vCPUs). In Saphir the business GUI domains take the GUI role; `sys-gui` is not declared by the product. |

These platform domains are disposable per the platform reset/cleaning mechanism (the reset destroys `sys-usb` and the business domains and recreates them — see [`../specifications/features.md`](features.md) F10).

---

## 5. Hardware configuration

The `configurations` array matches **specific hardware** by DMI identifier and applies device-specific settings. `topology.json` declares one configuration:

| Field | Value |
|-------|-------|
| `name` | `Durabook R8` |
| `identifier.sys_vendor` | `Durabook` |
| `identifier.product_name` | `R8AA` |
| `settings.screen.rotation` | `90` (the tablet is used in landscape/rotated orientation) |
| `settings.pci.blacklist` | `[]` (empty; the viewer variant uses `["00:0d.0"]`) |

When the platform boots on a machine whose DMI vendor/product name matches the `identifier`, the matching `settings` are applied on top of the base topology.

---

## 6. Resource management (vCPU allocation)

Resources (CPU, memory) are affected to domains as portions of the platform resources.

**Memory** is declared per domain (`memory`, in MB, §3) — Saphir allocates `1200` MB to the GUI domain(s), `3000`/`2400` MB to the ClamAV domain, `2100` MB to the ESET domain, plus per-domain `temp_disk_size` (a `/tmp` disk) and `swap_size` (a swap disk) where declared.

**vCPU** follows these platform rules:

- `Dom0` and `sys-usb` **cannot** be configured: Dom0 takes the 2 first vCPUs (1 if the system has fewer than 4); `sys-usb` shares the same vCPUs as Dom0.
- The remaining CPUs are the **allocatable pool** (`platform_cpus - reserved`).
- Allocatable pool = 15% to Dom0/sys-usb (shared, minimum 1) and **75% to the rest**, divided into the groups declared in `vcpu.groups` (the group values express 100% of that allocatable pool).
- Each business domain takes its group via `vcpu_group`; its vCPU count is `round(group_rate × allocatable_pool)` (at least 1).

With Saphir's groups (`gui: 0.2`, `antivirus: 0.8`) on a 12-core machine (allocatable pool = 10):

| Domain | Group | vCPUs |
|--------|-------|-------|
| `saphir-gui` | `gui` (0.2) | `round(0.2 × 10)` = **2** |
| `saphir-av-clamav` | `antivirus` (0.8) | `round(0.8 × 10)` = **8** |
| `saphir-av-eset` | `antivirus` (0.8) | `round(0.8 × 10)` = **8** |
| `saphir-viewer` (viewer variant) | `gui` (0.2) | **2** |

CPUs are then **pinned** to the group: the first cores go to Dom0/sys-usb, the next ones to `sys-gui`, then the remaining cores are distributed to the declared groups trying to avoid overlap.

> The numbers above are an **illustrative example** for a 12-core machine. The actual vCPU count depends on the hardware (`platform_cpus`).

---

## 7. How Safecor consumes the topology

The platform reads `/etc/safecor/topology.json` at boot (Dom0) and builds the system from it:

1. **Parse** — the JSON is read and decoded into a topology data structure (`System.get_topology_struct()` → `__analyse_topology_struct()`). The parser maps the product-level sections and the `business.domains` entries; the `sys-usb` core domain is added automatically (`memory: 512`, type `core`).
2. **Match the configuration** — the DMI identifier of the running machine is matched against `configurations[].identifier`; the matching `settings` (screen rotation, PCI blacklist) are applied.
3. **Create the domains** — for every business domain, the platform creates a VM, allocates its `memory`, pins its vCPUs per its `vcpu_group`, creates the `temp_disk_size` `/tmp` disk and the `swap_size` swap disk, and installs the `app-package` APK.
4. **Enable the screen** — because `screen.enabled: 1`, the platform sets up the display; the domain with `has_gui: 1` produces graphical content, and `screen.default_focus` (`saphir-gui`) receives the inputs on boot.
5. **Enable USB** — because `usb.use: 1`, the `sys-usb` domain is started and manages the external media; the shared repository (`__repository__`) is **disabled** (`repository.disabled: true` in the topology).
6. **Enable direct mounts** — domains with `direct_mount` mount `/media/usb` directly from `sys-usb` via vchan+sshfs in the declared `mode` (`ro` for Saphir's AV domains). This is the **sole** read path for analysis and viewer.
7. **Boot the product** — the `product` section provides the name and the `splash_bgcolor` for the boot logo.

The result: a multi-VM system in which the product domains (GUI, AV engines, and optionally the Viewer) run in isolation. The AV domains and Viewer access external media via direct USB mount (`direct_mount: { "mode": "ro" }`); the GUI communicates with `sys-usb` exclusively via the Safecor file API. Data exchange happens through MQTT topics (see [`../development/protocol.md`](../development/protocol.md)).

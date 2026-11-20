# Saphir — Configuration Management

> **Status**: Stable
> **Last updated**: 2026-11-20
> **Audience**: developers (human and AI agents) maintaining the Saphir packages, topology, or build environment
> **Scope**: what is configured where in Saphir (topology / VM allocation, per-hardware settings, boot services, the repository path at runtime, languages, dev mode) and how it flows from the APK packages to the running domains — plus an offline reference copy of the Safecor platform configuration-management concepts.

## Related documents

| Concern | Document |
|---------|----------|
| Topology fields, domain inventory & viewer variant (detail) | [`../specifications/topology.md`](../specifications/topology.md) |
| MQTT contract (`system/disks/repository_path`, `system/settings/languages/default`, …) | [`../development/protocol.md`](../development/protocol.md) |
| Package contents, APKBUILDs & build flow | [`../development/packaging.md`](../development/packaging.md) |
| Build paths (local dev Docker image, CI, chroot) | [`../development/building.md`](../development/building.md) |
| DevMode & Safecor emulator (test simulation) | [`../development/testing.md`](../development/testing.md) |
| Repository as the only data exchange point | [`decisions/0003-repository-only-data-exchange.md`](decisions/0003-repository-only-data-exchange.md) |
| Stateless system (no persistence of configuration/state) | [`decisions/0006-stateless-system-no-persistence.md`](decisions/0006-stateless-system-no-persistence.md) |
| Safecor divergences log | [`../safecor-divergences.md`](../safecor-divergences.md) |

---

## 1. Where configuration lives

| Configured | Where it is set | Mechanism |
|-----------|-----------------|-----------|
| Multi-VM topology (domains, memory, vCPU groups, GUI flag, temp disk, swap, read-only mounts) | `/etc/safecor/topology.json` on the appliance | `topology.json` packaged by the `saphir` APK (§2) |
| Product identity, splash screen | `product` section of the topology; `splash.png` → `/boot/splash.png` | same `saphir` APK (§2) |
| Hardware-specific settings (screen rotation, PCI blacklist) | `configurations` array of the topology, matched by DMI at boot | Safecor configuration management (§3) |
| Boot services (per domain) | `/etc/init.d/*` + `rc-update` | package install scripts (`*.initd`, `*.post-install`) (§4) |
| ClamAV engine tuning | `clamd.conf`, `freshclam.conf` | packaged by `saphir-av-clamav` (APKBUILD) |
| ESET LXC container (rootfs, config) | `/var/lib/saphir/saphir-container-eset.sqfs` + `/var/lib/lxc/saphir-container-eset/config` | `saphir-container-eset` APK, patched at install time (§4) |
| Repository mount path (runtime) | — (no static setting) | `system/disks/repository_path` request to the platform (§5.1) |
| Default language | platform setting | `system/settings/languages/default`; user switch at runtime, no persistence (§5.2) |
| Dev mode (no appliance) | `DEVMODE` environment variable; `.env` (PYTHONPATH) | dev environment (§5.3, §6) |

There is **no runtime configuration file written by the product**: everything is either baked in
at packaging time (topology, initd scripts, engine configs) or resolved at runtime from the
platform (repository path, default language). This is a direct consequence of the stateless
design ([`decisions/0006`](decisions/0006-stateless-system-no-persistence.md)) — the system keeps
no configuration state between cycles.

---

## 2. Topology & VM allocation

The **single source of truth** for the VM layout is `setup/packages/saphir/saphir/topology.json`,
installed by the `saphir` APKBUILD to `/etc/safecor/topology.json` (the package also ships
`splash.png` → `/boot/splash.png` and declares `product.name = "Saphir"`).

What it declares (see [`../specifications/topology.md`](../specifications/topology.md) for the
field semantics — this document does not duplicate them):

- **Product & platform switches**: `usb.use = 1`, `screen.enabled = 1` with
  `default_focus: "saphir-gui"`, `splash_bgcolor`.
- **vCPU groups**: `gui: 0.2`, `antivirus: 0.8`.
- **Business domains**:
  - `saphir-gui` — 1 200 MB, `has_gui: 1`, vCPU group `gui`, `temp_disk_size: 1024`.
  - `saphir-av-clamav` — 3 000 MB, vCPU group `antivirus`, `temp_disk_size: 4096`,
    `swap_size: 1024`, `direct_mount: { "mode": "ro" }`.
  - `saphir-av-eset` — 2 100 MB, vCPU group `antivirus`, `temp_disk_size: 4096`,
    `swap_size: 1024`, `direct_mount: { "mode": "ro" }`.
- **One hardware-specific configuration** (`Durabook R8`, DMI-matched): screen rotation 90.

Two additional facts about the topology file:

- A second variant, `topology.json.viewer`, is kept in the package source (it adds the
  `saphir-viewer` domain and has slightly different AV sizing); it is **not** installed by any
  build — `topology.json` is the reference.
- The topology format also supports `repository` and `storage` sections; **Saphir sets neither**
  — the shared `sys-usb` repository is enabled by default (the repository is the only data
  exchange point, [`decisions/0003`](decisions/0003-repository-only-data-exchange.md)).

---

## 3. Safecor platform configuration management

> **Offline reference copy** — Source: Safecor wiki `Configuration-management.md`. Synced: 2026-11-20. When Safecor changes, update here and log the divergence in `docs/safecor-divergences.md`.

A configuration is a set of parameters and behaviours that can be applied to a specific hardware.

In a fleet of heterogeneous devices, for example tablets and various computers, there will be
different sizes of displays, tablets will have a rotated (landscape) display with touchscreen
while computers will have a regular (landscape) display. But you might want to rotate the screen
differently to have a portrait orientation. Some hardware will need to be disabled for security
or operational reasons, particularly PCI devices or buses.

For all these reasons Safecor provides a configuration management system that helps you define
settings specific to a device family or type.

### Settings hierarchy

Some of the settings can be defined on the kernel's command line (for an ISO image or network
boot) or only in the topology. The hierarchy rule defines which setting is kept over the others:

> *When a setting is defined in the topology **and** on the command line, the **command line**
> value is kept.*

### Device management

The device is identified with the help of the DMI (Desktop Management Interface) API.
Safecor reads and analyzes the DMI information provided by the firmware of the device, and this
information can be used to match a configuration.

### Defining a configuration

A configuration is defined in the topology. A specific section can be added in a regular
topology file:

```json
"configurations": [
    {
        "name": "Durabook R8",
        "identifier": {
            "sys_vendor": "Durabook",
            "product_name": "R8AA"
        },
        "settings": {
            "gui": {
                "screen": {
                    "rotation": 90
                }
            },
            "pci": {
                "blacklist": "00:0d.0"
            }
        }
    }
]
```

The field `configurations` is an array and can be used to define as many configurations as
needed.

### Identify a product or a unit

All the files located in `/sys/class/dmi/id/` on the device can be used to identify it. The
device can be identified with the help of the following DMI fields:

| Field | Description |
|--|--|
| `product_name` | This is often the model of the device |
| `product_serial` | This is the serial number of the device which identifies the type of device |
| `product_sku` | This is a SKU that identifies a product, it can be empty |
| `product_uuid` | This field should identify a specific unit and can be used to target one unit specifically |
| `sys_vendor` | This field identifies the manufacturer of the device |

There may be more or less fields in the directory `/sys/class/dmi/id/` but you should be able to
find a combination that will match a product or a specific unit in your fleet.

The field `identifier` in the configuration is the place where the device or unit must be
identified using the name of a file located in `/sys/class/dmi/id/` as the key and the text it
contains as the value.

### Default configuration

If the device running Safecor matches none of the configurations, the default configuration is
applied. The default configuration corresponds to all the settings outside of the section
`configurations` in the topology.

> **Saphir instance**: the packaged `topology.json` declares exactly one configuration
> (`Durabook R8` — `sys_vendor: Durabook`, `product_name: R8AA` → screen rotation 90); every
> other device falls back to the default (settings outside `configurations`).

---

## 4. Boot services & install scripts

Each Saphir package ships OpenRC initd scripts (`/etc/init.d/*`) and install hooks. The APKBUILDs
install the files; the `*.post-install` scripts register and start the services in the domain.

| Package | Initd scripts | Post-install actions |
|---------|---------------|----------------------|
| `saphir` | `saphir.initd` | `hostname saphir.local`; run `/usr/lib/safecor/bin/post-install.sh` |
| `saphir-gui` | `gui-bundle.initd` (PyInstaller binary) / `gui-folder.initd` (dev variant via `start.sh`) | `rc-update add gui` + start |
| `saphir-viewer` | `viewer.initd` | `rc-update add viewer` + start |
| `saphir-av-clamav` | `clamav.initd` (starts `clamd`, `before av-controller`), `av-controller.initd` (starts the Python controller) | add `clamav` user to group `safecor`; create `/var/log/clamav` + `/run/clamav` (owned `clamav`); `rc-update add` + start both services; **remount the shared storage read-only** (9p, `nosuid,noexec,nodev`) |
| `saphir-av-eset` | `av-controller.initd` | start `cgroups`; `rc-update add av-controller` + start; patch the LXC config (bind-mount `/tmp` → `tmp` and `var/tmp`, `noexec,nodev,nosuid`); `lxc-start -n saphir-container-eset`; sysctl tuning (`vm.vfs_cache_pressure=200`, `vm.compaction_proactiveness=100`, `vm.min_free_kbytes=102400`) |
| `saphir-container-eset` | — | mount the squashfs rootfs read-only (`loop,ro`) + overlay (upper/work) under `/mnt/merged`; remount the shared storage read-only (no-op on CI where mounting is unavailable); pre-deinstall removes `/var/lib/lxc/saphir-container-eset` |

Key points:

- **`saphir.initd`** (Dom0) only starts the Safecor **orchestrator** (`rc-service orchestrator
  start`) — the orchestrator reads `/etc/safecor/topology.json` and builds the domains.
- **GUI/Viewer services** run under `DISPLAY=:0` and declare `need xserver`; the post-install
  scripts also create `/var/log/saphir`.
- **`saphir.post-deinstall`** removes `/var/log/safecor` (no log retention — stateless).
- The **ClamAV domain remounts the repository read-only** in its post-install — a belt-and-braces
  enforcement on top of the `direct_mount: { "mode": "ro" }` topology flag (NFR-2 territory: the
  source media is never written by Saphir — see
  [`../security/security-model.md`](../security/security-model.md)).

---

## 5. Runtime configuration

### 5.1 Repository path

The mount path of the shared `sys-usb` repository is **not configured by Saphir** — it is
*queried* from the platform with `system/disks/repository_path`
(`request_repository_path()`), which responds `{ "path": "/mnt/storage" }`. It is consumed by:

- the **GUI**: a boot-readiness condition;
- the **AV domains**: a readiness condition **and** the base path for the NFR-1 fingerprint check.

See [`../development/protocol.md`](../development/protocol.md) for the request/response contract.

### 5.2 Language

- The **platform default language** is obtained from the platform setting
  `system/settings/languages/default` (`get_default_language()`).
- The **user** can switch EN/FR at any time from the GUI (`btnLanguageEN`/`btnLanguageFR`); the
  switch is immediate (`__install_translations` + `engine.retranslate`).
- **Nothing is persisted** (stateless — [`decisions/0006`](decisions/0006-stateless-system-no-persistence.md)).
- Known gap: the PDF scan report does not follow the language (always EN — divergence D3, see
  [`../project-status.md`](../project-status.md) — Feature & NFR coverage).

### 5.3 Dev mode (`DEVMODE`)

- Enabled by the **environment variable** `DEVMODE` (any non-empty value) — read once by
  `libsaphir` (`_constants.py`) and propagated to QML as a context property.
- In DEVMODE the app runs **without a Safecor appliance** (mock MQTT / Safecor emulator,
  simulated disks) and auto-starts a full-disk analysis when the source disk connects
  (auto-pilot for testing). Fullscreen can only be disabled in DevMode (F20).
- The repository-root **`.env`** sets `PYTHONPATH` for local development (GUI + `libsaphir`
  sources and a **sibling `Safecor` checkout** — `../Safecor/python/lib/src`).
- See [`../development/testing.md`](../development/testing.md) §3.1 (DevMode) for the test-side
  usage.

---

## 6. Development environment (`setup/docker/local-dev/`)

The local build/dev environment is a **Docker image** (`saphir-dev`) plus wrapper scripts.
[`../development/building.md`](../development/building.md) §2 documents the build usage; this
section records what is configured there:

| Item | What it configures |
|------|--------------------|
| `Dockerfile` (base `alpine:3.24`) | abuild toolchain; the official Safecor + Saphir APK repositories with their **public signing keys** (`/etc/apk/keys/`); a `builder` user in the `abuild` group; the Saphir **public** abuild key in `~/.abuild` — the **private** key is mounted read-only at run time |
| `docker-cmd.sh` | container wiring: private abuild key → `/home/builder/.abuild/saphir.rsa`, Saphir source tree → `/home/builder/src/saphir`, abuild cache → `/var/cache/distfiles`, output repository → `/home/builder/packages/saphir`; x86_64 emulation when the host is not amd64 |
| Env vars consumed by `docker-cmd.sh` | `SAPHIR_SOURCE_PATH`, `LOCAL_CACHE`, `OUTPUT_REPOSITORY`, `PRIVATE_KEY`, `OVERRIDE_REPOSITORIES` (when set: bind-mounts the local `repositories` and `pip.conf` files) |
| `repositories` / `pip.conf` | alternate (edge) Alpine repositories + a devpi PyPI mirror, used when `OVERRIDE_REPOSITORIES` is set |
| `create-dev-image.sh` | builds the `saphir-dev` image (`docker build --platform linux/amd64`) |
| `update-all-checksums.sh` | runs `abuild checksum` for all seven package directories |

**Flow**: sources in the host checkout → abuild inside the container (signed with the mounted
private key) → APKs in the local output repository → (optionally) published to the signed Saphir
repository and installed into the domains built from the topology. The dev *runtime* environment
for the GUI itself (no appliance) is DEVMODE + emulator — §5.3 and
[`../development/testing.md`](../development/testing.md).

# Saphir — Packaging

> **Status**: Stable
> **Last updated**: 2026-11-20
> **Audience**: developers (human and AI agents) maintaining the Saphir Alpine packages or consuming them from the signed repository
> **Scope**: the Saphir Alpine package inventory (contents, target domains, versions), the wheel→PyInstaller→APK build flow, versioning & coherence, and the signed-repository publish flow (including the Safecor platform packages Saphir depends on).

## Related documents

| Concern | Document |
|---------|----------|
| Build paths (Docker, chroot, CI, ISO) | [`building.md`](building.md) |
| Which domain runs which package (topology) | [`../specifications/topology.md`](../specifications/topology.md) |
| Deployment architecture | [`../architecture/overview.md`](../architecture/overview.md) |
| Why ESET runs in a Debian LXC container | [`../architecture/decisions/0012-keep-eset-debian-lxc.md`](../architecture/decisions/0012-keep-eset-debian-lxc.md) |

---

## 1. Package inventory

The eight Saphir packages live in `setup/packages/saphir/<pkg>/APKBUILD` and are installed into the Safecor domains declared by the [`topology`](../specifications/topology.md).

| Package | Version | Arch | Target domain / role | Key contents |
|---------|---------|------|----------------------|--------------|
| `saphir` | 4.0-r0 | noarch | Platform (Dom0) — the product definition | `topology.json` → `/etc/safecor/topology.json`, `splash.png` → `/boot/splash.png`; depends on `safecor-core safecor-lib` |
| `saphir-lib` | 2.0-r0 | noarch | Shared by the AV & GUI domains | The Python library `libsaphir` (wheel installed with `python3 -m installer`); depends on `safecor-lib` |
| `saphir-gui` | 4.0-r0 | x86_64 | `saphir-gui` | PyInstaller bundle → `/usr/lib/saphir/saphir-gui` + `/etc/init.d/gui`; depends on `safecor-lib saphir-lib safecor-domu-base safecor-gui-base fontconfig freetype weasyprint` |
| `saphir-viewer` | 1.2-r0 | x86_64 | `saphir-viewer` | PyInstaller bundle → `/usr/lib/saphir/saphir-viewer` + `/etc/init.d/viewer`; depends on `safecor-lib safecor-domu-base safecor-gui-base fontconfig freetype libreoffice` |
| `saphir-splash` | 1.0-r1 | noarch | Boot splash | `splash.png` → `/boot/splash.png` |
| `saphir-av-clamav` | 1.0-r1 | noarch | `saphir-av-clamav` | `av-controller.py` + `/etc/init.d/av-controller`, ClamAV signatures (`main.cvd`, `bytecode.cvd`, `daily.cvd`), `clamd.conf` / `freshclam.conf` + `clamav` initd; depends on `safecor-lib safecor-domu-base saphir-lib clamav` |
| `saphir-av-eset` | 1.0-r1 | noarch | `saphir-av-eset` | `av-controller.py` + ESET wrapper scripts (`scan-file.sh`, `get-scan-result.sh`, `get-eea-version.sh`, `get-eea-description.sh`, `get-eea-licence.sh`, `stop-all-scans.sh`) + `/etc/init.d/av-controller`; depends on `saphir-container-eset saphir-lib safecor-lib safecor-domu-base` |
| `saphir-container-eset` | 2.1-r0 | x86_64 | Consumed by `saphir-av-eset` | LXC container: `config` → `/var/lib/lxc/saphir-container-eset/config`, `saphir-container-eset.sqfs` → `/var/lib/saphir/`; depends on `sudo lxc` |

> **`saphir-container-eset` is not built in CI** (the container archive cannot be built on GitHub — it needs host privileges and a live ESET binary download) and is excluded from `chroot-build.sh` `build all`. `saphir-av-eset` resolves it from the official Saphir repository.

> **Viewer version divergence**: `saphir-viewer` is at `1.2-r0` while the Viewer Python component is at `1.0.0` (see §3). This is a pre-existing divergence.

---

## 2. Build flow (source → APK)

All packages are built with **abuild** from the APKBUILDs in `setup/packages/saphir/`. The two non-trivial flows:

### 2.1 `saphir-lib` — wheel flow

1. `python/libsaphir` is built into a wheel (hatchling).
2. `package()` installs it with `python3 -m installer --destdir=$pkgdir libsaphir-<pkgver>.<pkgrel>-py3-none-any.whl`.

### 2.2 `saphir-gui` / `saphir-viewer` — PyInstaller bundle flow

1. `prepare()` copies `python/gui` (or `python/viewer`) from the repository tree into the build directory (`py_src_dir="../../../../../python"`), and installs PyInstaller from pip (no Alpine package exists for it).
2. `build()` compiles the French translation with `lrelease` (`fr.ts` → `fr.qm`), then runs `python3 -m PyInstaller saphir-gui.spec --noconfirm` (resp. the viewer spec).
3. `package()` copies the `dist/` bundle to `/usr/lib/saphir/` and installs the initd script.

Each of these APKBUILDs has a `bundle` flag: with `bundle="yes"` the package contains the PyInstaller bundle (`gui-bundle.initd`); with `bundle="no"` the package carries the Python source folder instead (`gui-folder.initd`).

### 2.3 Everything else

- `saphir` installs the `topology.json` (the packaged variant — not `topology.json.viewer`) and the boot splash.
- The AV packages install the `av-controller.py` entry point (which subclasses the `libsaphir` antivirus controllers), the ClamAV signatures/configs, or the ESET wrapper scripts.
- `saphir-container-eset` installs the Debian LXC container (`.sqfs`) and its LXC config.

---

## 3. Versioning & coherence

The versioning rules (`MAJOR.MINOR.PATCH`, patch = bug fix, minor = new feature, major = maintainer only) and the dependency-placement rules are defined in [`building.md` §6](building.md#6-versioning-and-coherence).

The package-side consequences:

- The Python `pkgver` must always match the Python component version (hatch dynamic version from `__init__.py`):

| Component | Python version | Alpine `pkgver` | Coherent? |
|-----------|----------------|-----------------|-----------|
| `libsaphir` | `2.0` | `saphir-lib` `2.0` | ✅ |
| Saphir GUI | `4.0.0` | `saphir` `4.0`, `saphir-gui` `4.0` | ✅ |
| Viewer | `1.0.0` | `saphir-viewer` `1.2` | ⚠️ **pre-existing divergence** — the APKBUILD is ahead of the Python component; align the two before the next release |

- The Alpine `pkgver` drops the patch digit (`4.0.0` → `4.0`); use `pkgrel` increments for rebuilds of the same `pkgver` (e.g. `saphir-splash` `1.0-r1`).
- When a component version changes, bump the matching APKBUILD `pkgver` in the same change so all versions stay coherent.

---

## 4. Signed repository & publish

### 4.1 Repository layout

| Repository | URL | Contents |
|------------|-----|----------|
| Stable | `https://alefbet.net/github/saphir` | `x86_64/*.apk` + signed `APKINDEX.tar.gz` |
| Edge | `https://alefbet.net/github/saphir/edge` | same layout for non-`main` branches |

- APKs are signed with the **Saphir** abuild key (`saphir.rsa`); the `APKINDEX.tar.gz` is rebuilt and **signed** (`abuild-sign`) on every publish.
- The publish step of the CI (see [`building.md` §4](building.md#4-ci-pipeline-github-actions)) rsyncs the APK over SSH (`ssh -p 222` to `github-saphir@alefbet.net`) into `/var/www/www.alefbet.net/github/saphir[/edge]/x86_64/`, then regenerates and signs the index on the server.
- Consumers (appliance domains, chroot, local Docker dev) register the repository in `/etc/apk/repositories` and fetch `saphir.rsa.pub` into `/etc/apk/keys`.

### 4.2 Safecor platform packages (offline reference copy)

> **Offline reference copy** — Source: Safecor wiki `Packages.md`. Synced: 2026-11-20. When Safecor changes, update here and log the divergence in [`../safecor-divergences.md`](../safecor-divergences.md).

Saphir packages depend on the following packages of the **Safecor** official repository (`https://alefbet.net/github/safecor`, edge at `.../edge`):

| Safecor package | Description (Safecor wiki) | Used by |
|-----------------|----------------------------|---------|
| `safecor-core` | The core of the Safecor system | `saphir` |
| `safecor-lib` | The Safecor python library for Domains | `saphir-lib`, `saphir-gui`, `saphir-viewer`, `saphir-av-clamav`, `saphir-av-eset` |
| `safecor-domu-base` | A basic package for business Domains; prepares the Domain integration in the system | `saphir-gui`, `saphir-viewer`, `saphir-av-clamav`, `saphir-av-eset` |
| `safecor-gui-base` | A basic package for any GUI Domain in Safecor | `saphir-gui`, `saphir-viewer` |
| `safecor-container-debian` | An LXC container with a minimal Debian, only for use in DomUs | `saphir-container-eset` (makedepends) |

CI always resolves Safecor dependencies from the **edge** repository (`https://www.alefbet.net/github/safecor/edge`), regardless of the Saphir branch being built.

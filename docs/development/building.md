# Saphir — Building

> **Status**: Stable
> **Last updated**: 2026-11-20
> **Audience**: developers (human and AI agents) building Saphir locally, in CI, or as a bootable ISO
> **Scope**: the build paths of Saphir — the local dev environment (Docker), the chroot validation build, the GitHub Actions CI pipeline, the bootable ISO build, and the versioning/coherence rules that bind them together.

## Related documents

| Concern | Document |
|---------|----------|
| Package inventory & publish flow | [`packaging.md`](packaging.md) |
| Coding & linting standards, dependency placement | [`coding-rules.md`](coding-rules.md) |
| Which package lands in which Safecor domain | [`../specifications/topology.md`](../specifications/topology.md) |
| Deployment architecture | [`../architecture/overview.md`](../architecture/overview.md) |

---

## 1. Build paths overview

| Path | Purpose | Tooling | Where it runs |
|------|---------|---------|---------------|
| **Local dev** | Iterate on packages with the official signing key | Docker image `saphir-dev` (Alpine + abuild) | Developer workstation |
| **Chroot validation** | Validate the whole APK set + boot the GUI bundle without a Safecor appliance | `setup/chroot/chroot-build.sh` (minirootfs chroot) | Developer workstation |
| **CI** | Build & publish the official APKs to the signed repository | GitHub Actions, `alpine:3.24` containers, abuild | GitHub runners |
| **ISO** | Produce the bootable Saphir ISO | `mkimg` profile + apkovl script | Safecor ISO toolchain |

All four paths build from the same sources: the `python/` tree and the `setup/packages/saphir/` APKBUILDs.

---

## 2. Local dev environment (Docker)

Located in `setup/docker/local-dev/`.

### 2.1 Creating the image

```bash
cd setup/docker/local-dev
bash create-dev-image.sh
```

The `Dockerfile` (base `alpine:3.24`) installs the abuild toolchain, registers the official Alefbet repositories (Safecor + Saphir, with their signing keys), creates a `builder` user in the `abuild` group, and drops in the Saphir **public** abuild key. The **private** key is not baked into the image — it is mounted at run time.

### 2.2 Running builds

`docker-cmd.sh` starts the container with:

- the Saphir abuild **private key** bind-mounted read-only to `/home/builder/.abuild/saphir.rsa`
- the Saphir source tree bind-mounted to `/home/builder/src/saphir`
- a local abuild cache on `/var/cache/distfiles`
- the output repository (built APKs) on `/home/builder/packages/saphir`

Configurable via environment variables (the script ships with macOS defaults):

| Variable | Meaning |
|----------|---------|
| `SAPHIR_SOURCE_PATH` | Host path of the Saphir repository |
| `LOCAL_CACHE` | Host path of the abuild distfiles cache |
| `OUTPUT_REPOSITORY` | Host path where built APKs land |
| `OVERRIDE_REPOSITORIES` | When set, bind-mounts a custom `/etc/apk/repositories` and pip config from the script directory |

If the host is not x86_64, the container is started with `--platform linux/amd64` emulation.

Inside the container, build as `builder` with abuild (e.g. `abuild checksum && abuild -r -f` in `setup/packages/saphir/<pkg>`).

---

## 3. Chroot validation build

`setup/chroot/chroot-build.sh` validates the Saphir packages in an Alpine chroot **without a K8s cluster or a Safecor appliance** (refactoring plan, Phase 8).

### 3.1 Commands

| Command | Effect |
|---------|--------|
| `init` | Create the chroot from the official minirootfs (idempotent): configure the Alefbet repositories (Safecor + Saphir), fetch the repository signing keys, install the build toolchain, create a `builder` user, generate a **local** abuild signing key (`localval`) |
| `sync` | Copy `python/` + `setup/` from the repository into the chroot at `/work/Saphir` |
| `build [PKG...]` | Build the given packages with abuild (default: `saphir-lib saphir-gui`); `build all` builds every buildable package in dependency order |
| `install [PKG...]` | Install the built APKs into the chroot (default: `saphir-lib saphir-gui` — the GUI domain) |
| `test-gui` | Boot the `saphir-gui` PyInstaller bundle in DEVMODE (offscreen) against a local mosquitto broker and verify the boot marker |
| `validate` | `sync` + `build` + `install` + `test-gui` |
| `list` | List the built packages |
| `destroy` | Remove the chroot and the cached minirootfs |

### 3.2 Environment overrides (all optional)

| Variable | Default |
|----------|---------|
| `CHROOT_DIR` | `/tmp/opencode/alpine` |
| `ALPINE_VERSION` | `3.21` |
| `ALPINE_RELEASE` | `3.21.9` |
| `CACHE_DIR` | parent of `CHROOT_DIR` |

### 3.3 Notes

- `init` requires sudo on the host and network access; `build` requires network inside the chroot (apk + pip).
- The local signing key (`localval`) is for validation only — the official CI signs with the Saphir key.
- **Build before install**: `install` adds runtime dependencies to the chroot world (e.g. `xe-guest-utilities` via `safecor-gui-base`), which conflicts with `xen` (pulled in by `safecor-core` when building the `saphir` package). abuild uninstalls its build dependencies after each build, so the world stays clean as long as all builds happen before the install step.
- The `test-gui` step boots `/usr/lib/saphir/saphir-gui` with `DEVMODE=1 QT_QPA_PLATFORM=offscreen`, starts a local mosquitto broker on port 1883 if needed, and polls the API log (`/tmp/saphir.log`) for the boot marker **`Saphir is ready`** (up to 30 s). It fails if the marker is not found.
- `build all` covers every buildable package in dependency order: `saphir-splash saphir-lib saphir saphir-gui saphir-viewer saphir-av-clamav saphir-av-eset`. **`saphir-container-eset` is excluded**: it fetches an ESET binary from a URL that currently 404s and needs host privileges, and the official CI skips it as well. `saphir-av-eset` resolves its `saphir-container-eset` dependency from the official Saphir repository.
- Not every `saphir-*` package can be installed in one world (see the build-before-install note), so install them **per domain**, e.g. `./chroot-build.sh install saphir saphir-splash`.

---

## 4. CI pipeline (GitHub Actions)

`.github/workflows/build-all.yml` builds and publishes the official APKs.

### 4.1 Triggers

- **Push** to any branch, when `setup/packages/saphir/**` or `python/**` changes.
- **Manual** (`workflow_dispatch`) with force flags: `force-all`, or one per package (`force-saphir-main`, `force-saphir-av-clamav`, `force-saphir-av-eset`, `force-saphir-gui`, `force-saphir-lib`, `force-saphir-splash`). There is no force flag for `saphir-container-eset` — the container archive cannot be built on GitHub.

### 4.2 Flow

```
detect-changes ──► prepare ──► build-<pkg> jobs (one per package)
                                          │
                                          ├─ prepare-build-env (composite)
                                          ├─ build-apk (composite)
                                          └─ publish (composite)
```

1. **`detect-changes`** — diffs the push (`before`…`sha`) for the package source path (`setup/packages/saphir/saphir` for the main package).
2. **`prepare`** — for each package, decides `do_build = package changed || force flag || force-all`.
3. **`build-<pkg>`** — one job per package (saphir, av-clamav, container-eset, av-eset, lib, gui, splash), each gated on its `prepare` output, each running in an **`alpine:3.24`** container:
   - **`prepare-build-env`** (composite): install `alpine-sdk`/`build-base`, create the `builder` user, restore the abuild private key from `secrets.ABUILD_PRIVATE_KEY` (base64) into `/home/builder/.abuild/saphir.rsa`, register the Saphir + Safecor repositories, copy the Saphir public key, download the Safecor public key.
   - **`build-apk`** (composite): as `builder`, run `abuild checksum` then `abuild -r` in the package's APKBUILD directory, then upload the APKs as an artifact.
   - **`publish`** (composite): rsync the APK to the official repository over SSH (`ssh -p 222` to `github-saphir@alefbet.net`), then recreate and **sign** the `APKINDEX.tar.gz` on the server (docker `alpine:3.24` + `abuild-sign` with the Saphir key).

   > **Alpine version note**: the workflow runs `alpine:3.24` containers (and the local-dev Dockerfile is based on `alpine:3.24`), while `AGENTS.md` and the chroot script's default reference Alpine 3.21. The CI container image is the ground truth for what actually builds the official packages; the chroot default is a validation convenience.

### 4.3 Repository targets (main vs. edge)

| Branch | Package repository URL (dependency resolution) | Publish branch | APK path on the server |
|--------|-----------------------------------------------|----------------|------------------------|
| `main` | `https://www.alefbet.net/github/saphir` (stable) | `main` | `/var/www/www.alefbet.net/github/saphir/x86_64/` |
| any other | `https://www.alefbet.net/github/saphir/edge` | `edge` | `/var/www/www.alefbet.net/github/saphir/edge/x86_64/` |

Dependency resolution always pulls **Safecor** from the **edge** repository: `https://www.alefbet.net/github/safecor/edge` (workflow env `SAFECOR_REPO_URL`).

### 4.4 The `saphir-container-eset` job

Its gate is `false && …`, so the job **never runs** on GitHub ("The container archive cannot be built on GitHub" — it needs host privileges and a live ESET binary download). `saphir-av-eset` resolves the container APK from the official Saphir repository instead.

---

## 5. Bootable ISO build

The ISO is produced with the Safecor `mkimg` toolchain using the Saphir profile in `setup/iso/saphir/`.

### 5.1 `mkimg.saphir.sh` — the mkimg profile

```sh
profile_saphir() {
    profile_xen
    kernel_cmdline="unionfs_size=512M console=tty0 console=ttyS0,115200"
    syslinux_serial="0 115200"
    kernel_addons=""
    apks="$apks xen xen-hypervisor saphir"
    ...
    apkovl="genapkovl-saphir.sh"
}
```

- Inherits the Safecor **`profile_xen`** (Xen paravirtualized guest).
- Adds the kernel cmdline (512 M unionfs overlay, serial console at 115200) and the serial console for syslinux.
- Appends `xen xen-hypervisor saphir` to the APK list (plus the kernel flavors).
- Points at `genapkovl-saphir.sh` for the per-host apkovl.

### 5.2 `genapkovl-saphir.sh` — the apkovl generator

Run as `genapkovl-saphir.sh <hostname>`, it produces `<hostname>.apkovl.tar.gz` containing:

- `/etc/hostname` — the given hostname.
- `/etc/modules` — Xen guest kernel modules: `xen_blkback`, `xenfs`, `xen-platform-pci`, `xen_wdt`, `tun`.
- `/etc/apk/world` — `xen` + `saphir` (the world that pulls the whole system).
- **Network is disabled** (no `/etc/network/interfaces` in the overlay).
- OpenRC runlevel links: `sysinit` (devfs, dmesg, udev, splash), `boot` (hwclock, modules, sysctl, hostname, bootmisc, syslog), `default` (udev-postmount, udev-trigger, xenstored, xenconsoled, **saphir**), `shutdown` (mount-ro, killprocs, savecache).

---

## 6. Versioning and coherence

### 6.1 Versioning scheme (`MAJOR.MINOR.PATCH`, e.g. `2.2.0`)

- A **bug fix** bumps the last digit (patch) only.
- A **new feature** bumps the second digit (minor) and resets the last digit to 0.
- The first digit (major) is bumped **only by the product maintainer**.

### 6.2 Coherence rules

- The Python package version (`pyproject.toml`) and the Alpine package version (`APKBUILD` `pkgver`) must **always** match. The Python packages use hatch dynamic versioning, so the source of truth is the `__version__` in each package's `__init__.py`:

| Component | Python version (`__init__.py` / `pyproject.toml`) | Alpine package | Coherent? |
|-----------|---------------------------------------------------|----------------|-----------|
| `libsaphir` | `2.0` | `saphir-lib` `2.0` | ✅ |
| Saphir GUI | `4.0.0` | `saphir` `4.0`, `saphir-gui` `4.0` | ✅ |
| Viewer | `1.0.0` | `saphir-viewer` `1.2` | ⚠️ pre-existing divergence (see [`packaging.md`](packaging.md) §4) |

  The Alpine `pkgver` drops the patch digit (`4.0.0` → `4.0`); bump `pkgrel` for rebuilds of the same `pkgver`.

- When component versions change, the Alpine packages must be updated to reflect the component versions, and all versions must stay coherent.

### 6.3 Python dependency placement

- Dependencies used **only** in development and tests must lie in `requirements-dev.txt`.
- Dependencies used in **production, development and tests** must lie in `requirements.txt`.

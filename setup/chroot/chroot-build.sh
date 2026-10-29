#!/usr/bin/env bash
#
# chroot-build.sh - Build and validate Saphir Alpine packages in a chroot.
#
# Capitalizes the local packaging workflow used to validate the Saphir
# packages without a K8s cluster (refactoring plan, Phase 8):
#
#   1. init     Create an Alpine chroot from the official minirootfs,
#               configure the Alefbet repositories (Safecor + Saphir),
#               create a `builder` user and a local abuild signing key.
#   2. sync     Sync the repository sources (python/ + setup/) into the
#               chroot at /work/Saphir.
#   3. build    Build the packages with abuild as the `builder` user.
#   4. install  Install the built APKs into the chroot.
#   5. test-gui Boot the saphir-gui PyInstaller bundle in DEVMODE
#               (offscreen) against a local mosquitto broker and verify
#               the boot marker "Saphir is ready" in the API log.
#
# Usage:
#   ./chroot-build.sh <command> [arguments]
#
# Commands:
#   init             Create the chroot (idempotent)
#   sync             Sync python/ and setup/ from this repository
#   build [PKG...]   Build the given packages (default: saphir-lib saphir-gui)
#   install          Install the built saphir-* APKs
#   test-gui         Boot the GUI bundle in DEVMODE and check the boot marker
#   validate         sync + build + install + test-gui
#   list             List the built packages
#   destroy          Remove the chroot and the cached minirootfs
#   help             Show this help
#
# Environment overrides (all optional):
#   CHROOT_DIR      chroot directory            (default: /tmp/opencode/alpine)
#   ALPINE_VERSION  Alpine branch               (default: 3.21)
#   ALPINE_RELEASE  Alpine release              (default: 3.21.9)
#   CACHE_DIR       minirootfs cache directory  (default: parent of CHROOT_DIR)
#
# Notes:
#   - `init` requires sudo on the host (chroot setup) and network access.
#   - `build` requires network access inside the chroot (apk + pip).
#   - The local signing key (localval.rsa) is for validation only; the
#     official CI signs with the Saphir key (see setup/docker/local-dev/).
#
set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
ALPINE_VERSION="${ALPINE_VERSION:-3.21}"
ALPINE_RELEASE="${ALPINE_RELEASE:-3.21.9}"
CHROOT_DIR="${CHROOT_DIR:-/tmp/opencode/alpine}"
CACHE_DIR="${CACHE_DIR:-$(dirname "$CHROOT_DIR")}"
MINIROOTFS="$CACHE_DIR/minirootfs.tar.gz"
MINIROOTFS_URL="https://dl-cdn.alpinelinux.org/alpine/v${ALPINE_VERSION}/releases/x86_64/alpine-minirootfs-${ALPINE_RELEASE}-x86_64.tar.gz"

SAFE_COR_REPO="https://www.alefbet.net/github/safecor"
SAPHIR_REPO="https://www.alefbet.net/github/saphir"
SAFE_COR_KEY_URL="https://alefbet.net/github/safecor/safecor.rsa.pub"
SAPHIR_KEY_URL="https://alefbet.net/github/saphir/saphir.rsa.pub"

BUILDER="builder"
WORK_DIR="/work/Saphir"
PKG_DIR="/home/${BUILDER}/packages/saphir/x86_64"
GUI_BIN="/usr/lib/saphir/saphir-gui"
BOOT_TIMEOUT=30

# Repo root (this script lives in <repo>/setup/chroot/)
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

DEFAULT_PKGS=(saphir-lib saphir-gui)

# Packages installed in the chroot during init (build toolchain + GUI
# dependencies + local MQTT broker for the DEVMODE boot test).
CHROOT_PKGS=(
    abuild alpine-sdk build-base file ca-certificates
    python3 python3-dev py3-pip py3-build py3-installer
    py3-pyside6 py3-jinja2 weasyprint qt6-qt5compat
    fontconfig freetype
    mosquitto mosquitto-clients
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
log()  { printf '\033[1;32m[chroot]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[chroot][warn]\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31m[chroot][error]\033[0m %s\n' "$*" >&2; exit 1; }

require_sudo() {
    if ! command -v sudo >/dev/null 2>&1; then
        die "sudo is required"
    fi
    if ! sudo -n true 2>/dev/null; then
        die "sudo access is required (run with a password-less sudo or as root)"
    fi
}

# Run a /bin/sh command line inside the chroot (as root)
chroot_sh() {
    sudo chroot "$CHROOT_DIR" /bin/sh -c "$1"
}

# Run a /bin/sh command line inside the chroot as the builder user
chroot_builder() {
    sudo chroot "$CHROOT_DIR" su "$BUILDER" -c "$1"
}

chroot_ready() {
    [ -d "$CHROOT_DIR" ] && [ -f "$CHROOT_DIR/etc/alpine-release" ]
}

show_help() {
    local end_line
    end_line=$(grep -n '^set -euo pipefail' "${BASH_SOURCE[0]}" | cut -d: -f1)
    sed -n "2,$((end_line - 2))p" "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
}

# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------
cmd_init() {
    if chroot_ready; then
        log "Chroot already initialized at $CHROOT_DIR (use destroy to rebuild)"
        return 0
    fi

    require_sudo
    command -v wget >/dev/null 2>&1 || command -v curl >/dev/null 2>&1 \
        || die "wget or curl is required on the host to download the minirootfs"

    log "Downloading Alpine ${ALPINE_RELEASE} minirootfs (x86_64)"
    mkdir -p "$CACHE_DIR"
    if [ ! -f "$MINIROOTFS" ]; then
        if command -v wget >/dev/null 2>&1; then
            wget -q -O "$MINIROOTFS" "$MINIROOTFS_URL"
        else
            curl -fsSL -o "$MINIROOTFS" "$MINIROOTFS_URL"
        fi
    else
        log "Reusing cached minirootfs: $MINIROOTFS"
    fi

    log "Extracting minirootfs into $CHROOT_DIR"
    mkdir -p "$CHROOT_DIR"
    sudo tar -xzpf "$MINIROOTFS" -C "$CHROOT_DIR"

    log "Configuring APK repositories"
    chroot_sh "printf '%s\n' \
        'https://dl-cdn.alpinelinux.org/alpine/v${ALPINE_VERSION}/main' \
        'https://dl-cdn.alpinelinux.org/alpine/v${ALPINE_VERSION}/community' \
        '${SAFE_COR_REPO}' \
        '${SAPHIR_REPO}' > /etc/apk/repositories"

    log "Fetching repository signing keys"
    chroot_sh "wget -q -O /etc/apk/keys/safecor.rsa.pub '${SAFE_COR_KEY_URL}'"
    chroot_sh "wget -q -O /etc/apk/keys/saphir.rsa.pub '${SAPHIR_KEY_URL}'"
    chroot_sh "chmod 644 /etc/apk/keys/safecor.rsa.pub /etc/apk/keys/saphir.rsa.pub"

    log "Installing build toolchain (${CHROOT_PKGS[*]})"
    chroot_sh "apk update && apk add --no-cache ${CHROOT_PKGS[*]}"

    log "Creating the ${BUILDER} user"
    chroot_sh "adduser -D -h /home/${BUILDER} -s /bin/sh ${BUILDER}"

    log "Generating the local abuild signing key (localval)"
    chroot_builder "mkdir -p ~/.abuild && \
        printf 'PACKAGER_NAME=\"Local Validation\"\nPACKAGER_EMAIL=\"validation@local\"\n' > ~/.abuild/abuild.conf && \
        abuild-keygen -a -i -n"

    log "Verifying abuild"
    chroot_builder "abuild --version"

    log "Chroot ready at $CHROOT_DIR (Alpine $(chroot_sh 'cat /etc/alpine-release'))"
}

# ---------------------------------------------------------------------------
# sync
# ---------------------------------------------------------------------------
cmd_sync() {
    chroot_ready || die "Chroot not initialized (run: $0 init)"

    log "Syncing $REPO_ROOT/python and $REPO_ROOT/setup into ${CHROOT_DIR}${WORK_DIR}"
    # Replace the synced trees (no rsync required on the host):
    sudo rm -rf "${CHROOT_DIR}${WORK_DIR}/python" "${CHROOT_DIR}${WORK_DIR}/setup"
    sudo mkdir -p "${CHROOT_DIR}${WORK_DIR}"
    tar -C "$REPO_ROOT" -cf - python | sudo tar -C "${CHROOT_DIR}${WORK_DIR}" -xf -
    tar -C "$REPO_ROOT" -cf - setup  | sudo tar -C "${CHROOT_DIR}${WORK_DIR}" -xf -

    log "Synced"
}

# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------
cmd_build() {
    chroot_ready || die "Chroot not initialized (run: $0 init)"
    local pkgs=("$@")
    [ "${#pkgs[@]}" -gt 0 ] || pkgs=("${DEFAULT_PKGS[@]}")

    local pkg
    for pkg in "${pkgs[@]}"; do
        log "Building ${pkg} (abuild, as ${BUILDER})"
        # -r install missing makedepends, -f forces a fresh build: the
        # up-to-date check only compares the APKBUILD timestamp, not the
        # synced Python sources, so a plain `abuild` would skip rebuilds.
        chroot_builder "cd ${WORK_DIR}/setup/packages/saphir/${pkg} && \
            abuild -r -f"
    done

    log "Built packages:"
    cmd_list
}

# ---------------------------------------------------------------------------
# install
# ---------------------------------------------------------------------------
cmd_install() {
    chroot_ready || die "Chroot not initialized (run: $0 init)"

    local apks
    apks=$(chroot_sh "ls ${PKG_DIR}/saphir-*.apk 2>/dev/null")
    [ -n "$apks" ] || die "No built saphir-*.apk found in ${PKG_DIR} (run: $0 build)"

    log "Installing: $(echo "$apks" | xargs -n1 basename | tr '\n' ' ')"
    # shellcheck disable=SC2086
    chroot_sh "apk add $(echo "$apks" | tr '\n' ' ')"
}

# ---------------------------------------------------------------------------
# test-gui
# ---------------------------------------------------------------------------
cmd_test_gui() {
    chroot_ready || die "Chroot not initialized (run: $0 init)"

    log "Booting the GUI bundle in DEVMODE (offscreen, up to ${BOOT_TIMEOUT}s)"

    # Process management happens on the host: the chroot has no /proc, so
    # pkill/pgrep do not work inside it. The bracket keeps pkill from
    # matching its own command line.
    sudo pkill -9 -f "/usr/lib/saphir/saphir[-]gui" 2>/dev/null || true
    sudo rm -rf "${CHROOT_DIR}/tmp/_MEI"* 2>/dev/null || true
    sudo mkdir -p "${CHROOT_DIR}/tmp"
    # Truncate the API log: the boot marker below is looked up there
    chroot_sh ": > /tmp/saphir.log"

    # DEVMODE talks to a broker on localhost:1883; start one if needed
    if ! (exec 3<>/dev/tcp/127.0.0.1/1883) 2>/dev/null; then
        log "Starting mosquitto on port 1883"
        sudo chroot "$CHROOT_DIR" /usr/sbin/mosquitto -p 1883 -d
        sleep 1
    fi

    # Launch in the background with file redirection. A command
    # substitution (pipe) would hang: the PyInstaller child process
    # survives SIGTERM and keeps the pipe open.
    sudo chroot "$CHROOT_DIR" /bin/sh -c \
        "DEVMODE=1 QT_QPA_PLATFORM=offscreen ${GUI_BIN} > /tmp/gui-test.log 2>&1 &"

    # Poll the API log (the Python stdout is block-buffered and is lost on
    # SIGKILL, so it is not a reliable marker).
    local i found=0
    for i in $(seq 1 "$BOOT_TIMEOUT"); do
        if chroot_sh "grep -q 'Saphir is ready' /tmp/saphir.log"; then
            found=1
            break
        fi
        sleep 1
    done

    # The PyInstaller bundle ignores SIGTERM: kill it for good
    sudo pkill -9 -f "/usr/lib/saphir/saphir[-]gui" 2>/dev/null || true

    if [ "$found" -eq 1 ]; then
        log "BOOT OK - 'Saphir is ready' found in /tmp/saphir.log"
        [ -f "${CHROOT_DIR}/tmp/gui-test.log" ] && tail -5 "${CHROOT_DIR}/tmp/gui-test.log"
        return 0
    fi

    [ -f "${CHROOT_DIR}/tmp/gui-test.log" ] && {
        echo "--- last lines of the GUI log ---" >&2
        tail -15 "${CHROOT_DIR}/tmp/gui-test.log" >&2
    }
    die "BOOT FAILED - 'Saphir is ready' not found within ${BOOT_TIMEOUT}s"
}

# ---------------------------------------------------------------------------
# validate / list / destroy
# ---------------------------------------------------------------------------
cmd_validate() {
    cmd_sync
    cmd_build
    cmd_install
    cmd_test_gui
    log "Validation complete"
}

cmd_list() {
    chroot_ready || die "Chroot not initialized (run: $0 init)"
    chroot_sh "ls -l ${PKG_DIR}/ 2>/dev/null || echo 'No packages built yet'"
}

cmd_destroy() {
    local target
    for target in "$CHROOT_DIR" "$MINIROOTFS"; do
        if [ -e "$target" ]; then
            log "Removing $target"
            sudo rm -rf "$target"
        fi
    done
    log "Destroyed"
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
cmd="${1:-help}"
shift || true

case "$cmd" in
    init)     cmd_init ;;
    sync)     cmd_sync ;;
    build)    cmd_build "$@" ;;
    install)  cmd_install ;;
    test-gui) cmd_test_gui ;;
    validate) cmd_validate ;;
    list)     cmd_list ;;
    destroy)  cmd_destroy ;;
    help|-h|--help) show_help ;;
    *) die "Unknown command: $cmd (see: $0 help)" ;;
esac

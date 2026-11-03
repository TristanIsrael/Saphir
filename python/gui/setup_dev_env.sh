#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Default venv dir: venv.nosync on macOS (Time Machine friendly), .venv elsewhere
if [[ "${SAPHIR_VENV_DIR:-}" ]]; then
    VENV_DIR="${SAPHIR_VENV_DIR}"
elif [[ "$(uname)" == "Darwin" ]]; then
    VENV_DIR="${SCRIPT_DIR}/venv.nosync"
else
    VENV_DIR="${SCRIPT_DIR}/.venv"
fi
SAFECOR_ROOT="${SAFECOR_ROOT:-/home/onyxia/work/Safecor}"

echo "=== Saphir GUI dev environment setup ==="

# 1. Create venv
if [ ! -d "${VENV_DIR}" ]; then
    echo "[1/4] Creating virtualenv at ${VENV_DIR}"
    python3 -m venv "${VENV_DIR}"
else
    echo "[1/4] Virtualenv already exists at ${VENV_DIR}"
fi

# 2. Install dependencies
echo "[2/4] Installing production + dev dependencies..."
"${VENV_DIR}/bin/pip" install --quiet --upgrade pip

# Linux-only and optional dependencies: try to install, warn if unavailable
OPTIONAL_DEPS=(libvirt-python evdev inotify_simple pyudev)
# Install the main requirements minus the optional deps
REQUIREMENTS_FILTERED=$(mktemp)
for dep in "${OPTIONAL_DEPS[@]}"; do
    grep -v "^${dep}" "${SCRIPT_DIR}/requirements.txt" >> "${REQUIREMENTS_FILTERED}" || true
done
"${VENV_DIR}/bin/pip" install --quiet -r "${REQUIREMENTS_FILTERED}"
rm "${REQUIREMENTS_FILTERED}"

# Try optional deps one by one
for dep in "${OPTIONAL_DEPS[@]}"; do
    if ! "${VENV_DIR}/bin/pip" install --quiet "${dep}" 2>/dev/null; then
        echo "  WARNING: ${dep} not installed (platform-specific or system dependency missing)."
    fi
done

"${VENV_DIR}/bin/pip" install --quiet -r "${SCRIPT_DIR}/requirements-dev.txt"

# 3. Create .pth files for local Safecor packages
SITE_PACKAGES="${VENV_DIR}/lib/python$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')/site-packages"

echo "[3/4] Creating .pth files for local Safecor packages..."
echo "${SAFECOR_ROOT}/python/lib/src" > "${SITE_PACKAGES}/safecor-local.pth"
echo "${SAFECOR_ROOT}/python/emulator/src" > "${SITE_PACKAGES}/safecor_emulator-local.pth"

# 4. Verify
echo "[4/4] Verifying imports..."
"${VENV_DIR}/bin/python" -c "
import safecor
import safecor_emulator
import pytest
print(f'  safecor:          {safecor.__file__}')
print(f'  safecor_emulator: {safecor_emulator.__file__}')
print(f'  pytest:           {pytest.__version__}')
"

echo ""
echo "=== Done. Activate with: source ${VENV_DIR}/bin/activate ==="

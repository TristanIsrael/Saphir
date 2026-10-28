#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/.venv"
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

# libvirt-python requires the system libvirt-dev package; skip it if unavailable
# (the Safecor library handles its absence gracefully)
REQUIREMENTS_NO_LIBVIRT=$(mktemp)
grep -v '^libvirt-python' "${SCRIPT_DIR}/requirements.txt" > "${REQUIREMENTS_NO_LIBVIRT}"
"${VENV_DIR}/bin/pip" install --quiet -r "${REQUIREMENTS_NO_LIBVIRT}"
rm "${REQUIREMENTS_NO_LIBVIRT}"

if ! "${VENV_DIR}/bin/pip" install --quiet libvirt-python 2>/dev/null; then
    echo "  WARNING: libvirt-python not installed (requires system libvirt-dev)."
    echo "  This is optional for emulator-based development."
fi

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

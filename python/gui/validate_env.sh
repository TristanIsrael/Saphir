#!/usr/bin/env bash
# Validation environment launcher.
#
# Starts the two mock AV engines (mock-clam, mock-eset) in the background,
# then the Saphir GUI on-screen. The emulator (mosquitto + mock Dom0/SysUSB)
# and the operator console must already be running as prerequisites.
#
# Usage:
#   bash validate_env.sh
#
# Stop with Ctrl+C (SIGINT) — the mock AVs are cleaned up automatically.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="${SCRIPT_DIR}/.venv"

if [[ ! -d "$VENV" ]]; then
    echo "ERROR: venv not found at $VENV" >&2
    echo "Run 'bash setup_dev_env.sh' first." >&2
    exit 1
fi

source "$VENV/bin/activate"

PYTHONPATH="${SCRIPT_DIR}/src/Saphir:${SCRIPT_DIR}/../libsaphir/src:${PYTHONPATH:-}"
export PYTHONPATH
export DEVMODE=1

# Check that the broker is reachable (emulator prerequisite)
if ! python -c "import socket; s=socket.socket(); s.settimeout(2); s.connect(('localhost',1883)); s.close()" 2>/dev/null; then
    echo "ERROR: MQTT broker not reachable on localhost:1883." >&2
    echo "Start the Safecor emulator first (see docs/validation-guide.md)." >&2
    exit 1
fi

MOCK_PIDS=()

cleanup() {
    echo ""
    echo "Cleaning up mock AVs..."
    for pid in "${MOCK_PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
            wait "$pid" 2>/dev/null || true
        fi
    done
    echo "Done."
}
trap cleanup SIGINT SIGTERM

start_mock_av() {
    local name="$1"
    python -u -m libsaphir._mock_antivirus_controller --name "$name" &
    local pid=$!
    MOCK_PIDS+=("$pid")
    echo "Started mock AV '$name' (pid $pid)"
}

echo "Starting mock AV engines..."
start_mock_av "mock-clam"
start_mock_av "mock-eset"

# Give the mock AVs time to connect to the broker
sleep 2

# Verify both are still alive
for pid in "${MOCK_PIDS[@]}"; do
    if ! kill -0 "$pid" 2>/dev/null; then
        echo "ERROR: a mock AV died at startup." >&2
        cleanup
        exit 1
    fi
done

echo ""
echo "Starting Saphir GUI..."
cd "${SCRIPT_DIR}/src/Saphir"
python main.py

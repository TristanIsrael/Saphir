"""C.1 — Nominal cycle characterization test.

Drives the full Saphir workflow through the Safecor emulator:
boot -> source -> analysis -> target -> copy -> report -> SystemMustBeReset.

The Saphir app runs as a subprocess (offscreen Qt, DEVMODE=1).
The test observes state transitions via the app's stdout.
"""

import os
import re
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src" / "Saphir"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "libsaphir" / "src"))

from safecor_emulator import Emulator, default_profile  # noqa: E402
from tests.mock_av_manager import MockAVManager  # noqa: E402


class StateTracker:
    """Reads a subprocess stdout and tracks SystemState transitions."""

    def __init__(self, process: subprocess.Popen):
        self.states: list[str] = []
        self._process = process
        self._thread = threading.Thread(target=self._read, daemon=True)

    _STATE_RE = re.compile(r"System state:\s*(SystemState\.\w+)")

    def _read(self):
        for line in iter(self._process.stdout.readline, b""):
            # A state line can be glued to a print from another thread
            # (non-atomic prints on the shared stdout), so search the
            # state marker anywhere in the line instead of startswith.
            m = self._STATE_RE.search(line.decode())
            if m:
                self.states.append(m.group(1))

    def start(self):
        self._thread.start()

    def wait_for(self, state_name: str, timeout: float = 30.0) -> bool:
        target = f"SystemState.{state_name}"
        deadline = time.time() + timeout
        while time.time() < deadline:
            if target in self.states:
                return True
            if self._process.poll() is not None:
                return False
            time.sleep(0.1)
        return False

    def has_sequence(self, expected: list[str]) -> bool:
        idx = 0
        for state in self.states:
            if idx < len(expected) and state == expected[idx]:
                idx += 1
        return idx == len(expected)


@pytest.fixture
def nominal_env():
    """Starts emulator + 2 mock AVs + Saphir app. Yields (emulator, tracker, cleanup)."""
    tmp = tempfile.mkdtemp(prefix="saphir_test_")
    source_dir = os.path.join(tmp, "source")
    os.makedirs(os.path.join(source_dir, "subfolder"), exist_ok=True)

    # Create test files
    test_files = {
        "file1.txt": "hello world",
        "file2.txt": "second file",
        os.path.join("subfolder", "file3.txt"): "nested file",
    }
    for rel_path, content in test_files.items():
        with open(os.path.join(source_dir, rel_path), "w") as f:
            f.write(content)

    target_dir = os.path.join(tmp, "target")
    os.makedirs(target_dir, exist_ok=True)

    # Emulator (no pre-attached disks)
    em = Emulator(
        profile=default_profile(),
        source_disks={},
        storage_path=os.path.join(tmp, "repo"),
        destination_disk_path=target_dir,
    )
    em.start()

    # Mock AVs
    # Point the mock AVs at the emulator repository so the NFR-1
    # fingerprint integrity check runs against the real test files.
    repo_path = os.path.join(tmp, "repo")
    av1 = MockAVManager("mock-clam", scan_delay=0.05, repository_path=repo_path)
    av2 = MockAVManager("mock-eset", scan_delay=0.05, repository_path=repo_path)
    av1.start()
    av2.start()

    # Saphir app subprocess
    gui_dir = Path(__file__).resolve().parent.parent
    python = sys.executable
    entry = Path(__file__).resolve().parent / "test_app_entry.py"
    env = os.environ.copy()
    env["DEVMODE"] = "1"
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["PYTHONPATH"] = os.pathsep.join([
        str(gui_dir / "src" / "Saphir"),
        str(gui_dir.parent / "libsaphir" / "src"),
        env.get("PYTHONPATH", ""),
    ])

    app_proc = subprocess.Popen(
        [python, "-u", str(entry)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
        cwd=str(gui_dir),
    )

    tracker = StateTracker(app_proc)
    tracker.start()

    yield em, tracker, source_dir, target_dir

    # Cleanup
    app_proc.terminate()
    try:
        app_proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        app_proc.kill()
        app_proc.wait()
    av1.stop()
    av2.stop()
    em.stop()

    import shutil
    shutil.rmtree(tmp, ignore_errors=True)


def test_nominal_cycle(nominal_env):
    """Full nominal cycle: boot -> analysis -> copy -> report -> SystemMustBeReset."""
    em, tracker, source_dir, target_dir = nominal_env

    # 1. Wait for the app to boot and reach SystemReady
    assert tracker.wait_for("SystemReady", timeout=30), (
        f"App never reached SystemReady.\nStates seen: {tracker.states}"
    )

    # 2. Attach the source disk
    em.attach_disk("disk0", source_dir)

    # 3. Wait for analysis to start (auto in DEVMODE after file listing)
    assert tracker.wait_for("SystemAnalysisRunning", timeout=30), (
        f"Analysis never started.\nStates seen: {tracker.states}"
    )

    # 4. Wait for analysis to complete
    assert tracker.wait_for("AnalysisCompleted", timeout=30), (
        f"Analysis never completed.\nStates seen: {tracker.states}"
    )

    # 5. Attach the target disk
    em.attach_disk("disk1", target_dir)

    # 6. Wait for the copy to start
    assert tracker.wait_for("CopyCleanFiles", timeout=30), (
        f"Copy never started.\nStates seen: {tracker.states}"
    )

    # 7. Wait for the full cycle to complete (report + journal copied)
    assert tracker.wait_for("SystemMustBeReset", timeout=60), (
        f"Never reached SystemMustBeReset.\nStates seen: {tracker.states}"
    )

    # 8. Verify the state sequence (characterization — captures actual behaviour)
    expected_sequence = [
        "SystemState.SystemReady",
        "SystemState.SafecorReady",
        "SystemState.SystemReady",
        "SystemState.SystemAnalysisRunning",
        "SystemState.SystemWaitingForUserAction",
        "SystemState.AnalysisCompleted",
        "SystemState.CopyCleanFiles",
        "SystemState.GeneratingReport",
        "SystemState.SystemMustBeReset",
    ]
    assert tracker.has_sequence(expected_sequence), (
        f"State sequence mismatch.\n"
        f"Expected: {expected_sequence}\n"
        f"Actual:   {tracker.states}"
    )

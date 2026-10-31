"""F1 — Full analysis of a multi-partition / multi-media source.

Drives the full Saphir workflow through the Safecor emulator with two
source disks attached before the scan starts (the partitions of a media
are disk entries in Safecor): both are analyzed and every clean file is
copied to the single target disk.

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
sys.path.insert(
    0, str(Path(__file__).resolve().parent.parent.parent / "libsaphir" / "src")
)

from safecor_emulator import Emulator, default_profile

from tests.mock_av_manager import MockAVManager


class StateTracker:
    """Reads a subprocess stdout and tracks SystemState transitions."""

    def __init__(self, process: subprocess.Popen):
        self.states: list[str] = []
        self._process = process
        self._thread = threading.Thread(target=self._read, daemon=True)

    _STATE_RE = re.compile(r"System state:\s*(SystemState\.\w+)")

    def _read(self):
        for line in iter(self._process.stdout.readline, b""):
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
def multi_source_env():
    """Starts emulator + 2 mock AVs + Saphir app with two source disks."""
    tmp = tempfile.mkdtemp(prefix="saphir_multi_")

    # Two source disks (the partitions of the source media): every
    # partition is a disk entry in Safecor
    source0_dir = os.path.join(tmp, "source0")
    os.makedirs(os.path.join(source0_dir, "sub0"), exist_ok=True)
    for rel_path, content in {
        "file0_a.txt": "disk0 file a",
        "file0_b.txt": "disk0 file b",
        os.path.join("sub0", "file0_c.txt"): "disk0 nested",
    }.items():
        with open(os.path.join(source0_dir, rel_path), "w") as f:
            f.write(content)

    source1_dir = os.path.join(tmp, "source1")
    os.makedirs(source1_dir, exist_ok=True)
    for rel_path, content in {
        "file1_a.txt": "disk1 file a",
        "file1_b.txt": "disk1 file b",
    }.items():
        with open(os.path.join(source1_dir, rel_path), "w") as f:
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
    env["PYTHONPATH"] = os.pathsep.join(
        [
            str(gui_dir / "src" / "Saphir"),
            str(gui_dir.parent / "libsaphir" / "src"),
            env.get("PYTHONPATH", ""),
        ]
    )

    app_proc = subprocess.Popen(
        [python, "-u", str(entry)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
        cwd=str(gui_dir),
    )

    tracker = StateTracker(app_proc)
    tracker.start()

    yield em, tracker, source0_dir, source1_dir, target_dir

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


def test_multi_source_full_analysis(multi_source_env):
    """Both source disks are analyzed and copied to the single target."""
    em, tracker, source0_dir, source1_dir, target_dir = multi_source_env

    # 1. Wait for the app to boot
    assert tracker.wait_for("SystemReady", timeout=30), (
        f"App never reached SystemReady.\nStates seen: {tracker.states}"
    )

    # 2. Attach the two source disks (the partitions of the media):
    # both are connected before the scan starts, both are sources
    em.attach_disk("disk0", source0_dir)
    em.attach_disk("disk1", source1_dir)

    # 3. The full analysis covers both disks (DEVMODE auto-start)
    assert tracker.wait_for("AnalysisCompleted", timeout=60), (
        f"Analysis never completed.\nStates seen: {tracker.states}"
    )

    # 4. Attach the target disk after the analysis: it becomes the target
    em.attach_disk("disk2", target_dir)
    assert tracker.wait_for("SystemMustBeReset", timeout=60), (
        f"The cycle never completed.\nStates seen: {tracker.states}"
    )

    # 5. The target contains every clean file, from every source disk
    target_files = set(os.listdir(target_dir))
    for expected in (
        "file0_a.txt",
        "file0_b.txt",
        "file1_a.txt",
        "file1_b.txt",
    ):
        assert expected in target_files, (
            f"{expected} was not copied to the target.\n"
            f"Target: {target_files}\nStates: {tracker.states}"
        )
    # The nested file is copied keeping its folder structure
    assert os.path.isfile(os.path.join(target_dir, "sub0", "file0_c.txt")), (
        f"The nested file was not copied to the target.\n"
        f"Target: {os.listdir(target_dir)}\nStates: {tracker.states}"
    )

    # 6. The nominal state sequence was followed
    assert tracker.has_sequence(
        [
            "SystemState.SystemReady",
            "SystemState.SafecorReady",
            "SystemState.SystemReady",
            "SystemState.SystemAnalysisRunning",
            "SystemState.AnalysisCompleted",
            "SystemState.CopyCleanFiles",
            "SystemState.GeneratingReport",
            "SystemState.SystemMustBeReset",
        ]
    ), f"Unexpected state sequence: {tracker.states}"

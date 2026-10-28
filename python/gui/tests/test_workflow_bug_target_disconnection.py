"""C.2 — Target disconnection during copy leads to SystemMustBeReset.

Scenario:
  nominal cycle up to CopyCleanFiles -> detach target -> expect SystemMustBeReset

The system transitions to SystemMustBeReset after the copy completes
and journal.log is created on the target. If the target is removed
before the copy finishes, the system will be stuck in CopyCleanFiles
until the copy can no longer proceed (files become inaccessible).
"""

import os
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
from tests.test_workflow_nominal import StateTracker  # noqa: E402


@pytest.fixture
def bug_env():
    """Same setup as C.1 (emulator + 2 mock AVs + Saphir app)."""
    tmp = tempfile.mkdtemp(prefix="saphir_bug_")
    source_dir = os.path.join(tmp, "source")
    os.makedirs(source_dir, exist_ok=True)

    # Many small files so the copy phase (N MQTT round-trips) takes time
    for i in range(200):
        with open(os.path.join(source_dir, f"file_{i:04d}.txt"), "w") as f:
            f.write(f"content {i}")

    target_dir = os.path.join(tmp, "target")
    os.makedirs(target_dir, exist_ok=True)

    em = Emulator(
        profile=default_profile(),
        source_disks={},
        storage_path=os.path.join(tmp, "repo"),
        destination_disk_path=target_dir,
    )
    em.start()

    av1 = MockAVManager("mock-clam", scan_delay=0.01)
    av2 = MockAVManager("mock-eset", scan_delay=0.01)
    av1.start()
    av2.start()

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


def test_target_disconnection_during_copy(bug_env):
    """Target removed during copy must lead to SystemMustBeReset.

    The system reaches SystemMustBeReset after the copy completes
    and the report/journal are written to the target.
    """
    em, tracker, source_dir, target_dir = bug_env

    # 1. Boot
    assert tracker.wait_for("SystemReady", timeout=30), (
        f"App never reached SystemReady.\nStates: {tracker.states}"
    )

    # 2. Source disk -> analysis
    em.attach_disk("disk0", source_dir)
    assert tracker.wait_for("SystemAnalysisRunning", timeout=30), (
        f"Analysis never started.\nStates: {tracker.states}"
    )
    assert tracker.wait_for("AnalysisCompleted", timeout=30), (
        f"Analysis never completed.\nStates: {tracker.states}"
    )

    # 3. Target disk -> copy starts
    em.attach_disk("disk1", target_dir)
    assert tracker.wait_for("CopyCleanFiles", timeout=30), (
        f"Copy never started.\nStates: {tracker.states}"
    )

    # 4. User removes the target disk during copy
    em.detach_disk("disk1")

    # 5. The app should transition to SystemMustBeReset
    assert tracker.wait_for("SystemMustBeReset", timeout=10), (
        f"BUG: Target disconnection during copy does NOT lead to SystemMustBeReset.\n"
        f"App is stuck. States: {tracker.states}"
    )

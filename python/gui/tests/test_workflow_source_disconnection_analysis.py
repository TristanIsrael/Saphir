"""8.8 — Source disconnection during analysis: the analysis is held and auto-resumes.

Scenario (Safecor v2):
  attach source -> SystemAnalysisRunning -> detach the source ->
  the AnalysisController enters hold mode ->
  re-attach the source -> the analysis auto-resumes -> AnalysisCompleted

In v2 there is no repository: files are scanned directly from the USB mount.
A disconnection during analysis puts the controller in a *hold* state:
in-flight fingerprints and AV scans are paused, and the copy loop is held.
On same-disk reconnect, in-flight files are reset and re-analysed.
"""

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src" / "Saphir"))
sys.path.insert(
    0, str(Path(__file__).resolve().parent.parent.parent / "libsaphir" / "src")
)

from safecor_emulator import Emulator, default_profile

from tests.mock_av_manager import MockAVManager
from tests.test_workflow_nominal import StateTracker


@pytest.fixture
def source_disc_env():
    """Emulator + 2 mock AVs + Saphir app, with a source of many files.

    Uses 50 files and 0.2 s scan delays so that analysis does NOT complete
    during the 3-second hold window after source disconnection.

    Timing budget (2 mock AVs * 0.2 s each + fingerprint overhead ≈ 0.5 s/file):
      - 2 s pre-disconnect  → ~4 files reach final state
      - 3 s hold            → ~6 more complete, ~40 still in-flight
      - After reconnect     → ~40 files re-analysed ≈ 20 s (fits 120 s timeout)
    """
    tmp = tempfile.mkdtemp(prefix="saphir_srcdisc_")
    source_dir = os.path.join(tmp, "source")
    os.makedirs(source_dir, exist_ok=True)

    # 50 files → enough in-flight files survive the 3-second hold window
    for i in range(50):
        with open(os.path.join(source_dir, f"file_{i:04d}.txt"), "w") as f:
            f.write(f"content {i}")

    target_dir = os.path.join(tmp, "target")
    os.makedirs(target_dir, exist_ok=True)

    em = Emulator(
        profile=default_profile(),
        source_disks={},
        storage_path=os.path.join(tmp, "repo"),
    )
    em.start()

    # Mock AVs – 0.2 s delay ensures analysis does not finish during hold.
    av1 = MockAVManager(
        "mock-clam",
        scan_delay=0.2,
    )
    av2 = MockAVManager(
        "mock-eset",
        scan_delay=0.2,
    )
    av1.start()
    av2.start()

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


def test_source_disconnection_during_analysis_holds_and_resumes(source_disc_env):
    """8.8: unplug the source during the analysis.

    The analysis must be held (no reset), and auto-resume on reconnect.
    """
    em, tracker, source_dir, target_dir = source_disc_env

    # 1. Boot
    assert tracker.wait_for("SystemReady", timeout=30), (
        f"App never reached SystemReady.\nStates: {tracker.states}"
    )

    # 2. Source disk -> analysis starts
    em.attach_disk("disk0", source_dir)
    assert tracker.wait_for("SystemAnalysisRunning", timeout=30), (
        f"Analysis never started.\nStates: {tracker.states}"
    )

    # Let some fingerprints/analyses start
    time.sleep(2)

    # 3. Unplug the source
    em.detach_disk("disk0")

    # 4. The analysis should NOT reset; it stays in analysis state
    time.sleep(3)
    assert "SystemState.SystemMustBeReset" not in tracker.states, (
        f"BUG: the system asked for a reset after source disconnection.\n"
        f"States: {tracker.states}"
    )

    # 5. Re-attach the same source disk
    em.attach_disk("disk0", source_dir)

    # 6. Analysis auto-resumes and completes
    assert tracker.wait_for("AnalysisCompleted", timeout=120), (
        f"Analysis never resumed/completed after reconnection.\n"
        f"States: {tracker.states}"
    )

    # 7. Continue the nominal cycle
    em.attach_disk("disk1", target_dir)
    assert tracker.wait_for("CopyCleanFiles", timeout=60), (
        f"Copy never started.\nStates: {tracker.states}"
    )
    assert tracker.wait_for("SystemMustBeReset", timeout=120), (
        f"Never reached SystemMustBeReset.\nStates: {tracker.states}"
    )


def test_different_disk_during_analysis_hold_rejects_and_resets(source_disc_env):
    """Different disk re-inserted during a hold triggers SystemMustBeReset."""
    em, tracker, source_dir, target_dir = source_disc_env

    # 1. Boot
    assert tracker.wait_for("SystemReady", timeout=30), (
        f"App never reached SystemReady.\nStates: {tracker.states}"
    )

    # 2. Attach source
    em.attach_disk("disk0", source_dir)
    assert tracker.wait_for("SystemAnalysisRunning", timeout=30), (
        f"Analysis never started.\nStates: {tracker.states}"
    )

    # Let analysis start
    time.sleep(2)

    # 3. Unplug the source -> hold mode
    em.detach_disk("disk0")
    time.sleep(2)

    # 4. Attach a DIFFERENT disk (disk1) while source is held
    em.attach_disk("disk1", target_dir)

    # 5. A different disk during hold -> SystemMustBeReset
    assert tracker.wait_for("SystemMustBeReset", timeout=30), (
        f"Expected SystemMustBeReset for different-disk reconnect.\n"
        f"States: {tracker.states}"
    )

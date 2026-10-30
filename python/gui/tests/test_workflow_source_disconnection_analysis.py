"""8.8 — Source disconnection during analysis: the analysis is held and auto-resumes.

Scenario:
  attach source -> SystemAnalysisRunning -> detach the source ->
  the analysis CONTINUES on the files already in the repository and the
  copy loop is HELD (the system must NOT reset) ->
  re-attach the source -> the analysis auto-resumes -> AnalysisCompleted
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
    """Emulator + 2 mock AVs + Saphir app, with a source of many files."""
    tmp = tempfile.mkdtemp(prefix="saphir_srcdisc_")
    source_dir = os.path.join(tmp, "source")
    os.makedirs(source_dir, exist_ok=True)

    # Enough files that the analysis is still running when the source
    # is unplugged (a few seconds after it starts).
    for i in range(60):
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

    # Point the mock AVs at the emulator repository so the NFR-1
    # fingerprint integrity check runs against the real test files.
    repo_path = os.path.join(tmp, "repo")
    av1 = MockAVManager("mock-clam", scan_delay=0.01, repository_path=repo_path)
    av2 = MockAVManager("mock-eset", scan_delay=0.01, repository_path=repo_path)
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

    The analysis must keep running on the repository files (no reset),
    hold the copy loop, and auto-resume when the source is re-inserted.
    """
    em, tracker, source_dir, target_dir = source_disc_env

    # 1. Boot
    assert tracker.wait_for("SystemReady", timeout=30), (
        f"App never reached SystemReady.\nStates: {tracker.states}"
    )

    # 2. Source disk -> analysis
    em.attach_disk("disk0", source_dir)
    assert tracker.wait_for("SystemAnalysisRunning", timeout=30), (
        f"Analysis never started.\nStates: {tracker.states}"
    )

    # Let the analysis copy a few files into the repository
    time.sleep(3)

    # 3. The user unplugs the source by mistake
    em.detach_disk("disk0")
    analysis_started_at = tracker.states.index("SystemState.SystemAnalysisRunning")

    # 4. The analysis is held: the system stays in SystemAnalysisRunning
    # (the AVs keep scanning the repository files), no reset is required.
    time.sleep(4)
    assert "SystemState.SystemMustBeReset" not in tracker.states, (
        f"BUG: the system asked for a reset after the source disconnection.\n"
        f"States: {tracker.states}"
    )
    assert "SystemState.SystemReady" not in tracker.states[analysis_started_at:], (
        f"BUG: the analysis was reset after the source disconnection.\n"
        f"States: {tracker.states}"
    )
    assert tracker.states[-1] == "SystemState.SystemAnalysisRunning", (
        f"BUG: the system left SystemAnalysisRunning while the source is "
        f"disconnected (the analysis should be held).\nStates: {tracker.states}"
    )

    # 5. The user re-inserts the same source disk
    em.attach_disk("disk0", source_dir)

    # 6. The analysis auto-resumes and completes.
    # Completing also proves the AVs kept scanning the repository files
    # during the hold (those results count toward the completion guard).
    # Generous timeout: the MQTT round-trips are slow on a loaded machine.
    assert tracker.wait_for("AnalysisCompleted", timeout=120), (
        f"Analysis never resumed/completed after the source reconnection.\n"
        f"States: {tracker.states}"
    )

    # 7. The nominal cycle continues: target -> copy -> report -> reset
    em.attach_disk("disk1", target_dir)
    assert tracker.wait_for("CopyCleanFiles", timeout=60), (
        f"Copy never started.\nStates: {tracker.states}"
    )
    assert tracker.wait_for("SystemMustBeReset", timeout=120), (
        f"Never reached SystemMustBeReset.\nStates: {tracker.states}"
    )

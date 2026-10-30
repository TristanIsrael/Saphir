"""NFR-3 — Antivirus engine failure during the analysis.

Scenario:
  attach source -> SystemAnalysisRunning -> an antivirus engine fails ->
  the incomplete files are declared in error and, because the number of
  available engines drops below ANTIVIRUS_NEEDED, the analysis is
  ABORTED (SystemWaitingForUserAction, no reset required, no completion).
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
def av_failure_env():
    """Emulator + 2 mock AVs + Saphir app, with a source of many files."""
    tmp = tempfile.mkdtemp(prefix="saphir_avfail_")
    source_dir = os.path.join(tmp, "source")
    os.makedirs(source_dir, exist_ok=True)

    # Enough files that the analysis is still running when the AV fails.
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
    av1 = MockAVManager("mock-clam", scan_delay=0.05, repository_path=repo_path)
    av2 = MockAVManager("mock-eset", scan_delay=0.05, repository_path=repo_path)
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

    yield em, tracker, av1, av2, source_dir

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


def test_av_failure_during_analysis_aborts(av_failure_env):
    """NFR-3: an antivirus engine fails during the analysis.

    The analysis must be aborted (SystemWaitingForUserAction): the
    incomplete files are declared in error and the number of available
    engines drops below ANTIVIRUS_NEEDED. The system must NOT complete
    the analysis and must NOT ask for a reset.
    """
    em, tracker, av1, _av2, source_dir = av_failure_env

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

    # 3. An antivirus engine fails
    av1.fail()

    # 4. The analysis is aborted: the system reaches
    # SystemWaitingForUserAction (analysis stopped), not AnalysisCompleted.
    assert tracker.wait_for("SystemWaitingForUserAction", timeout=60), (
        f"Analysis was not aborted after the AV failure.\nStates: {tracker.states}"
    )
    assert "AnalysisCompleted" not in tracker.states, (
        f"BUG: the analysis completed although an engine failed.\n"
        f"States: {tracker.states}"
    )
    assert "SystemMustBeReset" not in tracker.states, (
        f"BUG: the AV failure must not lock the system.\nStates: {tracker.states}"
    )

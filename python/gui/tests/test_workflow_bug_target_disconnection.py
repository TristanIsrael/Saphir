"""C.2 — Target disconnection during copy: the copy is held and auto-resumes (8.6).

Scenario:
  nominal cycle up to CopyCleanFiles -> detach target -> the copy is HELD
  (the system STAYS in CopyCleanFiles, no reset) -> re-attach the same
  target -> coherence check -> the copy auto-resumes -> SystemMustBeReset.

Before 8.6 the target disconnection during the copy led straight to
SystemMustBeReset (data loss); the copy is now paused and resumed when
the same target is re-inserted.
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

NB_FILES = 40


def _count_target_files(target_dir):
    return len(
        [
            f
            for f in os.listdir(target_dir)
            if os.path.isfile(os.path.join(target_dir, f))
        ]
    )


def _wait_for_partial_copy(target_dir, timeout=120.0):
    """Wait until at least one file is copied and the copy is not finished."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        count = _count_target_files(target_dir)
        if 0 < count < NB_FILES:
            return True
        time.sleep(0.2)
    return False


@pytest.fixture
def bug_env():
    """Same setup as C.1 (emulator + 2 mock AVs + Saphir app)."""
    tmp = tempfile.mkdtemp(prefix="saphir_bug_")
    source_dir = os.path.join(tmp, "source")
    os.makedirs(source_dir, exist_ok=True)

    # Enough content that the copy phase lasts a few seconds: the test
    # must be able to unplug the target while the copy is in progress.
    filler = "x" * 30_000_000
    for i in range(NB_FILES):
        with open(os.path.join(source_dir, f"file_{i:02d}.txt"), "w") as f:
            f.write(f"content {i} " + filler)

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


def test_target_disconnection_during_copy_holds_and_resumes(bug_env):
    """8.6: the target is removed during the copy.

    The copy must be held (the system stays in CopyCleanFiles, no reset),
    and it must auto-resume when the same target is re-inserted.
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
    assert tracker.wait_for("AnalysisCompleted", timeout=180), (
        f"Analysis never completed.\nStates: {tracker.states}"
    )

    # 3. Target disk -> copy starts
    em.attach_disk("disk1", target_dir)
    assert tracker.wait_for("CopyCleanFiles", timeout=60), (
        f"Copy never started.\nStates: {tracker.states}"
    )
    copy_started_at = tracker.states.index("SystemState.CopyCleanFiles")

    # Wait until some files are copied but the copy is not finished
    assert _wait_for_partial_copy(target_dir), (
        f"Never observed a partial copy.\nStates: {tracker.states}"
    )

    # 4. User removes the target disk during the copy
    em.detach_disk("disk1")

    # 5. The copy is held: the system stays in CopyCleanFiles, no reset
    time.sleep(3)
    assert "SystemState.SystemMustBeReset" not in tracker.states[copy_started_at:], (
        f"BUG: the system asked for a reset after the target disconnection.\n"
        f"States: {tracker.states}"
    )
    assert tracker.states[-1] == "SystemState.CopyCleanFiles", (
        f"BUG: the system left CopyCleanFiles while the target is "
        f"disconnected (the copy should be held).\nStates: {tracker.states}"
    )

    # 6. The user re-inserts the same target disk
    em.attach_disk("disk1", target_dir)

    # 7. The coherence check passes and the copy auto-resumes: the cycle
    # continues to the end (all files copied, report, reset required).
    assert tracker.wait_for("SystemMustBeReset", timeout=240), (
        f"Copy never resumed/completed after the target reconnection.\n"
        f"States: {tracker.states}"
    )

    # The resume re-copied the remaining files (the target also holds the
    # scan report and the journal, so check the source files by name)
    target_files = set(os.listdir(target_dir))
    missing = {f"file_{i:02d}.txt" for i in range(NB_FILES)} - target_files
    assert not missing, (
        f"BUG: {len(missing)}/{NB_FILES} source files missing on the target "
        f"after the resume. First missing: {sorted(missing)[:3]}"
    )

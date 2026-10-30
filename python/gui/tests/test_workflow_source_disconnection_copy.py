"""8.6 — Source/target disconnection during the copy: the copy is held and auto-resumes.

Scenario:
  attach source -> analysis -> attach target -> CopyCleanFiles ->
  detach the source mid-copy -> the copy is HELD (the system STAYS in
  CopyCleanFiles, no reset, no re-analysis) ->
  re-attach the same source -> coherence check -> the copy auto-resumes
  -> GeneratingReport -> SystemMustBeReset.

A second scenario re-attaches a DIFFERENT disk: the coherence check
fails and the system asks for a reset (NFR-4, I6).
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


def _wait_for_partial_copy(target_dir, timeout=60.0):
    """Wait until at least one file is copied and the copy is not finished."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        count = _count_target_files(target_dir)
        if 0 < count < NB_FILES:
            return True
        time.sleep(0.2)
    return False


@pytest.fixture
def copy_disc_env():
    """Emulator + 2 mock AVs + Saphir app, with a source of many files."""
    tmp = tempfile.mkdtemp(prefix="saphir_copydisc_")
    source_dir = os.path.join(tmp, "source")
    os.makedirs(source_dir, exist_ok=True)
    # Enough content that the copy phase lasts a few seconds: the test
    # must be able to unplug the source while the copy is in progress.
    filler = "x" * 30_000_000
    for i in range(NB_FILES):
        with open(os.path.join(source_dir, f"file_{i:02d}.txt"), "w") as f:
            f.write(f"content {i} " + filler)

    # A different disk (different content) for the NFR-4 scenario
    source2_dir = os.path.join(tmp, "source2")
    os.makedirs(source2_dir, exist_ok=True)
    for i in range(5):
        with open(os.path.join(source2_dir, f"other_{i:04d}.txt"), "w") as f:
            f.write(f"other content {i}")

    target_dir = os.path.join(tmp, "target")
    os.makedirs(target_dir, exist_ok=True)

    em = Emulator(
        profile=default_profile(),
        source_disks={},
        storage_path=os.path.join(tmp, "repo"),
        destination_disk_path=target_dir,
    )
    em.start()

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

    yield em, tracker, source_dir, source2_dir, target_dir

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


def _drive_to_copy(em, tracker, source_dir, target_dir):
    """Boot, analyze the source and start the copy. Returns the copy start index."""
    assert tracker.wait_for("SystemReady", timeout=30), (
        f"App never reached SystemReady.\nStates: {tracker.states}"
    )

    em.attach_disk("disk0", source_dir)
    assert tracker.wait_for("SystemAnalysisRunning", timeout=30), (
        f"Analysis never started.\nStates: {tracker.states}"
    )
    assert tracker.wait_for("AnalysisCompleted", timeout=180), (
        f"Analysis never completed.\nStates: {tracker.states}"
    )

    em.attach_disk("disk1", target_dir)
    assert tracker.wait_for("CopyCleanFiles", timeout=60), (
        f"Copy never started.\nStates: {tracker.states}"
    )
    return tracker.states.index("SystemState.CopyCleanFiles")


def test_source_disconnection_during_copy_holds_and_resumes(copy_disc_env):
    """8.6: unplug the source during the copy.

    The copy must be held (no reset, the system stays in CopyCleanFiles),
    and it must auto-resume when the same source is re-inserted.
    """
    em, tracker, source_dir, _source2_dir, target_dir = copy_disc_env

    copy_started_at = _drive_to_copy(em, tracker, source_dir, target_dir)

    # Wait until some files are copied but the copy is not finished
    assert _wait_for_partial_copy(target_dir), (
        f"Never observed a partial copy.\nStates: {tracker.states}"
    )
    copied_before = _count_target_files(target_dir)

    # The user unplugs the source by mistake
    em.detach_disk("disk0")

    # The copy is held: the system stays in CopyCleanFiles, no reset
    time.sleep(3)
    assert "SystemState.SystemMustBeReset" not in tracker.states[copy_started_at:], (
        f"BUG: the system asked for a reset after the source disconnection.\n"
        f"States: {tracker.states}"
    )
    assert tracker.states[-1] == "SystemState.CopyCleanFiles", (
        f"BUG: the system left CopyCleanFiles while the source is "
        f"disconnected (the copy should be held).\nStates: {tracker.states}"
    )

    # The user re-inserts the same source disk
    em.attach_disk("disk0", source_dir)

    # The coherence check passes and the copy auto-resumes: the cycle
    # continues to the end (all files copied, report, reset required).
    assert tracker.wait_for("SystemMustBeReset", timeout=240), (
        f"Copy never resumed/completed after the source reconnection.\n"
        f"States: {tracker.states}"
    )

    # The resume re-copied the remaining files (the target also holds the
    # scan report and the journal, so check the source files by name)
    target_files = set(os.listdir(target_dir))
    missing = {f"file_{i:02d}.txt" for i in range(NB_FILES)} - target_files
    assert not missing, (
        f"BUG: {len(missing)}/{NB_FILES} source files missing on the target "
        f"after the resume ({copied_before} were copied before the "
        f"disconnection). First missing: {sorted(missing)[:3]}"
    )


def test_different_disk_during_copy_pause_requires_reset(copy_disc_env):
    """NFR-4/I6: a different disk is re-inserted while the copy is paused.

    The coherence check fails and the system asks for a reset.
    """
    em, tracker, source_dir, source2_dir, target_dir = copy_disc_env

    copy_started_at = _drive_to_copy(em, tracker, source_dir, target_dir)

    assert _wait_for_partial_copy(target_dir), (
        f"Never observed a partial copy.\nStates: {tracker.states}"
    )

    # The user unplugs the source...
    em.detach_disk("disk0")
    time.sleep(2)

    # ...and re-inserts a DIFFERENT disk
    em.attach_disk("disk2", source2_dir)

    # The coherence check fails: reset required
    assert tracker.wait_for("SystemMustBeReset", timeout=30), (
        f"SystemMustBeReset never requested after the different disk.\n"
        f"States: {tracker.states}"
    )
    assert "SystemState.GeneratingReport" not in tracker.states[copy_started_at:], (
        f"BUG: the copy resumed on a different disk.\nStates: {tracker.states}"
    )

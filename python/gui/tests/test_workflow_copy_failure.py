"""F4 — Individual copy failure: the copy continues and the final check reports it.

Scenario:
  attach source -> analysis -> one source file is lost before the copy
  (simulating an I/O failure) -> attach target -> CopyCleanFiles ->
  the failed file is reported by the platform on events/error ->
  the copy continues on the other files -> the final check detects
  copied != clean -> the cycle still completes (report lists the
  failure) -> SystemMustBeReset.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src" / "Saphir"))
sys.path.insert(
    0, str(Path(__file__).resolve().parent.parent.parent / "libsaphir" / "src")
)

from safecor_emulator import Emulator, default_profile

from tests.mock_av_manager import MockAVManager
from tests.test_workflow_nominal import StateTracker

NB_FILES = 5
LOGFILE = os.path.join(tempfile.gettempdir(), "saphir.log")


@pytest.fixture
def copy_fail_env():
    """Emulator + 2 mock AVs + Saphir app, with a source of a few files."""
    tmp = tempfile.mkdtemp(prefix="saphir_copyfail_")
    source_dir = os.path.join(tmp, "source")
    os.makedirs(source_dir, exist_ok=True)
    for i in range(NB_FILES):
        with open(os.path.join(source_dir, f"file_{i:02d}.txt"), "w") as f:
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

    # Only the log lines written during this test are asserted on
    try:
        log_offset = os.path.getsize(LOGFILE)
    except OSError:
        log_offset = 0

    yield em, tracker, source_dir, target_dir, log_offset

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


def _new_log_lines(offset: int) -> str:
    try:
        with open(LOGFILE, "r", errors="replace") as f:
            f.seek(offset)
            return f.read()
    except OSError:
        return ""


def test_copy_failure_completes_with_final_check(copy_fail_env):
    """F4: one copy fails -> the copy continues, the final check reports
    the discrepancy and the cycle completes."""
    em, tracker, source_dir, target_dir, log_offset = copy_fail_env

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

    # Simulate the I/O failure: the file is lost on the source before the
    # copy starts, so the platform cannot copy it
    lost_file = os.path.join(source_dir, "file_02.txt")
    os.remove(lost_file)

    em.attach_disk("disk1", target_dir)
    assert tracker.wait_for("CopyCleanFiles", timeout=60), (
        f"Copy never started.\nStates: {tracker.states}"
    )

    # The copy of the other files must continue and the cycle must complete
    assert tracker.wait_for("SystemMustBeReset", timeout=180), (
        f"The cycle never completed after the copy failure.\nStates: {tracker.states}"
    )

    # The clean files except the lost one are on the target
    target_files = set(os.listdir(target_dir))
    missing = (
        {f"file_{i:02d}.txt" for i in range(NB_FILES)} - {"file_02.txt"} - target_files
    )
    assert not missing, (
        f"BUG: clean files missing on the target after the copy failure: "
        f"{sorted(missing)}"
    )
    assert "file_02.txt" not in target_files

    # The final check reported the discrepancy
    log = _new_log_lines(log_offset)
    assert "Copy final check failed" in log, (
        f"BUG: the copy final check did not report the failure.\nLog:\n{log[-2000:]}"
    )
    assert "4 file(s) copied for 5 clean file(s), 1 failure(s)" in log, (
        f"BUG: unexpected final check count.\nLog:\n{log[-2000:]}"
    )

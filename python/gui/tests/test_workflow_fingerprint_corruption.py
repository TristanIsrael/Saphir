"""C.4 — NFR-1 end-to-end: a file altered in the repository is not copied.

Scenario:
  - 2 files on the source disk: one clean, one corrupted in the repository
    by the mock AVs right after the analysis request (simulating a file
    altered between the NEW_FILE fingerprint and the AV integrity check).
  - The integrity check must reject the corrupted file (fingerprint_error
    response -> FileAnalysisError) and the copy phase must exclude it from
    the target disk.

If the NFR-1 check were skipped (e.g. wrong repository path in DEVMODE),
the mock AVs would report the corrupted file as clean and it would be
copied to the target: the test fails.
"""

import os
import shutil
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


@pytest.fixture
def corruption_env():
    """Starts emulator + 2 mock AVs (with NFR-1 verification) + Saphir app."""
    tmp = tempfile.mkdtemp(prefix="saphir_corrupt_")
    source_dir = os.path.join(tmp, "source")
    os.makedirs(source_dir, exist_ok=True)

    with open(os.path.join(source_dir, "good.txt"), "w") as f:
        f.write("clean content")
    with open(os.path.join(source_dir, "bad.txt"), "w") as f:
        f.write("content that will be corrupted in the repository")

    target_dir = os.path.join(tmp, "target")
    os.makedirs(target_dir, exist_ok=True)

    repo_path = os.path.join(tmp, "repo")

    em = Emulator(
        profile=default_profile(),
        source_disks={},
        storage_path=repo_path,
        destination_disk_path=target_dir,
    )
    em.start()

    # Both AVs verify the repository files (NFR-1) and corrupt the bad file
    # on analysis request, before their integrity check runs.
    av1 = MockAVManager("mock-clam", repository_path=repo_path, corrupt={"/bad.txt"})
    av2 = MockAVManager("mock-eset", repository_path=repo_path, corrupt={"/bad.txt"})
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
    shutil.rmtree(tmp, ignore_errors=True)


def test_corrupted_file_not_copied(corruption_env):
    """The corrupted file is rejected by NFR-1 and excluded from the target."""
    em, tracker, source_dir, target_dir = corruption_env

    assert tracker.wait_for("SystemReady", timeout=30), (
        f"App never reached SystemReady.\nStates seen: {tracker.states}"
    )

    em.attach_disk("disk0", source_dir)

    assert tracker.wait_for("SystemAnalysisRunning", timeout=30), (
        f"Analysis never started.\nStates seen: {tracker.states}"
    )

    # Analysis must complete: the corrupted file is rejected (FileAnalysisError,
    # counted like an infected file) and the clean file is analyzed normally.
    assert tracker.wait_for("AnalysisCompleted", timeout=30), (
        f"Analysis never completed (the corrupted file should be rejected,\n"
        f"not block the analysis).\nStates seen: {tracker.states}"
    )

    em.attach_disk("disk1", target_dir)

    assert tracker.wait_for("SystemMustBeReset", timeout=60), (
        f"Never reached SystemMustBeReset.\nStates seen: {tracker.states}"
    )

    # The clean file was copied...
    assert os.path.exists(os.path.join(target_dir, "good.txt")), (
        "Clean file was not copied to the target."
    )
    # ...and the corrupted file must NOT be.
    assert not os.path.exists(os.path.join(target_dir, "bad.txt")), (
        "Corrupted file was copied to the target: the NFR-1 integrity check "
        "did not run or did not reject the file."
    )

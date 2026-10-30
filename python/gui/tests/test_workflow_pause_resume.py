"""F3 — Pause/resume during the analysis without re-analyzing processed files.

Scenario:
  attach source -> analysis -> the analysis is paused (user stop) while
  some files are still in flight -> the analysis is resumed (user start)
  -> the files already analyzed are NOT re-analyzed (F3), the interrupted
  files are picked up again -> AnalysisCompleted -> copy -> reset.

The pause/resume is driven through a command file (SAPHIR_TEST_CMD) that
the test app entry point watches, like the GUI button would.

Observation: each mock AV logs every analysis request it receives
("<epoch> <component> <filepath>"). A file already analyzed before the
pause must not receive a new analysis request after the resume.
"""

import os
import re
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

NB_FILES = 3
SCAN_DELAY = 2.0


class CmdStateTracker(StateTracker):
    """StateTracker that also collects TEST_EVENT/TEST_CMD lines."""

    _LINE_RE = re.compile(r"TEST_(?:EVENT|CMD)\s+(\w+)(?:\s+(\S+))?")

    def __init__(self, process):
        super().__init__(process)
        self.lines: list[tuple[str, str]] = []

    def _read(self):
        for line in iter(self._process.stdout.readline, b""):
            s = line.decode(errors="replace")
            m = self._STATE_RE.search(s)
            if m:
                self.states.append(m.group(1))
            e = self._LINE_RE.search(s)
            if e:
                self.lines.append((e.group(1), e.group(2) or ""))

    def wait_for_state_after(
        self, state_name: str, idx: int, timeout: float = 30.0
    ) -> bool:
        """Wait for state_name to appear in states after position idx."""
        target = f"SystemState.{state_name}"
        deadline = time.time() + timeout
        while time.time() < deadline:
            for i in range(idx, len(self.states)):
                if self.states[i] == target:
                    return True
            if self._process.poll() is not None:
                return False
            time.sleep(0.1)
        return False


@pytest.fixture
def pause_env():
    """Emulator + 2 slow mock AVs + Saphir app with a pause/resume command file."""
    tmp = tempfile.mkdtemp(prefix="saphir_pause_")
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
    # Slow scans: the pause lands while the analysis is in progress.
    # The request logs make the F3 property observable.
    av1_log = os.path.join(tmp, "av1_requests.log")
    av2_log = os.path.join(tmp, "av2_requests.log")
    av1 = MockAVManager(
        "mock-clam",
        scan_delay=SCAN_DELAY,
        repository_path=repo_path,
        request_log=av1_log,
    )
    av2 = MockAVManager(
        "mock-eset",
        scan_delay=SCAN_DELAY,
        repository_path=repo_path,
        request_log=av2_log,
    )
    av1.start()
    av2.start()

    gui_dir = Path(__file__).resolve().parent.parent
    python = sys.executable
    entry = Path(__file__).resolve().parent / "test_app_entry.py"
    cmd_file = os.path.join(tmp, "cmd")
    env = os.environ.copy()
    env["DEVMODE"] = "1"
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["SAPHIR_TEST_CMD"] = cmd_file
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

    tracker = CmdStateTracker(app_proc)
    tracker.start()

    yield em, tracker, source_dir, target_dir, repo_path, av1_log, av2_log, cmd_file

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


def _send_command(cmd_file: str, cmd: str) -> str:
    nonce = f"{time.time()}"
    with open(cmd_file, "w") as f:
        f.write(f"{cmd}:{nonce}")
    return nonce


def _read_request_logs(*logs) -> list[tuple[float, str, str]]:
    entries = []
    for log in logs:
        try:
            with open(log) as f:
                for line in f:
                    parts = line.split()
                    if len(parts) == 3:
                        entries.append((float(parts[0]), parts[1], parts[2]))
        except OSError:
            pass
    return entries


def _repo_file_count(repo_path: str) -> int:
    try:
        return len(
            [
                f
                for f in os.listdir(repo_path)
                if os.path.isfile(os.path.join(repo_path, f))
            ]
        )
    except OSError:
        return 0


def test_pause_resume_does_not_reanalyze_completed_files(pause_env):
    """F3: pause the analysis mid-way, resume it.

    The files already analyzed keep their status and are NOT re-analyzed;
    the interrupted files are picked up again and the cycle completes.
    """
    (
        em,
        tracker,
        source_dir,
        target_dir,
        repo_path,
        av1_log,
        av2_log,
        cmd_file,
    ) = pause_env

    assert tracker.wait_for("SystemReady", timeout=30), (
        f"App never reached SystemReady.\nStates: {tracker.states}"
    )

    em.attach_disk("disk0", source_dir)
    assert tracker.wait_for("SystemAnalysisRunning", timeout=30), (
        f"Analysis never started.\nStates: {tracker.states}"
    )

    # Wait until the analysis is clearly in progress: first all the files
    # are in the repository (the copy happened), then at least one of
    # them has been analyzed (its repository slot is freed when the
    # analysis of the file is finished). The copy is instantaneous
    # compared to the scan delay, so the files that are NOT in the
    # repository at the pause moment are exactly the files already
    # analyzed before the pause.
    deadline = time.time() + 60
    while time.time() < deadline and _repo_file_count(repo_path) != NB_FILES:
        time.sleep(0.2)
    assert _repo_file_count(repo_path) == NB_FILES, (
        f"The files were never all copied in the repository.\n"
        f"Repo count: {_repo_file_count(repo_path)}\nStates: {tracker.states}"
    )
    deadline = time.time() + 60
    while time.time() < deadline and _repo_file_count(repo_path) == NB_FILES:
        time.sleep(0.2)
    assert _repo_file_count(repo_path) < NB_FILES, (
        f"Never observed an analyzed file before the pause.\n"
        f"Repo count: {_repo_file_count(repo_path)}\nStates: {tracker.states}"
    )

    # The user pauses the analysis
    t_pause = time.time()
    repo_at_pause = set(os.listdir(repo_path)) if os.path.isdir(repo_path) else set()
    _send_command(cmd_file, "pause")
    assert tracker.wait_for("SystemWaitingForUserAction", timeout=30), (
        f"Pause never registered.\nStates: {tracker.states}"
    )

    # Files whose slot was freed before the pause: analyzed before the
    # pause, the F3 property applies to them (no new analysis request
    # after the resume). The other files (still in the repository) were
    # interrupted and must be picked up again.
    all_files = {f"file_{i:02d}.txt" for i in range(NB_FILES)}
    analyzed_before = all_files - repo_at_pause
    assert analyzed_before, (
        f"BUG: no file was analyzed before the pause, the test cannot "
        f"verify the F3 property.\nRepo: {repo_at_pause}\nStates: {tracker.states}"
    )

    # Give the in-flight scans time to finish before the resume
    time.sleep(SCAN_DELAY + 2.0)

    # The user resumes the analysis
    states_before = len(tracker.states)
    _send_command(cmd_file, "resume")
    assert tracker.wait_for_state_after("SystemAnalysisRunning", states_before, 30), (
        f"Resume never registered.\nStates: {tracker.states}\nLines: {tracker.lines}"
    )

    # The interrupted files are picked up and the analysis completes
    assert tracker.wait_for("AnalysisCompleted", timeout=120), (
        f"Analysis never completed after the resume.\nStates: {tracker.states}\n"
        f"Lines: {tracker.lines}"
    )

    # F3: the files already analyzed before the pause are NOT re-analyzed:
    # no analysis request for them after the pause.
    for log_time, _component, filepath in _read_request_logs(av1_log, av2_log):
        name = os.path.basename(filepath)
        if name in analyzed_before:
            assert log_time < t_pause, (
                f"BUG: {name} was analyzed before the pause but received a "
                f"new analysis request after the resume (F3 violation).\n"
                f"t_pause={t_pause:.1f}, request at {log_time:.1f}"
            )

    # The interrupted files (still in the repository at the pause) were
    # picked up by the resume: either re-requested for analysis, or
    # completed by the in-flight scans that finished just after the pause
    # (their results are still counted). In both cases they must reach a
    # final state, which is guaranteed by AnalysisCompleted below (it only
    # fires when clean + infected == queue size).

    # The cycle continues to the copy and the reset
    em.attach_disk("disk1", target_dir)
    assert tracker.wait_for("SystemMustBeReset", timeout=180), (
        f"The cycle never completed.\nStates: {tracker.states}\nLines: {tracker.lines}"
    )
    target_files = set(os.listdir(target_dir))
    missing = {f"file_{i:02d}.txt" for i in range(NB_FILES)} - target_files
    assert not missing, (
        f"BUG: files missing on the target after the pause/resume: {sorted(missing)}"
    )

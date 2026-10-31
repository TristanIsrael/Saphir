"""Phase 12 (12.1, 12.2, 12.4, 12.6) - QML binding tests.

The real ``MainScreen.qml`` is loaded offscreen in a subprocess
(``test_qml_bindings_runner.py``) against a fake ``ApplicationController``
that exposes the same properties, signals and models as the real one. The
tests drive the fake controller and assert the declarative bindings:

- 12.1: panel visibility for every ``SystemState``
- 12.2: ``Bindings.qml`` derived properties (state color, status, counts)
- 12.4: ``AnalysisPanel`` state transitions (start button, ETA, alert)
- 12.6: ``SystemLoadingPanel`` progression (step circles, title, opacity)
"""

import contextlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

_GUI_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_GUI_DIR / "src" / "Saphir"))
sys.path.insert(0, str(_GUI_DIR.parent / "libsaphir" / "src"))

from Saphir.enums import SystemState


class QmlClient:
    """JSON-line client of the QML runner subprocess."""

    def __init__(self, proc: subprocess.Popen):
        self.proc = proc

    def _read_json(self) -> dict:
        """Read the next JSON line, skipping stray non-JSON prints.

        The runner imports ``libsaphir`` which prints a DEVMODE banner to
        stdout at import time; the protocol lines are the only JSON lines.
        """
        while True:
            line = self.proc.stdout.readline()
            if not line:
                raise RuntimeError(
                    "QML runner exited unexpectedly "
                    f"(rc={self.proc.poll()}, "
                    f"stderr={self.proc.stderr.read().decode()[:2000]})"
                )
            text = line.decode().strip()
            if not text.startswith("{"):
                continue
            return json.loads(text)

    def send(self, cmd: dict) -> dict:
        self.proc.stdin.write((json.dumps(cmd) + "\n").encode())
        self.proc.stdin.flush()
        return self._read_json()

    def set(self, **props):
        result = self.send({"op": "set", "props": props})
        assert result["status"] == "ok", result

    def get(self, ref: str):
        result = self.send({"op": "get", "ref": ref})
        assert result["status"] == "ok", result
        return result["value"]

    def wait(self, ref: str, cond: str, value, timeout_ms: int = 3000):
        result = self.send(
            {
                "op": "wait",
                "ref": ref,
                "cond": cond,
                "value": value,
                "timeout_ms": timeout_ms,
            }
        )
        assert result["status"] == "ok", (
            f"timeout waiting for {ref} {cond} {value} ({result})"
        )


@pytest.fixture(scope="module")
def qml():
    """Starts the QML runner subprocess and yields a connected client."""
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    # Empty (not "0"): libsaphir treats any non-empty DEVMODE string as True
    env["DEVMODE"] = ""
    env["PYTHONPATH"] = os.pathsep.join(
        [
            str(_GUI_DIR / "src" / "Saphir"),
            str(_GUI_DIR.parent / "libsaphir" / "src"),
            env.get("PYTHONPATH", ""),
        ]
    )

    proc = subprocess.Popen(
        [
            sys.executable,
            "-u",
            str(Path(__file__).parent / "test_qml_bindings_runner.py"),
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        cwd=str(_GUI_DIR),
    )

    client = QmlClient(proc)
    ready = client._read_json()
    assert ready["status"] == "ready", ready

    yield client

    with contextlib.suppress(Exception):
        client.send({"op": "quit"})
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()


def _reset(qml, **overrides):
    """Brings the fake controller to a known baseline, then applies overrides."""
    props = {
        "ready": True,
        "analysisReady": True,
        "systemState": SystemState.SystemReady.value,
        "sourceName": "/mnt/usb0",
        "cleanFilesCount": 0,
        "infectedFilesCount": 0,
        "queueSize": 0,
        "systemLoadingProgress": 1.0,
        "sourceDisconnected": False,
        "copyPaused": False,
    }
    props.update(overrides)
    qml.set(**props)


# --- 12.1: panel visibility ---------------------------------------------


@pytest.mark.parametrize(
    ("state", "overrides", "expected"),
    [
        # Boot states: the loading panel is shown (opacity, no animation on
        # the others), no main panel
        (
            SystemState.SystemInactive,
            {"ready": False, "analysisReady": False, "sourceName": ""},
            {
                "pnlLoading": True,
                "pnlFileSelection": False,
                "pnlAnalysis": False,
                "pnlFilesCopy": False,
                "dlgSystemMustBeReset": False,
                "dlgConnectStorage": False,
            },
        ),
        (
            SystemState.SystemStarting,
            {"ready": False, "analysisReady": False, "sourceName": ""},
            {
                "pnlLoading": True,
                "pnlFileSelection": False,
                "pnlAnalysis": False,
                "pnlFilesCopy": False,
                "dlgSystemMustBeReset": False,
                "dlgConnectStorage": False,
            },
        ),
        (
            SystemState.SafecorReady,
            {"ready": False, "analysisReady": False, "sourceName": ""},
            {
                "pnlLoading": True,
                "pnlFileSelection": False,
                "pnlAnalysis": False,
                "pnlFilesCopy": False,
                "dlgSystemMustBeReset": False,
                "dlgConnectStorage": False,
            },
        ),
        # Resetting: loading panel shown, must-be-reset dialog closed
        (
            SystemState.SystemResetting,
            {"ready": False, "analysisReady": False},
            {
                "pnlLoading": True,
                "pnlFileSelection": False,
                "pnlAnalysis": False,
                "pnlFilesCopy": False,
                "dlgSystemMustBeReset": False,
            },
        ),
        # Ready with no source: the "plug a media" dialog is shown
        (
            SystemState.SystemReady,
            {"sourceName": ""},
            {
                "pnlLoading": False,
                "pnlFileSelection": False,
                "pnlAnalysis": False,
                "pnlFilesCopy": False,
                "dlgConnectStorage": True,
            },
        ),
        # Ready with a source: the file selection panel is shown
        (
            SystemState.SystemReady,
            {},
            {
                "pnlLoading": False,
                "pnlFileSelection": True,
                "pnlAnalysis": False,
                "pnlFilesCopy": False,
                "dlgConnectStorage": False,
            },
        ),
        (
            SystemState.SystemWaitingForUserAction,
            {},
            {
                "pnlLoading": False,
                "pnlFileSelection": True,
                "pnlAnalysis": False,
                "pnlFilesCopy": False,
            },
        ),
        (
            SystemState.SystemGettingFilesList,
            {},
            {
                "pnlLoading": False,
                "pnlFileSelection": True,
                "pnlAnalysis": False,
                "pnlFilesCopy": False,
            },
        ),
        # Analysis states
        (
            SystemState.SystemAnalysisRunning,
            {},
            {
                "pnlLoading": False,
                "pnlFileSelection": False,
                "pnlAnalysis": True,
                "pnlFilesCopy": False,
            },
        ),
        (
            SystemState.AnalysisCompleted,
            {},
            {
                "pnlLoading": False,
                "pnlFileSelection": False,
                "pnlAnalysis": True,
                "pnlFilesCopy": False,
            },
        ),
        # Copy / report states
        (
            SystemState.CopyCleanFiles,
            {},
            {
                "pnlLoading": False,
                "pnlFileSelection": False,
                "pnlAnalysis": False,
                "pnlFilesCopy": True,
            },
        ),
        (
            SystemState.GeneratingReport,
            {},
            {
                "pnlLoading": False,
                "pnlFileSelection": False,
                "pnlAnalysis": False,
                "pnlFilesCopy": True,
            },
        ),
        (
            SystemState.ReportFailed,
            {},
            {
                "pnlLoading": False,
                "pnlFileSelection": False,
                "pnlAnalysis": False,
                "pnlFilesCopy": True,
            },
        ),
        # Must-be-reset: the dedicated dialog is shown
        (
            SystemState.SystemMustBeReset,
            {},
            {
                "pnlLoading": False,
                "pnlFileSelection": False,
                "pnlAnalysis": False,
                "pnlFilesCopy": False,
                "dlgSystemMustBeReset": True,
            },
        ),
        # Shutting down: no panel at all
        (
            SystemState.SystemShuttingDown,
            {},
            {
                "pnlLoading": False,
                "pnlFileSelection": False,
                "pnlAnalysis": False,
                "pnlFilesCopy": False,
            },
        ),
    ],
)
def test_panel_visibility(qml, state, overrides, expected):
    _reset(qml, systemState=state.value, **overrides)
    # The loading panel fades with a 1 s opacity behavior: wait for the
    # animation to settle (visible is bound to opacity > 0)
    if expected["pnlLoading"]:
        qml.wait("pnlLoading.opacity", "gt", 0.9)
    else:
        qml.wait("pnlLoading.opacity", "eq", 0)
    for ref, visible in expected.items():
        assert qml.get(f"{ref}.visible") is visible, (
            f"{ref}.visible expected {visible} in state {state.name}"
        )


# --- 12.2: Bindings.qml derived properties --------------------------------


def test_state_color_not_ready_wins(qml):
    _reset(qml, ready=False, infectedFilesCount=2, cleanFilesCount=2)
    assert qml.get("bindings.systemStateColor") == qml.get("env.colorFilterNotReady")


def test_state_color_infected(qml):
    _reset(qml, ready=True, infectedFilesCount=2, cleanFilesCount=0)
    assert qml.get("bindings.systemStateColor") == qml.get("env.colorFilterInfected")


def test_state_color_used(qml):
    _reset(qml, ready=True, infectedFilesCount=0, cleanFilesCount=1)
    assert qml.get("bindings.systemStateColor") == qml.get("env.colorFilterUsed")


def test_state_color_ready(qml):
    _reset(qml, ready=True, infectedFilesCount=0, cleanFilesCount=0)
    assert qml.get("bindings.systemStateColor") == qml.get("env.colorFilterReady")


def test_state_color_infected_beats_used(qml):
    _reset(qml, ready=True, infectedFilesCount=2, cleanFilesCount=5)
    assert qml.get("bindings.systemStateColor") == qml.get("env.colorFilterInfected")


@pytest.mark.xfail(
    reason=(
        "D8 (open): a single infected file must flip the system to Dirty, "
        "but Bindings.qml uses 'infected: nbInfected > 1'"
    ),
)
def test_infected_with_a_single_infected_file(qml):
    _reset(qml, ready=True, infectedFilesCount=1, cleanFilesCount=0)
    assert qml.get("bindings.infected") is True


def test_counts(qml):
    _reset(qml, queueSize=10, cleanFilesCount=3, infectedFilesCount=2)
    assert qml.get("bindings.nbClean") == 3
    assert qml.get("bindings.nbInfected") == 2
    assert qml.get("bindings.nbWaiting") == 5
    assert qml.get("bindings.nbFinished") == 5


def test_analyzing_flag(qml):
    _reset(qml, systemState=SystemState.SystemAnalysisRunning.value)
    assert qml.get("bindings.analyzing") is True
    _reset(qml, systemState=SystemState.AnalysisCompleted.value)
    assert qml.get("bindings.analyzing") is False


def test_passthrough_flags(qml):
    _reset(qml, sourceDisconnected=True, copyPaused=True)
    assert qml.get("bindings.sourceDisconnected") is True
    assert qml.get("bindings.copyPaused") is True
    _reset(qml, sourceDisconnected=False, copyPaused=False)
    assert qml.get("bindings.sourceDisconnected") is False
    assert qml.get("bindings.copyPaused") is False


# --- 12.4: AnalysisPanel state transitions --------------------------------


def test_start_button_disabled_with_empty_queue(qml):
    _reset(qml, systemState=SystemState.SystemReady.value, queueSize=0)
    assert qml.get("btnStartStop.enabled") is False


def test_start_button_enabled_with_queue(qml):
    _reset(qml, systemState=SystemState.SystemReady.value, queueSize=5)
    assert qml.get("btnStartStop.enabled") is True


def test_start_button_disabled_after_analysis(qml):
    _reset(qml, systemState=SystemState.AnalysisCompleted.value, queueSize=5)
    assert qml.get("btnStartStop.enabled") is False


def test_start_button_disabled_when_not_analysis_ready(qml):
    _reset(
        qml,
        systemState=SystemState.SystemReady.value,
        queueSize=5,
        analysisReady=False,
    )
    assert qml.get("btnStartStop.enabled") is False


def test_start_button_icon_start(qml):
    _reset(qml, systemState=SystemState.SystemReady.value, queueSize=5)
    assert qml.get("btnStartStop.icon") == qml.get("constants.iconStart")


def test_start_button_icon_pause_when_analyzing(qml):
    _reset(qml, systemState=SystemState.SystemAnalysisRunning.value, queueSize=5)
    assert qml.get("btnStartStop.icon") == qml.get("constants.iconPause")


def test_progress_gauge_values(qml):
    _reset(
        qml,
        systemState=SystemState.SystemAnalysisRunning.value,
        queueSize=10,
        cleanFilesCount=4,
        infectedFilesCount=2,
    )
    assert qml.get("filesProgress.currentValue") == 6
    assert qml.get("filesProgress.maximumValue") == 10


def test_source_disconnection_alert(qml):
    _reset(
        qml,
        systemState=SystemState.SystemAnalysisRunning.value,
        sourceDisconnected=True,
    )
    assert qml.get("srcDisconnectedAlert.visible") is True
    _reset(
        qml,
        systemState=SystemState.SystemAnalysisRunning.value,
        sourceDisconnected=False,
    )
    assert qml.get("srcDisconnectedAlert.visible") is False
    # The alert is only shown while the analysis is running
    _reset(
        qml,
        systemState=SystemState.SystemReady.value,
        sourceDisconnected=True,
    )
    assert qml.get("srcDisconnectedAlert.visible") is False


# --- 12.6: SystemLoadingPanel progression ---------------------------------


def _show_loading(qml):
    _reset(
        qml,
        ready=False,
        analysisReady=False,
        systemState=SystemState.SystemStarting.value,
    )
    qml.wait("pnlLoading.opacity", "gt", 0.9)
    assert qml.get("pnlLoading.visible") is True


def test_loading_panel_shown_while_not_ready(qml):
    _show_loading(qml)
    assert qml.get("pnlLoading.big") is True


def test_loading_panel_hidden_when_ready(qml):
    _show_loading(qml)
    _reset(
        qml,
        ready=True,
        analysisReady=True,
        systemState=SystemState.SystemReady.value,
    )
    qml.wait("pnlLoading.opacity", "eq", 0)
    assert qml.get("pnlLoading.visible") is False


def test_loading_steps_at_start(qml):
    _show_loading(qml)
    qml.set(systemLoadingProgress=0.15)
    clean = qml.get("env.colorClean")
    waiting = qml.get("env.colorWaiting")
    assert qml.get("circleBegin.color") == clean
    assert qml.get("circleCore.color") == waiting
    assert qml.get("circleAv.color") == waiting
    assert qml.get("circleReady.color") == waiting


def test_loading_steps_at_core(qml):
    _show_loading(qml)
    qml.set(systemLoadingProgress=0.5)
    clean = qml.get("env.colorClean")
    waiting = qml.get("env.colorWaiting")
    assert qml.get("circleCore.color") == clean
    assert qml.get("circleAv.color") == waiting
    assert qml.get("circleReady.color") == waiting


def test_loading_steps_at_complete(qml):
    _show_loading(qml)
    qml.set(systemLoadingProgress=1.0)
    clean = qml.get("env.colorClean")
    assert qml.get("circleCore.color") == clean
    assert qml.get("circleAv.color") == clean
    assert qml.get("circleReady.color") == clean


def test_loading_title_starting(qml):
    _show_loading(qml)
    assert qml.get("loadingTitle.text") == "Starting..."


def test_loading_title_cleaning_when_resetting(qml):
    _show_loading(qml)
    qml.set(systemState=SystemState.SystemResetting.value)
    assert qml.get("loadingTitle.text") == "Cleaning..."


def test_loading_panel_compact_outside_boot_states(qml):
    # Outside SystemInactive/SystemStarting/SystemResetting the panel keeps
    # its small 60 px form even while fading
    _reset(
        qml,
        ready=False,
        analysisReady=False,
        systemState=SystemState.SystemReady.value,
    )
    qml.wait("pnlLoading.opacity", "gt", 0.9)
    assert qml.get("pnlLoading.big") is False

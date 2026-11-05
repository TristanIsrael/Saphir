"""Single state authority for the system workflow with transition validation."""

import time
from typing import ClassVar

from libsaphir import DEVMODE
from PySide6.QtCore import QObject, Signal

from .enums import SystemState

_STATE_DUMP_FILE = "/tmp/saphir_state.log"


class WorkflowController(QObject):
    """Single authority for SystemState transitions.

    All state changes must go through `transition_to()`.
    """

    systemStateChanged = Signal(int)

    _VALID_TRANSITIONS: ClassVar[dict[SystemState, set[SystemState]]] = {
        SystemState.SystemInactive: {SystemState.SystemStarting},
        SystemState.SystemStarting: {SystemState.SafecorReady},
        SystemState.SafecorReady: {SystemState.SystemReady},
        SystemState.SystemReady: {
            SystemState.SystemGettingFilesList,
            SystemState.SystemMustBeReset,
            SystemState.SystemShuttingDown,
        },
        SystemState.SystemGettingFilesList: {
            SystemState.SystemWaitingForUserAction,
            SystemState.SystemAnalysisRunning,
            SystemState.SystemShuttingDown,
        },
        SystemState.SystemWaitingForUserAction: {
            SystemState.SystemAnalysisRunning,
            SystemState.SystemGettingFilesList,
            SystemState.SystemResetting,
            SystemState.SystemShuttingDown,
        },
        SystemState.SystemAnalysisRunning: {
            SystemState.AnalysisCompleted,
            SystemState.SystemWaitingForUserAction,
            SystemState.SystemShuttingDown,
        },
        SystemState.AnalysisCompleted: {
            SystemState.CopyCleanFiles,
            SystemState.SystemResetting,
            SystemState.SystemShuttingDown,
        },
        SystemState.CopyCleanFiles: {
            SystemState.GeneratingReport,
            SystemState.SystemMustBeReset,
            SystemState.SystemShuttingDown,
        },
        SystemState.GeneratingReport: {
            SystemState.SystemMustBeReset,
            SystemState.ReportFailed,
            SystemState.SystemShuttingDown,
        },
        SystemState.ReportFailed: {
            SystemState.SystemResetting,
            SystemState.SystemShuttingDown,
        },
        SystemState.SystemMustBeReset: {
            SystemState.SystemResetting,
            SystemState.SystemShuttingDown,
        },
        SystemState.SystemResetting: {
            SystemState.SystemReady,
            SystemState.SystemShuttingDown,
        },
        SystemState.SystemShuttingDown: set(),
    }

    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self._state = SystemState.SystemStarting
        if DEVMODE:
            open(_STATE_DUMP_FILE, "w").close()

    def _dump_state(self, event: str):
        if DEVMODE:
            with open(_STATE_DUMP_FILE, "a") as f:
                f.write(f"{time.time():.3f} {event} {self._state.name}\n")

    @property
    def state(self) -> SystemState:
        """Return the current workflow state."""
        return self._state

    def can_transition(self, to: SystemState) -> bool:
        """Return whether a transition to the given state is valid."""
        allowed = self._VALID_TRANSITIONS.get(self._state, set())
        return to in allowed

    def transition_to(self, to: SystemState) -> bool:
        """Validate and apply a state transition, returning whether it was accepted."""
        if not self.can_transition(to):
            print(f"[WorkflowController] BLOCKED: {self._state.name} -> {to.name}")
            if DEVMODE:
                with open(_STATE_DUMP_FILE, "a") as f:
                    f.write(
                        f"{time.time():.3f} BLOCKED {self._state.name} -> {to.name}\n"
                    )
            return False

        self._state = to
        print(f"[WorkflowController] {self._state.name}")
        self._dump_state("TRANSITION")
        self.systemStateChanged.emit(self._state.value)
        return True

    def force_state(self, state: SystemState):
        """Set state without validation. Use only for initialization or reset."""
        self._state = state
        self._dump_state("FORCE")
        self.systemStateChanged.emit(self._state.value)

    def is_in_states(self, states: set[SystemState]) -> bool:
        """Return whether the current state is one of the given states."""
        return self._state in states

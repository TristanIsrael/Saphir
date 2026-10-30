import unittest

from Saphir.enums import SystemState

from Saphir import WorkflowController


class TestWorkflowController(unittest.TestCase):

    def setUp(self):
        self.controller = WorkflowController()

    def test_initial_state(self):
        self.assertEqual(self.controller.state, SystemState.SystemStarting)

    def test_can_transition_valid(self):
        self.controller.force_state(SystemState.SystemStarting)
        self.assertTrue(self.controller.can_transition(SystemState.SafecorReady))

    def test_can_transition_invalid(self):
        self.controller.force_state(SystemState.SystemStarting)
        self.assertFalse(self.controller.can_transition(SystemState.SystemReady))

    def test_can_transition_from_unknown_state(self):
        self.controller.force_state(SystemState.SystemShuttingDown)
        self.assertFalse(self.controller.can_transition(SystemState.SystemReady))

    def test_transition_to_success(self):
        self.controller.force_state(SystemState.SystemStarting)
        states = []
        self.controller.systemStateChanged.connect(lambda v: states.append(v))

        result = self.controller.transition_to(SystemState.SafecorReady)

        self.assertTrue(result)
        self.assertEqual(self.controller.state, SystemState.SafecorReady)
        self.assertEqual(states, [SystemState.SafecorReady.value])

    def test_transition_to_blocked(self):
        self.controller.force_state(SystemState.SystemStarting)
        states = []
        self.controller.systemStateChanged.connect(lambda v: states.append(v))

        result = self.controller.transition_to(SystemState.SystemReady)

        self.assertFalse(result)
        self.assertEqual(self.controller.state, SystemState.SystemStarting)
        self.assertEqual(states, [])

    def test_transition_full_cycle(self):
        self.controller.force_state(SystemState.SystemInactive)

        self.assertTrue(self.controller.transition_to(SystemState.SystemStarting))
        self.assertTrue(self.controller.transition_to(SystemState.SafecorReady))
        self.assertTrue(self.controller.transition_to(SystemState.SystemReady))
        self.assertTrue(self.controller.transition_to(SystemState.SystemGettingFilesList))
        self.assertTrue(self.controller.transition_to(SystemState.SystemWaitingForUserAction))
        self.assertTrue(self.controller.transition_to(SystemState.SystemAnalysisRunning))
        self.assertTrue(self.controller.transition_to(SystemState.AnalysisCompleted))
        self.assertTrue(self.controller.transition_to(SystemState.CopyCleanFiles))
        self.assertTrue(self.controller.transition_to(SystemState.GeneratingReport))
        self.assertTrue(self.controller.transition_to(SystemState.SystemMustBeReset))
        self.assertTrue(self.controller.transition_to(SystemState.SystemResetting))
        self.assertTrue(self.controller.transition_to(SystemState.SystemReady))

    def test_transition_to_shutdown_from_multiple_states(self):
        for state in [
            SystemState.SystemReady,
            SystemState.SystemGettingFilesList,
            SystemState.SystemWaitingForUserAction,
            SystemState.SystemAnalysisRunning,
            SystemState.AnalysisCompleted,
            SystemState.CopyCleanFiles,
            SystemState.GeneratingReport,
            SystemState.ReportFailed,
            SystemState.SystemMustBeReset,
            SystemState.SystemResetting,
        ]:
            self.controller.force_state(state)
            self.assertTrue(self.controller.can_transition(SystemState.SystemShuttingDown))

    def test_shutdown_has_no_outgoing_transitions(self):
        self.controller.force_state(SystemState.SystemShuttingDown)
        for state in SystemState:
            self.assertFalse(self.controller.can_transition(state))

    def test_force_state_emits_signal(self):
        states = []
        self.controller.systemStateChanged.connect(lambda v: states.append(v))
        self.controller.force_state(SystemState.SystemReady)
        self.assertEqual(states, [SystemState.SystemReady.value])

    def test_force_state_skips_validation(self):
        self.controller.force_state(SystemState.SystemStarting)
        self.controller.force_state(SystemState.SystemMustBeReset)
        self.assertEqual(self.controller.state, SystemState.SystemMustBeReset)

    def test_is_in_states_match(self):
        self.controller.force_state(SystemState.SystemReady)
        self.assertTrue(self.controller.is_in_states({
            SystemState.SystemReady,
            SystemState.SystemWaitingForUserAction,
        }))

    def test_is_in_states_no_match(self):
        self.controller.force_state(SystemState.SystemReady)
        self.assertFalse(self.controller.is_in_states({
            SystemState.SystemMustBeReset,
            SystemState.SystemResetting,
        }))

    def test_analysis_running_to_waiting_for_user(self):
        self.controller.force_state(SystemState.SystemAnalysisRunning)
        self.assertTrue(self.controller.can_transition(SystemState.SystemWaitingForUserAction))

    def test_analysis_running_to_completed(self):
        self.controller.force_state(SystemState.SystemAnalysisRunning)
        self.assertTrue(self.controller.can_transition(SystemState.AnalysisCompleted))

    def test_copy_to_must_be_reset(self):
        self.controller.force_state(SystemState.CopyCleanFiles)
        self.assertTrue(self.controller.can_transition(SystemState.SystemMustBeReset))

    def test_generating_report_to_must_be_reset(self):
        self.controller.force_state(SystemState.GeneratingReport)
        self.assertTrue(self.controller.can_transition(SystemState.SystemMustBeReset))

    def test_resetting_to_ready(self):
        self.controller.force_state(SystemState.SystemResetting)
        self.assertTrue(self.controller.can_transition(SystemState.SystemReady))

    def test_generating_report_to_report_failed(self):
        self.controller.force_state(SystemState.GeneratingReport)
        self.assertTrue(self.controller.can_transition(SystemState.ReportFailed))

    def test_report_failed_to_resetting(self):
        self.controller.force_state(SystemState.ReportFailed)
        self.assertTrue(self.controller.can_transition(SystemState.SystemResetting))

    def test_report_failed_blocks_other_transitions(self):
        self.controller.force_state(SystemState.ReportFailed)
        for state in SystemState:
            if state in (SystemState.SystemResetting, SystemState.SystemShuttingDown):
                continue
            self.assertFalse(
                self.controller.can_transition(state),
                f"ReportFailed -> {state.name} should be blocked",
            )

    def test_report_failure_cycle(self):
        # GeneratingReport -> ReportFailed -> SystemResetting -> SystemReady
        self.controller.force_state(SystemState.GeneratingReport)
        self.assertTrue(self.controller.transition_to(SystemState.ReportFailed))
        self.assertTrue(self.controller.transition_to(SystemState.SystemResetting))
        self.assertTrue(self.controller.transition_to(SystemState.SystemReady))


if __name__ == "__main__":
    unittest.main()

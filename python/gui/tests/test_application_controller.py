import unittest
from unittest.mock import patch, MagicMock
from Saphir import ApplicationController
from Saphir.enums import SystemState, AnalysisMode


class TestApplicationController(unittest.TestCase):

    def setUp(self):
        with patch("Saphir.application_controller.Api"):
            self.controller = ApplicationController()

    def test_initial_system_state(self):
        self.assertEqual(self.controller.systemState, SystemState.SystemStarting.value)

    def test_set_system_state(self):
        self.controller._ApplicationController__set_system_state(SystemState.SystemReady)
        self.assertEqual(self.controller.systemState, SystemState.SystemReady.value)

    def test_system_state_changed_signal(self):
        states = []
        self.controller.systemStateChanged.connect(lambda v: states.append(v))
        self.controller._ApplicationController__set_system_state(SystemState.SystemReady)
        self.assertEqual(states, [SystemState.SystemReady.value])

    def test_source_name_initial(self):
        self.assertEqual(self.controller.sourceName, "")

    def test_source_name_set(self):
        self.controller._ApplicationController__storage_manager.add_source("disk1")
        self.assertEqual(self.controller.sourceName, "disk1")

    def test_source_ready(self):
        self.assertFalse(self.controller.sourceReady)
        self.controller._ApplicationController__storage_manager.add_source("disk1")
        self.assertTrue(self.controller.sourceReady)

    def test_target_name_initial(self):
        self.assertEqual(self.controller.targetName, "")

    def test_target_name_set(self):
        self.controller._ApplicationController__storage_manager.set_target("disk2")
        self.assertEqual(self.controller.targetName, "disk2")

    def test_target_ready(self):
        self.assertFalse(self.controller.targetReady)
        self.controller._ApplicationController__storage_manager.set_target("disk2")
        self.assertTrue(self.controller.targetReady)

    def test_queue_size(self):
        self.assertEqual(self.controller.queueSize, 0)

    def test_queue_size_after_enqueue(self):
        self.controller._ApplicationController__file_queue.enqueue("/test.txt", {"filepath": "/test.txt", "name": "test.txt", "size": 100})
        self.assertEqual(self.controller.queueSize, 1)

    def test_analysis_ready_initial(self):
        self.assertFalse(self.controller.analysisReady)

    def test_battery_level(self):
        self.assertEqual(self.controller.batteryLevel, 0)

    def test_plugged(self):
        self.assertFalse(self.controller.plugged)

    def test_analysis_mode_initial(self):
        self.assertEqual(self.controller.analysisMode, AnalysisMode.AnalyseSelection.value)

    def test_set_analysis_mode(self):
        self.controller.analysisMode = AnalysisMode.AnalyseWholeSource.value
        self.assertEqual(self.controller.analysisMode, AnalysisMode.AnalyseWholeSource.value)

    def test_set_analysis_mode_invalid(self):
        self.controller.analysisMode = 999
        self.assertEqual(self.controller.analysisMode, AnalysisMode.AnalyseSelection.value)

    def test_long_process_running(self):
        self.assertFalse(self.controller.longProcessRunning)

    def test_set_long_process_running(self):
        self.controller.set_long_process_running(True)
        self.assertTrue(self.controller.longProcessRunning)

    def test_system_used(self):
        self.assertFalse(self.controller.systemUsed)

    def test_handheld(self):
        self.assertTrue(self.controller.handheld)

    def test_transfer_started(self):
        self.assertFalse(self.controller.transferStarted)

    def test_transfer_started_after_transition(self):
        self.controller._ApplicationController__set_system_state(SystemState.CopyCleanFiles)
        self.assertTrue(self.controller.transferStarted)

    def test_copied_files_count(self):
        self.assertEqual(self.controller.copiedFilesCount, 0)

    def test_storages(self):
        self.assertEqual(self.controller.storages, [])

    def test_storages_count(self):
        self.assertEqual(self.controller.storagesCount, 0)

    def test_storages_after_add(self):
        self.controller._ApplicationController__storage_manager.on_storage_added("disk1")
        self.assertEqual(self.controller.storagesCount, 1)
        self.assertIn("disk1", self.controller.storages)

    def test_system_loading_progress(self):
        self.assertEqual(self.controller.systemLoadingProgress, 0.0)

    def test_set_system_loading_progress(self):
        self.controller._ApplicationController__set_system_loading_progress(0.5)
        self.assertEqual(self.controller.systemLoadingProgress, 0.5)

    def test_set_system_loading_progress_same(self):
        signals = []
        self.controller.systemLoadingProgressChanged.connect(lambda: signals.append(True))
        self.controller._ApplicationController__set_system_loading_progress(0.5)
        self.controller._ApplicationController__set_system_loading_progress(0.5)
        self.assertEqual(len(signals), 1)

    def test_is_file_in_queue(self):
        self.assertFalse(self.controller.is_file_in_queue("/nonexistent"))
        self.controller._ApplicationController__file_queue.enqueue("/test.txt", {"filepath": "/test.txt", "name": "test.txt", "size": 100})
        self.assertTrue(self.controller.is_file_in_queue("/test.txt"))

    def test_is_folder_in_queue(self):
        self.assertFalse(self.controller.is_folder_in_queue("/nonexistent"))
        self.controller._ApplicationController__file_queue.enqueue("/folder/file.txt", {"filepath": "/folder/file.txt", "name": "file.txt", "size": 100})
        self.assertTrue(self.controller.is_folder_in_queue("/folder"))

    def test_language_initial(self):
        self.assertEqual(self.controller.language, "")

    def test_clean_files_count(self):
        with patch.object(type(self.controller), '_ApplicationController__analysis_controller', create=True, new=None):
            self.assertEqual(self.controller.cleanFilesCount, 0)

    def test_infected_files_count(self):
        with patch.object(type(self.controller), '_ApplicationController__analysis_controller', create=True, new=None):
            self.assertEqual(self.controller.infectedFilesCount, 0)

    def test_clean_files_size(self):
        with patch.object(type(self.controller), '_ApplicationController__analysis_controller', create=True, new=None):
            self.assertEqual(self.controller.cleanFilesSize, 0)

    def test_global_progress_empty(self):
        self.assertEqual(self.controller.globalProgress, 0)

    def test_transfer_progress(self):
        self.assertEqual(self.controller.transferProgress, 0)

    def test_target_available_size(self):
        self.assertEqual(self.controller.targetAvailableSize, 0)

    def test_task_running(self):
        self.assertTrue(self.controller.taskRunning)

    def test_remaining_time(self):
        self.assertEqual(self.controller.remainingTime, 0)

    def test_current_folder(self):
        self.assertEqual(self.controller.currentFolder, "/")

    def test_components_model(self):
        self.assertIsNotNone(self.controller.componentsModel)

    def test_messages_list_model(self):
        self.assertIsNotNone(self.controller.messagesListModel)

    def test_system_information_model(self):
        self.assertIsNotNone(self.controller.systemInformationModel)

    def test_queue_list_model(self):
        self.assertIsNotNone(self.controller.queueListModel)

    def test_log_list_model(self):
        self.assertIsNotNone(self.controller.logListModel)

    def test_input_files_list_model(self):
        self.assertIsNotNone(self.controller.inputFilesListModel)

    def test_input_files_list_proxy_model(self):
        self.assertIsNotNone(self.controller.inputFilesListProxyModel)

    def test_analysis_controller_property(self):
        with patch.object(type(self.controller), '_ApplicationController__analysis_controller', create=True, new=None):
            self.assertIsNone(self.controller.analysisController)


if __name__ == "__main__":
    unittest.main()

import sys
import time
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from libsaphir import FileStatus
from PySide6.QtCore import QCoreApplication
from Saphir.enums import AnalysisMode, AnalysisState, SystemState

from Saphir import ApplicationController

# Ensure QCoreApplication exists (required for QObject)
if not hasattr(sys, "_app"):
    sys._app = QCoreApplication.instance() or QCoreApplication([])


def _make_mock_analysis_controller():
    """Create a mock AnalysisController with the required interface."""
    mock = MagicMock()
    mock.state = AnalysisState.AnalysisStopped
    mock.resultsChanged = MagicMock()
    mock.fileUpdated = MagicMock()
    mock.stateChanged = MagicMock()
    mock.systemUsed = MagicMock()
    mock.iterationDone = MagicMock()
    mock.get_analysis_state = MagicMock(return_value=AnalysisState.AnalysisStopped)
    mock.get_clean_files_count = MagicMock(return_value=0)
    mock.get_clean_files_size = MagicMock(return_value=0)
    mock.get_infected_files_count = MagicMock(return_value=0)
    mock.get_infected_files_size = MagicMock(return_value=0)
    mock.get_repository_size = MagicMock(return_value=0)
    mock.get_repository_capacity = MagicMock(return_value=0)
    mock.start_analysis = MagicMock()
    mock.stop_analysis = MagicMock()
    mock.reset = MagicMock()
    mock.set_source_disk = MagicMock()
    return mock


class TestApplicationControllerHandlers(unittest.TestCase):
    """Integration tests for ApplicationController MQTT message handlers.

    Directly invokes private handler methods with crafted payloads to verify
    state transitions and signal emissions without a real MQTT broker.
    """

    def setUp(self):
        self.__patcher = patch("Saphir.application_controller.Api")
        self.__patcher_ac = patch("Saphir.analysis_controller.Api")
        self.__patcher_tc = patch("Saphir.transfer_controller.Api")
        self.__mock_api = self.__patcher.start()
        self.__mock_api_ac = self.__patcher_ac.start()
        self.__mock_api_tc = self.__patcher_tc.start()
        self.__mock_api_instance = MagicMock()
        self.__mock_api.return_value = self.__mock_api_instance
        self.__mock_api_ac.return_value = self.__mock_api_instance
        self.__mock_api_tc.return_value = self.__mock_api_instance

        self.controller = ApplicationController()

        self.__files_queue = {}
        self.controller._ApplicationController__analysis_controller = (
            _make_mock_analysis_controller()
        )
        self.__mock_api_instance.get_files_list = MagicMock()
        self.__mock_api_instance.copy_file = MagicMock()
        self.__mock_api_instance.restart_domain = MagicMock()
        self.__mock_api_instance.shutdown = MagicMock()
        self.__mock_api_instance.create_file = MagicMock()
        self.__mock_api_instance.notify_gui_ready = MagicMock()
        self.__mock_api_instance.discover_components = MagicMock()
        self.__mock_api_instance.request_system_info = MagicMock()
        self.__mock_api_instance.get_disks_list = MagicMock()
        self.__mock_api_instance.switch_gui = MagicMock()

    def tearDown(self):
        self.__patcher.stop()
        self.__patcher_ac.stop()
        self.__patcher_tc.stop()

    # --- __handle_disk_state ---

    def test_handle_disk_state_connected_sets_source(self):
        self.controller._ApplicationController__workflow_controller.force_state(
            SystemState.SystemReady
        )
        self.controller._ApplicationController__handle_disk_state(
            {"disk": "usb0", "state": "connected"}
        )
        self.assertEqual(self.controller.sourceName, "usb0")

    def test_handle_disk_state_connected_target(self):
        self.controller._ApplicationController__workflow_controller.force_state(
            SystemState.AnalysisCompleted
        )
        self.controller._ApplicationController__storage_manager.set_source("source0")
        self.controller._ApplicationController__handle_disk_state(
            {"disk": "target0", "state": "connected"}
        )
        self.assertEqual(self.controller.targetName, "target0")

    def test_handle_disk_state_disconnected_source_not_used(self):
        self.controller._ApplicationController__workflow_controller.force_state(
            SystemState.SystemWaitingForUserAction
        )
        self.controller._ApplicationController__storage_manager.set_source("usb0")
        self.controller._ApplicationController__handle_disk_state(
            {"disk": "usb0", "state": "disconnected"}
        )
        self.assertEqual(self.controller.sourceName, "")

    def test_handle_disk_state_disconnected_source_used(self):
        self.controller._ApplicationController__workflow_controller.force_state(
            SystemState.AnalysisCompleted
        )
        self.controller._ApplicationController__storage_manager.set_source("usb0")
        self.controller._ApplicationController__system_used = True
        signals = []
        self.controller.systemMustBeReset.connect(lambda: signals.append(True))
        self.controller._ApplicationController__handle_disk_state(
            {"disk": "usb0", "state": "disconnected"}
        )
        self.assertEqual(
            self.controller.systemState, SystemState.SystemMustBeReset.value
        )
        self.assertTrue(signals)

    def test_handle_disk_state_disconnected_target_during_copy(self):
        self.controller._ApplicationController__workflow_controller.force_state(
            SystemState.CopyCleanFiles
        )
        self.controller._ApplicationController__storage_manager.set_source("source0")
        self.controller._ApplicationController__storage_manager.set_target("target0")
        signals = []
        self.controller.systemMustBeReset.connect(lambda: signals.append(True))
        self.controller._ApplicationController__handle_disk_state(
            {"disk": "target0", "state": "disconnected"}
        )
        self.assertEqual(
            self.controller.systemState, SystemState.SystemMustBeReset.value
        )
        self.assertTrue(signals)

    def test_handle_disk_state_locked_ignores(self):
        self.controller._ApplicationController__workflow_controller.force_state(
            SystemState.SystemMustBeReset
        )
        self.controller._ApplicationController__handle_disk_state(
            {"disk": "usb0", "state": "connected"}
        )
        self.assertEqual(self.controller.sourceName, "")

    def test_handle_disk_state_missing_disk(self):
        self.controller._ApplicationController__workflow_controller.force_state(
            SystemState.SystemReady
        )
        self.controller._ApplicationController__handle_disk_state(
            {"state": "connected"}
        )
        self.__mock_api_instance.error.assert_called()

    def test_handle_disk_state_missing_state(self):
        self.controller._ApplicationController__workflow_controller.force_state(
            SystemState.SystemReady
        )
        self.controller._ApplicationController__handle_disk_state({"disk": "usb0"})
        self.__mock_api_instance.error.assert_called()

    def test_handle_disk_state_single_disk_becomes_source(self):
        self.controller._ApplicationController__workflow_controller.force_state(
            SystemState.SystemReady
        )
        self.controller._ApplicationController__handle_disk_state(
            {"disk": "only_disk", "state": "connected"}
        )
        self.assertEqual(self.controller.sourceName, "only_disk")

    # --- __handle_list_disks ---

    def test_handle_list_disks_empty(self):
        self.controller._ApplicationController__workflow_controller.force_state(
            SystemState.SystemReady
        )
        self.controller._ApplicationController__handle_list_disks({"disks": []})
        self.__mock_api_instance.info.assert_called()

    def test_handle_list_disks_non_empty(self):
        self.controller._ApplicationController__workflow_controller.force_state(
            SystemState.SystemReady
        )
        self.controller._ApplicationController__handle_list_disks(
            {"disks": ["disk1", "disk2"]}
        )
        self.assertEqual(self.controller.sourceName, "disk1")
        self.assertEqual(self.controller.storagesCount, 2)

    def test_handle_list_disks_analysis_running_ignores(self):
        self.controller._ApplicationController__workflow_controller.force_state(
            SystemState.SystemAnalysisRunning
        )
        with patch.object(
            self.controller._ApplicationController__analysis_controller,
            "get_analysis_state",
            return_value=AnalysisState.AnalysisRunning,
        ):
            self.controller._ApplicationController__handle_list_disks(
                {"disks": ["disk1"]}
            )
        self.assertEqual(self.controller.sourceName, "")

    def test_handle_list_disks_malformed(self):
        self.controller._ApplicationController__workflow_controller.force_state(
            SystemState.SystemReady
        )
        self.controller._ApplicationController__handle_list_disks({})
        self.__mock_api_instance.error.assert_called()

    # --- __handle_list_files ---

    def test_handle_list_files_selection_mode(self):
        self.controller._ApplicationController__workflow_controller.force_state(
            SystemState.SystemWaitingForUserAction
        )
        self.controller._ApplicationController__storage_manager.set_source("usb0")
        self.controller._ApplicationController__file_browser.folders_to_query = 1
        self.controller._ApplicationController__file_browser.is_enqueuing = False

        files = [
            {"type": "file", "path": "/", "name": "test.txt", "size": 100},
            {"type": "folder", "path": "/", "name": "subdir", "size": 0},
        ]
        self.controller._ApplicationController__handle_list_files(
            {"disk": "usb0", "files": files}
        )

        self.assertIn(
            "/test.txt",
            self.controller._ApplicationController__file_browser.input_files_list,
        )
        self.assertFalse(self.controller.longProcessRunning)
        self.assertEqual(
            self.controller.systemState, SystemState.SystemWaitingForUserAction.value
        )

    def test_handle_list_files_enqueuing_mode(self):
        self.controller._ApplicationController__workflow_controller.force_state(
            SystemState.SystemGettingFilesList
        )
        self.controller._ApplicationController__storage_manager.set_source("usb0")
        self.controller._ApplicationController__file_browser.folders_to_query = 1
        self.controller._ApplicationController__file_browser.is_enqueuing = True

        files = [
            {"type": "file", "path": "/", "name": "test.txt", "size": 100},
        ]
        self.controller._ApplicationController__handle_list_files(
            {"disk": "usb0", "files": files}
        )

        self.assertIn(
            "/test.txt", self.controller._ApplicationController__file_queue.files
        )
        self.assertFalse(self.controller.longProcessRunning)
        self.assertFalse(
            self.controller._ApplicationController__file_browser.is_enqueuing
        )

    def test_handle_list_files_enqueuing_folder_triggers_subquery(self):
        self.controller._ApplicationController__workflow_controller.force_state(
            SystemState.SystemGettingFilesList
        )
        self.controller._ApplicationController__storage_manager.set_source("usb0")
        self.controller._ApplicationController__file_browser.folders_to_query = 1
        self.controller._ApplicationController__file_browser.is_enqueuing = True

        files = [
            {"type": "folder", "path": "/", "name": "subdir", "size": 0},
        ]
        self.controller._ApplicationController__handle_list_files(
            {"disk": "usb0", "files": files}
        )

        self.assertEqual(
            self.controller._ApplicationController__file_browser.folders_to_query, 1
        )
        self.__mock_api_instance.get_files_list.assert_called()

    def test_handle_list_files_analysis_running_ignores(self):
        self.controller._ApplicationController__workflow_controller.force_state(
            SystemState.SystemAnalysisRunning
        )
        self.controller._ApplicationController__handle_list_files(
            {"disk": "usb0", "files": []}
        )
        self.__mock_api_instance.error.assert_not_called()

    def test_handle_list_files_missing_disk(self):
        self.controller._ApplicationController__workflow_controller.force_state(
            SystemState.SystemReady
        )
        self.controller._ApplicationController__handle_list_files({"files": []})
        self.__mock_api_instance.error.assert_called()

    def test_handle_list_files_missing_files(self):
        self.controller._ApplicationController__workflow_controller.force_state(
            SystemState.SystemReady
        )
        self.controller._ApplicationController__file_browser.folders_to_query = 1
        self.controller._ApplicationController__handle_list_files(
            {"disk": "usb0", "files": None}
        )
        self.__mock_api_instance.error.assert_called()

    def test_handle_list_files_full_analysis_starts_analysis(self):
        self.controller._ApplicationController__workflow_controller.force_state(
            SystemState.SystemGettingFilesList
        )
        self.controller._ApplicationController__storage_manager.set_source("usb0")
        self.controller._ApplicationController__analysis_mode = (
            AnalysisMode.AnalyseWholeSource
        )
        self.controller._ApplicationController__file_browser.folders_to_query = 1
        self.controller._ApplicationController__file_browser.is_enqueuing = True

        files = [
            {"type": "file", "path": "/", "name": "test.txt", "size": 100},
        ]
        self.controller._ApplicationController__handle_list_files(
            {"disk": "usb0", "files": files}
        )

        self.assertIn(
            "/test.txt", self.controller._ApplicationController__file_queue.files
        )
        self.assertFalse(
            self.controller._ApplicationController__file_browser.is_enqueuing
        )

    # --- __handle_discover_components ---

    def test_handle_discover_components(self):
        components = [
            {"id": "safecor_disk_controller", "type": "disk", "state": "ready"},
            {
                "id": "av1",
                "type": "antivirus",
                "state": "ready",
                "domain_name": "d1",
                "label": "AV1",
                "version": "1.0",
            },
            {
                "id": "av2",
                "type": "antivirus",
                "state": "ready",
                "domain_name": "d2",
                "label": "AV2",
                "version": "2.0",
            },
        ]
        self.controller._ApplicationController__handle_discover_components(
            {"components": components}
        )
        self.assertTrue(self.controller.analysisReady)

    def test_handle_discover_components_malformed(self):
        self.controller._ApplicationController__handle_discover_components({})
        self.__mock_api_instance.error.assert_called()

    def test_handle_discover_components_empty(self):
        self.controller._ApplicationController__handle_discover_components(
            {"components": []}
        )
        self.assertFalse(self.controller.analysisReady)

    # --- __check_components_availability ---

    def test_check_components_availability_all_ready(self):
        components = [
            {"id": "safecor_disk_controller", "type": "disk", "state": "ready"},
            {
                "id": "av1",
                "type": "antivirus",
                "state": "ready",
                "domain_name": "d1",
                "label": "AV1",
                "version": "1.0",
            },
            {
                "id": "av2",
                "type": "antivirus",
                "state": "ready",
                "domain_name": "d2",
                "label": "AV2",
                "version": "2.0",
            },
        ]
        self.controller._ApplicationController__components_helper.update(components)
        self.controller._ApplicationController__check_components_availability()
        self.assertTrue(self.controller.analysisReady)
        self.assertEqual(self.controller.systemState, SystemState.SystemReady.value)

    def test_check_components_availability_partial(self):
        components = [
            {"id": "safecor_disk_controller", "type": "disk", "state": "ready"},
            {
                "id": "av1",
                "type": "antivirus",
                "state": "ready",
                "domain_name": "d1",
                "label": "AV1",
                "version": "1.0",
            },
            {
                "id": "av2",
                "type": "antivirus",
                "state": "off",
                "domain_name": "d2",
                "label": "AV2",
                "version": "2.0",
            },
        ]
        self.controller._ApplicationController__components_helper.update(components)
        self.controller._ApplicationController__check_components_availability()
        self.assertFalse(self.controller.analysisReady)

    def test_check_components_availability_disk_controller_first_ready(self):
        components = [
            {"id": "safecor_disk_controller", "type": "disk", "state": "ready"},
        ]
        self.controller._ApplicationController__components_helper.update(components)
        self.controller._ApplicationController__check_components_availability()
        self.__mock_api_instance.get_disks_list.assert_called()

    def test_check_components_availability_av_removed(self):
        components = [
            {"id": "safecor_disk_controller", "type": "disk", "state": "ready"},
            {
                "id": "av1",
                "type": "antivirus",
                "state": "ready",
                "domain_name": "d1",
                "label": "AV1",
                "version": "1.0",
            },
            {
                "id": "av2",
                "type": "antivirus",
                "state": "ready",
                "domain_name": "d2",
                "label": "AV2",
                "version": "2.0",
            },
        ]
        self.controller._ApplicationController__components_helper.update(components)
        self.controller._ApplicationController__check_components_availability()
        self.assertTrue(self.controller.analysisReady)

        components[2]["state"] = "off"
        self.controller._ApplicationController__components_helper.update(components)
        self.controller._ApplicationController__check_components_availability()
        self.assertFalse(self.controller.analysisReady)

    def test_check_components_availability_no_backward_state_force(self):
        components = [
            {"id": "safecor_disk_controller", "type": "disk", "state": "ready"},
            {
                "id": "av1",
                "type": "antivirus",
                "state": "ready",
                "domain_name": "d1",
                "label": "AV1",
                "version": "1.0",
            },
            {
                "id": "av2",
                "type": "antivirus",
                "state": "ready",
                "domain_name": "d2",
                "label": "AV2",
                "version": "2.0",
            },
        ]
        self.controller._ApplicationController__components_helper.update(components)
        self.controller._ApplicationController__check_components_availability()
        self.assertEqual(self.controller.systemState, SystemState.SystemReady.value)

        # The workflow moves on to analysis
        self.controller._ApplicationController__set_system_state(
            SystemState.SystemAnalysisRunning
        )

        # A late all-ready component response arrives
        self.controller._ApplicationController__check_components_availability()

        # The state must not be pulled back to SystemReady
        self.assertEqual(
            self.controller.systemState, SystemState.SystemAnalysisRunning.value
        )

    # --- __app_ready ---

    def test_app_ready_is_idempotent(self):
        energy = self.controller._ApplicationController__energy_monitor
        with (
            patch("Saphir.application_controller.AnalysisController") as mock_ac,
            patch.object(type(energy), "start_polling"),
            patch("Saphir.translation_manager.Api", return_value=self.__mock_api_instance),
            patch("Saphir.log_list_model.Api", return_value=self.__mock_api_instance),
        ):
            self.controller._ApplicationController__app_ready()
            self.controller._ApplicationController__app_ready()

        self.__mock_api_instance.notify_gui_ready.assert_called_once()
        self.__mock_api_instance.discover_components.assert_called_once()
        self.__mock_api_instance.request_system_info.assert_called_once()
        mock_ac.assert_called_once()
        self.assertTrue(self.controller._ApplicationController__ready)

    # --- __on_api_ready ---

    def test_on_api_ready_re_discovers_during_boot(self):
        with patch("Saphir.api_lifecycle.Api", return_value=self.__mock_api_instance):
            self.__mock_api_instance.subscribe.return_value = (0, 1)
            self.__mock_api_instance.discover_components.reset_mock()
            self.controller._ApplicationController__on_api_ready()
        self.__mock_api_instance.discover_components.assert_called_once()

    def test_on_api_ready_no_re_discover_after_boot(self):
        self.controller._ApplicationController__set_system_state(SystemState.SystemReady)
        with patch("Saphir.api_lifecycle.Api", return_value=self.__mock_api_instance):
            self.__mock_api_instance.subscribe.return_value = (0, 1)
            self.__mock_api_instance.discover_components.reset_mock()
            self.controller._ApplicationController__on_api_ready()
        self.__mock_api_instance.discover_components.assert_not_called()

    # --- __handle_copy_file ---

    def test_handle_copy_file(self):
        self.controller._ApplicationController__storage_manager.set_source("src")
        self.controller._ApplicationController__storage_manager.set_target("tgt")
        self.__files_queue["/clean.txt"] = {
            "filepath": "/clean.txt",
            "name": "clean.txt",
            "size": 100,
            "status": FileStatus.FileClean,
        }
        self.controller._ApplicationController__file_queue.enqueue(
            "/clean.txt", self.__files_queue["/clean.txt"]
        )

        updates = []
        self.controller.fileUpdated.connect(
            lambda path, fields: updates.append((path, fields))
        )

        self.controller._ApplicationController__handle_copy_file(
            {
                "filepath": "/clean.txt",
                "status": "ok",
                "fingerprint": "abc123",
            }
        )
        self.assertEqual(len(updates), 1)
        self.assertEqual(updates[0][0], "/clean.txt")

    def test_handle_copy_file_no_filepath(self):
        self.controller._ApplicationController__handle_copy_file(
            {"status": "ok", "fingerprint": "abc"}
        )
        self.__mock_api_instance.error.assert_called()

    # --- __handle_energy_state ---

    def test_handle_energy_state(self):
        self.controller._ApplicationController__handle_energy_state(
            {
                "battery_level": 85,
                "plugged": False,
            }
        )
        self.assertEqual(self.controller.batteryLevel, 85)
        self.assertFalse(self.controller.plugged)

    # --- __handle_system_info ---

    def test_handle_system_info(self):
        payload = {
            "core": {"version": "1.0"},
            "system": {
                "machine": {"cpu": 4},
                "uuid": "test-uuid",
                "safecor_version": "3.0",
            },
        }
        self.controller._ApplicationController__handle_system_info(payload)

    def test_handle_system_info_malformed(self):
        self.controller._ApplicationController__handle_system_info({})

    # --- __handle_create_file ---

    def test_handle_create_file_journal_log(self):
        self.controller._ApplicationController__storage_manager.set_target("target0")
        self.controller._ApplicationController__handle_create_file(
            {
                "disk": "target0",
                "filepath": "/report/journal.log",
            }
        )
        self.assertEqual(
            self.controller.systemState, SystemState.SystemMustBeReset.value
        )

    def test_handle_create_file_other_file(self):
        self.controller._ApplicationController__storage_manager.set_target("target0")
        self.controller._ApplicationController__handle_create_file(
            {
                "disk": "target0",
                "filepath": "/report/other.txt",
            }
        )
        self.assertNotEqual(
            self.controller.systemState, SystemState.SystemMustBeReset.value
        )

    # --- __on_results_changed ---

    def test_on_results_changed_all_done(self):
        self.__files_queue["/clean.txt"] = {
            "filepath": "/clean.txt",
            "name": "clean.txt",
            "size": 100,
            "status": FileStatus.FileClean,
        }
        self.__files_queue["/infected.txt"] = {
            "filepath": "/infected.txt",
            "name": "infected.txt",
            "size": 200,
            "status": FileStatus.FileInfected,
        }
        self.controller._ApplicationController__file_queue.enqueue(
            "/clean.txt", self.__files_queue["/clean.txt"]
        )
        self.controller._ApplicationController__file_queue.enqueue(
            "/infected.txt", self.__files_queue["/infected.txt"]
        )

        self.controller._ApplicationController__analysis_controller.get_clean_files_count = MagicMock(
            return_value=1
        )
        self.controller._ApplicationController__analysis_controller.get_infected_files_count = MagicMock(
            return_value=1
        )

        self.controller._ApplicationController__on_results_changed()
        self.assertEqual(
            self.controller.systemState, SystemState.AnalysisCompleted.value
        )

    def test_on_results_changed_partial(self):
        self.__files_queue["/clean.txt"] = {
            "filepath": "/clean.txt",
            "name": "clean.txt",
            "size": 100,
            "status": FileStatus.FileClean,
        }
        self.__files_queue["/pending.txt"] = {
            "filepath": "/pending.txt",
            "name": "pending.txt",
            "size": 200,
            "status": FileStatus.FileStatusUndefined,
        }
        self.controller._ApplicationController__file_queue.enqueue(
            "/clean.txt", self.__files_queue["/clean.txt"]
        )
        self.controller._ApplicationController__file_queue.enqueue(
            "/pending.txt", self.__files_queue["/pending.txt"]
        )

        self.controller._ApplicationController__on_results_changed()
        self.assertNotEqual(
            self.controller.systemState, SystemState.AnalysisCompleted.value
        )

    # --- __on_analysis_state_changed ---

    def test_on_analysis_state_changed_running(self):
        self.controller._ApplicationController__workflow_controller.force_state(
            SystemState.SystemWaitingForUserAction
        )
        self.controller._ApplicationController__on_analysis_state_changed(
            AnalysisState.AnalysisRunning
        )
        self.assertEqual(
            self.controller.systemState, SystemState.SystemAnalysisRunning.value
        )

    def test_on_analysis_state_changed_stopped(self):
        self.controller._ApplicationController__workflow_controller.force_state(
            SystemState.SystemAnalysisRunning
        )
        self.controller._ApplicationController__on_analysis_state_changed(
            AnalysisState.AnalysisStopped
        )
        self.assertEqual(
            self.controller.systemState, SystemState.SystemWaitingForUserAction.value
        )

    # --- __on_system_used ---

    def test_on_system_used(self):
        signals = []
        self.controller.systemUsedChanged.connect(lambda: signals.append(True))
        self.controller._ApplicationController__on_system_used()
        self.assertTrue(self.controller.systemUsed)
        self.assertTrue(signals)

    # --- reset ---

    def test_reset(self):
        self.controller._ApplicationController__workflow_controller.force_state(
            SystemState.SystemWaitingForUserAction
        )
        self.controller._ApplicationController__storage_manager.set_source("usb0")
        self.__files_queue["/test.txt"] = {
            "filepath": "/test.txt",
            "name": "test.txt",
            "size": 100,
        }
        self.controller._ApplicationController__file_queue.enqueue(
            "/test.txt", self.__files_queue["/test.txt"]
        )

        self.controller.reset()

        self.assertEqual(self.controller.systemState, SystemState.SystemResetting.value)
        self.assertEqual(self.controller.sourceName, "")
        self.assertEqual(self.controller.queueSize, 0)
        self.assertFalse(self.controller.analysisReady)

    # --- start_full_analysis ---

    def test_start_full_analysis(self):
        self.controller._ApplicationController__storage_manager.set_source("usb0")
        self.controller._ApplicationController__workflow_controller.force_state(
            SystemState.SystemReady
        )
        self.controller.start_full_analysis()

        self.assertEqual(
            self.controller._ApplicationController__analysis_mode,
            AnalysisMode.AnalyseWholeSource,
        )
        self.assertTrue(self.controller.longProcessRunning)
        self.__mock_api_instance.get_files_list.assert_called_with("usb0", False, "/")

    # --- enqueue_file / dequeue_file ---

    def test_enqueue_file(self):
        self.controller._ApplicationController__storage_manager.set_source("usb0")
        file = {
            "filepath": "/test.txt",
            "name": "test.txt",
            "size": 100,
            "type": "file",
        }
        self.controller._ApplicationController__file_browser.input_files_list[
            "/test.txt"
        ] = file

        self.controller.enqueue_file("file", "/test.txt")
        self.assertIn(
            "/test.txt", self.controller._ApplicationController__file_queue.files
        )
        self.assertFalse(self.controller.longProcessRunning)

    def test_enqueue_folder(self):
        self.controller._ApplicationController__storage_manager.set_source("usb0")
        folder = {"filepath": "/subdir", "name": "subdir", "size": 0, "type": "folder"}
        self.controller._ApplicationController__file_browser.input_files_list[
            "/subdir"
        ] = folder

        self.controller.enqueue_file("folder", "/subdir")
        self.assertTrue(self.controller.longProcessRunning)
        self.__mock_api_instance.get_files_list.assert_called()

    def test_dequeue_file(self):
        self.controller._ApplicationController__storage_manager.set_source("usb0")
        file = {
            "filepath": "/test.txt",
            "name": "test.txt",
            "size": 100,
            "type": "file",
            "inqueue": True,
        }
        self.controller._ApplicationController__file_browser.input_files_list[
            "/test.txt"
        ] = file
        self.controller._ApplicationController__file_queue.enqueue("/test.txt", file)

        self.controller.dequeue_file("/test.txt")
        self.assertNotIn(
            "/test.txt", self.controller._ApplicationController__file_queue.files
        )
        self.assertFalse(self.controller.longProcessRunning)

    def test_dequeue_folder(self):
        self.controller._ApplicationController__storage_manager.set_source("usb0")
        folder = {
            "filepath": "/subdir",
            "name": "subdir",
            "size": 0,
            "type": "folder",
            "inqueue": True,
        }
        self.controller._ApplicationController__file_browser.input_files_list[
            "/subdir"
        ] = folder
        self.controller._ApplicationController__file_queue.enqueue(
            "/subdir/file.txt",
            {
                "filepath": "/subdir/file.txt",
                "name": "file.txt",
                "size": 50,
                "type": "file",
            },
        )

        self.controller.dequeue_file("/subdir")
        time.sleep(0.2)
        self.assertFalse(self.controller.longProcessRunning)
        self.assertNotIn(
            "/subdir/file.txt", self.controller._ApplicationController__file_queue.files
        )

    def test_dequeue_file_not_found(self):
        self.controller._ApplicationController__storage_manager.set_source("usb0")
        self.controller.dequeue_file("/nonexistent")
        self.__mock_api_instance.error.assert_not_called()

    # --- __on_transfer_complete ---

    def test_on_transfer_complete(self):
        self.controller._ApplicationController__storage_manager.set_source("src")
        self.controller._ApplicationController__storage_manager.set_target("tgt")
        self.controller._ApplicationController__analysis_end_time = datetime.now()
        with (
            patch.object(
                self.controller._ApplicationController__report_controller, "make_report"
            ),
            patch("builtins.open", MagicMock()),
        ):
            self.controller._ApplicationController__on_transfer_complete()
        self.assertEqual(
            self.controller.systemState, SystemState.GeneratingReport.value
        )

    # --- shutdown ---

    def test_shutdown(self):
        self.controller.shutdown()
        self.assertEqual(
            self.controller.systemState, SystemState.SystemShuttingDown.value
        )
        self.__mock_api_instance.shutdown.assert_called()

    # --- switch_to_viewer ---

    def test_switch_to_viewer(self):
        self.controller.switch_to_viewer()
        self.__mock_api_instance.switch_gui.assert_called_with("saphir-viewer")

    # --- go_to_folder / go_to_parent_folder ---

    def test_go_to_folder(self):
        self.controller._ApplicationController__storage_manager.set_source("usb0")
        self.controller.go_to_folder("/subdir")
        self.assertEqual(self.controller.currentFolder, "/subdir")
        self.__mock_api_instance.get_files_list.assert_called_with(
            "usb0", False, "/subdir"
        )

    def test_go_to_parent_folder(self):
        self.controller._ApplicationController__storage_manager.set_source("usb0")
        self.controller._ApplicationController__file_browser.current_folder = "/a/b/c"
        self.controller.go_to_parent_folder()
        self.assertEqual(self.controller.currentFolder, "/a/b")

    # --- select/deselect all clean files ---

    def test_select_all_clean_files_for_copy(self):
        self.__files_queue["/clean.txt"] = {
            "filepath": "/clean.txt",
            "name": "clean.txt",
            "size": 100,
            "status": FileStatus.FileClean,
        }
        self.__files_queue["/infected.txt"] = {
            "filepath": "/infected.txt",
            "name": "infected.txt",
            "size": 200,
            "status": FileStatus.FileInfected,
        }
        self.controller._ApplicationController__file_queue.enqueue(
            "/clean.txt", self.__files_queue["/clean.txt"]
        )
        self.controller._ApplicationController__file_queue.enqueue(
            "/infected.txt", self.__files_queue["/infected.txt"]
        )

        self.controller.select_all_clean_files_for_copy()
        self.assertTrue(self.__files_queue["/clean.txt"]["select_for_copy"])
        self.assertFalse(
            self.__files_queue["/infected.txt"].get("select_for_copy", False)
        )

    def test_deselect_all_clean_files_for_copy(self):
        self.__files_queue["/clean.txt"] = {
            "filepath": "/clean.txt",
            "name": "clean.txt",
            "size": 100,
            "status": FileStatus.FileClean,
            "select_for_copy": True,
        }
        self.controller._ApplicationController__file_queue.enqueue(
            "/clean.txt", self.__files_queue["/clean.txt"]
        )

        self.controller.deselect_all_clean_files_for_copy()
        self.assertFalse(self.__files_queue["/clean.txt"]["select_for_copy"])

    # --- start_stop_analysis ---

    def test_start_stop_analysis_start(self):
        with (
            patch.object(
                self.controller._ApplicationController__analysis_controller,
                "state",
                AnalysisState.AnalysisStopped,
            ),
            patch.object(
                self.controller._ApplicationController__analysis_controller,
                "start_analysis",
            ) as mock_start,
        ):
            self.controller.start_stop_analysis()
            mock_start.assert_called()

    def test_start_stop_analysis_stop(self):
        with (
            patch.object(
                self.controller._ApplicationController__analysis_controller,
                "state",
                AnalysisState.AnalysisRunning,
            ),
            patch.object(
                self.controller._ApplicationController__analysis_controller,
                "stop_analysis",
            ) as mock_stop,
        ):
            self.controller.start_stop_analysis()
            mock_stop.assert_called()

    # --- on_storage_selected ---

    def test_on_storage_selected(self):
        self.controller.on_storage_selected("new_disk")
        self.assertEqual(self.controller.sourceName, "new_disk")

    # --- debug/info/warn/error slots ---

    def test_debug_slot(self):
        self.controller.debug("test message")
        self.__mock_api_instance.debug.assert_called_with("test message", "Saphir")

    def test_info_slot(self):
        self.controller.info("test info")
        self.__mock_api_instance.info.assert_called_with("test info", "Saphir")

    def test_warn_slot(self):
        self.controller.warn("test warning")
        self.__mock_api_instance.warn.assert_called_with("test warning", "Saphir")

    def test_error_slot(self):
        self.controller.error("test error")
        self.__mock_api_instance.error.assert_called_with("test error", "Saphir")

    # --- __on_shutdown ---

    def test_on_shutdown_accepted(self):
        messages = []
        self.controller.showMessage.connect(
            lambda title, msg, alert, modal: messages.append((title, msg))
        )
        self.controller._ApplicationController__on_shutdown(True)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0][0], "Shutdown")

    def test_on_shutdown_refused(self):
        messages = []
        self.controller.showMessage.connect(
            lambda title, msg, alert, modal: messages.append((title, msg, modal))
        )
        self.controller._ApplicationController__on_shutdown(False, "timeout")
        self.assertEqual(len(messages), 1)
        self.assertFalse(messages[0][2])

    # --- __on_iteration_done ---

    def test_on_iteration_done(self):
        with patch("builtins.open", MagicMock()):
            self.controller._ApplicationController__on_iteration_done(1.5, 1024)
        self.assertIsNotNone(self.controller.remainingTime)

    # --- __on_disk_controller_state_changed ---

    def test_on_disk_controller_state_changed_ready(self):
        self.controller._ApplicationController__on_disk_controller_state_changed(True)
        self.__mock_api_instance.get_disks_list.assert_called()

    def test_on_disk_controller_state_changed_not_ready(self):
        self.__mock_api_instance.get_disks_list.reset_mock()
        self.controller._ApplicationController__on_disk_controller_state_changed(False)
        self.__mock_api_instance.get_disks_list.assert_not_called()

    # --- start_transfer ---

    def test_start_transfer(self):
        self.controller._ApplicationController__storage_manager.set_source("src")
        self.controller._ApplicationController__storage_manager.set_target("tgt")
        self.controller._ApplicationController__workflow_controller.force_state(
            SystemState.AnalysisCompleted
        )
        self.controller.start_transfer()
        self.assertEqual(self.controller.systemState, SystemState.CopyCleanFiles.value)

    # --- __make_analysis_report ---

    def test_make_analysis_report(self):
        self.controller._ApplicationController__storage_manager.set_source("usb0")
        self.controller._ApplicationController__analysis_end_time = datetime.now()
        self.__files_queue["/clean.txt"] = {
            "filepath": "/clean.txt",
            "name": "clean.txt",
            "size": 100,
            "status": FileStatus.FileClean,
        }
        self.controller._ApplicationController__file_queue.enqueue(
            "/clean.txt", self.__files_queue["/clean.txt"]
        )
        self.controller._ApplicationController__analysis_controller.get_clean_files_count = MagicMock(
            return_value=1
        )
        self.controller._ApplicationController__analysis_controller.get_infected_files_count = MagicMock(
            return_value=0
        )

        components = [
            {
                "id": "av1",
                "type": "antivirus",
                "state": "ready",
                "version": "1.0",
                "description": "Test AV\nline2",
            },
        ]
        self.controller._ApplicationController__components_helper.update(components)

        with patch.object(
            self.controller._ApplicationController__report_controller, "make_report"
        ) as mock_report:
            self.controller._ApplicationController__make_analysis_report()
            mock_report.assert_called_once()
            call_kwargs = mock_report.call_args[1]
            self.assertEqual(call_kwargs["storage_name"], "usb0")
            self.assertEqual(call_kwargs["clean_files_count"], 1)

    # --- __on_report_generated ---

    def test_on_report_generated(self):
        self.controller._ApplicationController__on_report_generated()

    # --- update_source_files_list ---

    def test_update_source_files_list_no_source(self):
        self.controller.update_source_files_list()
        self.__mock_api_instance.get_files_list.assert_not_called()

    def test_update_source_files_list_with_source(self):
        self.controller._ApplicationController__storage_manager.set_source("usb0")
        self.controller.update_source_files_list()
        self.__mock_api_instance.get_files_list.assert_called_with("usb0", False)

    # --- start_analysis / stop_analysis ---

    def test_start_analysis(self):
        with patch.object(
            self.controller._ApplicationController__analysis_controller,
            "state",
            AnalysisState.AnalysisStopped,
        ):
            self.controller._ApplicationController__analysis_ready = True
            with patch.object(
                self.controller._ApplicationController__analysis_controller,
                "start_analysis",
            ) as mock_start:
                self.controller.start_analysis()
                mock_start.assert_called()

    def test_start_analysis_not_ready(self):
        with patch.object(
            self.controller._ApplicationController__analysis_controller,
            "state",
            AnalysisState.AnalysisStopped,
        ):
            self.controller._ApplicationController__analysis_ready = False
            with patch.object(
                self.controller._ApplicationController__analysis_controller,
                "start_analysis",
            ) as mock_start:
                self.controller.start_analysis()
                mock_start.assert_not_called()

    def test_stop_analysis(self):
        with (
            patch.object(
                self.controller._ApplicationController__analysis_controller,
                "state",
                AnalysisState.AnalysisRunning,
            ),
            patch.object(
                self.controller._ApplicationController__analysis_controller,
                "stop_analysis",
            ) as mock_stop,
        ):
            self.controller.stop_analysis()
            mock_stop.assert_called()

    def test_stop_analysis_not_running(self):
        with (
            patch.object(
                self.controller._ApplicationController__analysis_controller,
                "state",
                AnalysisState.AnalysisStopped,
            ),
            patch.object(
                self.controller._ApplicationController__analysis_controller,
                "stop_analysis",
            ) as mock_stop,
        ):
            self.controller.stop_analysis()
            mock_stop.assert_not_called()

    # --- __set_language ---

    def test_set_language(self):
        self.controller._ApplicationController__set_language("fr")
        self.assertEqual(self.controller.language, "fr")

    # --- __dequeue_folder ---

    def test_dequeue_folder_internal(self):
        self.__files_queue["/sub/file.txt"] = {
            "filepath": "/sub/file.txt",
            "name": "file.txt",
            "size": 50,
        }
        self.controller._ApplicationController__file_queue.enqueue(
            "/sub/file.txt", self.__files_queue["/sub/file.txt"]
        )
        self.controller._ApplicationController__dequeue_folder("/sub")
        self.assertNotIn(
            "/sub/file.txt", self.controller._ApplicationController__file_queue.files
        )


if __name__ == "__main__":
    unittest.main()

"""Unit tests for the viewer ApplicationController (plan 13.2)."""

import os
import unittest
from unittest.mock import MagicMock, patch

from safecor import ConnectionType, DiskState, Topics
from Viewer import (
    ApplicationController,
    DevModeHelper,
    FileType,
    SafecorInputFilesListModel,
    ViewerConstants,
)


class ApplicationControllerTestCase(unittest.TestCase):
    def setUp(self):
        self.api_patch = patch("Viewer.application_controller.Api")
        self.mock_api_class = self.api_patch.start()
        self.api = self.mock_api_class.return_value
        self.controller = ApplicationController()

    def tearDown(self):
        self.api_patch.stop()

    def _ready_flow(self):
        """Drives the subscription flow and returns the collected mids."""
        mids = []

        def fake_subscribe(topic):
            mid = len(mids)
            mids.append(topic)
            return (True, mid)

        self.api.subscribe.side_effect = fake_subscribe
        self.controller._ApplicationController__on_api_ready()
        return mids

    def _make_mount_ready(self):
        """Simulates the USB mount point becoming ready."""
        self.controller._ApplicationController__on_usb_mountpoint_ready()

    def _trigger_api_ready(self):
        """Runs __on_api_ready with a working (mocked) subscribe."""
        self.api.subscribe.side_effect = lambda topic: (True, 1)
        self.controller._ApplicationController__on_api_ready()


class TestInit(ApplicationControllerTestCase):
    def test_creates_input_files_list_model(self):
        self.assertIsInstance(
            self.controller.inputFilesListModel, SafecorInputFilesListModel
        )

    def test_initial_properties(self):
        self.assertFalse(self.controller.ready)
        self.assertEqual(self.controller.currentFolder, "")
        self.assertEqual(self.controller.currentDisk, "")
        self.assertEqual(self.controller.currentStep, "")
        self.assertEqual(self.controller.currentFilepath, "")
        self.assertEqual(self.controller.currentFiletype, FileType.Unknown.value)
        self.assertEqual(self.controller.language, "")
        self.assertEqual(self.controller.batteryLevel, 0)
        self.assertFalse(self.controller.plugged)
        self.assertTrue(self.controller.handheld)
        self.assertFalse(self.controller.sourceReady)
        self.assertEqual(self.controller.repositoryPath, "")

    def test_repository_path_devmode(self):
        # DEVMODE is forced by conftest: the media path is the fake tree,
        # without a trailing slash, per current disk
        self.controller._ApplicationController__handle_list_disks({"disks": ["usb1"]})
        self.assertEqual(self.controller.repositoryPath, "/tmp/saphir/media/usb1")

        self.controller.on_disk_selected("usb2")
        self.assertEqual(self.controller.repositoryPath, "/tmp/saphir/media/usb2")


class TestRepositoryPath(ApplicationControllerTestCase):
    def test_repository_path_production(self):
        with patch("Viewer.application_controller.DevModeHelper") as mock_dev:
            mock_dev.DEVMODE = False
            self.controller._ApplicationController__handle_list_disks(
                {"disks": ["usb1"]}
            )
            self.assertEqual(self.controller.repositoryPath, "/media/usb/usb1")

    def test_repository_path_is_empty_without_disk(self):
        self.assertEqual(self.controller.repositoryPath, "")

    def test_repository_path_notifies_on_disk_change(self):
        events = []
        self.controller.repositoryPathChanged.connect(lambda: events.append(1))

        self.controller._ApplicationController__handle_list_disks({"disks": ["usb1"]})
        self.assertEqual(self.controller.repositoryPath, "/tmp/saphir/media/usb1")
        self.assertEqual(len(events), 1)

        self.controller.on_disk_selected("usb2")
        self.assertEqual(self.controller.repositoryPath, "/tmp/saphir/media/usb2")
        self.assertEqual(len(events), 2)


class TestStart(ApplicationControllerTestCase):
    def test_devmode_uses_dev_mqtt_client(self):
        with patch("Viewer.application_controller.DevModeHelper") as mock_dev:
            mock_dev.DEVMODE = True
            mock_dev.create_mqtt_client.return_value = "dev-mqtt-client"
            self.controller.start(MagicMock())

        self.api.add_ready_callback.assert_called_once()
        self.api.start.assert_called_once()
        kwargs = self.api.start.call_args.kwargs
        self.assertEqual(kwargs["mqtt_client"], "dev-mqtt-client")
        self.assertEqual(kwargs["domain_identifier"], "Viewer")
        self.assertTrue(kwargs["recording"])
        self.assertEqual(kwargs["logfile"].split("/")[-1], "saphir.log")

    def test_production_uses_domu_mqtt_client(self):
        with (
            patch("Viewer.application_controller.DevModeHelper") as mock_dev,
            patch("Viewer.application_controller.MqttFactory") as mock_factory,
        ):
            mock_dev.DEVMODE = False
            mock_factory.create_mqtt_client_domu.return_value = "domu-mqtt-client"
            self.controller.start(MagicMock())

        self.api.start.assert_called_once()
        self.assertEqual(
            self.api.start.call_args.kwargs["mqtt_client"], "domu-mqtt-client"
        )


class TestReadyFlow(ApplicationControllerTestCase):
    def test_on_api_ready_subscribes_expected_topics(self):
        mids = self._ready_flow()

        self.assertEqual(
            mids,
            [
                Topics.DISK_STATE,
                f"{Topics.LIST_DISKS}/response",
                f"{Topics.LIST_FILES}/response",
                f"{Topics.DISCOVER_COMPONENTS}/response",
                f"{Topics.ENERGY_STATE}/response",
                f"{Topics.DEFAULT_LANGUAGE}/response",
            ],
        )

    def test_ready_callback_fired_when_all_subscribed(self):
        ready = MagicMock()
        with (
            patch("Viewer.application_controller.DevModeHelper") as mock_dev,
            patch("Viewer.application_controller.threading.Timer") as mock_timer,
        ):
            mock_dev.DEVMODE = True
            self.controller.start(ready)

            mids = [1, 2, 3, 4, 5, 6]
            self.api.subscribe.side_effect = lambda topic: (True, mids.pop())
            self.controller._ApplicationController__on_api_ready()

            for mid in [6, 5, 4, 3, 2]:
                self.controller._ApplicationController__on_subscribed(mid)
                ready.assert_not_called()

            self.controller._ApplicationController__on_subscribed(1)
            ready.assert_called_once()

        self.api.notify_gui_ready.assert_called_once()
        self.api.get_default_language.assert_called_once()
        self.api.get_disks_list.assert_called_once()
        self.api.request_energy_state.assert_called_once()
        mock_timer.assert_called_once()

    def test_on_subscribed_ignores_unknown_mid(self):
        mids = self._ready_flow()
        self.controller._ApplicationController__on_subscribed(999)
        self.assertEqual(len(mids), 6)


class TestMountReadiness(ApplicationControllerTestCase):
    def test_devmode_mount_gate_bypassed(self):
        # DEVMODE is forced by conftest: the gate is bypassed in
        # __on_api_ready
        self._trigger_api_ready()
        self.assertTrue(self.controller._ApplicationController__usb_mount_ready)

    def test_production_mount_not_ready_is_not_ready(self):
        with (
            patch("Viewer.application_controller.DevModeHelper") as mock_dev,
            patch("Viewer.application_controller.System") as mock_system,
        ):
            mock_dev.DEVMODE = False
            mock_system.return_value.is_usb_mountpoint_ready.return_value = False

            self._trigger_api_ready()
            # The callback is registered with the platform watcher
            mock_system.return_value.on_usb_mountpoint_ready.assert_called_once()
            self.assertFalse(self.controller._ApplicationController__usb_mount_ready)

            # A disk is connected but the mount is not ready: not ready
            self.controller._ApplicationController__handle_disk_state(
                {"disk": "usb1", "state": DiskState.CONNECTED.value}
            )
            self.assertFalse(self.controller.ready)

    def test_production_mount_ready_callback_makes_ready(self):
        with (
            patch("Viewer.application_controller.DevModeHelper") as mock_dev,
            patch("Viewer.application_controller.System") as mock_system,
        ):
            mock_dev.DEVMODE = False
            mock_system.return_value.is_usb_mountpoint_ready.return_value = False

            self._trigger_api_ready()
            callback = mock_system.return_value.on_usb_mountpoint_ready.call_args[0][0]

            self.controller._ApplicationController__handle_disk_state(
                {"disk": "usb1", "state": DiskState.CONNECTED.value}
            )
            self.assertFalse(self.controller.ready)

            # The mount point becomes ready: the readiness is re-evaluated
            callback()
            self.assertTrue(self.controller.ready)

    def test_production_mount_already_ready(self):
        with (
            patch("Viewer.application_controller.DevModeHelper") as mock_dev,
            patch("Viewer.application_controller.System") as mock_system,
        ):
            mock_dev.DEVMODE = False
            mock_system.return_value.is_usb_mountpoint_ready.return_value = True

            self._trigger_api_ready()
            self.assertTrue(self.controller._ApplicationController__usb_mount_ready)

            self.controller._ApplicationController__handle_disk_state(
                {"disk": "usb1", "state": DiskState.CONNECTED.value}
            )
            self.assertTrue(self.controller.ready)

    def test_mount_ready_without_disk_is_not_ready(self):
        self._make_mount_ready()
        self.assertFalse(self.controller.ready)

    def test_mount_ready_callback_is_idempotent(self):
        events = []
        self.controller.readyChanged.connect(lambda v: events.append(v))
        self._make_mount_ready()
        self._make_mount_ready()
        self.assertEqual(events, [])


class TestDiskState(ApplicationControllerTestCase):
    def test_connected_disk_marks_ready(self):
        events = []
        self.controller.readyChanged.connect(lambda v: events.append(v))
        self._make_mount_ready()
        self.controller._ApplicationController__handle_disk_state(
            {"disk": "usb1", "state": DiskState.CONNECTED.value}
        )
        self.assertTrue(self.controller.ready)
        self.assertEqual(events, [True])
        self.assertIn("usb1", self.controller.disks)

    def test_disconnected_disk_clears_ready(self):
        self._make_mount_ready()
        self.controller._ApplicationController__handle_disk_state(
            {"disk": "usb1", "state": DiskState.CONNECTED.value}
        )
        self.assertTrue(self.controller.ready)
        self.controller._ApplicationController__handle_disk_state(
            {"disk": "usb1", "state": DiskState.DISCONNECTED.value}
        )
        self.assertFalse(self.controller.ready)

    def test_stale_current_disk_is_reset(self):
        disk_events = []
        repo_events = []
        self.controller.currentDiskChanged.connect(lambda: disk_events.append(1))
        self.controller.repositoryPathChanged.connect(lambda: repo_events.append(1))

        self._make_mount_ready()
        self.controller._ApplicationController__handle_list_disks({"disks": ["usb1"]})
        self.assertEqual(self.controller.currentDisk, "usb1")
        self.assertEqual(self.controller.repositoryPath, "/tmp/saphir/media/usb1")
        nb_disk_events = len(disk_events)
        nb_repo_events = len(repo_events)

        # The current disk is disconnected
        self.controller._ApplicationController__handle_disk_state(
            {"disk": "usb1", "state": DiskState.DISCONNECTED.value}
        )
        self.assertEqual(self.controller.currentDisk, "")
        self.assertEqual(self.controller.repositoryPath, "")
        self.assertEqual(len(disk_events), nb_disk_events + 1)
        self.assertEqual(len(repo_events), nb_repo_events + 1)

    def test_missing_disk_is_an_error(self):
        self.controller._ApplicationController__handle_disk_state(
            {"state": "connected"}
        )
        self.api.error.assert_called_once()

    def test_missing_state_is_an_error(self):
        self.controller._ApplicationController__handle_disk_state({"disk": "usb1"})
        self.api.error.assert_called_once()


class TestListDisks(ApplicationControllerTestCase):
    def test_list_disks_sets_current_disk_and_requests_files(self):
        self._make_mount_ready()
        self.controller._ApplicationController__handle_list_disks(
            {"disks": ["usb1", "usb2"]}
        )
        self.assertTrue(self.controller.ready)
        self.assertEqual(self.controller.currentDisk, "usb1")
        self.assertTrue(self.controller.sourceReady)
        self.api.get_files_list.assert_called_once_with(
            "usb1", True, "", ViewerConstants.FILES_FILTERS
        )

    def test_empty_list_disks_not_ready(self):
        self._make_mount_ready()
        self.controller._ApplicationController__handle_list_disks({"disks": []})
        self.assertFalse(self.controller.ready)
        self.api.info.assert_called()
        self.api.get_files_list.assert_not_called()

    def test_malformed_payload_is_an_error(self):
        self.controller._ApplicationController__handle_list_disks({})
        self.api.error.assert_called_once()
        self.api.get_files_list.assert_not_called()


class TestListFiles(ApplicationControllerTestCase):
    def test_list_files_populates_model(self):
        events = []
        self.controller.filesListChanged.connect(lambda: events.append("reset"))
        self.controller._ApplicationController__handle_list_files(
            {
                "disk": "usb1",
                "files": [
                    {"path": "/folder", "name": "photo.jpg"},
                    {"path": "/folder", "name": "notes.txt"},
                ],
            }
        )
        model = self.controller.inputFilesListModel
        self.assertEqual(model.rowCount(), 2)
        self.assertEqual(self.controller.currentFolder, "/folder")
        self.assertEqual(events, ["reset"])
        names = {model.data(model.index(i, 0), 0x100 + 2) for i in range(2)}
        self.assertEqual(names, {"photo.jpg", "notes.txt"})

    def test_list_files_builds_filepaths(self):
        self.controller._ApplicationController__handle_list_files(
            {"disk": "usb1", "files": [{"path": "/folder", "name": "photo.jpg"}]}
        )
        model = self.controller.inputFilesListModel
        self.assertEqual(model.data(model.index(0, 0), 0x100 + 3), "/folder/photo.jpg")

    def test_list_files_root_path_has_no_double_slash(self):
        self.controller._ApplicationController__handle_list_files(
            {"disk": "usb1", "files": [{"path": "/", "name": "photo.jpg"}]}
        )
        model = self.controller.inputFilesListModel
        self.assertEqual(model.data(model.index(0, 0), 0x100 + 3), "/photo.jpg")

    def test_missing_disk_is_an_error(self):
        self.controller._ApplicationController__handle_list_files({"files": []})
        self.api.error.assert_called_once()

    def test_missing_files_is_an_error(self):
        self.controller._ApplicationController__handle_list_files(
            {"disk": "usb1", "files": None}
        )
        self.api.error.assert_called_once()


class TestViewFile(ApplicationControllerTestCase):
    def test_native_file_is_viewed_directly(self):
        # Safecor v2: no repository staging, the relative filepath is used
        # as-is (the media path comes from repositoryPath in QML)
        self.controller._ApplicationController__handle_list_disks({"disks": ["usb1"]})
        self.controller.view_file("/folder/photo.jpg")

        self.api.read_file.assert_not_called()
        self.assertEqual(self.controller.currentFilepath, "/folder/photo.jpg")
        self.assertEqual(self.controller.currentFiletype, FileType.Image.value)

    def test_office_file_is_converted_from_the_media(self):
        with patch("Viewer.application_controller.OfficeHelper") as mock_office:
            mock_office.convert_to_pdf.return_value = "/tmp/doc.pdf"
            self.controller._ApplicationController__handle_list_disks(
                {"disks": ["usb1"]}
            )
            self.controller.view_file("/folder/doc.docx")

        mock_office.convert_to_pdf.assert_called_once_with("usb1", "/folder/doc.docx")
        self.assertEqual(self.controller.currentFilepath, "/tmp/doc.pdf")
        self.assertEqual(self.controller.currentFiletype, FileType.Pdf.value)
        self.assertEqual(self.controller.currentStep, "File file has been converted")

    def test_office_file_without_disk(self):
        with patch("Viewer.application_controller.OfficeHelper") as mock_office:
            mock_office.convert_to_pdf.return_value = "/tmp/doc.pdf"
            self.controller.view_file("/folder/doc.docx")

        # No disk selected: the conversion is still attempted with an
        # empty disk
        mock_office.convert_to_pdf.assert_called_once_with("", "/folder/doc.docx")

    def test_native_file_without_disk(self):
        self.controller.view_file("/folder/photo.jpg")
        self.api.read_file.assert_not_called()
        self.assertEqual(self.controller.currentFilepath, "/folder/photo.jpg")

    def test_pdf_file_is_viewed_directly(self):
        self.controller._ApplicationController__handle_list_disks({"disks": ["usb1"]})
        with patch("Viewer.application_controller.OfficeHelper") as mock_office:
            self.controller.view_file("/folder/report.pdf")

        mock_office.convert_to_pdf.assert_not_called()
        self.assertEqual(self.controller.currentFilepath, "/folder/report.pdf")
        self.assertEqual(self.controller.currentFiletype, FileType.Pdf.value)


class TestEnergyState(ApplicationControllerTestCase):
    def test_energy_state_updates_properties(self):
        battery_events = []
        plugged_events = []
        self.controller.batteryLevelChanged.connect(lambda: battery_events.append(1))
        self.controller.pluggedChanged.connect(lambda: plugged_events.append(1))
        self.controller._ApplicationController__handle_energy_state(
            {"battery_level": 55, "plugged": 1}
        )
        self.assertEqual(self.controller.batteryLevel, 55)
        self.assertTrue(self.controller.plugged)
        self.assertEqual(len(battery_events), 1)
        self.assertEqual(len(plugged_events), 1)

    def test_malformed_energy_state_ignored(self):
        self.controller._ApplicationController__handle_energy_state({})
        self.assertEqual(self.controller.batteryLevel, 0)
        self.assertFalse(self.controller.plugged)


class TestMessageDispatch(ApplicationControllerTestCase):
    def test_dispatch_by_topic(self):
        self._make_mount_ready()
        self.controller._ApplicationController__on_message_received(
            Topics.DISK_STATE, {"disk": "usb1", "state": "connected"}
        )
        self.assertTrue(self.controller.ready)

        self.controller._ApplicationController__on_message_received(
            f"{Topics.LIST_DISKS}/response", {"disks": []}
        )
        self.assertFalse(self.controller.ready)

    def test_dispatch_list_files(self):
        self.controller._ApplicationController__on_message_received(
            f"{Topics.LIST_FILES}/response",
            {"disk": "usb1", "files": [{"path": "/", "name": "photo.jpg"}]},
        )
        self.assertEqual(self.controller.inputFilesListModel.rowCount(), 1)

    def test_dispatch_energy_state(self):
        self.controller._ApplicationController__on_message_received(
            f"{Topics.ENERGY_STATE}/response", {"battery_level": 42, "plugged": 0}
        )
        self.assertEqual(self.controller.batteryLevel, 42)
        self.assertFalse(self.controller.plugged)

    def test_language_response_installs_translations(self):
        with patch("Viewer.application_controller.QCoreApplication"):
            self.controller._ApplicationController__on_message_received(
                f"{Topics.DEFAULT_LANGUAGE}/response", {"language": "fr"}
            )
        self.assertEqual(self.controller.language, "fr")

    def test_language_response_without_language_key_ignored(self):
        self.controller._ApplicationController__on_message_received(
            f"{Topics.DEFAULT_LANGUAGE}/response", {}
        )
        self.assertEqual(self.controller.language, "")


class TestSlots(ApplicationControllerTestCase):
    def test_go_to_folder(self):
        self.controller._ApplicationController__handle_list_disks({"disks": ["usb1"]})
        self.controller.go_to_folder("/sub/folder")
        self.assertEqual(
            self.api.get_files_list.call_args,
            (("usb1", True, "/sub/folder", ViewerConstants.FILES_FILTERS), {}),
        )

    def test_go_to_parent_folder(self):
        self.controller._ApplicationController__handle_list_disks({"disks": ["usb1"]})
        self.controller._ApplicationController__handle_list_files(
            {"disk": "usb1", "files": [{"path": "/a/b", "name": "f.jpg"}]}
        )
        self.controller.go_to_parent_folder()
        self.assertEqual(
            self.api.get_files_list.call_args,
            (("usb1", True, "/a", ViewerConstants.FILES_FILTERS), {}),
        )

    def test_on_disk_selected(self):
        disk_events = []
        repo_events = []
        self.controller.currentDiskChanged.connect(lambda: disk_events.append(1))
        self.controller.repositoryPathChanged.connect(lambda: repo_events.append(1))
        self.controller.on_disk_selected("usb2")
        self.assertEqual(self.controller.currentDisk, "usb2")
        self.assertEqual(len(disk_events), 1)
        self.assertEqual(len(repo_events), 1)
        self.api.get_files_list.assert_called_once_with(
            "usb2", True, "", ViewerConstants.FILES_FILTERS
        )

    def test_clear_current_file(self):
        self.controller._ApplicationController__handle_list_disks({"disks": ["usb1"]})
        self.controller.view_file("/folder/photo.jpg")
        self.controller.clear_current_file()
        self.assertEqual(self.controller.currentFilepath, "")

    def test_shutdown(self):
        self.controller.shutdown()
        self.api.shutdown.assert_called_once()

    def test_back_to_saphir(self):
        self.controller.back_to_saphir()
        self.api.switch_gui.assert_called_once_with("saphir-gui")


class TestFileTypeDetection(ApplicationControllerTestCase):
    def test_detection_per_extension(self):
        get_file_type = self.controller._ApplicationController__get_file_type
        self.assertEqual(get_file_type("photo.jpg"), FileType.Image)
        self.assertEqual(get_file_type("video.mp4"), FileType.Video)
        self.assertEqual(get_file_type("sheet.xlsx"), FileType.Office)
        self.assertEqual(get_file_type("doc.docx"), FileType.Office)
        self.assertEqual(get_file_type("slides.pptx"), FileType.Office)
        self.assertEqual(get_file_type("song.mp3"), FileType.Audio)
        self.assertEqual(get_file_type("doc.pdf"), FileType.Pdf)
        self.assertEqual(get_file_type("unknown.xyz"), FileType.Unknown)
        self.assertEqual(get_file_type(None), FileType.Unknown)


class TestSetters(ApplicationControllerTestCase):
    def test_set_ready_emits_only_on_change(self):
        events = []
        self.controller.readyChanged.connect(lambda v: events.append(v))
        self.controller._ApplicationController__set_ready(False)
        self.assertEqual(events, [])
        self.controller._ApplicationController__set_ready(True)
        self.assertEqual(events, [True])

    def test_set_current_step_noop_when_same(self):
        events = []
        self.controller.currentStepChanged.connect(lambda: events.append(1))
        self.controller._ApplicationController__set_current_step("step 1")
        self.controller._ApplicationController__set_current_step("step 1")
        self.assertEqual(len(events), 1)

    def test_set_current_filepath_emits_both_signals(self):
        path_events = []
        type_events = []
        self.controller.currentFilepathChanged.connect(lambda: path_events.append(1))
        self.controller.currentFiletypeChanged.connect(lambda: type_events.append(1))
        self.controller._ApplicationController__set_current_filepath(
            "/folder/photo.jpg"
        )
        self.assertEqual(len(path_events), 1)
        self.assertEqual(len(type_events), 1)

    def test_set_current_filepath_noop_when_same(self):
        events = []
        self.controller.currentFilepathChanged.connect(lambda: events.append(1))
        self.controller._ApplicationController__set_current_filepath(
            "/folder/photo.jpg"
        )
        self.controller._ApplicationController__set_current_filepath(
            "/folder/photo.jpg"
        )
        self.assertEqual(len(events), 1)

    def test_set_current_disk_emits_disk_and_repository_signals(self):
        disk_events = []
        repo_events = []
        self.controller.currentDiskChanged.connect(lambda: disk_events.append(1))
        self.controller.repositoryPathChanged.connect(lambda: repo_events.append(1))
        self.controller._ApplicationController__set_current_disk("usb1")
        self.assertEqual(len(disk_events), 1)
        self.assertEqual(len(repo_events), 1)

    def test_on_shutdown_is_a_noop(self):
        self.controller._ApplicationController__on_shutdown(True, "test")

    def test_request_energy_state_disabled(self):
        self.controller._ApplicationController__monitor_energy = False
        self.controller._ApplicationController__request_energy_state()
        self.api.request_energy_state.assert_not_called()

    def test_set_source_ready(self):
        events = []
        self.controller.sourceReadyChanged.connect(lambda: events.append(1))
        self.controller._ApplicationController__set_source_ready(True)
        self.assertTrue(self.controller.sourceReady)
        self.assertEqual(len(events), 1)


class TestTranslations(ApplicationControllerTestCase):
    def test_install_translations_same_language_is_noop(self):
        with (
            patch("Viewer.application_controller.QCoreApplication"),
            patch("Viewer.application_controller.QTranslator") as mock_translator,
        ):
            self.controller._ApplicationController__install_translations("fr")
            self.assertEqual(mock_translator.call_count, 1)
            self.controller._ApplicationController__install_translations("fr")
            self.assertEqual(mock_translator.call_count, 1)

    def test_install_translations_empty_language_removes_translator(self):
        with (
            patch("Viewer.application_controller.QCoreApplication") as mock_app,
            patch("Viewer.application_controller.QTranslator"),
        ):
            self.controller._ApplicationController__install_translations("fr")
            self.controller._ApplicationController__install_translations("")
            mock_app.instance.return_value.removeTranslator.assert_called_once()

    def test_set_language_property(self):
        with (
            patch("Viewer.application_controller.QCoreApplication"),
            patch("Viewer.application_controller.QTranslator"),
        ):
            self.controller.language = "fr"
            self.assertEqual(self.controller.language, "fr")


class TestDevModeHelper(unittest.TestCase):
    def test_media_path(self):
        # The fake media tree root (Safecor v2 USB direct mount emulation)
        self.assertEqual(DevModeHelper.get_media_path(), "/tmp/saphir/media")

    def test_create_mqtt_client_points_at_local_broker(self):
        client = DevModeHelper.create_mqtt_client("Viewer")
        self.assertEqual(client.identifier, "Viewer")
        self.assertEqual(client.connection_type, ConnectionType.TCP_DEBUG)
        self.assertEqual(client.connection_string, "localhost")

    def test_set_qt_plugins_path(self):
        saved = os.environ.get("QT_QPA_PLATFORM_PLUGIN_PATH")
        try:
            with patch.dict(os.environ, {"VIRTUAL_ENV": "/fake/venv"}):
                DevModeHelper.set_qt_plugins_path()
                self.assertEqual(
                    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"],
                    "/fake/venv/lib/python3.14/site-packages/"
                    "PySide6/Qt/plugins/platforms",
                )
        finally:
            if saved is None:
                os.environ.pop("QT_QPA_PLATFORM_PLUGIN_PATH", None)
            else:
                os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = saved


if __name__ == "__main__":
    unittest.main()

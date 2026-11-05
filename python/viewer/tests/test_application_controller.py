"""Unit tests for the viewer ApplicationController (plan 13.2)."""

import unittest
from unittest.mock import MagicMock, patch

from safecor import DiskState, Topics
from Viewer import (
    ApplicationController,
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

    def test_repository_path_devmode(self):
        self.assertEqual(self.controller.repositoryPath, "/tmp/saphir/repository")


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
                Topics.NEW_FILE,
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

            mids = [1, 2, 3, 4, 5, 6, 7]
            self.api.subscribe.side_effect = lambda topic: (True, mids.pop())
            self.controller._ApplicationController__on_api_ready()

            for mid in [7, 6, 5, 4, 3, 2]:
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
        self.assertEqual(len(mids), 7)


class TestDiskState(ApplicationControllerTestCase):
    def test_connected_disk_marks_ready(self):
        events = []
        self.controller.readyChanged.connect(lambda v: events.append(v))
        self.controller._ApplicationController__handle_disk_state(
            {"disk": "usb1", "state": DiskState.CONNECTED.value}
        )
        self.assertTrue(self.controller.ready)
        self.assertEqual(events, [True])
        self.assertIn("usb1", self.controller.disks)

    def test_disconnected_disk_clears_ready(self):
        self.controller._ApplicationController__handle_disk_state(
            {"disk": "usb1", "state": DiskState.CONNECTED.value}
        )
        self.assertTrue(self.controller.ready)
        self.controller._ApplicationController__handle_disk_state(
            {"disk": "usb1", "state": DiskState.DISCONNECTED.value}
        )
        self.assertFalse(self.controller.ready)

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


class TestNewFile(ApplicationControllerTestCase):
    def test_office_file_is_converted_to_pdf(self):
        with patch("Viewer.application_controller.OfficeHelper") as mock_office:
            mock_office.convert_to_pdf.return_value = "/tmp/doc.pdf"
            self.controller._ApplicationController__handle_new_file(
                {"filepath": "/folder/doc.docx"}
            )

        mock_office.convert_to_pdf.assert_called_once_with("/folder/doc.docx")
        self.assertEqual(self.controller.currentFilepath, "/tmp/doc.pdf")
        self.assertEqual(self.controller.currentFiletype, FileType.Pdf.value)
        self.assertEqual(self.controller.currentStep, "File file has been converted")

    def test_image_file_is_not_converted(self):
        with patch("Viewer.application_controller.OfficeHelper") as mock_office:
            self.controller._ApplicationController__handle_new_file(
                {"filepath": "/folder/photo.jpg"}
            )

        mock_office.convert_to_pdf.assert_not_called()
        self.assertEqual(self.controller.currentFilepath, "/folder/photo.jpg")
        self.assertEqual(self.controller.currentFiletype, FileType.Image.value)

    def test_malformed_payload_sets_error_step(self):
        self.controller._ApplicationController__handle_new_file({})
        self.assertEqual(
            self.controller.currentStep, "An error occured when reading the file."
        )

    def test_view_file_reads_the_disk_file(self):
        self.controller._ApplicationController__handle_list_disks({"disks": ["usb1"]})
        self.controller.view_file("/folder/photo.jpg")
        self.api.read_file.assert_called_once_with("usb1", "/folder/photo.jpg")
        self.assertEqual(self.controller.currentStep, "Reading the file...")


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

    def test_dispatch_new_file(self):
        self.controller._ApplicationController__on_message_received(
            Topics.NEW_FILE, {"filepath": "/photo.jpg"}
        )
        self.assertEqual(self.controller.currentFilepath, "/photo.jpg")

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
        events = []
        self.controller.currentDiskChanged.connect(lambda: events.append(1))
        self.controller.on_disk_selected("usb2")
        self.assertEqual(self.controller.currentDisk, "usb2")
        self.assertEqual(len(events), 1)
        self.api.get_files_list.assert_called_once_with(
            "usb2", True, "", ViewerConstants.FILES_FILTERS
        )

    def test_clear_current_file(self):
        self.controller._ApplicationController__handle_new_file(
            {"filepath": "/folder/photo.jpg"}
        )
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

    def test_on_shutdown_is_a_noop(self):
        self.controller._ApplicationController__on_shutdown(True, "test")

    def test_request_energy_state_disabled(self):
        self.controller._ApplicationController__monitor_energy = False
        self.controller._ApplicationController__request_energy_state()
        self.api.request_energy_state.assert_not_called()

    def test_repository_path_production(self):
        with patch("Viewer.application_controller.DevModeHelper") as mock_dev:
            mock_dev.DEVMODE = False
            self.assertEqual(self.controller.repositoryPath, "/mnt/storage")

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


if __name__ == "__main__":
    unittest.main()

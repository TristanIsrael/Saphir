import os
import unittest
from unittest.mock import patch, MagicMock
from PySide6.QtCore import QModelIndex, Qt
from libsaphir import FileStatus
from Saphir import (
    QueueListModel,
    ComponentsModel,
    SystemInformationModel,
    LogListModel,
    MessagesListModel,
    SafecorInputFilesListModel,
    SafecorInputFilesListProxyModel,
    SafecorOutputFilesListProxyModel,
)
from Saphir import Roles


def make_file(filepath, name, ftype="file", status=FileStatus.FileStatusUndefined, **kw):
    d = {"filepath": filepath, "name": name, "path": "/", "type": ftype, "status": status, "progress": 0, "selected": False}
    d.update(kw)
    return d


class TestQueueListModel(unittest.TestCase):

    def setUp(self):
        self.files = {
            "/clean.txt": make_file("/clean.txt", "clean.txt", status=FileStatus.FileClean),
            "/infected.txt": make_file("/infected.txt", "infected.txt", status=FileStatus.FileInfected),
            "/pending.txt": make_file("/pending.txt", "pending.txt", status=FileStatus.FileAnalysing),
        }
        self.model = QueueListModel(self.files)

    def test_row_count_all(self):
        self.assertEqual(self.model.rowCount(), 3)

    def test_row_count_empty(self):
        model = QueueListModel({})
        self.assertEqual(model.rowCount(), 0)

    def test_data_filename(self):
        idx = self.model.index(0, 0)
        self.assertIn("clean.txt", self.model.data(idx, Roles.RoleFilename))

    def test_data_invalid_index(self):
        self.assertIsNone(self.model.data(QModelIndex()))

    def test_data_status(self):
        for i in range(self.model.rowCount()):
            val = self.model.data(self.model.index(i, 0), Roles.RoleStatus)
            self.assertIsNotNone(val)

    def test_data_infected(self):
        for i in range(self.model.rowCount()):
            idx = self.model.index(i, 0)
            if self.model.data(idx, Roles.RoleFilename) == "infected.txt":
                self.assertTrue(self.model.data(idx, Roles.RoleInfected))

    def test_role_names(self):
        roles = self.model.roleNames()
        self.assertIn(Roles.RoleFilename, roles)
        self.assertIn(Roles.RoleStatus, roles)

    def test_filter_clean(self):
        self.assertTrue(self.model.get_filter_clean())
        self.model.set_filter_clean(False)
        self.assertFalse(self.model.get_filter_clean())

    def test_filter_infected(self):
        self.assertTrue(self.model.get_filter_infected())
        self.model.set_filter_infected(False)
        self.assertFalse(self.model.get_filter_infected())

    def test_filter_other(self):
        self.assertTrue(self.model.get_filter_other())
        self.model.set_filter_other(False)
        self.assertFalse(self.model.get_filter_other())

    def test_filter_excludes_infected(self):
        self.model.set_filter_infected(False)
        self.model.set_filter_clean(False)
        self.model.set_filter_other(True)
        names = [self.model.data(self.model.index(i, 0), Roles.RoleFilename) for i in range(self.model.rowCount())]
        self.assertNotIn("infected.txt", names)

    def test_on_file_updated_existing(self):
        self.model.on_file_updated("/clean.txt", ["progress"])
        self.assertEqual(self.model.rowCount(), 3)

    def test_on_file_updated_nonexistent(self):
        self.model.on_file_updated("/nonexistent.txt", ["status"])
        self.assertEqual(self.model.rowCount(), 3)

    def test_on_file_updated_status_change(self):
        self.files["/pending.txt"]["status"] = FileStatus.FileClean
        self.model.on_file_updated("/pending.txt", ["status"])

    def test_on_file_updated_not_in_cache(self):
        self.model.set_filter_infected(False)
        self.model.set_filter_clean(False)
        self.model.set_filter_other(True)
        self.files["/infected.txt"]["status"] = FileStatus.FileClean
        self.model.on_file_updated("/infected.txt", ["status"])

    def test_on_file_updated_remove_from_cache(self):
        self.model.set_filter_clean(False)
        self.model.set_filter_infected(True)
        self.model.set_filter_other(True)
        self.files["/clean.txt"]["status"] = FileStatus.FileClean
        self.model.on_file_updated("/clean.txt", ["status"])
        names = [self.model.data(self.model.index(i, 0), Roles.RoleFilename) for i in range(self.model.rowCount())]
        self.assertNotIn("clean.txt", names)

    def test_data_progress(self):
        for i in range(self.model.rowCount()):
            val = self.model.data(self.model.index(i, 0), Roles.RoleProgress)
            self.assertIsInstance(val, int)

    def test_data_selected(self):
        for i in range(self.model.rowCount()):
            val = self.model.data(self.model.index(i, 0), Roles.RoleSelected)
            self.assertIsInstance(val, bool)

    def test_data_path(self):
        idx = self.model.index(0, 0)
        self.assertEqual(self.model.data(idx, Roles.RolePath), "/")

    def test_data_filepath(self):
        idx = self.model.index(0, 0)
        self.assertIn("/", self.model.data(idx, Roles.RoleFilepath))

    def test_reset(self):
        self.model.set_filter_clean(False)
        self.model.reset()
        self.assertEqual(self.model.rowCount(), 2)

    def test_auto_filter_max_rows(self):
        many_files = {f"/f{i}": make_file(f"/f{i}", f"f{i}", status=FileStatus.FileClean) for i in range(1000000)}
        model = QueueListModel(many_files)
        self.assertFalse(model.get_filter_clean())


class TestComponentsModel(unittest.TestCase):

    def setUp(self):
        from safecor import ComponentState
        self.ComponentState = ComponentState
        self.helper = MagicMock()
        self.helper.get_components.return_value = [
            {"type": "antivirus", "label": "ClamAV", "state": ComponentState.READY},
            {"type": "controller", "label": "Disk", "state": ComponentState.STARTING},
        ]
        self.model = ComponentsModel(self.helper)

    def test_row_count(self):
        self.assertEqual(self.model.rowCount(), 2)

    def test_column_count(self):
        self.assertEqual(self.model.columnCount(), 3)

    def test_data_type(self):
        idx = self.model.index(0, 0)
        self.assertEqual(self.model.data(idx), "antivirus")

    def test_data_label(self):
        idx = self.model.index(0, 1)
        self.assertEqual(self.model.data(idx), "ClamAV")

    def test_data_state_ready(self):
        idx = self.model.index(0, 2)
        self.assertEqual(self.model.data(idx), "Ready")

    def test_data_state_starting(self):
        idx = self.model.index(1, 2)
        self.assertEqual(self.model.data(idx), "Starting")

    def test_data_state_error(self):
        self.helper.get_components.return_value = [
            {"type": "av", "label": "E", "state": self.ComponentState.ERROR},
        ]
        idx = self.model.index(0, 2)
        self.assertEqual(self.model.data(idx), "Error")

    def test_data_state_off(self):
        self.helper.get_components.return_value = [
            {"type": "av", "label": "O", "state": self.ComponentState.OFF},
        ]
        idx = self.model.index(0, 2)
        self.assertEqual(self.model.data(idx), "Off")

    def test_data_state_unknown(self):
        self.helper.get_components.return_value = [
            {"type": "av", "label": "U", "state": self.ComponentState.UNKNOWN},
        ]
        idx = self.model.index(0, 2)
        self.assertEqual(self.model.data(idx), "Unknown")

    def test_data_invalid(self):
        self.assertIsNone(self.model.data(QModelIndex()))

    def test_data_non_display_role(self):
        idx = self.model.index(0, 0)
        self.assertIsNone(self.model.data(idx, Qt.EditRole))

    def test_components_updated(self):
        self.model.components_updated()


class TestSystemInformationModel(unittest.TestCase):

    def setUp(self):
        self.model = SystemInformationModel(handheld=True)
        self.model._SystemInformationModel__system_information.clear()
        self.model._SystemInformationModel__system_information_data = {}

    def test_initial_row_count(self):
        self.assertEqual(self.model.rowCount(), 0)

    def test_column_count(self):
        self.assertEqual(self.model.columnCount(), 2)

    def test_information_updated(self):
        self.model.information_updated({"core": {"version": "1.0.0", "debug_on": True}})
        self.assertGreater(self.model.rowCount(), 0)

    def test_get_uuid(self):
        self.model.information_updated({"system": {"uuid": "abc-123"}})
        self.assertEqual(self.model.get_uuid(), "abc-123")

    def test_get_uuid_empty(self):
        self.model.information_updated({})
        self.assertEqual(self.model.get_uuid(), "")

    def test_get_safecor_version(self):
        self.model.information_updated({"core": {"version": "2.0.0"}})
        self.assertEqual(self.model.get_safecor_version(), "2.0.0")

    def test_get_safecor_version_unknown(self):
        self.model.information_updated({})
        self.assertEqual(self.model.get_safecor_version(), "unknown")

    def test_set_battery_level(self):
        self.model.set_battery_level(75)
        self.assertGreater(self.model.rowCount(), 0)

    def test_set_power_plugged(self):
        self.model.set_power_plugged(True)
        self.assertGreater(self.model.rowCount(), 0)

    def test_data_invalid(self):
        self.assertIsNone(self.model.data(QModelIndex()))

    def test_data_key_value(self):
        self.model.information_updated({"core": {"version": "1.0"}})
        idx = self.model.index(0, 0)
        self.assertIsNotNone(self.model.data(idx))


class TestLogListModel(unittest.TestCase):

    def setUp(self):
        self.model = LogListModel()
        self.model._LogListModel__logs = []

    def test_initial_row_count(self):
        self.assertEqual(self.model.rowCount(), 0)

    def test_column_count(self):
        self.assertEqual(self.model.columnCount(), 3)

    def test_data_invalid(self):
        self.assertIsNone(self.model.data(QModelIndex()))

    def test_listen_to_logs(self):
        with patch("Saphir.log_list_model.Api") as mock_api:
            self.model.listen_to_logs()
            mock_api.return_value.add_message_callback.assert_called_once()
            mock_api.return_value.subscribe.assert_called_once()

    def test_on_message_adds_log(self):
        from safecor import Topics
        self.model._LogListModel__on_message(
            f"{Topics.EVENTS}/debug",
            {"module": "Test", "datetime": "2024-01-01 12:00:00.123456", "description": "Hello"}
        )
        self.assertEqual(self.model.rowCount(), 1)

    def test_on_message_data(self):
        from safecor import Topics
        self.model._LogListModel__on_message(
            f"{Topics.EVENTS}/info",
            {"module": "GUI", "datetime": "2024-01-01 12:00:00.123456", "description": "Test"}
        )
        idx = self.model.index(0, 0)
        self.assertEqual(self.model.data(idx, Qt.DisplayRole), "12:00:00.123")
        idx = self.model.index(0, 1)
        self.assertEqual(self.model.data(idx, Qt.DisplayRole), "GUI")
        idx = self.model.index(0, 2)
        self.assertEqual(self.model.data(idx, Qt.DisplayRole), "Test")

    def test_on_message_non_event_topic(self):
        self.model._LogListModel__on_message("other/topic", {"module": "X"})
        self.assertEqual(self.model.rowCount(), 0)

    def test_to_datetime(self):
        result = self.model._LogListModel__to_datetime("2024-01-01 12:34:56.789012")
        self.assertEqual(result, "12:34:56.789")


class TestMessagesListModel(unittest.TestCase):

    def setUp(self):
        self.model = MessagesListModel()
        self.model._MessagesListModel__messages = []

    def test_initial_row_count(self):
        self.assertEqual(self.model.rowCount(), 0)

    def test_add_message(self):
        self.model.addMessage("Hello")
        self.assertEqual(self.model.rowCount(), 1)

    def test_add_multiple(self):
        self.model.addMessage("A")
        self.model.addMessage("B")
        self.assertEqual(self.model.rowCount(), 2)

    def test_data(self):
        self.model.addMessage("Test")
        idx = self.model.index(0, 0)
        self.assertEqual(self.model.data(idx), "Test")

    def test_data_invalid(self):
        self.assertIsNone(self.model.data(QModelIndex()))

    def test_clear(self):
        self.model.addMessage("A")
        self.model.clear()
        self.assertEqual(self.model.rowCount(), 0)


class TestSafecorInputFilesListModel(unittest.TestCase):

    def setUp(self):
        self.files = {
            "/file1.txt": make_file("/file1.txt", "file1.txt", status=FileStatus.FileStatusUndefined),
            "/folder1": make_file("/folder1", "folder1", ftype="folder", status=FileStatus.FileStatusUndefined),
        }
        self.queued = {}
        self.model = SafecorInputFilesListModel(self.files, self.queued)
        self.model.reset()

    def test_row_count(self):
        self.assertEqual(self.model.rowCount(), 2)

    def test_data_filename(self):
        idx = self.model.index(0, 0)
        self.assertEqual(self.model.data(idx, Roles.RoleFilename), "file1.txt")

    def test_data_type(self):
        idx = self.model.index(0, 0)
        self.assertEqual(self.model.data(idx, Roles.RoleType), "file")

    def test_data_filepath(self):
        idx = self.model.index(0, 0)
        self.assertEqual(self.model.data(idx, Roles.RoleFilepath), "/file1.txt")

    def test_data_selected_file(self):
        idx = self.model.index(0, 0)
        self.assertFalse(self.model.data(idx, Roles.RoleSelected))

    def test_data_selected_folder(self):
        idx = self.model.index(1, 0)
        self.assertFalse(self.model.data(idx, Roles.RoleSelected))

    def test_data_inqueue_file(self):
        idx = self.model.index(0, 0)
        self.assertFalse(self.model.data(idx, Roles.RoleInQueue))

    def test_data_inqueue_folder(self):
        idx = self.model.index(1, 0)
        self.assertFalse(self.model.data(idx, Roles.RoleInQueue))

    def test_data_invalid(self):
        self.assertIsNone(self.model.data(QModelIndex()))

    def test_role_names(self):
        roles = self.model.roleNames()
        self.assertIn(Roles.RoleFilename, roles)
        self.assertIn(Roles.RoleType, roles)

    def test_on_file_added(self):
        self.model.on_file_added()

    def test_on_file_updated(self):
        self.model.on_file_updated("/file1.txt", ["status"])

    def test_on_file_updated_nonexistent(self):
        self.model.on_file_updated("/nonexistent", ["status"])

    def test_flags(self):
        idx = self.model.index(0, 0)
        self.assertTrue(self.model.flags(idx) & Qt.ItemIsEditable)

    def test_on_source_changed(self):
        signals = []
        self.model.updateFilesList.connect(lambda: signals.append(True))
        self.model.onSourceChanged()
        self.assertEqual(len(signals), 1)


class TestSafecorInputFilesListProxyModel(unittest.TestCase):

    def setUp(self):
        self.files = {"/f1": make_file("/f1", "f1", status=FileStatus.FileStatusUndefined)}
        self.queued = {}
        self.source = SafecorInputFilesListModel(self.files, self.queued)
        self.source.reset()
        self.proxy = SafecorInputFilesListProxyModel(self.source)

    def test_filter_accepts_all(self):
        self.assertTrue(self.proxy.filterAcceptsRow(0, QModelIndex()))

    def test_current_folder_default(self):
        self.assertEqual(self.proxy.currentFolder, "/")

    def test_set_current_folder(self):
        self.proxy.set_current_folder("/new")
        self.assertEqual(self.proxy.currentFolder, "/new")

    def test_set_current_folder_same(self):
        signals = []
        self.proxy.currentFolderChanged.connect(lambda: signals.append(True))
        self.proxy.set_current_folder("/")
        self.assertEqual(len(signals), 0)


class TestSafecorOutputFilesListProxyModel(unittest.TestCase):

    def _make_source(self, files):
        return QueueListModel(files)

    def test_filter_file_clean_rejected(self):
        files = {"/f1": make_file("/f1", "f1", status=FileStatus.FileClean)}
        source = self._make_source(files)
        proxy = SafecorOutputFilesListProxyModel(source)
        self.assertFalse(proxy.filterAcceptsRow(0, QModelIndex()))

    def test_filter_folder_rejected(self):
        files = {"/d": make_file("/d", "d", ftype="folder", status=FileStatus.FileClean)}
        source = self._make_source(files)
        proxy = SafecorOutputFilesListProxyModel(source)
        self.assertFalse(proxy.filterAcceptsRow(0, QModelIndex()))

    def test_filter_none_status_rejected(self):
        files = {"/f1": make_file("/f1", "f1", status=None)}
        source = self._make_source(files)
        proxy = SafecorOutputFilesListProxyModel(source)
        self.assertFalse(proxy.filterAcceptsRow(0, QModelIndex()))


class TestDevModeHelper(unittest.TestCase):

    def test_create_mqtt_client(self):
        from Saphir.devmode_helper import DevModeHelper
        client = DevModeHelper.create_mqtt_client("test")
        self.assertIsNotNone(client)

    def test_set_qt_plugins_path_no_venv(self):
        from Saphir.devmode_helper import DevModeHelper
        with patch.dict(os.environ, {}, clear=True):
            DevModeHelper.set_qt_plugins_path()

    def test_set_qt_plugins_path_with_venv(self):
        from Saphir.devmode_helper import DevModeHelper
        with patch.dict(os.environ, {"VIRTUAL_ENV": "/tmp/venv"}):
            DevModeHelper.set_qt_plugins_path()
            self.assertIn("QT_QPA_PLATFORM_PLUGIN_PATH", os.environ)


if __name__ == "__main__":
    unittest.main()

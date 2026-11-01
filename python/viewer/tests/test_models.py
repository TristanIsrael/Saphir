"""Unit tests for the viewer file list models and enums (plan 13.3)."""

import unittest

from PySide6.QtCore import Qt
from Viewer import (
    FileType,
    Roles,
    SafecorInputFilesListModel,
    SafecorInputFilesListProxyModel,
    SystemState,
)


class TestSafecorInputFilesListModel(unittest.TestCase):
    def setUp(self):
        self.files = {
            "/folder/photo.jpg": {
                "name": "photo.jpg",
                "path": "/folder",
                "filepath": "/folder/photo.jpg",
                "disk": "usb1",
                "type": 1,
            },
            "/folder/video.mp4": {
                "name": "video.mp4",
                "path": "/folder",
                "filepath": "/folder/video.mp4",
                "disk": "usb1",
                "type": 2,
            },
        }
        self.model = SafecorInputFilesListModel(self.files)

    def test_row_count(self):
        self.assertEqual(self.model.rowCount(), 2)
        self.assertEqual(self.model.rowCount(self.model.index(0, 0)), 0)

    def test_data_file_name(self):
        self.assertEqual(
            self.model.data(self.model.index(0, 0), Roles.RoleFileName), "photo.jpg"
        )
        self.assertEqual(
            self.model.data(self.model.index(1, 0), Roles.RoleFileName), "video.mp4"
        )

    def test_data_file_path(self):
        self.assertEqual(
            self.model.data(self.model.index(0, 0), Roles.RoleFilePath),
            "/folder/photo.jpg",
        )

    def test_data_path(self):
        self.assertEqual(
            self.model.data(self.model.index(0, 0), Roles.RolePath), "/folder"
        )

    def test_data_file_type(self):
        self.assertEqual(self.model.data(self.model.index(0, 0), Roles.RoleFileType), 1)
        self.assertEqual(self.model.data(self.model.index(1, 0), Roles.RoleFileType), 2)

    def test_data_role_id_same_as_filepath(self):
        self.assertEqual(
            self.model.data(self.model.index(0, 0), Roles.RoleId),
            self.model.data(self.model.index(0, 0), Roles.RoleFilePath),
        )

    def test_data_invalid_index_returns_none(self):
        self.assertIsNone(self.model.data(self.model.index(-1, 0), Roles.RoleFileName))

    def test_data_unknown_role_returns_none(self):
        self.assertIsNone(self.model.data(self.model.index(0, 0), Roles.RoleStatus))

    def test_role_names(self):
        roles = self.model.roleNames()
        self.assertEqual(roles[Roles.RoleFileType], b"type")
        self.assertEqual(roles[Roles.RoleFileName], b"filename")
        self.assertEqual(roles[Roles.RolePath], b"path")
        self.assertEqual(roles[Roles.RoleFilePath], b"filepath")
        self.assertEqual(roles[Roles.RoleStatus], b"status")
        self.assertEqual(roles[Roles.RoleId], b"backId")

    def test_reset_notifies(self):
        resets = []
        self.model.modelReset.connect(lambda *args: resets.append(1))
        self.model.reset()
        self.assertEqual(len(resets), 1)


class TestSafecorInputFilesListProxyModel(unittest.TestCase):
    def setUp(self):
        self.files = {
            "/folder/photo.jpg": {
                "name": "photo.jpg",
                "path": "/folder",
                "filepath": "/folder/photo.jpg",
                "disk": "usb1",
                "type": 1,
            },
        }
        self.source = SafecorInputFilesListModel(self.files)
        self.proxy = SafecorInputFilesListProxyModel(self.source)

    def test_proxy_exposes_source_rows(self):
        self.assertEqual(self.proxy.rowCount(), 1)
        self.assertEqual(
            self.proxy.data(self.proxy.index(0, 0), Roles.RoleFileName), "photo.jpg"
        )

    def test_filter_accepts_every_row(self):
        self.assertTrue(self.proxy.filterAcceptsRow(0, self.source.index(0, 0)))

    def test_set_current_folder_emits_signal(self):
        events = []
        self.proxy.currentFolderChanged.connect(lambda: events.append(1))
        self.proxy.set_current_folder("/folder")
        self.assertEqual(self.proxy.currentFolder, "/folder")
        self.assertEqual(len(events), 1)

    def test_set_current_folder_same_value_is_noop(self):
        events = []
        self.proxy.currentFolderChanged.connect(lambda: events.append(1))
        self.proxy.set_current_folder("/")
        self.assertEqual(events, [])

    def test_current_folder_default(self):
        self.assertEqual(self.proxy.currentFolder, "/")


class TestEnums(unittest.TestCase):
    def test_file_type_values_are_sequential(self):
        self.assertEqual(
            [t.value for t in FileType],
            [FileType.Unknown.value, 1, 2, 3, 4, 5],
        )

    def test_file_type_values_are_unique(self):
        self.assertEqual(len({t.value for t in FileType}), len(FileType))

    def test_roles_are_unique_user_roles(self):
        values = [
            Roles.RoleFileType,
            Roles.RoleFileName,
            Roles.RoleFilePath,
            Roles.RolePath,
            Roles.RoleProgress,
            Roles.RoleStatus,
            Roles.RoleInfected,
            Roles.RoleId,
        ]
        self.assertEqual(len(set(values)), len(values))
        for value in values:
            self.assertGreater(value, Qt.UserRole)

    def test_system_state_values(self):
        self.assertEqual(SystemState.SystemInactive.value, 0)


if __name__ == "__main__":
    unittest.main()

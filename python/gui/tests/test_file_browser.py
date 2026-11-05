import unittest
from Saphir import FileBrowser


class TestFileBrowser(unittest.TestCase):

    def setUp(self):
        self.browser = FileBrowser()

    def test_initial_state(self):
        self.assertEqual(self.browser.current_folder, "/")
        self.assertFalse(self.browser.is_enqueuing)
        self.assertEqual(self.browser.folders_to_query, 0)
        self.assertEqual(len(self.browser.input_files_list), 0)

    def test_set_current_folder(self):
        self.browser.current_folder = "/home/user"
        self.assertEqual(self.browser.current_folder, "/home/user")

    def test_current_folder_changed_signal(self):
        signals = []
        self.browser.currentFolderChanged.connect(lambda: signals.append(True))
        self.browser.current_folder = "/new/folder"
        self.assertEqual(len(signals), 1)

    def test_current_folder_changed_signal_on_reset(self):
        signals = []
        self.browser.currentFolderChanged.connect(lambda: signals.append(True))
        self.browser.current_folder = "/some/folder"
        signals.clear()
        self.browser.current_folder = "/another"
        self.assertEqual(len(signals), 1)

    def test_set_is_enqueuing(self):
        self.browser.is_enqueuing = True
        self.assertTrue(self.browser.is_enqueuing)
        self.browser.is_enqueuing = False
        self.assertFalse(self.browser.is_enqueuing)

    def test_set_folders_to_query(self):
        self.browser.folders_to_query = 5
        self.assertEqual(self.browser.folders_to_query, 5)

    def test_add_file(self):
        file = {"name": "test.txt", "type": "file", "size": 100}
        self.browser.add_file("/test.txt", file)
        self.assertIn("/test.txt", self.browser.input_files_list)
        self.assertEqual(self.browser.input_files_list["/test.txt"]["name"], "test.txt")

    def test_get_file(self):
        file = {"name": "test.txt", "type": "file", "size": 100}
        self.browser.add_file("/test.txt", file)
        result = self.browser.get_file("/test.txt")
        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "test.txt")

    def test_get_file_nonexistent(self):
        result = self.browser.get_file("/nonexistent")
        self.assertIsNone(result)

    def test_clear(self):
        file = {"name": "test.txt", "type": "file", "size": 100}
        self.browser.add_file("/test.txt", file)
        self.browser.clear()
        self.assertEqual(len(self.browser.input_files_list), 0)

    def test_reset(self):
        self.browser.current_folder = "/some/folder"
        self.browser.is_enqueuing = True
        self.browser.folders_to_query = 3
        file = {"name": "test.txt", "type": "file", "size": 100}
        self.browser.add_file("/test.txt", file)

        self.browser.reset()

        self.assertEqual(self.browser.current_folder, "/")
        self.assertFalse(self.browser.is_enqueuing)
        self.assertEqual(self.browser.folders_to_query, 0)
        self.assertEqual(len(self.browser.input_files_list), 0)

    def test_reset_emits_signal(self):
        signals = []
        self.browser.currentFolderChanged.connect(lambda: signals.append(True))
        self.browser.current_folder = "/some/folder"
        signals.clear()
        self.browser.reset()
        self.assertEqual(len(signals), 1)

    def test_input_files_list_property(self):
        self.assertIsInstance(self.browser.input_files_list, dict)

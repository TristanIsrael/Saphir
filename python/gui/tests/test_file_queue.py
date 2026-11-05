import unittest
from Saphir import FileQueue
from libsaphir import FileStatus


class TestFileQueue(unittest.TestCase):

    def setUp(self):
        self.queue = FileQueue()

    def test_initial_state(self):
        self.assertEqual(self.queue.count(), 0)
        self.assertEqual(self.queue.size(), 0)
        self.assertFalse(self.queue.contains("/any/file"))

    def test_enqueue_and_count(self):
        file = {"name": "test.txt", "type": "file", "size": 100, "status": FileStatus.FileStatusUndefined}
        self.queue.enqueue("/test.txt", file)
        self.assertEqual(self.queue.count(), 1)
        self.assertTrue(self.queue.contains("/test.txt"))

    def test_enqueue_multiple(self):
        f1 = {"name": "a.txt", "type": "file", "size": 100, "status": FileStatus.FileStatusUndefined}
        f2 = {"name": "b.txt", "type": "file", "size": 200, "status": FileStatus.FileStatusUndefined}
        self.queue.enqueue("/a.txt", f1)
        self.queue.enqueue("/b.txt", f2)
        self.assertEqual(self.queue.count(), 2)

    def test_dequeue(self):
        file = {"name": "test.txt", "type": "file", "size": 100, "status": FileStatus.FileStatusUndefined}
        self.queue.enqueue("/test.txt", file)
        self.queue.dequeue("/test.txt")
        self.assertEqual(self.queue.count(), 0)
        self.assertFalse(self.queue.contains("/test.txt"))

    def test_dequeue_nonexistent(self):
        self.queue.dequeue("/nonexistent")
        self.assertEqual(self.queue.count(), 0)

    def test_clear(self):
        f1 = {"name": "a.txt", "type": "file", "size": 100, "status": FileStatus.FileStatusUndefined}
        f2 = {"name": "b.txt", "type": "file", "size": 200, "status": FileStatus.FileStatusUndefined}
        self.queue.enqueue("/a.txt", f1)
        self.queue.enqueue("/b.txt", f2)
        self.queue.clear()
        self.assertEqual(self.queue.count(), 0)
        self.assertEqual(self.queue.size(), 0)

    def test_get(self):
        file = {"name": "test.txt", "type": "file", "size": 100, "status": FileStatus.FileClean}
        self.queue.enqueue("/test.txt", file)
        result = self.queue.get("/test.txt")
        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "test.txt")

    def test_get_nonexistent(self):
        result = self.queue.get("/nonexistent")
        self.assertIsNone(result)

    def test_add_size(self):
        self.queue.add_size(500)
        self.queue.add_size(300)
        self.assertEqual(self.queue.size(), 800)

    def test_add_size_reset_on_clear(self):
        self.queue.add_size(500)
        self.queue.clear()
        self.assertEqual(self.queue.size(), 0)

    def test_contains(self):
        file = {"name": "test.txt", "type": "file", "size": 100, "status": FileStatus.FileStatusUndefined}
        self.queue.enqueue("/test.txt", file)
        self.assertTrue(self.queue.contains("/test.txt"))
        self.assertFalse(self.queue.contains("/other.txt"))

    def test_folder_contains(self):
        f1 = {"name": "a.txt", "type": "file", "size": 100, "status": FileStatus.FileStatusUndefined}
        f2 = {"name": "b.txt", "type": "file", "size": 200, "status": FileStatus.FileStatusUndefined}
        self.queue.enqueue("/folder/a.txt", f1)
        self.queue.enqueue("/other/b.txt", f2)
        self.assertTrue(self.queue.folder_contains("/folder"))
        self.assertFalse(self.queue.folder_contains("/nonexistent"))

    def test_dequeue_folder(self):
        f1 = {"name": "a.txt", "type": "file", "size": 100, "status": FileStatus.FileStatusUndefined}
        f2 = {"name": "b.txt", "type": "file", "size": 200, "status": FileStatus.FileStatusUndefined}
        f3 = {"name": "c.txt", "type": "file", "size": 300, "status": FileStatus.FileStatusUndefined}
        self.queue.enqueue("/folder/a.txt", f1)
        self.queue.enqueue("/folder/sub/b.txt", f2)
        self.queue.enqueue("/other/c.txt", f3)
        self.queue.dequeue_folder("/folder")
        self.assertEqual(self.queue.count(), 1)
        self.assertTrue(self.queue.contains("/other/c.txt"))
        self.assertFalse(self.queue.contains("/folder/a.txt"))
        self.assertFalse(self.queue.contains("/folder/sub/b.txt"))

    def test_get_clean_files(self):
        f1 = {"name": "a.txt", "type": "file", "size": 100, "status": FileStatus.FileClean}
        f2 = {"name": "b.txt", "type": "file", "size": 200, "status": FileStatus.FileInfected}
        f3 = {"name": "c.txt", "type": "file", "size": 300, "status": FileStatus.FileClean}
        self.queue.enqueue("/a.txt", f1)
        self.queue.enqueue("/b.txt", f2)
        self.queue.enqueue("/c.txt", f3)
        clean = self.queue.get_clean_files()
        self.assertEqual(len(clean), 2)
        paths = [p for p, _ in clean]
        self.assertIn("/a.txt", paths)
        self.assertIn("/c.txt", paths)

    def test_get_transferred_ratio_empty(self):
        self.assertEqual(self.queue.get_transferred_ratio(), 0)

    def test_get_transferred_ratio_no_clean(self):
        f1 = {"name": "a.txt", "type": "file", "size": 100, "status": FileStatus.FileInfected}
        self.queue.enqueue("/a.txt", f1)
        self.assertEqual(self.queue.get_transferred_ratio(), 0)

    def test_get_transferred_ratio_partial(self):
        f1 = {"name": "a.txt", "type": "file", "size": 100, "status": FileStatus.FileClean}
        f2 = {"name": "b.txt", "type": "file", "size": 200, "status": FileStatus.FileCopySuccess}
        f3 = {"name": "c.txt", "type": "file", "size": 300, "status": FileStatus.FileCopyError}
        f4 = {"name": "d.txt", "type": "file", "size": 400, "status": FileStatus.FileClean}
        self.queue.enqueue("/a.txt", f1)
        self.queue.enqueue("/b.txt", f2)
        self.queue.enqueue("/c.txt", f3)
        self.queue.enqueue("/d.txt", f4)
        # 2 clean, 1 success + 1 failed = 2 copied out of 2 clean
        self.assertAlmostEqual(self.queue.get_transferred_ratio(), 1.0)

    def test_items(self):
        f1 = {"name": "a.txt", "type": "file", "size": 100, "status": FileStatus.FileStatusUndefined}
        self.queue.enqueue("/a.txt", f1)
        items = self.queue.items()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0][0], "/a.txt")

    def test_files_property_returns_dict(self):
        self.assertIsInstance(self.queue.files, dict)

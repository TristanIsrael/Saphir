import unittest
from unittest.mock import patch

from libsaphir import FileStatus

from Saphir import FileQueue, TransferController


class TestTransferController(unittest.TestCase):

    def setUp(self):
        self.file_queue = FileQueue()
        self.transfer = TransferController(self.file_queue)

    def test_initial_state(self):
        self.assertFalse(self.transfer.is_started)
        self.assertEqual(self.transfer.copied_files_count, 0)
        self.assertEqual(self.transfer.progress, 0)

    def test_start_sets_state(self):
        f1 = {"name": "a.txt", "type": "file", "size": 100, "status": FileStatus.FileClean}
        self.file_queue.enqueue("/a.txt", f1)

        with patch("Saphir.transfer_controller.threading.Timer"):
            self.transfer.start("source", "target")

        self.assertTrue(self.transfer.is_started)
        self.assertEqual(self.transfer.copied_files_count, 0)

    def test_start_counts_clean_files(self):
        f1 = {"name": "a.txt", "type": "file", "size": 100, "status": FileStatus.FileClean}
        f2 = {"name": "b.txt", "type": "file", "size": 200, "status": FileStatus.FileInfected}
        self.file_queue.enqueue("/a.txt", f1)
        self.file_queue.enqueue("/b.txt", f2)

        with patch("Saphir.transfer_controller.threading.Timer"):
            self.transfer.start("source", "target")

        self.assertEqual(self.transfer.progress, 0)

    def test_on_copy_file_success(self):
        f1 = {"name": "a.txt", "type": "file", "size": 100, "status": FileStatus.FileClean}
        self.file_queue.enqueue("/a.txt", f1)

        with patch("Saphir.transfer_controller.threading.Timer"):
            self.transfer.start("source", "target")

        payload = {"filepath": "/a.txt", "status": "ok", "fingerprint": "abc123"}
        self.transfer.on_copy_file(payload)

        self.assertEqual(self.transfer.copied_files_count, 1)
        self.assertEqual(self.transfer.progress, 1.0)

    def test_on_copy_file_failure(self):
        f1 = {"name": "a.txt", "type": "file", "size": 100, "status": FileStatus.FileClean}
        self.file_queue.enqueue("/a.txt", f1)

        with patch("Saphir.transfer_controller.threading.Timer"):
            self.transfer.start("source", "target")

        payload = {"filepath": "/a.txt", "status": "error", "fingerprint": ""}
        self.transfer.on_copy_file(payload)

        self.assertEqual(self.transfer.copied_files_count, 0)
        self.assertEqual(self.transfer.progress, 0)

    def test_on_copy_file_updates_file_status(self):
        f1 = {"name": "a.txt", "type": "file", "size": 100, "status": FileStatus.FileClean}
        self.file_queue.enqueue("/a.txt", f1)

        with patch("Saphir.transfer_controller.threading.Timer"):
            self.transfer.start("source", "target")

        payload = {"filepath": "/a.txt", "status": "ok", "fingerprint": "abc"}
        self.transfer.on_copy_file(payload)

        self.assertEqual(self.file_queue.get("/a.txt")["status"], FileStatus.FileCopySuccess)

    def test_on_copy_file_failure_status(self):
        f1 = {"name": "a.txt", "type": "file", "size": 100, "status": FileStatus.FileClean}
        self.file_queue.enqueue("/a.txt", f1)

        with patch("Saphir.transfer_controller.threading.Timer"):
            self.transfer.start("source", "target")

        payload = {"filepath": "/a.txt", "status": "error", "fingerprint": ""}
        self.transfer.on_copy_file(payload)

        self.assertEqual(self.file_queue.get("/a.txt")["status"], FileStatus.FileCopyError)

    def test_transfer_complete_signal(self):
        f1 = {"name": "a.txt", "type": "file", "size": 100, "status": FileStatus.FileClean}
        self.file_queue.enqueue("/a.txt", f1)

        with patch("Saphir.transfer_controller.threading.Timer"):
            self.transfer.start("source", "target")

        signals = []
        self.transfer.transferComplete.connect(lambda: signals.append(True))

        payload = {"filepath": "/a.txt", "status": "ok", "fingerprint": "abc"}
        self.transfer.on_copy_file(payload)

        self.assertEqual(len(signals), 1)

    def test_transfer_not_complete_before_all_copied(self):
        f1 = {"name": "a.txt", "type": "file", "size": 100, "status": FileStatus.FileClean}
        f2 = {"name": "b.txt", "type": "file", "size": 200, "status": FileStatus.FileClean}
        self.file_queue.enqueue("/a.txt", f1)
        self.file_queue.enqueue("/b.txt", f2)

        with patch("Saphir.transfer_controller.threading.Timer"):
            self.transfer.start("source", "target")

        signals = []
        self.transfer.transferComplete.connect(lambda: signals.append(True))

        payload1 = {"filepath": "/a.txt", "status": "ok", "fingerprint": "abc"}
        self.transfer.on_copy_file(payload1)

        self.assertEqual(len(signals), 0)
        self.assertEqual(self.transfer.progress, 0.5)

    def test_copied_files_count_changed_signal(self):
        f1 = {"name": "a.txt", "type": "file", "size": 100, "status": FileStatus.FileClean}
        self.file_queue.enqueue("/a.txt", f1)

        with patch("Saphir.transfer_controller.threading.Timer"):
            self.transfer.start("source", "target")

        signals = []
        self.transfer.copiedFilesCountChanged.connect(lambda: signals.append(True))

        payload = {"filepath": "/a.txt", "status": "ok", "fingerprint": "abc"}
        self.transfer.on_copy_file(payload)

        self.assertEqual(len(signals), 1)

    def test_progress_changed_signal(self):
        f1 = {"name": "a.txt", "type": "file", "size": 100, "status": FileStatus.FileClean}
        self.file_queue.enqueue("/a.txt", f1)

        with patch("Saphir.transfer_controller.threading.Timer"):
            self.transfer.start("source", "target")

        signals = []
        self.transfer.transferProgressChanged.connect(lambda: signals.append(True))

        payload = {"filepath": "/a.txt", "status": "ok", "fingerprint": "abc"}
        self.transfer.on_copy_file(payload)

        self.assertGreaterEqual(len(signals), 1)

    def test_on_copy_file_nonexistent(self):
        with patch("Saphir.transfer_controller.threading.Timer"):
            self.transfer.start("source", "target")

        signals = []
        self.transfer.transferComplete.connect(lambda: signals.append(True))

        payload = {"filepath": "/nonexistent", "status": "ok", "fingerprint": "abc"}
        self.transfer.on_copy_file(payload)

        self.assertEqual(len(signals), 0)

    def test_reset(self):
        f1 = {"name": "a.txt", "type": "file", "size": 100, "status": FileStatus.FileClean}
        self.file_queue.enqueue("/a.txt", f1)

        with patch("Saphir.transfer_controller.threading.Timer"):
            self.transfer.start("source", "target")

        payload = {"filepath": "/a.txt", "status": "ok", "fingerprint": "abc"}
        self.transfer.on_copy_file(payload)

        self.transfer.reset()

        self.assertFalse(self.transfer.is_started)
        self.assertEqual(self.transfer.copied_files_count, 0)
        self.assertEqual(self.transfer.progress, 0)

    def test_start_emits_signals(self):
        f1 = {"name": "a.txt", "type": "file", "size": 100, "status": FileStatus.FileClean}
        self.file_queue.enqueue("/a.txt", f1)

        progress_signals = []
        count_signals = []
        self.transfer.transferProgressChanged.connect(lambda: progress_signals.append(True))
        self.transfer.copiedFilesCountChanged.connect(lambda: count_signals.append(True))

        with patch("Saphir.transfer_controller.threading.Timer"):
            self.transfer.start("source", "target")

        self.assertGreaterEqual(len(progress_signals), 1)
        self.assertGreaterEqual(len(count_signals), 1)

    def test_no_clean_files_progress_is_zero(self):
        f1 = {"name": "a.txt", "type": "file", "size": 100, "status": FileStatus.FileInfected}
        self.file_queue.enqueue("/a.txt", f1)

        with patch("Saphir.transfer_controller.threading.Timer"):
            self.transfer.start("source", "target")

        self.assertEqual(self.transfer.progress, 0)

    def test_on_copy_file_fingerprint_match_keeps_success(self):
        f1 = {
            "name": "a.txt",
            "type": "file",
            "size": 100,
            "status": FileStatus.FileClean,
            "fingerprint": "abc123",
        }
        self.file_queue.enqueue("/a.txt", f1)

        with patch("Saphir.transfer_controller.threading.Timer"):
            self.transfer.start("source", "target")

        payload = {"filepath": "/a.txt", "status": "ok", "fingerprint": "abc123"}
        self.transfer.on_copy_file(payload)

        self.assertEqual(self.file_queue.get("/a.txt")["status"], FileStatus.FileCopySuccess)
        self.assertEqual(self.transfer.copied_files_count, 1)

    def test_on_copy_file_fingerprint_mismatch_marks_error(self):
        f1 = {
            "name": "a.txt",
            "type": "file",
            "size": 100,
            "status": FileStatus.FileClean,
            "fingerprint": "abc123",
        }
        self.file_queue.enqueue("/a.txt", f1)

        with patch("Saphir.transfer_controller.threading.Timer"):
            self.transfer.start("source", "target")

        payload = {"filepath": "/a.txt", "status": "ok", "fingerprint": "def456"}
        self.transfer.on_copy_file(payload)

        self.assertEqual(self.file_queue.get("/a.txt")["status"], FileStatus.FileCopyError)
        self.assertEqual(self.transfer.copied_files_count, 0)

    def test_on_copy_file_missing_recorded_fingerprint_skips_check(self):
        f1 = {"name": "a.txt", "type": "file", "size": 100, "status": FileStatus.FileClean}
        self.file_queue.enqueue("/a.txt", f1)

        with patch("Saphir.transfer_controller.threading.Timer"):
            self.transfer.start("source", "target")

        payload = {"filepath": "/a.txt", "status": "ok", "fingerprint": "abc123"}
        self.transfer.on_copy_file(payload)

        self.assertEqual(self.file_queue.get("/a.txt")["status"], FileStatus.FileCopySuccess)

    def test_do_start_transfer_calls_api(self):
        f1 = {"name": "a.txt", "type": "file", "size": 100, "status": FileStatus.FileClean}
        self.file_queue.enqueue("/a.txt", f1)

        with patch("Saphir.transfer_controller.Api") as mock_api:
            with patch("Saphir.transfer_controller.threading.Timer") as mock_timer:
                self.transfer.start("src_disk", "dst_disk")

            callback = mock_timer.call_args[0][1]
            callback()

            mock_api().copy_file.assert_called_once_with("src_disk", "/a.txt", "dst_disk")

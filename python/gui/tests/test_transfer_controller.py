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
        f1 = {
            "name": "a.txt",
            "type": "file",
            "size": 100,
            "status": FileStatus.FileClean,
        }
        self.file_queue.enqueue("/a.txt", f1)

        with patch("Saphir.transfer_controller.threading.Timer"):
            self.transfer.start("source", "target")

        self.assertTrue(self.transfer.is_started)
        self.assertEqual(self.transfer.copied_files_count, 0)

    def test_start_counts_clean_files(self):
        f1 = {
            "name": "a.txt",
            "type": "file",
            "size": 100,
            "status": FileStatus.FileClean,
        }
        f2 = {
            "name": "b.txt",
            "type": "file",
            "size": 200,
            "status": FileStatus.FileInfected,
        }
        self.file_queue.enqueue("/a.txt", f1)
        self.file_queue.enqueue("/b.txt", f2)

        with patch("Saphir.transfer_controller.threading.Timer"):
            self.transfer.start("source", "target")

        self.assertEqual(self.transfer.progress, 0)

    def test_on_copy_file_success(self):
        f1 = {
            "name": "a.txt",
            "type": "file",
            "size": 100,
            "status": FileStatus.FileClean,
        }
        self.file_queue.enqueue("/a.txt", f1)

        with patch("Saphir.transfer_controller.threading.Timer"):
            self.transfer.start("source", "target")

        payload = {"filepath": "/a.txt", "status": "ok", "fingerprint": "abc123"}
        self.transfer.on_copy_file(payload)

        self.assertEqual(self.transfer.copied_files_count, 1)
        self.assertEqual(self.transfer.progress, 1.0)

    def test_on_copy_file_failure(self):
        f1 = {
            "name": "a.txt",
            "type": "file",
            "size": 100,
            "status": FileStatus.FileClean,
        }
        self.file_queue.enqueue("/a.txt", f1)

        with patch("Saphir.transfer_controller.threading.Timer"):
            self.transfer.start("source", "target")

        payload = {"filepath": "/a.txt", "status": "error", "fingerprint": ""}
        self.transfer.on_copy_file(payload)

        self.assertEqual(self.transfer.copied_files_count, 0)
        self.assertEqual(self.transfer.progress, 0)

    def test_on_copy_file_updates_file_status(self):
        f1 = {
            "name": "a.txt",
            "type": "file",
            "size": 100,
            "status": FileStatus.FileClean,
        }
        self.file_queue.enqueue("/a.txt", f1)

        with patch("Saphir.transfer_controller.threading.Timer"):
            self.transfer.start("source", "target")

        payload = {"filepath": "/a.txt", "status": "ok", "fingerprint": "abc"}
        self.transfer.on_copy_file(payload)

        self.assertEqual(
            self.file_queue.get("/a.txt")["status"], FileStatus.FileCopySuccess
        )

    def test_on_copy_file_failure_status(self):
        f1 = {
            "name": "a.txt",
            "type": "file",
            "size": 100,
            "status": FileStatus.FileClean,
        }
        self.file_queue.enqueue("/a.txt", f1)

        with patch("Saphir.transfer_controller.threading.Timer"):
            self.transfer.start("source", "target")

        payload = {"filepath": "/a.txt", "status": "error", "fingerprint": ""}
        self.transfer.on_copy_file(payload)

        self.assertEqual(
            self.file_queue.get("/a.txt")["status"], FileStatus.FileCopyError
        )

    def test_transfer_complete_signal(self):
        f1 = {
            "name": "a.txt",
            "type": "file",
            "size": 100,
            "status": FileStatus.FileClean,
        }
        self.file_queue.enqueue("/a.txt", f1)

        with patch("Saphir.transfer_controller.threading.Timer"):
            self.transfer.start("source", "target")

        signals = []
        self.transfer.transferComplete.connect(lambda: signals.append(True))

        payload = {"filepath": "/a.txt", "status": "ok", "fingerprint": "abc"}
        self.transfer.on_copy_file(payload)

        self.assertEqual(len(signals), 1)

    def test_transfer_not_complete_before_all_copied(self):
        f1 = {
            "name": "a.txt",
            "type": "file",
            "size": 100,
            "status": FileStatus.FileClean,
        }
        f2 = {
            "name": "b.txt",
            "type": "file",
            "size": 200,
            "status": FileStatus.FileClean,
        }
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
        f1 = {
            "name": "a.txt",
            "type": "file",
            "size": 100,
            "status": FileStatus.FileClean,
        }
        self.file_queue.enqueue("/a.txt", f1)

        with patch("Saphir.transfer_controller.threading.Timer"):
            self.transfer.start("source", "target")

        signals = []
        self.transfer.copiedFilesCountChanged.connect(lambda: signals.append(True))

        payload = {"filepath": "/a.txt", "status": "ok", "fingerprint": "abc"}
        self.transfer.on_copy_file(payload)

        self.assertEqual(len(signals), 1)

    def test_progress_changed_signal(self):
        f1 = {
            "name": "a.txt",
            "type": "file",
            "size": 100,
            "status": FileStatus.FileClean,
        }
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
        f1 = {
            "name": "a.txt",
            "type": "file",
            "size": 100,
            "status": FileStatus.FileClean,
        }
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
        f1 = {
            "name": "a.txt",
            "type": "file",
            "size": 100,
            "status": FileStatus.FileClean,
        }
        self.file_queue.enqueue("/a.txt", f1)

        progress_signals = []
        count_signals = []
        self.transfer.transferProgressChanged.connect(
            lambda: progress_signals.append(True)
        )
        self.transfer.copiedFilesCountChanged.connect(
            lambda: count_signals.append(True)
        )

        with patch("Saphir.transfer_controller.threading.Timer"):
            self.transfer.start("source", "target")

        self.assertGreaterEqual(len(progress_signals), 1)
        self.assertGreaterEqual(len(count_signals), 1)

    def test_no_clean_files_progress_is_zero(self):
        f1 = {
            "name": "a.txt",
            "type": "file",
            "size": 100,
            "status": FileStatus.FileInfected,
        }
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

        self.assertEqual(
            self.file_queue.get("/a.txt")["status"], FileStatus.FileCopySuccess
        )
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

        self.assertEqual(
            self.file_queue.get("/a.txt")["status"], FileStatus.FileCopyError
        )
        self.assertEqual(self.transfer.copied_files_count, 0)

    def test_on_copy_file_missing_recorded_fingerprint_skips_check(self):
        f1 = {
            "name": "a.txt",
            "type": "file",
            "size": 100,
            "status": FileStatus.FileClean,
        }
        self.file_queue.enqueue("/a.txt", f1)

        with patch("Saphir.transfer_controller.threading.Timer"):
            self.transfer.start("source", "target")

        payload = {"filepath": "/a.txt", "status": "ok", "fingerprint": "abc123"}
        self.transfer.on_copy_file(payload)

        self.assertEqual(
            self.file_queue.get("/a.txt")["status"], FileStatus.FileCopySuccess
        )

    def test_do_start_transfer_calls_api(self):
        f1 = {
            "name": "a.txt",
            "type": "file",
            "size": 100,
            "status": FileStatus.FileClean,
        }
        self.file_queue.enqueue("/a.txt", f1)

        with patch("Saphir.transfer_controller.Api") as mock_api:
            with patch("Saphir.transfer_controller.threading.Timer") as mock_timer:
                self.transfer.start("src_disk", "dst_disk")

            callback = mock_timer.call_args[0][1]
            callback()

            mock_api().copy_file.assert_called_once_with(
                "src_disk", "/a.txt", "dst_disk"
            )

    def _start_with_clean_files(self, *paths):
        for path in paths:
            self.file_queue.enqueue(
                path,
                {
                    "name": path,
                    "type": "file",
                    "size": 100,
                    "status": FileStatus.FileClean,
                },
            )
        with patch("Saphir.transfer_controller.threading.Timer"):
            self.transfer.start("source", "target")

    def test_copy_failure_completes_transfer_with_error(self):
        # F4: 3 clean files, 1 fails -> transferError(1) + transferComplete
        self._start_with_clean_files("/a.txt", "/b.txt", "/c.txt")

        errors = []
        completes = []
        self.transfer.transferError.connect(lambda n: errors.append(n))
        self.transfer.transferComplete.connect(lambda: completes.append(True))

        self.transfer.on_copy_file(
            {"filepath": "/a.txt", "status": "ok", "fingerprint": "abc"}
        )
        self.transfer.on_copy_file(
            {"filepath": "/b.txt", "status": "error", "fingerprint": ""}
        )
        self.assertEqual(len(completes), 0)
        self.assertEqual(len(errors), 0)

        self.transfer.on_copy_file(
            {"filepath": "/c.txt", "status": "ok", "fingerprint": "cde"}
        )

        self.assertEqual(completes, [True])
        self.assertEqual(errors, [1])
        self.assertEqual(self.transfer.copied_files_count, 2)
        self.assertEqual(self.transfer.failed_files_count, 1)
        self.assertFalse(self.transfer.is_copying)
        self.assertEqual(
            self.file_queue.get("/b.txt")["status"], FileStatus.FileCopyError
        )

    def test_all_copied_no_error_signal(self):
        # F4: every clean file is copied -> transferComplete, no transferError
        self._start_with_clean_files("/a.txt", "/b.txt")

        errors = []
        completes = []
        self.transfer.transferError.connect(lambda n: errors.append(n))
        self.transfer.transferComplete.connect(lambda: completes.append(True))

        self.transfer.on_copy_file(
            {"filepath": "/a.txt", "status": "ok", "fingerprint": "abc"}
        )
        self.transfer.on_copy_file(
            {"filepath": "/b.txt", "status": "ok", "fingerprint": "def"}
        )

        self.assertEqual(completes, [True])
        self.assertEqual(errors, [])
        self.assertEqual(self.transfer.failed_files_count, 0)

    def test_all_failed_completes_with_error(self):
        # F4: no file is copied -> the transfer still completes, all failed
        self._start_with_clean_files("/a.txt")

        errors = []
        completes = []
        self.transfer.transferError.connect(lambda n: errors.append(n))
        self.transfer.transferComplete.connect(lambda: completes.append(True))

        self.transfer.on_copy_file(
            {"filepath": "/a.txt", "status": "error", "fingerprint": ""}
        )

        self.assertEqual(completes, [True])
        self.assertEqual(errors, [1])
        self.assertEqual(self.transfer.copied_files_count, 0)

    def test_reset_clears_failed_files_count(self):
        self._start_with_clean_files("/a.txt")
        self.transfer.on_copy_file(
            {"filepath": "/a.txt", "status": "error", "fingerprint": ""}
        )
        self.assertEqual(self.transfer.failed_files_count, 1)

        self.transfer.reset()
        self.assertEqual(self.transfer.failed_files_count, 0)

    def test_on_copy_error_marks_file_failed_and_completes(self):
        # F4: the platform reports an I/O error on events/error
        self._start_with_clean_files("/a.txt", "/b.txt")

        errors = []
        completes = []
        self.transfer.transferError.connect(lambda n: errors.append(n))
        self.transfer.transferComplete.connect(lambda: completes.append(True))

        self.transfer.on_copy_file(
            {"filepath": "/a.txt", "status": "ok", "fingerprint": "abc"}
        )

        payload = {
            "disk": "source",
            "filepath": "/b.txt",
            "error": "The file could not be copied",
        }
        self.transfer.on_copy_error(payload)

        self.assertEqual(completes, [True])
        self.assertEqual(errors, [1])
        self.assertEqual(
            self.file_queue.get("/b.txt")["status"], FileStatus.FileCopyError
        )
        self.assertFalse(self.transfer.is_copying)

    def test_on_copy_error_ignored_when_not_copying(self):
        self._start_with_clean_files("/a.txt")
        self.transfer.reset()

        self.transfer.on_copy_error(
            {"disk": "source", "filepath": "/a.txt", "error": "boom"}
        )

        self.assertEqual(self.transfer.failed_files_count, 0)
        self.assertEqual(self.file_queue.get("/a.txt")["status"], FileStatus.FileClean)

    def test_on_copy_error_ignored_for_already_copied_file(self):
        self._start_with_clean_files("/a.txt")

        self.transfer.on_copy_file(
            {"filepath": "/a.txt", "status": "ok", "fingerprint": "abc"}
        )

        self.transfer.on_copy_error(
            {"disk": "source", "filepath": "/a.txt", "error": "boom"}
        )

        self.assertEqual(self.transfer.failed_files_count, 0)
        self.assertEqual(
            self.file_queue.get("/a.txt")["status"], FileStatus.FileCopySuccess
        )

    def test_on_copy_error_ignored_for_already_failed_file(self):
        self._start_with_clean_files("/a.txt")

        self.transfer.on_copy_file(
            {"filepath": "/a.txt", "status": "error", "fingerprint": ""}
        )

        self.transfer.on_copy_error(
            {"disk": "source", "filepath": "/a.txt", "error": "boom"}
        )

        self.assertEqual(self.transfer.failed_files_count, 1)

    def test_on_copy_error_ignored_while_paused(self):
        # 8.6: an error on a paused copy is re-tried on resume
        self._start_with_clean_files("/a.txt")
        self.transfer._TransferController__on_disk_state("source", "disconnected")

        self.transfer.on_copy_error(
            {"disk": "source", "filepath": "/a.txt", "error": "boom"}
        )

        self.assertEqual(self.transfer.failed_files_count, 0)
        self.assertTrue(self.transfer.is_copy_paused)

    def test_on_copy_error_missing_payload_is_ignored(self):
        # The events/error topic also carries the Safecor log broadcast
        # (component/module/datetime/description payloads): those are
        # ignored silently, logging them would be re-published on the
        # same topic and loop.
        self._start_with_clean_files("/a.txt")

        with patch("Saphir.transfer_controller.Api") as mock_api:
            self.transfer.on_copy_error({"disk": "source"})
            self.transfer.on_copy_error(
                {
                    "component": "dom0",
                    "module": "Api",
                    "datetime": "2026-01-01 00:00:00",
                    "description": "some log event",
                }
            )
            mock_api().error.assert_not_called()

        self.assertEqual(self.transfer.failed_files_count, 0)


class TestTransferControllerCopyPause(unittest.TestCase):
    """Scenario 8.6: source/target disconnection during the copy (pause + auto-resume)."""

    def setUp(self):
        self.file_queue = FileQueue()
        self.transfer = TransferController(self.file_queue)

    def _start_transfer(self):
        with patch("Saphir.transfer_controller.threading.Timer"):
            self.transfer.start("source", "target")

    def _on_disk_state(self, disk, state):
        self.transfer._TransferController__on_disk_state(disk, state)

    def _on_list(self, disk, files):
        self.transfer._TransferController__on_coherence_check_list(disk, files)

    def test_source_disconnect_during_copy_sets_pause(self):
        f1 = {
            "name": "a.txt",
            "type": "file",
            "size": 100,
            "status": FileStatus.FileClean,
        }
        self.file_queue.enqueue("/a.txt", f1)
        self._start_transfer()
        self.assertFalse(self.transfer.is_copy_paused)

        self._on_disk_state("source", "disconnected")

        self.assertTrue(self.transfer.is_copy_paused)
        self.assertTrue(self.transfer.is_copying)

    def test_target_disconnect_during_copy_sets_pause(self):
        f1 = {
            "name": "a.txt",
            "type": "file",
            "size": 100,
            "status": FileStatus.FileClean,
        }
        self.file_queue.enqueue("/a.txt", f1)
        self._start_transfer()

        self._on_disk_state("target", "disconnected")

        self.assertTrue(self.transfer.is_copy_paused)

    def test_disconnect_other_disk_ignored(self):
        f1 = {
            "name": "a.txt",
            "type": "file",
            "size": 100,
            "status": FileStatus.FileClean,
        }
        self.file_queue.enqueue("/a.txt", f1)
        self._start_transfer()

        self._on_disk_state("other", "disconnected")

        self.assertFalse(self.transfer.is_copy_paused)

    def test_disconnect_when_not_copying_ignored(self):
        self._on_disk_state("source", "disconnected")

        self.assertFalse(self.transfer.is_copy_paused)
        self.assertFalse(self.transfer.is_copying)

    def test_double_disconnect_keeps_first_disk(self):
        f1 = {
            "name": "a.txt",
            "type": "file",
            "size": 100,
            "status": FileStatus.FileClean,
        }
        self.file_queue.enqueue("/a.txt", f1)
        self._start_transfer()

        self._on_disk_state("source", "disconnected")
        self._on_disk_state("target", "disconnected")

        self.assertTrue(self.transfer.is_copy_paused)
        self.assertEqual(self.transfer._paused_disk, "source")

    def test_on_copy_file_failure_while_paused_keeps_file_clean(self):
        f1 = {
            "name": "a.txt",
            "type": "file",
            "size": 100,
            "status": FileStatus.FileClean,
        }
        self.file_queue.enqueue("/a.txt", f1)
        self._start_transfer()
        self._on_disk_state("source", "disconnected")

        payload = {"filepath": "/a.txt", "status": "error", "fingerprint": ""}
        self.transfer.on_copy_file(payload)

        self.assertEqual(self.file_queue.get("/a.txt")["status"], FileStatus.FileClean)
        self.assertEqual(self.transfer.copied_files_count, 0)

    def test_on_copy_file_stale_failure_after_success_ignored(self):
        f1 = {
            "name": "a.txt",
            "type": "file",
            "size": 100,
            "status": FileStatus.FileClean,
        }
        self.file_queue.enqueue("/a.txt", f1)
        self._start_transfer()

        self.transfer.on_copy_file(
            {"filepath": "/a.txt", "status": "ok", "fingerprint": "abc"}
        )
        self.transfer.on_copy_file(
            {"filepath": "/a.txt", "status": "error", "fingerprint": ""}
        )

        self.assertEqual(
            self.file_queue.get("/a.txt")["status"], FileStatus.FileCopySuccess
        )
        self.assertEqual(self.transfer.copied_files_count, 1)

    def test_reconnect_same_disk_requests_files_list(self):
        f1 = {
            "name": "a.txt",
            "type": "file",
            "size": 100,
            "status": FileStatus.FileClean,
        }
        self.file_queue.enqueue("/a.txt", f1)
        self._start_transfer()
        self._on_disk_state("source", "disconnected")

        with patch("Saphir.transfer_controller.Api") as mock_api:
            self._on_disk_state("source", "connected")

        mock_api().get_files_list.assert_called_once_with("source", recursive=True)

    def test_reconnect_different_disk_fails_coherence(self):
        f1 = {
            "name": "a.txt",
            "type": "file",
            "size": 100,
            "status": FileStatus.FileClean,
        }
        self.file_queue.enqueue("/a.txt", f1)
        self._start_transfer()
        self._on_disk_state("source", "disconnected")

        signals = []
        self.transfer.coherenceCheckFailed.connect(
            lambda reason: signals.append(reason)
        )
        self._on_disk_state("other", "connected")

        self.assertEqual(len(signals), 1)
        self.assertIn("other", signals[0])

    def test_coherence_check_ok_resumes_and_recopies_remaining(self):
        f1 = {
            "name": "a.txt",
            "type": "file",
            "size": 100,
            "status": FileStatus.FileClean,
        }
        f2 = {
            "name": "b.txt",
            "type": "file",
            "size": 200,
            "status": FileStatus.FileClean,
        }
        self.file_queue.enqueue("/a.txt", f1)
        self.file_queue.enqueue("/b.txt", f2)
        self._start_transfer()

        self.transfer.on_copy_file(
            {"filepath": "/a.txt", "status": "ok", "fingerprint": "abc"}
        )
        self._on_disk_state("source", "disconnected")

        with patch("Saphir.transfer_controller.Api") as mock_api:
            self._on_disk_state("source", "connected")
            self._on_list(
                "source",
                [{"path": "/", "name": "a.txt"}, {"path": "/", "name": "b.txt"}],
            )

        self.assertFalse(self.transfer.is_copy_paused)
        mock_api().copy_file.assert_called_once_with("source", "/b.txt", "target")

    def test_coherence_check_missing_file_fails(self):
        f1 = {
            "name": "a.txt",
            "type": "file",
            "size": 100,
            "status": FileStatus.FileClean,
        }
        f2 = {
            "name": "b.txt",
            "type": "file",
            "size": 200,
            "status": FileStatus.FileClean,
        }
        self.file_queue.enqueue("/a.txt", f1)
        self.file_queue.enqueue("/b.txt", f2)
        self._start_transfer()

        self.transfer.on_copy_file(
            {"filepath": "/a.txt", "status": "ok", "fingerprint": "abc"}
        )
        self._on_disk_state("source", "disconnected")

        signals = []
        self.transfer.coherenceCheckFailed.connect(
            lambda reason: signals.append(reason)
        )
        with patch("Saphir.transfer_controller.Api"):
            self._on_disk_state("source", "connected")
            self._on_list("source", [{"path": "/", "name": "a.txt"}])

        self.assertEqual(len(signals), 1)
        self.assertTrue(self.transfer.is_copy_paused)

    def test_coherence_check_wrong_disk_ignored(self):
        f1 = {
            "name": "a.txt",
            "type": "file",
            "size": 100,
            "status": FileStatus.FileClean,
        }
        self.file_queue.enqueue("/a.txt", f1)
        self._start_transfer()
        self._on_disk_state("source", "disconnected")

        with patch("Saphir.transfer_controller.Api") as mock_api:
            self._on_list("other", [{"path": "/", "name": "a.txt"}])

        self.assertTrue(self.transfer.is_copy_paused)
        mock_api().copy_file.assert_not_called()

    def test_coherence_check_target_ok_resumes(self):
        f1 = {
            "name": "a.txt",
            "type": "file",
            "size": 100,
            "status": FileStatus.FileClean,
        }
        f2 = {
            "name": "b.txt",
            "type": "file",
            "size": 200,
            "status": FileStatus.FileClean,
        }
        f3 = {
            "name": "c.txt",
            "type": "file",
            "size": 300,
            "status": FileStatus.FileClean,
        }
        self.file_queue.enqueue("/a.txt", f1)
        self.file_queue.enqueue("/b.txt", f2)
        self.file_queue.enqueue("/c.txt", f3)
        self._start_transfer()

        self.transfer.on_copy_file(
            {"filepath": "/a.txt", "status": "ok", "fingerprint": "abc"}
        )
        self.transfer.on_copy_file(
            {"filepath": "/b.txt", "status": "ok", "fingerprint": "def"}
        )
        self._on_disk_state("target", "disconnected")

        with patch("Saphir.transfer_controller.Api") as mock_api:
            self._on_disk_state("target", "connected")
            self._on_list(
                "target",
                [
                    {"path": "/", "name": "a.txt"},
                    {"path": "/", "name": "b.txt"},
                    {"path": "/", "name": "c.txt"},
                ],
            )

        self.assertFalse(self.transfer.is_copy_paused)
        mock_api().copy_file.assert_called_once_with("source", "/c.txt", "target")

    def test_reset_clears_pause(self):
        f1 = {
            "name": "a.txt",
            "type": "file",
            "size": 100,
            "status": FileStatus.FileClean,
        }
        self.file_queue.enqueue("/a.txt", f1)
        self._start_transfer()
        self._on_disk_state("source", "disconnected")

        self.transfer.reset()

        self.assertFalse(self.transfer.is_copy_paused)
        self.assertFalse(self.transfer.is_copying)
        self.assertEqual(self.transfer._paused_disk, "")

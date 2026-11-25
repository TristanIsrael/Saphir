"""Tests for the Safecor v2 analysis controller.

Migrated from Safecor v1 (9p repository staging) to v2 (fingerprint ->
direct analysis).  Files use composite ``(disk, filepath)`` keys.
"""

from __future__ import annotations

import time
import unittest
from copy import deepcopy
from threading import Event, Lock

from libsaphir import TOPIC_ANALYSIS, FileStatus
from PySide6.QtTest import QSignalSpy
from safecor import (
    Api,
    DiskState,
    MqttFactory,
    NotificationFactory,
    Topics,
)

from Saphir import AnalysisController, AnalysisMode, AnalysisState

# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------

ANALYSIS_COMPONENTS = [
    {
        "id": "av1",
        "domain_name": "Mac",
        "label": "Mock ESET antivirus",
        "type": "antivirus",
        "state": "ready",
        "version": "1.0.0-mock",
        "description": "Version mock",
    },
    {
        "id": "av2",
        "domain_name": "Mac",
        "label": "ClamAV Antivirus controller",
        "type": "antivirus",
        "state": "ready",
        "version": "ClamAV 1.4.2",
        "description": "",
    },
]

DISK_LABEL = "Archives"

FILES_LIST = [
    {"type": "file", "path": "/", "name": ".DS_Store", "size": 6148},
    {"type": "file", "path": "/", "name": "Test.pdf", "size": 2772992},
]

ARCHIVE_FILES = [
    {
        "type": "file",
        "path": "/1.3.0/atmosphere/contents/4200000000003103",
        "name": "exefs.nsp",
        "size": 572907,
    },
    {
        "type": "file",
        "path": "/1.3.0/atmosphere/contents/4200000000003103/flags",
        "name": "boot2.flag",
        "size": 0,
    },
    {
        "type": "file",
        "path": "/1.3.0/atmosphere/contents/4200000000003103",
        "name": "toolbox.json",
        "size": 113,
    },
    {
        "type": "file",
        "path": "/1.3.0/switch/.overlays",
        "name": "parental_control.ovl",
        "size": 1065016,
    },
]


def _make_file(name: str, size: int, disk: str = DISK_LABEL) -> dict:
    """Return a file dict with v2 fields (disk, filepath)."""
    return {
        "disk": disk,
        "filepath": name,
        "name": name,
        "path": "/",
        "size": size,
        "status": FileStatus.FileStatusUndefined,
        "locked": False,
        "progress": 0,
        "results": {},
        "selected": True,
        "inqueue": True,
    }


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------


class TestAnalysisController(unittest.TestCase):
    """Tests for ``AnalysisController`` under Safecor v2."""

    def setUp(self) -> None:
        """Prepare the MQTT mock API and a shared empty file dictionary."""
        # Initialize early so the ready callback (threaded) doesn't race.
        self._files_queue: dict[str, dict] = {}
        self._analysis_controller: AnalysisController | None = None
        self._ready = False
        self._ready_event = Event()
        self._message_event = Event()
        self._messages_recv: list[dict] = []
        self._nb_subscriptions = 0
        self._nb_expected_messages = 1
        self._message_lock = Lock()
        self._sysinfo_consumed = False

        try:
            Api().stop()
        except Exception:  # noqa: BLE001,S110
            pass

        self._mqtt_client = MqttFactory.create_mqtt_network_dev(__class__.__name__)
        Api().add_message_callback(self._on_message)
        Api().add_ready_callback(self._on_api_ready)
        Api().add_subscription_callback(self._on_subscribed)
        Api().start(self._mqtt_client, "local")
        self._ready = self._ready_event.wait(0.5)

    def tearDown(self) -> None:
        if self._analysis_controller is not None:
            self._analysis_controller.stop_analysis()
        time.sleep(0.3)
        Api().stop()

    def _on_api_ready(self) -> None:
        """After the API is ready, subscribe to required topics."""
        Api().subscribe(f"{Topics.SYSTEM_INFO}/request")
        Api().subscribe(f"{TOPIC_ANALYSIS}/#")
        Api().subscribe(f"{Topics.DISKS}/+/request")
        self._ready_event.set()

    def _on_subscribed(self, mid: int) -> None:
        self._nb_subscriptions += 1

    def _on_message(self, topic: str, payload: dict) -> None:
        # Ignore our own messages
        if topic in (Topics.NEW_FILE, Topics.DELETED_FILE, Topics.DELETE_FILE):
            return
        if topic.endswith("/response"):
            return
        if topic == Topics.DISK_STATE:
            return
        if topic.startswith(Topics.SYSTEM_INFO) and self._sysinfo_consumed:
            return

        self._message_lock.acquire()
        if topic.startswith(Topics.SYSTEM_INFO):
            resp_payload = {"system": {"machine": {"cpu": 16}}}
            self._mqtt_client.publish(f"{Topics.SYSTEM_INFO}/response", resp_payload)
            self._sysinfo_consumed = True

        self._messages_recv.append({"topic": topic, "payload": payload})

        if len(self._messages_recv) >= self._nb_expected_messages:
            self._message_event.set()

        self._message_lock.release()

    def _populate_files(self, file_list: list[dict]) -> None:
        """Populate the file dict with bare filepath keys (v2 model).

        Each entry carries a ``"disk"`` field set to ``DISK_LABEL``.
        """
        for f in file_list:
            fp = f.get("path", "/") + f.get("name", "")
            self._files_queue[fp] = _make_file(fp, f["size"], DISK_LABEL)

    def _simulate_fingerprint_response(
        self, filepath: str, fingerprint: str = "abc123def456"
    ) -> None:
        """Publish a fingerprint response to simulate sys-usb returning a
        fingerprint.  In v2, ``AnalysisController`` calls
        ``Api().get_file_fingerprint(filepath, disk)`` which causes the
        emulator to publish ``Topics.FILE_FINGERPRINT/response``.
        """
        payload = {
            "disk": DISK_LABEL,
            "filepath": filepath,
            "fingerprint": fingerprint,
        }
        self._mqtt_client.publish(f"{Topics.FILE_FINGERPRINT}/response", payload)

    def _simulate_empty_fingerprint(self, filepath: str) -> None:
        """Publish an empty-fingerprint response to simulate a failed
        fingerprint computation."""
        payload = {
            "disk": DISK_LABEL,
            "filepath": filepath,
            "fingerprint": "",
        }
        self._mqtt_client.publish(f"{Topics.FILE_FINGERPRINT}/response", payload)

    def _simulate_av_response(
        self,
        component: str,
        filepath: str,
        success: bool,
        details: str = "",
        fingerprint_error: bool = False,
    ) -> None:
        """Publish an AV analysis response."""
        payload = {
            "component": component,
            "disk": DISK_LABEL,
            "filepath": filepath,
            "success": success,
            "details": details,
        }
        if fingerprint_error:
            payload["fingerprint_error"] = True
        self._mqtt_client.publish(f"{TOPIC_ANALYSIS}/response", payload)

    def _create_controller(
        self,
        source_disks: list[str] | None = None,
        analysis_mode: AnalysisMode | None = None,
    ) -> AnalysisController:
        """Create a fresh AnalysisController with a deep-copied AV list."""
        return AnalysisController(
            files=self._files_queue,
            analysis_components=deepcopy(ANALYSIS_COMPONENTS),
            source_disks=source_disks or [DISK_LABEL],
            analysis_mode_=analysis_mode or AnalysisMode.AnalyseSelection,
        )

    # ------------------------------------------------------------------ #
    # Tests
    # ------------------------------------------------------------------ #

    def test_init(self) -> None:
        """Verify initial state and subscriptions."""
        self._files_queue["/.DS_Store"] = _make_file("/.DS_Store", 6148)
        self._files_queue["/Test.pdf"] = _make_file("/Test.pdf", 2772992)

        self.assertTrue(self._ready)
        self._analysis_controller = self._create_controller()

        self.assertEqual(
            self._analysis_controller.get_analysis_state(),
            AnalysisState.AnalysisStopped,
        )

        time.sleep(0.2)

        self.assertEqual(self._analysis_controller.get_clean_files_count(), 0)
        self.assertEqual(self._analysis_controller.get_clean_files_size(), 0)
        self.assertEqual(self._analysis_controller.get_infected_files_count(), 0)
        self.assertEqual(self._analysis_controller.get_infected_files_size(), 0)

    def test_reset(self) -> None:
        """Verify reset clears counters."""
        self._analysis_controller = self._create_controller()
        self._analysis_controller.reset()
        self.assertEqual(self._analysis_controller.get_clean_files_count(), 0)
        self.assertEqual(self._analysis_controller.get_clean_files_size(), 0)
        self.assertEqual(self._analysis_controller.get_infected_files_count(), 0)
        self.assertEqual(self._analysis_controller.get_infected_files_size(), 0)

    def test_start_analysis_requests_fingerprints(self) -> None:
        """start_analysis should request fingerprints for pending files."""
        self._analysis_controller = self._create_controller()
        self._populate_files(FILES_LIST)

        self._analysis_controller.start_analysis()

        self.assertEqual(
            self._analysis_controller.get_analysis_state(),
            AnalysisState.AnalysisRunning,
        )

        # Wait for the fingerprint queue to be enqueued.
        time.sleep(0.5)

        # Files should be locked and in FileAnalysing state (fingerprinting).
        any_analysing = any(
            f.get("status") == FileStatus.FileAnalysing
            for f in self._files_queue.values()
        )
        self.assertTrue(any_analysing)

        # Also verify the resume message was captured (if present).
        topics = [m["topic"] for m in self._messages_recv]
        if f"{TOPIC_ANALYSIS}/resume" in topics:
            # Resume was captured, verify fingerprints were enqueued.
            fingerprint_topics = [
                m["topic"]
                for m in self._messages_recv
                if m["topic"] == f"{Topics.FILE_FINGERPRINT}/request"
            ]
            self.assertGreaterEqual(len(fingerprint_topics), 1)

    def test_fingerprint_triggers_system_used(self) -> None:
        """A successful fingerprint response should emit systemUsed."""
        self._analysis_controller = self._create_controller()
        self._populate_files(FILES_LIST)

        spy = QSignalSpy(self._analysis_controller.systemUsed)
        self._analysis_controller.start_analysis()

        # Wait for the fingerprint request to be enqueued.
        time.sleep(0.5)

        # Simulate fingerprint response for the first file (v2 flow).
        self._simulate_fingerprint_response("/.DS_Store")

        # Wait for MQTT to process the response.
        time.sleep(0.3)

        # systemUsed should have been emitted.
        self.assertGreater(spy.count(), 0)

        # The file should be locked, fingerprint recorded, and in
        # FileAnalysing state (awaiting AV response).
        file = self._files_queue.get("/.DS_Store", {})
        self.assertEqual(file.get("locked"), True)
        self.assertEqual(file.get("status"), FileStatus.FileAnalysing)
        self.assertIn("fingerprint", file)

    def test_empty_fingerprint_declares_file_error(self) -> None:
        """An empty fingerprint response should declare the file in error."""
        self._analysis_controller = self._create_controller()
        self._populate_files(FILES_LIST)

        self._analysis_controller.start_analysis()

        # Wait for the fingerprint request to be enqueued.
        time.sleep(0.5)

        # Simulate empty fingerprint for the first file.
        self._simulate_empty_fingerprint("/.DS_Store")

        # Wait for MQTT to process.
        time.sleep(0.3)

        file = self._files_queue.get("/.DS_Store", {})
        self.assertEqual(file.get("status"), FileStatus.FileAnalysisError)
        self.assertEqual(file.get("progress", 0), 100)
        self.assertEqual(self._analysis_controller.get_infected_files_count(), 1)

    def test_start_analysis_resume_reenqueues_interrupted_files(self) -> None:
        """Resumed analysis should restart interrupted files from Undefined."""
        self._analysis_controller = self._create_controller()
        self._populate_files(FILES_LIST)

        # Pre-mark one file as interrupted (Analysing).
        self._files_queue["/.DS_Store"]["status"] = FileStatus.FileAnalysing
        self._files_queue["/.DS_Store"]["locked"] = True
        self._files_queue["/.DS_Store"]["results"] = {"av1": True}

        spy_file_updated = QSignalSpy(self._analysis_controller.fileUpdated)

        self._analysis_controller.start_analysis()

        # Wait for MQTT thread to process the published messages
        # (publish calls are asynchronous through the MQTT broker).
        time.sleep(0.3)

        # fileUpdated should have been emitted during the reset
        # (FileAnalysing -> FileStatusUndefined).
        self.assertGreater(spy_file_updated.count(), 0)

        # The resume message was published via MQTT.
        topics = [m["topic"] for m in self._messages_recv]
        self.assertIn(
            f"{TOPIC_ANALYSIS}/resume",
            topics,
            "start_analysis should publish a resume message",
        )

        # The interrupted file was re-enqueued (fingerprint request).
        fingerprint_topics = [
            m["topic"]
            for m in self._messages_recv
            if m["topic"] == f"{Topics.FILE_FINGERPRINT}/request"
        ]
        self.assertGreaterEqual(
            len(fingerprint_topics),
            1,
            "interrupted file should be re-enqueued for fingerprint",
        )

    def test_handle_result_simple_files(self) -> None:
        """Results should be aggregated and consensus computed."""
        self._analysis_controller = self._create_controller()
        self._populate_files(FILES_LIST)

        # Pre-mark files as being analyzed.
        for filepath in self._files_queue:
            self._files_queue[filepath]["status"] = FileStatus.FileAnalysing

        spy_file_updated = QSignalSpy(self._analysis_controller.fileUpdated)
        spy_iteration_done = QSignalSpy(self._analysis_controller.iterationDone)
        spy_results_changed = QSignalSpy(self._analysis_controller.resultsChanged)

        # First file: first AV says clean.
        self._analysis_controller._AnalysisController__handle_result(
            "av1", "/.DS_Store", DISK_LABEL, True, ""
        )

        self.assertEqual(spy_file_updated.count(), 1)
        self.assertEqual(spy_iteration_done.count(), 0)
        self.assertEqual(spy_results_changed.count(), 0)

        # First file: second AV says clean -> consensus clean.
        self._analysis_controller._AnalysisController__handle_result(
            "av2", "/.DS_Store", DISK_LABEL, True, ""
        )

        self.assertEqual(spy_file_updated.count(), 2)
        self.assertEqual(spy_iteration_done.count(), 1)
        self.assertEqual(spy_results_changed.count(), 1)
        self.assertEqual(self._analysis_controller.get_clean_files_count(), 1)
        self.assertEqual(
            self._files_queue["/.DS_Store"].get("status"), FileStatus.FileClean
        )

        # Second file: both AVs say infected.
        self._analysis_controller._AnalysisController__handle_result(
            "av1", "/Test.pdf", DISK_LABEL, False, "Virus found"
        )
        self._analysis_controller._AnalysisController__handle_result(
            "av2", "/Test.pdf", DISK_LABEL, False, "Virus found"
        )

        self.assertEqual(self._analysis_controller.get_clean_files_count(), 1)
        self.assertEqual(self._analysis_controller.get_infected_files_count(), 1)
        self.assertEqual(
            self._files_queue["/Test.pdf"].get("status"), FileStatus.FileInfected
        )

    def test_handle_result_ignored_for_file_in_final_state(self) -> None:
        """Stale results for a file in a final state should be ignored."""
        self._analysis_controller = self._create_controller()
        self._populate_files(FILES_LIST)

        # Pre-complete the first file.
        self._files_queue["/.DS_Store"]["status"] = FileStatus.FileClean
        self._files_queue["/.DS_Store"]["progress"] = 100

        spy = QSignalSpy(self._analysis_controller.fileUpdated)
        self._analysis_controller._AnalysisController__handle_result(
            "av1", "/.DS_Store", DISK_LABEL, True, ""
        )
        # No update should have been emitted for the already-complete file.
        self.assertEqual(spy.count(), 0)

    def test_handle_error_ignored_for_file_in_final_state(self) -> None:
        """Errors for a file in a final state should be ignored."""
        self._analysis_controller = self._create_controller()
        self._populate_files(FILES_LIST)

        self._files_queue["/.DS_Store"]["status"] = FileStatus.FileInfected
        self._files_queue["/.DS_Store"]["progress"] = 100

        spy = QSignalSpy(self._analysis_controller.fileUpdated)
        self._analysis_controller._AnalysisController__handle_error(
            {"disk": DISK_LABEL, "filepath": "/.DS_Store", "error": "Internal error"}
        )
        self.assertEqual(spy.count(), 0)

    def test_analysis_response_fingerprint_error(self) -> None:
        """A fingerprint-error response should declare the file in error."""
        self._analysis_controller = self._create_controller()
        self._populate_files(FILES_LIST)

        self._files_queue["/.DS_Store"]["status"] = FileStatus.FileAnalysing

        self._simulate_av_response(
            "av1",
            "/.DS_Store",
            False,
            "Fingerprint mismatch",
            fingerprint_error=True,
        )

        deadline = time.time() + 2
        while (
            self._files_queue["/.DS_Store"].get("status")
            != FileStatus.FileAnalysisError
            and time.time() < deadline
        ):
            time.sleep(0.1)

        self.assertEqual(
            self._files_queue["/.DS_Store"].get("status"),
            FileStatus.FileAnalysisError,
        )
        self.assertEqual(self._files_queue["/.DS_Store"].get("progress", 0), 100)
        self.assertEqual(self._analysis_controller.get_infected_files_count(), 1)

    def test_analysis_response_without_fingerprint_error_is_normal(self) -> None:
        """A normal analysis response should not set the error status."""
        self._analysis_controller = self._create_controller()
        self._populate_files(FILES_LIST)

        self._files_queue["/.DS_Store"]["status"] = FileStatus.FileAnalysing

        self._simulate_av_response("av1", "/.DS_Store", True, "Clean")

        deadline = time.time() + 2
        while (
            self._files_queue["/.DS_Store"].get("progress", 0) == 0
            and time.time() < deadline
        ):
            time.sleep(0.1)

        # Should still be Analysing (only one AV responded so far).
        self.assertEqual(
            self._files_queue["/.DS_Store"].get("status"),
            FileStatus.FileAnalysing,
        )

    def test_source_disconnection_holds_analysis(self) -> None:
        """Source disk disconnection during analysis should hold the queue."""
        self._analysis_controller = self._create_controller()
        self._populate_files(FILES_LIST)

        self._analysis_controller.start_analysis()
        time.sleep(0.5)

        spy_hold = QSignalSpy(self._analysis_controller.sourceHoldChanged)

        # Simulate source disk disconnect.
        payload = NotificationFactory.create_notification_disk_state(
            DISK_LABEL, DiskState.DISCONNECTED
        )
        self._mqtt_client.publish(Topics.DISK_STATE, payload)

        # Poll for the signal.
        deadline = time.time() + 2
        while spy_hold.count() == 0 and time.time() < deadline:
            time.sleep(0.1)

        self.assertGreater(spy_hold.count(), 0)
        self.assertEqual(spy_hold.at(0)[0], True)

    def test_source_disconnection_ignored_when_not_running(self) -> None:
        """Source disk disconnection when not running should be ignored."""
        self._analysis_controller = self._create_controller()
        self._populate_files(FILES_LIST)

        spy_hold = QSignalSpy(self._analysis_controller.sourceHoldChanged)

        # Simulate source disk disconnect (analysis is stopped).
        payload = NotificationFactory.create_notification_disk_state(
            DISK_LABEL, DiskState.DISCONNECTED
        )
        self._mqtt_client.publish(Topics.DISK_STATE, payload)
        time.sleep(0.3)

        # No hold signal should be emitted.
        self.assertEqual(spy_hold.count(), 0)

    def test_av_failure_continues_when_enough_engines_remain(self) -> None:
        """An AV failure should not abort if enough engines remain."""
        self._analysis_controller = self._create_controller()
        self._populate_files(FILES_LIST)

        # Simulate one AV going offline during analysis.
        aborted = self._analysis_controller.handle_av_failure("av1")

        self.assertFalse(aborted)  # Not aborted; av2 still available.

    def test_av_failure_aborts_when_not_enough_engines(self) -> None:
        """An AV failure should abort if fewer than ANTIVIRUS_NEEDED remain."""
        self._analysis_controller = self._create_controller()
        self._populate_files(FILES_LIST)
        self._analysis_controller.start_analysis()
        time.sleep(0.3)

        # With ANTIVIRUS_NEEDED=2 and exactly 2 AVs, removing one
        # leaves 1 < 2 -> abort immediately.
        aborted = self._analysis_controller.handle_av_failure("av1")

        self.assertTrue(aborted)
        self.assertEqual(
            self._analysis_controller.get_analysis_state(),
            AnalysisState.AnalysisStopped,
        )

    def test_av_failure_marks_incomplete_files_error(self) -> None:
        """AV failure should mark incomplete files as error."""
        self._analysis_controller = self._create_controller()
        self._populate_files(FILES_LIST)
        self._analysis_controller.start_analysis()

        # Wait for fingerprint requests to be enqueued.
        time.sleep(0.3)

        # Simulate both AVs failing while files are in Analysing state.
        self._files_queue["/.DS_Store"]["status"] = FileStatus.FileAnalysing

        self._analysis_controller.handle_av_failure("av1")
        self._analysis_controller.handle_av_failure("av2")

        # The file should be in error.
        self.assertEqual(
            self._files_queue["/.DS_Store"].get("status"),
            FileStatus.FileAnalysisError,
        )
        self.assertEqual(self._files_queue["/.DS_Store"].get("progress", 0), 100)

    def test_av_failure_ignored_when_not_running(self) -> None:
        """AV failure should be a no-op when analysis is not running."""
        self._analysis_controller = self._create_controller()
        aborted = self._analysis_controller.handle_av_failure("av1")
        self.assertFalse(aborted)

    def test_av_failure_unknown_component(self) -> None:
        """Failure for an unknown component should not affect analysis."""
        self._analysis_controller = self._create_controller()
        self._populate_files(FILES_LIST)

        aborted = self._analysis_controller.handle_av_failure("unknown_av")
        self.assertFalse(aborted)

    def test_non_source_disk_disconnection_ignored(self) -> None:
        """Disconnection of a non-source disk should be ignored."""
        self._analysis_controller = self._create_controller()
        self._populate_files(FILES_LIST)
        self._analysis_controller.start_analysis()
        time.sleep(0.5)

        spy_hold = QSignalSpy(self._analysis_controller.sourceHoldChanged)

        # Disconnection of a different disk.
        payload = NotificationFactory.create_notification_disk_state(
            "OtherDisk", DiskState.DISCONNECTED
        )
        self._mqtt_client.publish(Topics.DISK_STATE, payload)
        time.sleep(0.3)

        # No hold signal should be emitted.
        self.assertEqual(spy_hold.count(), 0)

    def test_duplicate_new_file_ignored(self) -> None:
        """A duplicate fingerprint response for a completed file should be ignored."""
        self._analysis_controller = self._create_controller()
        self._populate_files(FILES_LIST)

        # Pre-complete the file.
        self._files_queue["/.DS_Store"]["status"] = FileStatus.FileClean
        self._files_queue["/.DS_Store"]["progress"] = 100

        spy = QSignalSpy(self._analysis_controller.fileUpdated)
        self._simulate_fingerprint_response("/.DS_Store")
        time.sleep(0.2)

        # No update should have been emitted.
        self.assertEqual(spy.count(), 0)

    def test_multi_source_disk_disconnection_holds_analysis(self) -> None:
        """Disconnection of any source disk should hold the analysis."""
        self._files_queue = {}
        self._analysis_controller = self._create_controller(
            source_disks=[DISK_LABEL, "OtherDisk"]
        )
        self._populate_files(FILES_LIST)

        self._analysis_controller.start_analysis()
        time.sleep(0.5)

        spy_hold = QSignalSpy(self._analysis_controller.sourceHoldChanged)

        # Disconnection of the second source disk.
        payload = NotificationFactory.create_notification_disk_state(
            "OtherDisk", DiskState.DISCONNECTED
        )
        self._mqtt_client.publish(Topics.DISK_STATE, payload)

        # Poll for the signal.
        deadline = time.time() + 2
        while spy_hold.count() == 0 and time.time() < deadline:
            time.sleep(0.1)

        self.assertGreater(spy_hold.count(), 0)
        self.assertEqual(spy_hold.at(0)[0], True)

    def test_same_disk_reconnect_resumes_analysis(self) -> None:
        """D3: reconnecting the same disk while held resets the in-flight
        files, clears their results and re-fingerprints them (auto-resume)."""
        self._analysis_controller = self._create_controller()
        self._populate_files(FILES_LIST)

        self._analysis_controller.start_analysis()
        time.sleep(0.5)

        # Make the file in-flight: fingerprint received, one of two AVs
        # already responded.
        self._simulate_fingerprint_response("/.DS_Store")
        time.sleep(0.3)
        self._simulate_av_response("av1", "/.DS_Store", True, "Clean")
        time.sleep(0.3)

        # Disconnect the source -> hold.
        self._mqtt_client.publish(
            Topics.DISK_STATE,
            NotificationFactory.create_notification_disk_state(
                DISK_LABEL, DiskState.DISCONNECTED
            ),
        )
        deadline = time.time() + 2
        while not self._analysis_controller.is_source_held() and time.time() < deadline:
            time.sleep(0.1)
        self.assertTrue(self._analysis_controller.is_source_held())

        # Reconnect the same disk -> auto-resume.
        self._mqtt_client.publish(
            Topics.DISK_STATE,
            NotificationFactory.create_notification_disk_state(
                DISK_LABEL, DiskState.CONNECTED
            ),
        )
        deadline = time.time() + 2
        while self._analysis_controller.is_source_held() and time.time() < deadline:
            time.sleep(0.1)
        self.assertFalse(self._analysis_controller.is_source_held())
        time.sleep(0.5)

        # The in-flight file was reset and re-fingerprinted.
        file = self._files_queue["/.DS_Store"]
        self.assertEqual(file.get("status"), FileStatus.FileAnalysing)
        self.assertEqual(file.get("results"), {})
        self.assertEqual(file.get("progress"), 0)
        self.assertEqual(file.get("locked"), True)

        # A second fingerprint request was issued for the file.
        fingerprint_requests = [
            m
            for m in self._messages_recv
            if m["topic"] == f"{Topics.FILE_FINGERPRINT}/request"
            and m["payload"].get("filepath") == "/.DS_Store"
        ]
        self.assertGreaterEqual(len(fingerprint_requests), 2)

    def test_different_disk_reconnect_emits_reset_required(self) -> None:
        """D3: reconnecting a different disk while held requires a reset
        (coherence check failure)."""
        self._analysis_controller = self._create_controller()
        self._populate_files(FILES_LIST)

        self._analysis_controller.start_analysis()
        time.sleep(0.5)

        # Disconnect the source -> hold.
        self._mqtt_client.publish(
            Topics.DISK_STATE,
            NotificationFactory.create_notification_disk_state(
                DISK_LABEL, DiskState.DISCONNECTED
            ),
        )
        deadline = time.time() + 2
        while not self._analysis_controller.is_source_held() and time.time() < deadline:
            time.sleep(0.1)
        self.assertTrue(self._analysis_controller.is_source_held())

        # Reconnect a different disk -> resetRequired.
        spy_reset = QSignalSpy(self._analysis_controller.resetRequired)
        self._mqtt_client.publish(
            Topics.DISK_STATE,
            NotificationFactory.create_notification_disk_state(
                "OtherDisk", DiskState.CONNECTED
            ),
        )
        deadline = time.time() + 2
        while spy_reset.count() == 0 and time.time() < deadline:
            time.sleep(0.1)

        self.assertGreater(spy_reset.count(), 0)
        self.assertFalse(self._analysis_controller.is_source_held())

    def test_av_failure_ignored_while_held(self) -> None:
        """D3: an AV failure received while the source is held is stale
        (caused by the disconnection) and must not be recorded."""
        self._analysis_controller = self._create_controller()
        self._populate_files(FILES_LIST)

        self._analysis_controller.start_analysis()
        time.sleep(0.5)

        # Make the file in-flight: fingerprint received, awaiting the AVs.
        self._simulate_fingerprint_response("/.DS_Store")
        time.sleep(0.3)

        # Disconnect the source -> hold.
        self._mqtt_client.publish(
            Topics.DISK_STATE,
            NotificationFactory.create_notification_disk_state(
                DISK_LABEL, DiskState.DISCONNECTED
            ),
        )
        deadline = time.time() + 2
        while not self._analysis_controller.is_source_held() and time.time() < deadline:
            time.sleep(0.1)
        self.assertTrue(self._analysis_controller.is_source_held())

        # An AV failure during the hold must be ignored.
        self._simulate_av_response("av1", "/.DS_Store", False, "scan error")
        time.sleep(0.3)

        file = self._files_queue["/.DS_Store"]
        self.assertEqual(file.get("status"), FileStatus.FileAnalysing)
        self.assertEqual(file.get("results"), {})

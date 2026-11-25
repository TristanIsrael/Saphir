"""Unit tests for the NFR-1 repository integrity check in the AV controller."""

import hashlib
import os
import tempfile
import unittest
from unittest.mock import patch

from libsaphir import TOPIC_ANALYSIS, AbstractAntivirusController
from safecor import ComponentState, Constants, FileHelper


class FakeAVController(AbstractAntivirusController):
    """Minimal concrete AV controller that records analyzed files."""

    def __init__(self):
        super().__init__("TestAV", "test antivirus", max_workers=1)
        self.analysed = []

    def _on_api_ready(self) -> None:
        pass

    def _get_component_state(self):
        return ComponentState.READY

    def _analyse_file(self, filepath: str, disk: str = "") -> None:
        self.analysed.append(filepath)

    def _stop_immediately(self):
        pass

    def _get_component_version(self) -> str:
        return "1.0"

    def _get_component_description(self) -> str:
        return "test"

    def _restart(self, domain_name: str):
        pass


def _make_file(directory: str, name: str, content: bytes) -> str:
    path = os.path.join(directory, name.lstrip("/"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(content)
    return path


def _fingerprint(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.file_digest(f, Constants.FINGERPRINT_METHOD).hexdigest()


class TestAVIntegrityCheck(unittest.TestCase):
    def setUp(self):
        self.__tmpdir = tempfile.mkdtemp()
        self.__controller = FakeAVController()
        # Prevent the analysis loop from scheduling background timers
        self.__controller._AbstractAntivirusController__can_run = False

    def tearDown(self):
        import shutil

        for name in os.listdir(self.__tmpdir):
            path = os.path.join(self.__tmpdir, name)
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        os.rmdir(self.__tmpdir)

    def _run_check(
        self, filepath: str, fingerprint: str, disk: str = "TestDisk"
    ) -> unittest.mock.MagicMock:
        api_patch = patch("libsaphir._abstract_antivirus_controller.Api")
        timer_patch = patch("threading.Timer")
        # usb_mount_point + disk + filepath = tmpdir + TestDisk + /a.txt
        disk_root = os.path.join(self.__tmpdir, disk)
        os.makedirs(disk_root, exist_ok=True)
        mock_api = api_patch.start()
        timer_patch.start()
        try:
            # _usb_mount_point is a protected (single-underscore) attribute.
            # The production code appends ``/{disk}{filepath}`` after it.
            self.__controller._usb_mount_point = self.__tmpdir
            self.__controller._AbstractAntivirusController__analyse_with_integrity_check(
                filepath, fingerprint, disk
            )
        finally:
            timer_patch.stop()
            api_patch.stop()
        return mock_api

    def test_matching_fingerprint_proceeds_to_analysis(self):
        path = _make_file(self.__tmpdir, "/TestDisk/a.txt", b"hello world")
        fingerprint = _fingerprint(path)

        self._run_check("/a.txt", fingerprint)

        self.assertEqual(self.__controller.analysed, ["/a.txt"])

    def test_mismatching_fingerprint_stops_analysis(self):
        _make_file(self.__tmpdir, "/TestDisk/a.txt", b"hello world")

        mock_api = self._run_check("/a.txt", "wrong-fingerprint")

        self.assertEqual(self.__controller.analysed, [])
        mock_api.return_value.publish.assert_called_once()
        topic, payload = mock_api.return_value.publish.call_args[0]
        self.assertEqual(topic, f"{TOPIC_ANALYSIS}/response")
        self.assertTrue(payload["fingerprint_error"])
        self.assertFalse(payload["success"])

    def test_missing_file_proceeds_to_analysis(self):
        # The file is absent from the repository: the concrete AV controller
        # reports the missing file itself, the integrity check is skipped.
        self._run_check("/missing.txt", "some-fingerprint")

        self.assertEqual(self.__controller.analysed, ["/missing.txt"])

    def test_empty_fingerprint_skips_the_check(self):
        self._run_check("/a.txt", "")

        self.assertEqual(self.__controller.analysed, ["/a.txt"])

    def test_fingerprint_is_computed_with_safecor_algorithm(self):
        # FileHelper uses Constants.FINGERPRINT_METHOD: the test recomputes
        # the digest with the same method to stay in sync with Safecor.
        path = _make_file(self.__tmpdir, "/b.txt", b"content")
        self.assertEqual(_fingerprint(path), FileHelper.calculate_fingerprint(path))

    def test_devmode_bypasses_usb_mount_readiness_gate(self):
        """G7: In DEVMODE, the AV controller should not wait for a real USB
        mount point.  The readiness gate is bypassed and the component
        transitions to READY immediately after ``__on_api_ready`` is called.
        """
        dev_controller = FakeAVController()
        dev_controller._AbstractAntivirusController__can_run = False

        with (
            patch("libsaphir._abstract_antivirus_controller.DEVMODE", True),
            patch("libsaphir._abstract_antivirus_controller.Api") as mock_api,
        ):
            mock_api.return_value.debug.return_value = None
            mock_api.return_value.subscribe.return_value = (True, 0)
            mock_api.return_value.publish.return_value = None
            mock_api.return_value.publish_components.return_value = None

            # Calling __on_api_ready in DEVMODE bypasses the USB mount
            # gate (no System().on_usb_mountpoint_ready() call).
            dev_controller._AbstractAntivirusController__on_api_ready()

            # The component should be READY because DEVMODE sets
            # __usb_ready = True and _engine_is_ready() returns True.
            self.assertEqual(
                dev_controller._AbstractAntivirusController__state,
                ComponentState.READY,
            )
            # usb_ready should have been set to True (gate bypassed).
            self.assertTrue(dev_controller._AbstractAntivirusController__usb_ready)
            # subscribe was called for the analysis topics.
            subscribe_calls = mock_api.return_value.subscribe.call_count
            self.assertGreaterEqual(subscribe_calls, 1)


if __name__ == "__main__":
    unittest.main()

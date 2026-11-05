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

    def _analyse_file(self, filepath: str) -> None:
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
        for name in os.listdir(self.__tmpdir):
            os.remove(os.path.join(self.__tmpdir, name))
        os.rmdir(self.__tmpdir)

    def _run_check(self, filepath: str, fingerprint: str):
        api_patch = patch("libsaphir._abstract_antivirus_controller.Api")
        timer_patch = patch("threading.Timer")
        const_patch = patch.object(Constants, "DOMU_REPOSITORY_PATH", self.__tmpdir)
        mock_api = api_patch.start()
        timer_patch.start()
        const_patch.start()
        try:
            self.__controller._AbstractAntivirusController__analyse_with_integrity_check(
                filepath, fingerprint
            )
        finally:
            timer_patch.stop()
            const_patch.stop()
            api_patch.stop()
        return mock_api

    def test_matching_fingerprint_proceeds_to_analysis(self):
        path = _make_file(self.__tmpdir, "/a.txt", b"hello world")
        fingerprint = _fingerprint(path)

        self._run_check("/a.txt", fingerprint)

        self.assertEqual(self.__controller.analysed, ["/a.txt"])

    def test_mismatching_fingerprint_stops_analysis(self):
        _make_file(self.__tmpdir, "/a.txt", b"hello world")

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


if __name__ == "__main__":
    unittest.main()

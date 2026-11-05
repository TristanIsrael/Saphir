import os
import unittest
from datetime import datetime
from unittest.mock import patch
try:
    from Saphir import ReportController
except Exception:
    pass
from libsaphir import FileStatus

class TestReportController(unittest.TestCase):

    STORAGE_FILES = {
        "/.DS_Store": {"type": "file", "filepath": "/.DS_Store", "fingerprint": "01234567890", "path": "/", "name": ".DS_Store", "size": 6148, "status": FileStatus.FileClean, "results": { "MockAV": { "result": "Infected", "details": "No comment"}, "TestAV": { "result": "Infected", "details": "No comment"}}},
        "/Test.pdf": {"type": "file", "filepath": "/Test.pdf", "fingerprint": "01234567890", "path": "/", "name": "Test.pdf", "size": 2772992, "status": FileStatus.FileInfected, "results": { "MockAV": { "result": "Clean", "details": "No comment"}, "TestAV": { "result": "Clean", "details": "No comment"}}}        
    }
    ANALYSIS_COMPONENTS = {
        "MockAV": { "version": "1.0", "description" : "Mocked AV"},
        "TestAV": { "version": "2.1", "description" : "Test AV"},
    }

    def _make_report(self, ctrl):
        ctrl.make_report(
            self.STORAGE_FILES,
            1,
            1,
            2,
            2,
            0,
            datetime.now(),
            datetime.now(),
            "12345678901234567890",
            "UnitTest",
            "1.2",
            "3.0",
            self.ANALYSIS_COMPONENTS,
        )

    def test_report_generation(self):
        ctrl = ReportController()
        self._make_report(ctrl)

        report_filepath = ctrl.get_report_filepath()
        self.assertTrue(os.path.exists(report_filepath))
        self.assertTrue(os.path.getsize(report_filepath) > 0)

    def test_report_generation_emits_report_generated(self):
        ctrl = ReportController()
        generated = []
        ctrl.reportGenerated.connect(lambda: generated.append(True))

        self._make_report(ctrl)

        self.assertEqual(generated, [True])

    def test_report_generation_failure_emits_report_failed(self):
        ctrl = ReportController()
        failures = []
        generated = []
        ctrl.reportFailed.connect(lambda reason: failures.append(reason))
        ctrl.reportGenerated.connect(lambda: generated.append(True))

        with patch.object(
            ReportController, "_write_pdf", side_effect=OSError("disk full")
        ):
            self._make_report(ctrl)

        self.assertEqual(len(failures), 1)
        self.assertIn("disk full", failures[0])
        self.assertEqual(generated, [])

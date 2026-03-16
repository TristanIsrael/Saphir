import unittest
import os
from datetime import datetime
from copy import deepcopy
try:
    from Saphir import ReportController
except Exception:
    pass
from libsaphir import TOPIC_ANALYSIS, FileStatus

class TestReportController(unittest.TestCase):

    STORAGE_FILES = {
        "/.DS_Store": {"type": "file", "filepath": "/.DS_Store", "fingerprint": "01234567890", "path": "/", "name": ".DS_Store", "size": 6148, "status": FileStatus.FileClean, "results": { "MockAV": { "result": "Infected", "details": "No comment"}, "TestAV": { "result": "Infected", "details": "No comment"}}},
        "/Test.pdf": {"type": "file", "filepath": "/Test.pdf", "fingerprint": "01234567890", "path": "/", "name": "Test.pdf", "size": 2772992, "status": FileStatus.FileInfected, "results": { "MockAV": { "result": "Clean", "details": "No comment"}, "TestAV": { "result": "Clean", "details": "No comment"}}}        
    }
    ANALYSIS_COMPONENTS = {
        "MockAV": { "version": "1.0", "description" : "Mocked AV"},
        "TestAV": { "version": "2.1", "description" : "Test AV"},
    }

    def test_report_generation(self):
        ctrl = ReportController()
        ctrl.make_report(
            self.STORAGE_FILES,
            1,
            1,
            2,
            2,
            datetime.now(),
            datetime.now(),
            "12345678901234567890",
            "UnitTest",
            "1.2",
            "3.0",
            self.ANALYSIS_COMPONENTS
        )

        report_filepath = ctrl.get_report_filepath()
        self.assertTrue(os.path.exists(report_filepath))
        self.assertTrue(os.path.getsize(report_filepath) > 0)

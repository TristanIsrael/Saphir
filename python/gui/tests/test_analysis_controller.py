import unittest
from copy import deepcopy
import sys
print(sys.path)
from Saphir import AnalysisController, AnalysisState, AnalysisMode

class TestAnalysisController(unittest.TestCase):

    STORAGE_FILES = {"disk": "Archives", "files": [{"type": "folder", "path": "/", "name": "NSParentalControl"}, {"type": "file", "path": "/", "name": ".DS_Store", "size": 6148}, {"type": "file", "path": "/", "name": "Test.iso", "size": 2772992}]}
    ARCHIVE_FILES = {"disk": "Test.iso", "files": [{"type": "folder", "path": "/", "name": "1.3.0"}, {"type": "folder", "path": "/1.3.0", "name": "atmosphere"}, {"type": "folder", "path": "/1.3.0/atmosphere", "name": "contents"}, {"type": "folder", "path": "/1.3.0/atmosphere/contents", "name": "4200000000003103"}, {"type": "file", "path": "/1.3.0/atmosphere/contents/4200000000003103", "name": "exefs.nsp", "size": 572907}, {"type": "folder", "path": "/1.3.0/atmosphere/contents/4200000000003103", "name": "flags"}, {"type": "file", "path": "/1.3.0/atmosphere/contents/4200000000003103/flags", "name": "boot2.flag", "size": 0}, {"type": "file", "path": "/1.3.0/atmosphere/contents/4200000000003103", "name": "toolbox.json", "size": 113}, {"type": "folder", "path": "/1.3.0", "name": "switch"}, {"type": "folder", "path": "/1.3.0/switch", "name": ".overlays"}, {"type": "file", "path": "/1.3.0/switch/.overlays", "name": "parental_control.ovl", "size": 1065016}]}
    ANALYSIS_COMPONENTS = [
        {"id": "Mock ESET", "domain_name": "Mac", "label": "Mock ESET antivirus", "type": "antivirus", "state": "ready", "version": "1.0.0-mock", "description": "Version mock"},
        {"id": "ClamAV", "domain_name": "Mac", "label": "ClamAV Antivirus controller", "type": "antivirus", "state": "ready", "version": "ClamAV 1.4.2/27164/Wed Jan 24 10:45:32 2024", "description": ""}
    ]

    def test_init(self):
        queue = self.__make_selection()

        a = AnalysisController(queue, self.ANALYSIS_COMPONENTS, "Archives", AnalysisMode.AnalyseSelection)

        self.assertEqual(a.get_analysis_state(), AnalysisState.AnalysisStopped)

    def __make_selection(self):
        files = deepcopy(self.STORAGE_FILES)

        for f in files.get("files", {}):
            f["inqueue"] = True

        return files

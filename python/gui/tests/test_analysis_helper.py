import unittest
from copy import deepcopy
from Saphir import AnalysisHelper
from libsaphir import FileStatus

class TestAnalysisHelper(unittest.TestCase):

    STORAGE_FILES = {"disk": "Archives", "files": { ".DS_Store": {"type": "file", "path": "/", "name": ".DS_Store", "size": 6148}, "Test.iso": {"type": "file", "path": "/", "name": "Test.iso", "size": 2772992}}}
    ARCHIVE_CONTENT = {    "/1.3.0/atmosphere/contents/4200000000003103/exefs.nsp":    {        "type": "file",        "path": "/1.3.0/atmosphere/contents/4200000000003103",        "name": "exefs.nsp",        "size": 572907    },        "/1.3.0/atmosphere/contents/4200000000003103/flags/boot2.flag": {        "type": "file",        "path": "/1.3.0/atmosphere/contents/4200000000003103/flags",        "name": "boot2.flag",        "size": 0    },    "/1.3.0/atmosphere/contents/4200000000003103/toolbox.json": {        "type": "file",        "path": "/1.3.0/atmosphere/contents/4200000000003103",        "name": "toolbox.json",        "size": 113    },            "/1.3.0/switch/.overlays/parental_control.ovl": {        "type": "file",        "path": "/1.3.0/switch/.overlays",        "name": "parental_control.ovl",        "size": 1065016    }}
    ANALYSIS_COMPONENTS = [
        {"id": "Mock ESET", "domain_name": "Mac", "label": "Mock ESET antivirus", "type": "antivirus", "state": "ready", "version": "1.0.0-mock", "description": "Version mock"},
        {"id": "ClamAV", "domain_name": "Mac", "label": "ClamAV Antivirus controller", "type": "antivirus", "state": "ready", "version": "ClamAV 1.4.2/27164/Wed Jan 24 10:45:32 2024", "description": ""}
    ]

    def test_evaluate_result_consensus(self):
        results = {
            "av1": { "result": "Clean" },
            "av2": { "result": "Clean" }
        }

        file = { "results": results }

        self.assertTrue(AnalysisHelper.evaluate_result_consensus(file))

        results["av1"]["result"] = "Infected"
        self.assertFalse(AnalysisHelper.evaluate_result_consensus(file))

        results["av1"]["result"] = "Clean"
        results["av2"]["result"] = "Infected"
        self.assertFalse(AnalysisHelper.evaluate_result_consensus(file))

        results["av1"]["result"] = "Infected"
        self.assertFalse(AnalysisHelper.evaluate_result_consensus(file))

    def test_evaluate_result_consensus_archive(self):
        results = {
            "av1": { "result": "Clean" },
            "av2": { "result": "Clean" }
        }

        file = { 
            "filepath": "/file/path",
            "content": {
                "file1": { "results": results }
            }
        }

        self.assertTrue(AnalysisHelper.evaluate_result_consensus_archive(file))

        results["av1"]["result"] = "Infected"        
        self.assertFalse(AnalysisHelper.evaluate_result_consensus_archive(file))

        results["av1"]["result"] = "Clean"
        results["av2"]["result"] = "Infected"
        self.assertFalse(AnalysisHelper.evaluate_result_consensus_archive(file))

        results["av1"]["result"] = "Infected"
        self.assertFalse(AnalysisHelper.evaluate_result_consensus_archive(file))
        

    def test_update_file_results(self):
        files = deepcopy(self.STORAGE_FILES["files"])

        success, size = AnalysisHelper.update_file_result(files, ".DS_Store", True, "av1", "this is OK", self.ANALYSIS_COMPONENTS)        
        file = files[".DS_Store"]
        self.assertEqual(len(file["results"]), 1)
        av_result = file["results"]["av1"]
        self.assertTrue(av_result["result"])
        self.assertTrue(success)
        self.assertEqual(size, 6148)
        self.assertIsNotNone(file.get("status", None))
        self.assertEqual(file.get("status", None), FileStatus.FileAnalysing)
        
        success, size = AnalysisHelper.update_file_result(files, ".DS_Store", True, "av2", "this is OK", self.ANALYSIS_COMPONENTS)
        self.assertEqual(file["status"], FileStatus.FileClean)
        self.assertEqual(len(file["results"]), 2)
        av_result = file["results"]["av1"]
        self.assertTrue(av_result["result"])
        av_result = file["results"]["av2"]
        self.assertTrue(av_result["result"])
        self.assertTrue(success)
        self.assertEqual(size, 6148)       
        self.assertEqual(file.get("status", None), FileStatus.FileClean) 

        success, size = AnalysisHelper.update_file_result(files, ".DS_Store", False, "av2", "this is not OK", self.ANALYSIS_COMPONENTS)        
        self.assertEqual(len(file["results"]), 2)
        av_result = file["results"]["av1"]
        self.assertEqual(av_result["result"], "Clean")
        av_result = file["results"]["av2"]
        self.assertEqual(av_result["result"], "Infected")
        self.assertFalse(success)
        self.assertEqual(size, 6148)
        self.assertEqual(file.get("status", None), FileStatus.FileInfected) 


    def test_update_archive_result(self):
        files = deepcopy(self.STORAGE_FILES["files"])
        archive_mounted = "Test.iso"
        archive_file = files[archive_mounted]
        archive_content = deepcopy(self.ARCHIVE_CONTENT)
        archive_file["content"] = archive_content
        filepath = "/1.3.0/atmosphere/contents/4200000000003103/exefs.nsp"

        success, size = AnalysisHelper.update_archive_result(archive_file, filepath, True, "av1", "This is OK", self.ANALYSIS_COMPONENTS)
        self.assertTrue(success)
        self.assertEqual(size, 2772992)
        self.assertEqual(archive_file.get("status", None), FileStatus.FileAnalysing) 
        self.assertEqual(archive_file.get("progress", None), 12.5)

        filepath = "/1.3.0/atmosphere/contents/4200000000003103/toolbox.json"
        success, size = AnalysisHelper.update_archive_result(archive_file, filepath, False, "av2", "This is not OK", self.ANALYSIS_COMPONENTS)
        self.assertFalse(success)
        self.assertEqual(size, 2772992)
        self.assertEqual(archive_file.get("status", None), FileStatus.FileAnalysing) 
        self.assertEqual(archive_file.get("progress", None), 25.0)

        filepath = "/1.3.0/atmosphere/contents/4200000000003103/exefs.nsp"
        AnalysisHelper.update_archive_result(archive_file, filepath, True, "av2", "This is OK", self.ANALYSIS_COMPONENTS)
        filepath = "/1.3.0/atmosphere/contents/4200000000003103/toolbox.json"
        AnalysisHelper.update_archive_result(archive_file, filepath, False, "av1", "This is not OK", self.ANALYSIS_COMPONENTS)
        
        filepath = "/1.3.0/switch/.overlays/parental_control.ovl"
        AnalysisHelper.update_archive_result(archive_file, filepath, False, "av1", "This is not OK", self.ANALYSIS_COMPONENTS)
        AnalysisHelper.update_archive_result(archive_file, filepath, False, "av2", "This is not OK", self.ANALYSIS_COMPONENTS)
        
        filepath = "/1.3.0/atmosphere/contents/4200000000003103/flags/boot2.flag"
        AnalysisHelper.update_archive_result(archive_file, filepath, False, "av1", "This is not OK", self.ANALYSIS_COMPONENTS)
        AnalysisHelper.update_archive_result(archive_file, filepath, False, "av2", "This is not OK", self.ANALYSIS_COMPONENTS)
        self.assertEqual(archive_file.get("status", None), FileStatus.FileInfected)


    def test_get_file_in_archive(self):
        files = deepcopy(self.STORAGE_FILES["files"])
        archive_mounted = "Test.iso"
        archive_file = files[archive_mounted]
        archive_content = deepcopy(self.ARCHIVE_CONTENT)
        archive_file["content"] = archive_content
        filepath = "/1.3.0/atmosphere/contents/4200000000003103/exefs.nsp"

        file_in_archive = AnalysisHelper.get_file_in_archive(archive_file, filepath)
        self.assertEqual(file_in_archive.get("name", None), "exefs.nsp")

    def test_get_file_progress(self):
        files = deepcopy(self.STORAGE_FILES["files"])
        file = files["Test.iso"]
        file["progress"] = 78.9

        self.assertEqual(AnalysisHelper.get_file_progress(files, "Test.iso"), 78.9)

    def test_get_archive_progress(self):
        files = deepcopy(self.STORAGE_FILES["files"])
        archive_mounted = "Test.iso"
        archive_file = files[archive_mounted]
        archive_content = deepcopy(self.ARCHIVE_CONTENT)
        archive_file["content"] = archive_content
        
        self.assertEqual(AnalysisHelper.get_archive_progress(archive_file), 0.0)

        filepath = "/1.3.0/atmosphere/contents/4200000000003103/toolbox.json"
        AnalysisHelper.update_archive_result(archive_file, filepath, False, "av2", "This is not OK", self.ANALYSIS_COMPONENTS)
        self.assertEqual(AnalysisHelper.get_archive_progress(archive_file), 12.5)
    
    def test_is_analysis_finished_file(self):
        files = deepcopy(self.STORAGE_FILES["files"])

        AnalysisHelper.update_file_result(files, ".DS_Store", True, "av1", "this is OK", self.ANALYSIS_COMPONENTS)
        self.assertFalse(AnalysisHelper.is_analysis_finished(files, ".DS_Store"))

        AnalysisHelper.update_file_result(files, ".DS_Store", True, "av2", "this is OK", self.ANALYSIS_COMPONENTS)
        self.assertTrue(AnalysisHelper.is_analysis_finished(files, ".DS_Store"))

    def test_is_analysis_finished_archive(self):
        files = deepcopy(self.STORAGE_FILES["files"])
        archive_mounted = "Test.iso"
        archive_file = files[archive_mounted]
        archive_content = deepcopy(self.ARCHIVE_CONTENT)
        archive_file["content"] = archive_content

        filepath = "/1.3.0/atmosphere/contents/4200000000003103/exefs.nsp"
        AnalysisHelper.update_archive_result(archive_file, filepath, True, "av1", "This is OK", self.ANALYSIS_COMPONENTS)
        AnalysisHelper.update_archive_result(archive_file, filepath, True, "av2", "This is OK", self.ANALYSIS_COMPONENTS)
        self.assertFalse(AnalysisHelper.is_analysis_finished(files, archive_mounted))
        
        filepath = "/1.3.0/atmosphere/contents/4200000000003103/toolbox.json"
        AnalysisHelper.update_archive_result(archive_file, filepath, True, "av1", "This is OK", self.ANALYSIS_COMPONENTS)
        AnalysisHelper.update_archive_result(archive_file, filepath, True, "av2", "This is OK", self.ANALYSIS_COMPONENTS)
        self.assertFalse(AnalysisHelper.is_analysis_finished(files, archive_mounted))

        filepath = "/1.3.0/switch/.overlays/parental_control.ovl"
        AnalysisHelper.update_archive_result(archive_file, filepath, True, "av1", "This is OK", self.ANALYSIS_COMPONENTS)
        AnalysisHelper.update_archive_result(archive_file, filepath, True, "av2", "This is OK", self.ANALYSIS_COMPONENTS)
        self.assertFalse(AnalysisHelper.is_analysis_finished(files, archive_mounted))

        filepath = "/1.3.0/atmosphere/contents/4200000000003103/flags/boot2.flag"
        AnalysisHelper.update_archive_result(archive_file, filepath, True, "av1", "This is OK", self.ANALYSIS_COMPONENTS)
        AnalysisHelper.update_archive_result(archive_file, filepath, True, "av2", "This is OK", self.ANALYSIS_COMPONENTS)
        self.assertTrue(AnalysisHelper.is_analysis_finished(files, archive_mounted))


    def test_calculate_archive_progress(self):
        files = deepcopy(self.STORAGE_FILES["files"])
        archive_mounted = "Test.iso"
        archive_file = files[archive_mounted]
        archive_content = deepcopy(self.ARCHIVE_CONTENT)
        archive_file["content"] = archive_content
        
        self.assertEqual(AnalysisHelper.calculate_archive_progress(archive_file), 0.0)

        filepath = "/1.3.0/atmosphere/contents/4200000000003103/exefs.nsp"
        file = archive_content.get(filepath, {})
        file["progress"] = 50.0
        self.assertEqual(AnalysisHelper.calculate_archive_progress(archive_file), 12.5)

        filepath = "/1.3.0/atmosphere/contents/4200000000003103/flags/boot2.flag"
        file = archive_content.get(filepath, {})
        file["progress"] = 50.0
        self.assertEqual(AnalysisHelper.calculate_archive_progress(archive_file), 25.0)

        filepath = "/1.3.0/atmosphere/contents/4200000000003103/toolbox.json"
        file = archive_content.get(filepath, {})
        file["progress"] = 50.0
        self.assertEqual(AnalysisHelper.calculate_archive_progress(archive_file), 37.5)

        filepath = "/1.3.0/switch/.overlays/parental_control.ovl"
        file = archive_content.get(filepath, {})
        file["progress"] = 50.0
        self.assertEqual(AnalysisHelper.calculate_archive_progress(archive_file), 50.0)

        filepath = "/1.3.0/atmosphere/contents/4200000000003103/exefs.nsp"
        file = archive_content.get(filepath, {})
        file["progress"] = 100.0
        self.assertEqual(AnalysisHelper.calculate_archive_progress(archive_file), 62.5)

        filepath = "/1.3.0/atmosphere/contents/4200000000003103/flags/boot2.flag"
        file = archive_content.get(filepath, {})
        file["progress"] = 100.0
        self.assertEqual(AnalysisHelper.calculate_archive_progress(archive_file), 75.0)

        filepath = "/1.3.0/atmosphere/contents/4200000000003103/toolbox.json"
        file = archive_content.get(filepath, {})
        file["progress"] = 100.0
        self.assertEqual(AnalysisHelper.calculate_archive_progress(archive_file), 87.5)

        filepath = "/1.3.0/switch/.overlays/parental_control.ovl"
        file = archive_content.get(filepath, {})
        file["progress"] = 100.0
        self.assertEqual(AnalysisHelper.calculate_archive_progress(archive_file), 100.0)

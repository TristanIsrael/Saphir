"""Unit tests for the viewer ViewerConstants (plan 13.4)."""

import unittest

from Viewer import ViewerConstants


class TestViewerConstants(unittest.TestCase):
    EXTENSION_LISTS = (
        "CALC_EXTENTIONS",
        "WRITER_EXTENSIONS",
        "IMPRESS_EXTENSIONS",
        "IMAGES_EXTENSIONS",
        "VIDEOS_EXTENSIONS",
        "AUDIO_EXTENSIONS",
    )

    def test_extension_lists_are_not_empty(self):
        for name in self.EXTENSION_LISTS:
            self.assertTrue(getattr(ViewerConstants, name), f"{name} is empty")

    def test_extension_patterns_are_wildcarded(self):
        all_patterns = [
            pattern
            for name in self.EXTENSION_LISTS
            for pattern in getattr(ViewerConstants, name)
        ]
        for pattern in all_patterns:
            self.assertTrue(pattern.startswith("*."), pattern)
            self.assertGreater(len(pattern), 3)

    def test_documented_formats_are_covered(self):
        self.assertIn("*.docx", ViewerConstants.WRITER_EXTENSIONS)
        self.assertIn("*.xlsx", ViewerConstants.CALC_EXTENTIONS)
        self.assertIn("*.pptx", ViewerConstants.IMPRESS_EXTENSIONS)
        self.assertIn("*.jpg", ViewerConstants.IMAGES_EXTENSIONS)
        self.assertIn("*.png", ViewerConstants.IMAGES_EXTENSIONS)
        self.assertIn("*.mp4", ViewerConstants.VIDEOS_EXTENSIONS)
        self.assertIn("*.mp3", ViewerConstants.AUDIO_EXTENSIONS)

    def test_files_filters_is_the_deduplicated_union(self):
        expected = set()
        for name in self.EXTENSION_LISTS:
            expected.update(getattr(ViewerConstants, name))
        self.assertEqual(set(ViewerConstants.FILES_FILTERS), expected)
        self.assertEqual(len(ViewerConstants.FILES_FILTERS), len(expected))


if __name__ == "__main__":
    unittest.main()

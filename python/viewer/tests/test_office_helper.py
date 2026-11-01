"""Unit tests for the viewer OfficeHelper (plan 13.4)."""

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from Viewer.office_helper import OfficeHelper


class TestConvertToPdf(unittest.TestCase):
    def test_devmode_uses_local_libreoffice(self):
        with (
            patch("Viewer.office_helper.subprocess") as mock_subprocess,
            patch("Viewer.office_helper.Logger"),
        ):
            mock_subprocess.run.return_value = MagicMock(returncode=0)
            result = OfficeHelper.convert_to_pdf("/folder/doc.docx")

        self.assertEqual(result, "/tmp/doc.pdf")
        cmd = mock_subprocess.run.call_args[0][0]
        self.assertIn("--headless", cmd)
        self.assertIn("--convert-to", cmd)
        self.assertIn("pdf", cmd)
        self.assertIn("/tmp/saphir/repository/folder/doc.docx", cmd)
        self.assertIn("/tmp", cmd)

    def test_production_uses_system_libreoffice(self):
        fake_dev = SimpleNamespace(
            DEVMODE=False,
            get_libreoffice_path=MagicMock(),
            get_repository_path=MagicMock(),
        )
        with (
            patch("Viewer.office_helper.subprocess") as mock_subprocess,
            patch("Viewer.office_helper.Logger"),
            patch("Viewer.office_helper.DevModeHelper", fake_dev),
        ):
            mock_subprocess.run.return_value = MagicMock(returncode=0)
            result = OfficeHelper.convert_to_pdf("/folder/doc.docx")

        self.assertEqual(result, "/tmp/doc.pdf")
        cmd = mock_subprocess.run.call_args[0][0]
        self.assertEqual(cmd[0], "soffice")
        self.assertIn("/mnt/storage/folder/doc.docx", cmd)

    def test_conversion_error_returns_empty_path(self):
        with (
            patch("Viewer.office_helper.subprocess") as mock_subprocess,
            patch("Viewer.office_helper.Logger") as mock_logger,
        ):
            mock_subprocess.run.return_value = MagicMock(returncode=1)
            result = OfficeHelper.convert_to_pdf("/folder/doc.docx")

        self.assertEqual(result, "")
        mock_logger.return_value.warn.assert_called_once()

    def test_pdf_output_path_strips_the_source_extension(self):
        with (
            patch("Viewer.office_helper.subprocess") as mock_subprocess,
            patch("Viewer.office_helper.Logger"),
        ):
            mock_subprocess.run.return_value = MagicMock(returncode=0)
            result = OfficeHelper.convert_to_pdf("/folder/report.presentation.pptx")

        self.assertEqual(result, "/tmp/report.presentation.pdf")


if __name__ == "__main__":
    unittest.main()

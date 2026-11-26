import os
import subprocess

from PySide6.QtCore import QObject
from safecor import Constants, Logger

from . import DevModeHelper


class OfficeHelper:
    """This class deals with the Office documents files"""

    @staticmethod
    def convert_to_pdf(disk: str, document_filepath: str) -> str:
        """Converts an office document to a PDF file

        The source document is read directly from the USB media
        (``f"{Constants.USB_MOUNT_POINT}/{disk}{document_filepath}"`` in
        production, the DEVMODE fake media tree otherwise).

        Returns the path of the file created
        """

        filename = os.path.basename(document_filepath)

        if DevModeHelper.DEVMODE:
            soffice_cmd = DevModeHelper.get_libreoffice_path()
            media_path = DevModeHelper.get_media_path()
        else:
            soffice_cmd = "soffice"
            media_path = Constants.USB_MOUNT_POINT

        cmd = [
            soffice_cmd,
            "--headless",
            "--convert-to",
            "pdf",
            f"{media_path}/{disk}{document_filepath}",
            "--outdir",
            "/tmp",
        ]

        # Convert the file to PDF using LibreOffice
        res = subprocess.run(cmd, check=False)

        if res.returncode > 0:
            Logger().warn(
                QObject.tr(
                    f"An error occured while converting the file {filename} to PDF"
                )
            )
            return ""
        else:
            Logger().info(
                QObject.tr(f"Succesfully converted the file {filename} to PDF")
            )

        filename_without_ext = os.path.splitext(filename)[0]
        return f"/tmp/{filename_without_ext}.pdf"

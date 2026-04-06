import os
import subprocess
from PySide6.QtCore import QObject
from safecor import Logger
from . import DevModeHelper

class OfficeHelper():
    """ This class deals with the Office documents files """

    @staticmethod
    def convert_to_pdf(document_filepath:str) -> str:
        """ Converts an office document to a PDF file 
        
        Returns the path of the file created
        """

        filename = os.path.basename(document_filepath)

        if DevModeHelper.DEVMODE:
            soffice_cmd = DevModeHelper.get_libreoffice_path()
            repository_filepath = DevModeHelper.get_repository_path()
        else:
            soffice_cmd = "soffice"
            repository_filepath = "/mnt/storage"

        cmd = [ soffice_cmd, "--headless", "--convert-to", "pdf", repository_filepath + document_filepath, "--outdir", "/tmp" ]

        # Convert the file to PDF using LibreOffice
        res = subprocess.run(cmd, check=False)

        if res.returncode > 0:
            Logger().warn(QObject.tr(f"An error occured while converting the file {filename} to PDF"))
            return ""
        else:
            Logger().info(QObject.tr(f"Succesfully converted the file {filename} to PDF"))

        filename_without_ext = os.path.splitext(filename)[0]
        return f"/tmp/{filename_without_ext}.pdf"
